from __future__ import annotations

from datetime import datetime, timezone
from operator import add
from typing import Annotated, Any, TypedDict

from app.agent.tool_types import CustomerRecord, OrderRecord
from app.models import PolicyDecision
from app.policy.types import RefundPolicyResult, RefundReason


class ExecutionTraceEvent(TypedDict, total=False):
    """Safe execution event stored temporarily in graph state."""

    timestamp: str
    event_type: str
    graph_node: str
    tool_name: str | None
    execution_status: str
    retry_count: int
    decision: str | None
    rule_codes: list[str]
    input_summary: dict[str, Any] | None
    output_summary: dict[str, Any] | None
    error_message: str | None


class AgentState(TypedDict, total=False):
    """Shared state passed between LangGraph nodes."""

    session_id: str
    customer_id: str | None
    order_id: str | None
    user_message: str

    conversation_messages: Annotated[
        list[dict[str, str]],
        add,
    ]
    execution_trace: Annotated[
        list[ExecutionTraceEvent],
        add,
    ]

    requested_quantity: int | None
    refund_reason: RefundReason | None
    missing_fields: list[str]

    customer: CustomerRecord | None
    order: OrderRecord | None

    policy_version: str | None
    policy_rule_codes: list[str]
    policy_result: RefundPolicyResult | None
    refund_request_id: str | None

    final_decision: PolicyDecision | None
    final_response: str | None

    refund_reference: str | None
    human_review_case_id: str | None

    model_provider_name: str

    retry_count: int
    total_retry_count: int
    max_retries: int

    transient_error: bool
    last_failed_node: str | None
    error_code: str | None
    error_message: str | None

    simulate_transient_failure: bool
    simulated_failure_consumed: bool


def create_trace_event(
    *,
    event_type: str,
    graph_node: str,
    execution_status: str,
    retry_count: int = 0,
    tool_name: str | None = None,
    decision: str | None = None,
    rule_codes: list[str] | None = None,
    input_summary: dict[str, Any] | None = None,
    output_summary: dict[str, Any] | None = None,
    error_message: str | None = None,
) -> ExecutionTraceEvent:
    """Create a safe structured graph execution event."""

    return ExecutionTraceEvent(
        timestamp=datetime.now(timezone.utc).isoformat(),
        event_type=event_type,
        graph_node=graph_node,
        tool_name=tool_name,
        execution_status=execution_status,
        retry_count=retry_count,
        decision=decision,
        rule_codes=rule_codes or [],
        input_summary=input_summary,
        output_summary=output_summary,
        error_message=error_message,
    )