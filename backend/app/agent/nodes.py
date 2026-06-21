from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.agent.model_provider import (
    DeterministicModelProvider,
    FinalResponseContext,
    ModelProvider,
    ModelProviderError,
)
from app.agent.state import (
    AgentState,
    create_trace_event,
)
from app.agent.tool_types import (
    ToolErrorCode,
    ToolStatus,
)
from app.agent.tools import (
    create_human_review as create_human_review_tool,
    evaluate_refund_eligibility as evaluate_policy_tool,
    get_customer as get_customer_tool,
    get_order as get_order_tool,
    get_refund_policy as get_policy_tool,
    issue_refund as issue_refund_tool,
    record_refund_denial as record_denial_tool,
)
from app.models import (
    PolicyDecision,
    ProductCondition,
)
from app.policy.types import (
    CustomerPolicyData,
    OrderPolicyData,
    RefundReason,
    RefundRequestContext,
)


@dataclass(frozen=True)
class AgentToolset:
    """Injectable tool functions used by graph nodes."""

    get_customer: Callable[..., Any] = get_customer_tool
    get_order: Callable[..., Any] = get_order_tool
    get_refund_policy: Callable[..., Any] = get_policy_tool

    evaluate_refund_eligibility: Callable[
        ...,
        Any,
    ] = evaluate_policy_tool

    issue_refund: Callable[..., Any] = issue_refund_tool
    record_refund_denial: Callable[
        ...,
        Any,
    ] = record_denial_tool
    create_human_review: Callable[
        ...,
        Any,
    ] = create_human_review_tool


class RefundGraphNodes:
    """Collection of node functions used by the refund graph."""

    def __init__(
        self,
        *,
        session_factory: Callable[[], Session],
        model_provider: ModelProvider,
        toolset: AgentToolset,
    ) -> None:
        self.session_factory = session_factory
        self.model_provider = model_provider
        self.fallback_provider = (
            DeterministicModelProvider()
        )
        self.toolset = toolset

    @staticmethod
    def _clear_error() -> dict[str, Any]:
        return {
            "transient_error": False,
            "last_failed_node": None,
            "error_code": None,
            "error_message": None,
            "retry_count": 0,
        }

    @staticmethod
    def _failure_update(
        *,
        node_name: str,
        tool_name: str,
        error_code: ToolErrorCode | str | None,
        error_message: str | None,
        retry_count: int,
    ) -> dict[str, Any]:
        error_code_value = (
            error_code.value
            if isinstance(error_code, ToolErrorCode)
            else error_code
        )

        transient_error = (
            error_code == ToolErrorCode.DATABASE_ERROR
        )

        return {
            "transient_error": transient_error,
            "last_failed_node": (
                node_name if transient_error else None
            ),
            "error_code": error_code_value,
            "error_message": error_message,
            "execution_trace": [
                create_trace_event(
                    event_type="TOOL_FAILED",
                    graph_node=node_name,
                    tool_name=tool_name,
                    execution_status="FAILED",
                    retry_count=retry_count,
                    error_message=error_message,
                )
            ],
        }

    def understand_request(
        self,
        state: AgentState,
    ) -> dict[str, Any]:
        node_name = "understand_request"
        user_message = state.get(
            "user_message",
            "",
        ).strip()

        if not user_message:
            return {
                "error_code": "EMPTY_MESSAGE",
                "error_message": (
                    "A customer message is required."
                ),
                "transient_error": False,
                "execution_trace": [
                    create_trace_event(
                        event_type="INTENT_IDENTIFICATION_FAILED",
                        graph_node=node_name,
                        execution_status="FAILED",
                        error_message=(
                            "The customer message was empty."
                        ),
                    )
                ],
            }

        provider_name = self.model_provider.name
        trace_events = []

        try:
            parsed_request = (
                self.model_provider.parse_request(
                    user_message
                )
            )

        except ModelProviderError:
            parsed_request = (
                self.fallback_provider.parse_request(
                    user_message
                )
            )
            provider_name = self.fallback_provider.name

            trace_events.append(
                create_trace_event(
                    event_type="MODEL_FALLBACK_USED",
                    graph_node=node_name,
                    execution_status="SUCCEEDED",
                    error_message=(
                        "The configured model provider failed. "
                        "The deterministic development fallback "
                        "was used."
                    ),
                )
            )

        customer_id = state.get("customer_id")
        order_id = (
            parsed_request.order_id
            or state.get("order_id")
        )
        requested_quantity = (
            parsed_request.requested_quantity
            or state.get("requested_quantity")
        )
        refund_reason = (
            parsed_request.reason
            or state.get("refund_reason")
        )

        missing_fields: list[str] = []

        if not customer_id:
            missing_fields.append("customer_id")

        if not order_id:
            missing_fields.append("order_id")

        if refund_reason is None:
            missing_fields.append("refund_reason")

        trace_events.append(
            create_trace_event(
                event_type="INTENT_IDENTIFIED",
                graph_node=node_name,
                execution_status="SUCCEEDED",
                input_summary={
                    "message_received": True,
                },
                output_summary={
                    "customer_id_present": bool(
                        customer_id
                    ),
                    "order_id": order_id,
                    "requested_quantity": (
                        requested_quantity
                    ),
                    "refund_reason": (
                        refund_reason.value
                        if refund_reason
                        else None
                    ),
                    "missing_fields": missing_fields,
                    "provider": provider_name,
                },
            )
        )

        return {
            "order_id": order_id,
            "requested_quantity": requested_quantity,
            "refund_reason": refund_reason,
            "missing_fields": missing_fields,
            "model_provider_name": provider_name,
            "execution_trace": trace_events,
            **self._clear_error(),
        }

    def ask_customer(
        self,
        state: AgentState,
    ) -> dict[str, Any]:
        node_name = "ask_customer"
        missing_fields = state.get(
            "missing_fields",
            [],
        )

        field_labels = {
            "customer_id": "your customer identity",
            "order_id": "your order ID",
            "refund_reason": (
                "the reason for the refund"
            ),
            "requested_quantity": (
                "the quantity you want to return"
            ),
        }

        readable_fields = [
            field_labels.get(field, field)
            for field in missing_fields
        ]

        if not readable_fields:
            response = (
                "Please provide the missing refund-request "
                "information."
            )
        elif len(readable_fields) == 1:
            response = (
                f"Please provide {readable_fields[0]} "
                "so I can continue."
            )
        else:
            response = (
                "Please provide "
                + ", ".join(readable_fields[:-1])
                + f" and {readable_fields[-1]} "
                "so I can continue."
            )

        return {
            "final_response": response,
            "conversation_messages": [
                {
                    "role": "assistant",
                    "content": response,
                }
            ],
            "execution_trace": [
                create_trace_event(
                    event_type="MISSING_INFORMATION",
                    graph_node=node_name,
                    execution_status="COMPLETED",
                    output_summary={
                        "missing_fields": missing_fields,
                    },
                )
            ],
        }

    def fetch_customer(
        self,
        state: AgentState,
    ) -> dict[str, Any]:
        node_name = "fetch_customer"

        if (
            state.get(
                "simulate_transient_failure",
                False,
            )
            and not state.get(
                "simulated_failure_consumed",
                False,
            )
        ):
            return {
                "simulated_failure_consumed": True,
                "transient_error": True,
                "last_failed_node": node_name,
                "error_code": (
                    "SIMULATED_TRANSIENT_CRM_FAILURE"
                ),
                "error_message": (
                    "A development-only transient CRM "
                    "failure was simulated."
                ),
                "execution_trace": [
                    create_trace_event(
                        event_type="TOOL_FAILED",
                        graph_node=node_name,
                        tool_name="get_customer",
                        execution_status="FAILED",
                        retry_count=state.get(
                            "retry_count",
                            0,
                        ),
                        error_message=(
                            "Simulated transient CRM failure."
                        ),
                    )
                ],
            }

        with self.session_factory() as database_session:
            result = self.toolset.get_customer(
                database_session,
                customer_id=state.get("customer_id"),
            )

        if result.status == ToolStatus.ERROR:
            return self._failure_update(
                node_name=node_name,
                tool_name="get_customer",
                error_code=result.error_code,
                error_message=result.error_message,
                retry_count=state.get(
                    "retry_count",
                    0,
                ),
            )

        return {
            "customer": result.customer,
            "execution_trace": [
                create_trace_event(
                    event_type="TOOL_SUCCEEDED",
                    graph_node=node_name,
                    tool_name="get_customer",
                    execution_status="SUCCEEDED",
                    retry_count=state.get(
                        "retry_count",
                        0,
                    ),
                    output_summary={
                        "customer_found": True,
                        "customer_id": (
                            result.customer.customer_id
                            if result.customer
                            else None
                        ),
                    },
                )
            ],
            **self._clear_error(),
        }

    def fetch_order(
        self,
        state: AgentState,
    ) -> dict[str, Any]:
        node_name = "fetch_order"

        with self.session_factory() as database_session:
            result = self.toolset.get_order(
                database_session,
                order_id=state.get("order_id") or "",
                customer_id=(
                    state.get("customer_id") or ""
                ),
            )

        if result.status == ToolStatus.ERROR:
            return self._failure_update(
                node_name=node_name,
                tool_name="get_order",
                error_code=result.error_code,
                error_message=result.error_message,
                retry_count=state.get(
                    "retry_count",
                    0,
                ),
            )

        requested_quantity = state.get(
            "requested_quantity"
        )
        missing_fields: list[str] = []

        if (
            requested_quantity is None
            and result.order is not None
        ):
            if result.order.quantity == 1:
                requested_quantity = 1
            else:
                missing_fields.append(
                    "requested_quantity"
                )

        return {
            "order": result.order,
            "requested_quantity": requested_quantity,
            "missing_fields": missing_fields,
            "execution_trace": [
                create_trace_event(
                    event_type="TOOL_SUCCEEDED",
                    graph_node=node_name,
                    tool_name="get_order",
                    execution_status="SUCCEEDED",
                    retry_count=state.get(
                        "retry_count",
                        0,
                    ),
                    output_summary={
                        "order_found": True,
                        "order_id": (
                            result.order.order_id
                            if result.order
                            else None
                        ),
                        "ownership_verified": True,
                        "missing_fields": missing_fields,
                    },
                )
            ],
            **self._clear_error(),
        }

    def load_policy(
        self,
        state: AgentState,
    ) -> dict[str, Any]:
        node_name = "load_policy"
        result = self.toolset.get_refund_policy()

        if result.status == ToolStatus.ERROR:
            return self._failure_update(
                node_name=node_name,
                tool_name="get_refund_policy",
                error_code=result.error_code,
                error_message=result.error_message,
                retry_count=state.get(
                    "retry_count",
                    0,
                ),
            )

        return {
            "policy_version": result.policy_version,
            "policy_rule_codes": result.rule_codes,
            "execution_trace": [
                create_trace_event(
                    event_type="TOOL_SUCCEEDED",
                    graph_node=node_name,
                    tool_name="get_refund_policy",
                    execution_status="SUCCEEDED",
                    output_summary={
                        "policy_version": (
                            result.policy_version
                        ),
                        "rule_count": len(
                            result.rule_codes
                        ),
                    },
                )
            ],
            **self._clear_error(),
        }

    def evaluate_refund_policy(
        self,
        state: AgentState,
    ) -> dict[str, Any]:
        node_name = "evaluate_refund_policy"

        customer = state.get("customer")
        order = state.get("order")
        refund_reason = state.get("refund_reason")
        requested_quantity = state.get(
            "requested_quantity"
        )

        if (
            customer is None
            or order is None
            or refund_reason is None
            or requested_quantity is None
        ):
            return {
                "error_code": "POLICY_INPUT_MISSING",
                "error_message": (
                    "Verified policy input is missing."
                ),
                "transient_error": False,
                "execution_trace": [
                    create_trace_event(
                        event_type="POLICY_EVALUATION_FAILED",
                        graph_node=node_name,
                        execution_status="FAILED",
                        error_message=(
                            "Verified policy input was missing."
                        ),
                    )
                ],
            }

        expected_conditions = {
            RefundReason.DAMAGED: (
                ProductCondition.DAMAGED
            ),
            RefundReason.DEFECTIVE: (
                ProductCondition.DEFECTIVE
            ),
            RefundReason.INCORRECT_ITEM: (
                ProductCondition.INCORRECT_ITEM
            ),
        }

        expected_condition = expected_conditions.get(
            refund_reason
        )

        issue_verified = (
            expected_condition is not None
            and order.product_condition
            == expected_condition
        )

        request_context = RefundRequestContext(
            customer_id=customer.customer_id,
            order_id=order.order_id,
            requested_quantity=requested_quantity,
            reason=refund_reason,
            identity_verified=True,
            ownership_verified=True,
            required_details_verified=True,
            issue_verified=issue_verified,
        )

        with self.session_factory() as database_session:
            result = (
                self.toolset
                .evaluate_refund_eligibility(
                    database_session,
                    customer=(
                        CustomerPolicyData.model_validate(
                            customer
                        )
                    ),
                    order=(
                        OrderPolicyData.model_validate(
                            order
                        )
                    ),
                    request_context=request_context,
                    session_id=state.get("session_id"),
                )
            )

        if result.status == ToolStatus.ERROR:
            return self._failure_update(
                node_name=node_name,
                tool_name=(
                    "evaluate_refund_eligibility"
                ),
                error_code=result.error_code,
                error_message=result.error_message,
                retry_count=state.get(
                    "retry_count",
                    0,
                ),
            )

        policy_result = result.policy_result

        return {
            "refund_request_id": (
                result.refund_request_id
            ),
            "policy_result": policy_result,
            "execution_trace": [
                create_trace_event(
                    event_type="POLICY_EVALUATED",
                    graph_node=node_name,
                    tool_name=(
                        "evaluate_refund_eligibility"
                    ),
                    execution_status="SUCCEEDED",
                    decision=(
                        policy_result.decision.value
                        if policy_result
                        else None
                    ),
                    rule_codes=(
                        policy_result.rule_codes
                        if policy_result
                        else []
                    ),
                    output_summary={
                        "refund_request_id": (
                            result.refund_request_id
                        ),
                        "refundable_amount": (
                            str(
                                policy_result
                                .refundable_amount
                            )
                            if policy_result
                            else None
                        ),
                    },
                )
            ],
            **self._clear_error(),
        }

    @staticmethod
    def _create_idempotency_key(
        state: AgentState,
    ) -> str:
        raw_value = (
            f"{state.get('session_id', '')}:"
            f"{state.get('refund_request_id', '')}:"
            f"{state.get('order_id', '')}"
        )

        digest = sha256(
            raw_value.encode("utf-8")
        ).hexdigest()

        return f"refund-{digest}"

    def execute_refund(
        self,
        state: AgentState,
    ) -> dict[str, Any]:
        node_name = "execute_refund"
        policy_result = state.get("policy_result")

        if (
            policy_result is None
            or policy_result.decision
            != PolicyDecision.APPROVED
        ):
            return {
                "error_code": "APPROVAL_REQUIRED",
                "error_message": (
                    "The policy result is not APPROVED."
                ),
                "transient_error": False,
            }

        with self.session_factory() as database_session:
            result = self.toolset.issue_refund(
                database_session,
                order_id=state.get("order_id") or "",
                amount=(
                    policy_result.refundable_amount
                ),
                idempotency_key=(
                    self._create_idempotency_key(
                        state
                    )
                ),
            )

        if result.status == ToolStatus.ERROR:
            return self._failure_update(
                node_name=node_name,
                tool_name="issue_refund",
                error_code=result.error_code,
                error_message=result.error_message,
                retry_count=state.get(
                    "retry_count",
                    0,
                ),
            )

        return {
            "final_decision": (
                PolicyDecision.APPROVED
            ),
            "refund_reference": (
                result.refund_reference
            ),
            "execution_trace": [
                create_trace_event(
                    event_type="REFUND_APPROVED",
                    graph_node=node_name,
                    tool_name="issue_refund",
                    execution_status="SUCCEEDED",
                    decision="APPROVED",
                    rule_codes=(
                        policy_result.rule_codes
                    ),
                    output_summary={
                        "order_id": result.order_id,
                        "amount": str(result.amount),
                        "refund_reference": (
                            result.refund_reference
                        ),
                        "idempotent_replay": (
                            result.idempotent_replay
                        ),
                    },
                )
            ],
            **self._clear_error(),
        }

    def record_denial(
        self,
        state: AgentState,
    ) -> dict[str, Any]:
        node_name = "record_denial"
        policy_result = state.get("policy_result")

        if (
            policy_result is None
            or policy_result.decision
            != PolicyDecision.DENIED
        ):
            return {
                "error_code": "DENIAL_REQUIRED",
                "error_message": (
                    "The policy result is not DENIED."
                ),
                "transient_error": False,
            }

        denial_reason = " ".join(
            policy_result.reasons
        )

        with self.session_factory() as database_session:
            result = self.toolset.record_refund_denial(
                database_session,
                order_id=state.get("order_id") or "",
                rule_codes=policy_result.rule_codes,
                reason=denial_reason,
            )

        if result.status == ToolStatus.ERROR:
            return self._failure_update(
                node_name=node_name,
                tool_name="record_refund_denial",
                error_code=result.error_code,
                error_message=result.error_message,
                retry_count=state.get(
                    "retry_count",
                    0,
                ),
            )

        return {
            "final_decision": PolicyDecision.DENIED,
            "execution_trace": [
                create_trace_event(
                    event_type="REFUND_DENIED",
                    graph_node=node_name,
                    tool_name="record_refund_denial",
                    execution_status="SUCCEEDED",
                    decision="DENIED",
                    rule_codes=result.rule_codes,
                    output_summary={
                        "order_id": result.order_id,
                    },
                )
            ],
            **self._clear_error(),
        }

    def create_human_review(
        self,
        state: AgentState,
    ) -> dict[str, Any]:
        node_name = "create_human_review"
        policy_result = state.get("policy_result")

        if (
            policy_result is None
            or policy_result.decision
            != PolicyDecision.ESCALATED
        ):
            return {
                "error_code": "ESCALATION_REQUIRED",
                "error_message": (
                    "The policy result is not ESCALATED."
                ),
                "transient_error": False,
            }

        review_reason = " ".join(
            policy_result.reasons
        )

        with self.session_factory() as database_session:
            result = self.toolset.create_human_review(
                database_session,
                order_id=state.get("order_id") or "",
                reason=review_reason,
            )

        if result.status == ToolStatus.ERROR:
            return self._failure_update(
                node_name=node_name,
                tool_name="create_human_review",
                error_code=result.error_code,
                error_message=result.error_message,
                retry_count=state.get(
                    "retry_count",
                    0,
                ),
            )

        return {
            "final_decision": (
                PolicyDecision.ESCALATED
            ),
            "human_review_case_id": result.case_id,
            "execution_trace": [
                create_trace_event(
                    event_type="HUMAN_REVIEW_CREATED",
                    graph_node=node_name,
                    tool_name="create_human_review",
                    execution_status="SUCCEEDED",
                    decision="ESCALATED",
                    rule_codes=(
                        policy_result.rule_codes
                    ),
                    output_summary={
                        "order_id": result.order_id,
                        "case_id": result.case_id,
                        "idempotent_replay": (
                            result.idempotent_replay
                        ),
                    },
                )
            ],
            **self._clear_error(),
        }

    def retry_tool(
        self,
        state: AgentState,
    ) -> dict[str, Any]:
        new_retry_count = (
            state.get("retry_count", 0) + 1
        )
        total_retry_count = (
            state.get("total_retry_count", 0) + 1
        )

        return {
            "retry_count": new_retry_count,
            "total_retry_count": total_retry_count,
            "execution_trace": [
                create_trace_event(
                    event_type="RETRY_STARTED",
                    graph_node="retry_tool",
                    execution_status="RUNNING",
                    retry_count=new_retry_count,
                    output_summary={
                        "retrying_node": state.get(
                            "last_failed_node"
                        ),
                    },
                )
            ],
        }

    def generate_final_response(
        self,
        state: AgentState,
    ) -> dict[str, Any]:
        node_name = "generate_final_response"

        if state.get("error_code"):
            response = (
                "I’m sorry, but I could not complete the refund "
                "request because "
                f"{state.get('error_message') or 'a backend error occurred'}. "
                "No refund has been issued."
            )

            return {
                "final_response": response,
                "conversation_messages": [
                    {
                        "role": "assistant",
                        "content": response,
                    }
                ],
                "execution_trace": [
                    create_trace_event(
                        event_type="RESPONSE_GENERATED",
                        graph_node=node_name,
                        execution_status="COMPLETED",
                        error_message=state.get(
                            "error_message"
                        ),
                    )
                ],
            }

        policy_result = state.get("policy_result")
        final_decision = state.get(
            "final_decision"
        )
        order = state.get("order")

        if (
            policy_result is None
            or final_decision is None
            or order is None
        ):
            response = (
                "I’m sorry, but the refund request could not "
                "be completed. No refund has been issued."
            )

        else:
            context = FinalResponseContext(
                decision=final_decision,
                order_id=order.order_id,
                refundable_amount=(
                    policy_result.refundable_amount
                ),
                rule_codes=policy_result.rule_codes,
                reasons=policy_result.reasons,
                payment_method=(
                    policy_result.refund_method
                ),
                refund_reference=state.get(
                    "refund_reference"
                ),
                human_review_case_id=state.get(
                    "human_review_case_id"
                ),
            )

            try:
                response = (
                    self.model_provider
                    .generate_final_response(context)
                )
                provider_name = (
                    self.model_provider.name
                )

            except ModelProviderError:
                response = (
                    self.fallback_provider
                    .generate_final_response(context)
                )
                provider_name = (
                    self.fallback_provider.name
                )

            state_provider_name = provider_name

            return {
                "final_response": response,
                "model_provider_name": (
                    state_provider_name
                ),
                "conversation_messages": [
                    {
                        "role": "assistant",
                        "content": response,
                    }
                ],
                "execution_trace": [
                    create_trace_event(
                        event_type="RESPONSE_GENERATED",
                        graph_node=node_name,
                        execution_status="COMPLETED",
                        decision=final_decision.value,
                        rule_codes=(
                            policy_result.rule_codes
                        ),
                        output_summary={
                            "provider": provider_name,
                        },
                    )
                ],
            }

        return {
            "final_response": response,
            "conversation_messages": [
                {
                    "role": "assistant",
                    "content": response,
                }
            ],
            "execution_trace": [
                create_trace_event(
                    event_type="RESPONSE_GENERATED",
                    graph_node=node_name,
                    execution_status="COMPLETED",
                )
            ],
        }