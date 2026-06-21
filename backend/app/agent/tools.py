from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.agent.tool_types import (
    CustomerLookupResult,
    CustomerRecord,
    DenialRecordResult,
    HumanReviewCreationResult,
    OrderLookupResult,
    OrderRecord,
    PolicyEvaluationToolResult,
    RefundExecutionResult,
    RefundPolicyDocumentResult,
    ToolErrorCode,
    ToolStatus,
)
from app.models import (
    Customer,
    HumanReviewCase,
    Order,
    PolicyDecision,
    RefundRequest,
    RefundStatus,
    ReviewStatus,
)
from app.policy.engine import evaluate_refund_policy
from app.policy.types import (
    CustomerPolicyData,
    OrderPolicyData,
    POLICY_VERSION,
    RefundRequestContext,
)


POLICY_FILE_PATH = (
    Path(__file__).resolve().parent.parent
    / "policy"
    / "refund_policy.md"
)

POLICY_RULE_CODES = [
    f"RP-{rule_number:03d}"
    for rule_number in range(1, 13)
]

MONEY_QUANTUM = Decimal("0.01")


def clean_text(value: str | None) -> str | None:
    """Trim optional string input."""

    if value is None:
        return None

    cleaned_value = value.strip()

    return cleaned_value or None


def normalize_money(
    amount: Decimal | str | int | float,
) -> Decimal | None:
    """Convert an external amount into safe two-decimal currency."""

    try:
        normalized_amount = Decimal(str(amount)).quantize(
            MONEY_QUANTUM
        )
    except (InvalidOperation, ValueError):
        return None

    if normalized_amount <= Decimal("0.00"):
        return None

    return normalized_amount


def generate_identifier(prefix: str) -> str:
    """Generate a readable unique identifier."""

    return (
        f"{prefix}-"
        f"{uuid4().hex[:12].upper()}"
    )


def get_customer(
    database_session: Session,
    *,
    customer_id: str | None = None,
    email: str | None = None,
) -> CustomerLookupResult:
    """
    Return a CRM customer by ID or email.

    When both identifiers are supplied, they must refer to the
    same customer.
    """

    normalized_customer_id = clean_text(customer_id)
    normalized_email = clean_text(email)

    if normalized_email is not None:
        normalized_email = normalized_email.lower()

    if (
        normalized_customer_id is None
        and normalized_email is None
    ):
        return CustomerLookupResult(
            status=ToolStatus.ERROR,
            error_code=ToolErrorCode.INVALID_INPUT,
            error_message=(
                "A customer ID or email address is required."
            ),
        )

    try:
        customer: Customer | None = None

        if normalized_customer_id is not None:
            customer = database_session.get(
                Customer,
                normalized_customer_id,
            )

            if customer is None:
                return CustomerLookupResult(
                    status=ToolStatus.ERROR,
                    error_code=(
                        ToolErrorCode.CUSTOMER_NOT_FOUND
                    ),
                    error_message=(
                        "The requested customer could not be found."
                    ),
                )

            if (
                normalized_email is not None
                and customer.email.lower()
                != normalized_email
            ):
                return CustomerLookupResult(
                    status=ToolStatus.ERROR,
                    error_code=(
                        ToolErrorCode
                        .CUSTOMER_IDENTIFIER_MISMATCH
                    ),
                    error_message=(
                        "The supplied customer ID and email do "
                        "not identify the same CRM profile."
                    ),
                )

        elif normalized_email is not None:
            customer = database_session.scalar(
                select(Customer).where(
                    func.lower(Customer.email)
                    == normalized_email
                )
            )

            if customer is None:
                return CustomerLookupResult(
                    status=ToolStatus.ERROR,
                    error_code=(
                        ToolErrorCode.CUSTOMER_NOT_FOUND
                    ),
                    error_message=(
                        "The requested customer could not be found."
                    ),
                )

        return CustomerLookupResult(
            status=ToolStatus.SUCCESS,
            customer=CustomerRecord.model_validate(
                customer
            ),
        )

    except SQLAlchemyError:
        return CustomerLookupResult(
            status=ToolStatus.ERROR,
            error_code=ToolErrorCode.DATABASE_ERROR,
            error_message=(
                "The customer database is temporarily unavailable."
            ),
        )


def get_order(
    database_session: Session,
    *,
    order_id: str,
    customer_id: str,
) -> OrderLookupResult:
    """
    Return an order only when it belongs to the supplied customer.

    Ownership failures do not reveal the identity of the actual
    order owner.
    """

    normalized_order_id = clean_text(order_id)
    normalized_customer_id = clean_text(customer_id)

    if (
        normalized_order_id is None
        or normalized_customer_id is None
    ):
        return OrderLookupResult(
            status=ToolStatus.ERROR,
            error_code=ToolErrorCode.INVALID_INPUT,
            error_message=(
                "Both order ID and customer ID are required."
            ),
        )

    try:
        order = database_session.get(
            Order,
            normalized_order_id,
        )

        if order is None:
            return OrderLookupResult(
                status=ToolStatus.ERROR,
                error_code=ToolErrorCode.ORDER_NOT_FOUND,
                error_message=(
                    "The requested order could not be found."
                ),
            )

        if order.customer_id != normalized_customer_id:
            return OrderLookupResult(
                status=ToolStatus.ERROR,
                error_code=(
                    ToolErrorCode.ORDER_OWNERSHIP_MISMATCH
                ),
                error_message=(
                    "The order could not be verified for the "
                    "selected customer."
                ),
            )

        return OrderLookupResult(
            status=ToolStatus.SUCCESS,
            order=OrderRecord.model_validate(order),
        )

    except SQLAlchemyError:
        return OrderLookupResult(
            status=ToolStatus.ERROR,
            error_code=ToolErrorCode.DATABASE_ERROR,
            error_message=(
                "The order database is temporarily unavailable."
            ),
        )


def get_refund_policy() -> RefundPolicyDocumentResult:
    """Return refund-policy version, rule codes and Markdown."""

    try:
        markdown_content = POLICY_FILE_PATH.read_text(
            encoding="utf-8"
        )
    except OSError:
        return RefundPolicyDocumentResult(
            status=ToolStatus.ERROR,
            error_code=(
                ToolErrorCode.POLICY_FILE_UNAVAILABLE
            ),
            error_message=(
                "The refund-policy document is unavailable."
            ),
        )

    if not markdown_content.strip():
        return RefundPolicyDocumentResult(
            status=ToolStatus.ERROR,
            error_code=(
                ToolErrorCode.POLICY_FILE_UNAVAILABLE
            ),
            error_message=(
                "The refund-policy document is empty."
            ),
        )

    return RefundPolicyDocumentResult(
        status=ToolStatus.SUCCESS,
        policy_version=POLICY_VERSION,
        rule_codes=POLICY_RULE_CODES,
        markdown=markdown_content,
    )


def evaluate_refund_eligibility(
    database_session: Session,
    *,
    customer: CustomerPolicyData,
    order: OrderPolicyData,
    request_context: RefundRequestContext,
    session_id: str | None = None,
) -> PolicyEvaluationToolResult:
    """
    Evaluate policy using authoritative database records.

    The result is stored as a RefundRequest before any refund,
    denial or escalation action can occur.
    """

    if (
        request_context.customer_id
        != customer.customer_id
        or request_context.order_id != order.order_id
    ):
        return PolicyEvaluationToolResult(
            status=ToolStatus.ERROR,
            error_code=ToolErrorCode.INVALID_INPUT,
            error_message=(
                "The policy request identifiers do not match "
                "the supplied customer and order."
            ),
        )

    try:
        database_customer = database_session.get(
            Customer,
            customer.customer_id,
        )
        database_order = database_session.get(
            Order,
            order.order_id,
        )

        if database_customer is None:
            return PolicyEvaluationToolResult(
                status=ToolStatus.ERROR,
                error_code=(
                    ToolErrorCode.CUSTOMER_NOT_FOUND
                ),
                error_message=(
                    "The requested customer could not be found."
                ),
            )

        if database_order is None:
            return PolicyEvaluationToolResult(
                status=ToolStatus.ERROR,
                error_code=ToolErrorCode.ORDER_NOT_FOUND,
                error_message=(
                    "The requested order could not be found."
                ),
            )

        if (
            database_order.customer_id
            != database_customer.customer_id
        ):
            return PolicyEvaluationToolResult(
                status=ToolStatus.ERROR,
                error_code=(
                    ToolErrorCode.ORDER_OWNERSHIP_MISMATCH
                ),
                error_message=(
                    "The order could not be verified for the "
                    "selected customer."
                ),
            )

        authoritative_customer = (
            CustomerPolicyData.model_validate(
                database_customer
            )
        )
        authoritative_order = (
            OrderPolicyData.model_validate(
                database_order
            )
        )

        policy_result = evaluate_refund_policy(
            authoritative_customer,
            authoritative_order,
            request_context,
        )

        refund_request = RefundRequest(
            refund_request_id=generate_identifier("RREQ"),
            session_id=clean_text(session_id),
            customer_id=database_customer.customer_id,
            order_id=database_order.order_id,
            request_reason=request_context.reason.value,
            requested_quantity=(
                request_context.requested_quantity
            ),
            decision=policy_result.decision,
            rule_codes=list(policy_result.rule_codes),
            reasons=list(policy_result.reasons),
            refundable_amount=(
                policy_result.refundable_amount
            ),
            human_review_required=(
                policy_result.human_review_required
            ),
        )

        database_session.add(refund_request)
        database_session.commit()
        database_session.refresh(refund_request)

        return PolicyEvaluationToolResult(
            status=ToolStatus.SUCCESS,
            refund_request_id=(
                refund_request.refund_request_id
            ),
            policy_result=policy_result,
        )

    except SQLAlchemyError:
        database_session.rollback()

        return PolicyEvaluationToolResult(
            status=ToolStatus.ERROR,
            error_code=ToolErrorCode.DATABASE_ERROR,
            error_message=(
                "The refund evaluation could not be saved."
            ),
        )


def latest_refund_request(
    database_session: Session,
    *,
    order_id: str,
    decision: PolicyDecision,
    unexecuted_only: bool = False,
) -> RefundRequest | None:
    """Return the latest matching request for an order."""

    statement = (
        select(RefundRequest)
        .where(
            RefundRequest.order_id == order_id,
            RefundRequest.decision == decision,
        )
        .order_by(
            RefundRequest.created_at.desc(),
            RefundRequest.refund_request_id.desc(),
        )
    )

    if unexecuted_only:
        statement = statement.where(
            RefundRequest.refund_reference.is_(None)
        )

    return database_session.scalar(statement)


def issue_refund(
    database_session: Session,
    *,
    order_id: str,
    amount: Decimal | str | int | float,
    idempotency_key: str,
) -> RefundExecutionResult:
    """
    Execute a refund only after an APPROVED policy result.

    Reusing the same idempotency key returns the original result
    without issuing a second refund.
    """

    normalized_order_id = clean_text(order_id)
    normalized_idempotency_key = clean_text(
        idempotency_key
    )
    normalized_amount = normalize_money(amount)

    if (
        normalized_order_id is None
        or normalized_idempotency_key is None
        or normalized_amount is None
    ):
        return RefundExecutionResult(
            status=ToolStatus.ERROR,
            error_code=ToolErrorCode.INVALID_INPUT,
            error_message=(
                "A valid order ID, positive amount and "
                "idempotency key are required."
            ),
        )

    try:
        existing_idempotent_request = (
            database_session.scalar(
                select(RefundRequest).where(
                    RefundRequest.idempotency_key
                    == normalized_idempotency_key
                )
            )
        )

        if existing_idempotent_request is not None:
            if (
                existing_idempotent_request.order_id
                != normalized_order_id
                or existing_idempotent_request
                .refundable_amount
                != normalized_amount
            ):
                return RefundExecutionResult(
                    status=ToolStatus.ERROR,
                    error_code=(
                        ToolErrorCode.IDEMPOTENCY_CONFLICT
                    ),
                    error_message=(
                        "The idempotency key was already used "
                        "for a different refund operation."
                    ),
                )

            if (
                existing_idempotent_request
                .refund_reference
                is not None
            ):
                existing_order = database_session.get(
                    Order,
                    normalized_order_id,
                )

                if existing_order is None:
                    return RefundExecutionResult(
                        status=ToolStatus.ERROR,
                        error_code=(
                            ToolErrorCode.ORDER_NOT_FOUND
                        ),
                        error_message=(
                            "The requested order could not "
                            "be found."
                        ),
                    )

                return RefundExecutionResult(
                    status=ToolStatus.SUCCESS,
                    refund_request_id=(
                        existing_idempotent_request
                        .refund_request_id
                    ),
                    order_id=existing_order.order_id,
                    refund_reference=(
                        existing_idempotent_request
                        .refund_reference
                    ),
                    amount=(
                        existing_idempotent_request
                        .refundable_amount
                    ),
                    payment_method=(
                        existing_order.payment_method
                    ),
                    refund_status=(
                        existing_order.refund_status
                    ),
                    idempotent_replay=True,
                )

        order = database_session.get(
            Order,
            normalized_order_id,
        )

        if order is None:
            return RefundExecutionResult(
                status=ToolStatus.ERROR,
                error_code=ToolErrorCode.ORDER_NOT_FOUND,
                error_message=(
                    "The requested order could not be found."
                ),
            )

        if order.refund_status == RefundStatus.FULL:
            return RefundExecutionResult(
                status=ToolStatus.ERROR,
                error_code=ToolErrorCode.ALREADY_REFUNDED,
                error_message=(
                    "The order has already been fully refunded."
                ),
            )

        approved_request = latest_refund_request(
            database_session,
            order_id=normalized_order_id,
            decision=PolicyDecision.APPROVED,
            unexecuted_only=True,
        )

        if approved_request is None:
            return RefundExecutionResult(
                status=ToolStatus.ERROR,
                error_code=ToolErrorCode.APPROVAL_REQUIRED,
                error_message=(
                    "A stored APPROVED policy result is required "
                    "before a refund can be issued."
                ),
            )

        if (
            approved_request.refundable_amount
            != normalized_amount
        ):
            return RefundExecutionResult(
                status=ToolStatus.ERROR,
                error_code=ToolErrorCode.AMOUNT_MISMATCH,
                error_message=(
                    "The requested refund amount does not match "
                    "the authoritative policy result."
                ),
            )

        if (
            approved_request.idempotency_key is not None
            and approved_request.idempotency_key
            != normalized_idempotency_key
        ):
            return RefundExecutionResult(
                status=ToolStatus.ERROR,
                error_code=(
                    ToolErrorCode.IDEMPOTENCY_CONFLICT
                ),
                error_message=(
                    "The approved refund already has a different "
                    "idempotency key."
                ),
            )

        previously_refunded_quantity = (
            database_session.scalar(
                select(
                    func.coalesce(
                        func.sum(
                            RefundRequest
                            .requested_quantity
                        ),
                        0,
                    )
                ).where(
                    RefundRequest.order_id
                    == normalized_order_id,
                    RefundRequest.refund_reference
                    .is_not(None),
                )
            )
            or 0
        )

        total_refunded_quantity = (
            int(previously_refunded_quantity)
            + approved_request.requested_quantity
        )

        new_refund_status = (
            RefundStatus.FULL
            if total_refunded_quantity >= order.quantity
            else RefundStatus.PARTIAL
        )

        refund_reference = generate_identifier("RFND")

        approved_request.idempotency_key = (
            normalized_idempotency_key
        )
        approved_request.refund_reference = (
            refund_reference
        )

        order.refund_status = new_refund_status

        customer = database_session.get(
            Customer,
            order.customer_id,
        )

        if customer is not None:
            customer.previous_refunds += 1

        database_session.commit()
        database_session.refresh(approved_request)
        database_session.refresh(order)

        return RefundExecutionResult(
            status=ToolStatus.SUCCESS,
            refund_request_id=(
                approved_request.refund_request_id
            ),
            order_id=order.order_id,
            refund_reference=refund_reference,
            amount=normalized_amount,
            payment_method=order.payment_method,
            refund_status=order.refund_status,
            idempotent_replay=False,
        )

    except IntegrityError:
        database_session.rollback()

        return RefundExecutionResult(
            status=ToolStatus.ERROR,
            error_code=(
                ToolErrorCode.IDEMPOTENCY_CONFLICT
            ),
            error_message=(
                "The refund operation conflicts with an "
                "existing idempotency key."
            ),
        )

    except SQLAlchemyError:
        database_session.rollback()

        return RefundExecutionResult(
            status=ToolStatus.ERROR,
            error_code=ToolErrorCode.DATABASE_ERROR,
            error_message=(
                "The refund operation could not be completed."
            ),
        )


def record_refund_denial(
    database_session: Session,
    *,
    order_id: str,
    rule_codes: list[str],
    reason: str,
) -> DenialRecordResult:
    """Store the final denial status for a denied request."""

    normalized_order_id = clean_text(order_id)
    normalized_reason = clean_text(reason)

    normalized_rule_codes = list(
        dict.fromkeys(
            rule_code.strip()
            for rule_code in rule_codes
            if rule_code.strip()
        )
    )

    if (
        normalized_order_id is None
        or normalized_reason is None
        or not normalized_rule_codes
    ):
        return DenialRecordResult(
            status=ToolStatus.ERROR,
            error_code=ToolErrorCode.INVALID_INPUT,
            error_message=(
                "Order ID, policy rule codes and denial reason "
                "are required."
            ),
        )

    try:
        order = database_session.get(
            Order,
            normalized_order_id,
        )

        if order is None:
            return DenialRecordResult(
                status=ToolStatus.ERROR,
                error_code=ToolErrorCode.ORDER_NOT_FOUND,
                error_message=(
                    "The requested order could not be found."
                ),
            )

        denied_request = latest_refund_request(
            database_session,
            order_id=normalized_order_id,
            decision=PolicyDecision.DENIED,
        )

        if denied_request is None:
            return DenialRecordResult(
                status=ToolStatus.ERROR,
                error_code=(
                    ToolErrorCode.DENIAL_RECORD_NOT_FOUND
                ),
                error_message=(
                    "A stored DENIED policy result is required "
                    "before recording the denial."
                ),
            )

        denied_request.rule_codes = (
            normalized_rule_codes
        )
        denied_request.reasons = [normalized_reason]

        order.refund_status = RefundStatus.DENIED

        database_session.commit()
        database_session.refresh(denied_request)
        database_session.refresh(order)

        return DenialRecordResult(
            status=ToolStatus.SUCCESS,
            refund_request_id=(
                denied_request.refund_request_id
            ),
            order_id=order.order_id,
            rule_codes=normalized_rule_codes,
            reason=normalized_reason,
            refund_status=order.refund_status,
        )

    except SQLAlchemyError:
        database_session.rollback()

        return DenialRecordResult(
            status=ToolStatus.ERROR,
            error_code=ToolErrorCode.DATABASE_ERROR,
            error_message=(
                "The refund denial could not be saved."
            ),
        )


def create_human_review(
    database_session: Session,
    *,
    order_id: str,
    reason: str,
) -> HumanReviewCreationResult:
    """Create one open review case for an escalated request."""

    normalized_order_id = clean_text(order_id)
    normalized_reason = clean_text(reason)

    if (
        normalized_order_id is None
        or normalized_reason is None
    ):
        return HumanReviewCreationResult(
            status=ToolStatus.ERROR,
            error_code=ToolErrorCode.INVALID_INPUT,
            error_message=(
                "Order ID and human-review reason are required."
            ),
        )

    try:
        order = database_session.get(
            Order,
            normalized_order_id,
        )

        if order is None:
            return HumanReviewCreationResult(
                status=ToolStatus.ERROR,
                error_code=ToolErrorCode.ORDER_NOT_FOUND,
                error_message=(
                    "The requested order could not be found."
                ),
            )

        escalated_request = latest_refund_request(
            database_session,
            order_id=normalized_order_id,
            decision=PolicyDecision.ESCALATED,
        )

        if escalated_request is None:
            return HumanReviewCreationResult(
                status=ToolStatus.ERROR,
                error_code=(
                    ToolErrorCode
                    .ESCALATION_RECORD_NOT_FOUND
                ),
                error_message=(
                    "A stored ESCALATED policy result is required "
                    "before creating human review."
                ),
            )

        existing_case = database_session.scalar(
            select(HumanReviewCase).where(
                HumanReviewCase.refund_request_id
                == escalated_request.refund_request_id,
                HumanReviewCase.status
                == ReviewStatus.OPEN,
            )
        )

        if existing_case is not None:
            return HumanReviewCreationResult(
                status=ToolStatus.SUCCESS,
                case_id=existing_case.case_id,
                refund_request_id=(
                    escalated_request.refund_request_id
                ),
                order_id=normalized_order_id,
                review_status=existing_case.status,
                idempotent_replay=True,
            )

        review_case = HumanReviewCase(
            case_id=generate_identifier("HRC"),
            refund_request_id=(
                escalated_request.refund_request_id
            ),
            customer_id=(
                escalated_request.customer_id
            ),
            order_id=normalized_order_id,
            reason=normalized_reason,
            status=ReviewStatus.OPEN,
        )

        database_session.add(review_case)
        order.refund_status = RefundStatus.HUMAN_REVIEW

        database_session.commit()
        database_session.refresh(review_case)
        database_session.refresh(order)

        return HumanReviewCreationResult(
            status=ToolStatus.SUCCESS,
            case_id=review_case.case_id,
            refund_request_id=(
                escalated_request.refund_request_id
            ),
            order_id=normalized_order_id,
            review_status=review_case.status,
            idempotent_replay=False,
        )

    except SQLAlchemyError:
        database_session.rollback()

        return HumanReviewCreationResult(
            status=ToolStatus.ERROR,
            error_code=ToolErrorCode.DATABASE_ERROR,
            error_message=(
                "The human-review case could not be created."
            ),
        )