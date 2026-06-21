from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agent.tool_types import (
    ToolErrorCode,
    ToolStatus,
)
from app.agent.tools import (
    create_human_review,
    evaluate_refund_eligibility,
    get_customer,
    get_order,
    get_refund_policy,
    issue_refund,
    record_refund_denial,
)
from app.models import (
    Customer,
    HumanReviewCase,
    MembershipTier,
    Order,
    OrderStatus,
    PolicyDecision,
    ProductCondition,
    RefundRequest,
    RefundStatus,
    ReviewStatus,
)
from app.policy.types import (
    CustomerPolicyData,
    OrderPolicyData,
    RefundReason,
    RefundRequestContext,
)


def add_customer_and_order(
    database_session: Session,
    *,
    customer_id: str = "CUST-TOOL-001",
    order_id: str = "ORD-TOOL-001",
    email: str = "tool.customer@example.com",
    item_price: Decimal = Decimal("100.00"),
    shipping_amount: Decimal = Decimal("10.00"),
    quantity: int = 1,
    final_sale: bool = False,
    fraud_review_flag: bool = False,
) -> tuple[Customer, Order]:
    customer = Customer(
        customer_id=customer_id,
        full_name="Tool Test Customer",
        email=email,
        phone="+1-202-555-0199",
        address_line="100 Test Avenue",
        city="Seattle",
        state="Washington",
        postal_code="98101",
        country="United States",
        membership_tier=MembershipTier.GOLD,
        account_created_at=(
            datetime.now(timezone.utc)
            - timedelta(days=365)
        ),
        fraud_review_flag=fraud_review_flag,
        total_orders=1,
        previous_refunds=0,
    )

    order = Order(
        order_id=order_id,
        customer_id=customer_id,
        product_name="Test Keyboard",
        product_category="ELECTRONICS",
        quantity=quantity,
        item_price=item_price,
        shipping_amount=shipping_amount,
        total_amount=(
            item_price * quantity
            + shipping_amount
        ),
        order_date=date.today() - timedelta(days=9),
        delivery_date=(
            date.today() - timedelta(days=5)
        ),
        order_status=OrderStatus.DELIVERED,
        product_condition=(
            ProductCondition.UNOPENED
        ),
        final_sale=final_sale,
        personalized=False,
        downloadable=False,
        hygiene_sensitive=False,
        payment_method="Visa ending in 4242",
        refund_status=RefundStatus.NONE,
    )

    database_session.add_all([customer, order])
    database_session.commit()

    return customer, order


def create_request_context(
    *,
    customer_id: str = "CUST-TOOL-001",
    order_id: str = "ORD-TOOL-001",
) -> RefundRequestContext:
    return RefundRequestContext(
        customer_id=customer_id,
        order_id=order_id,
        requested_quantity=1,
        reason=RefundReason.CHANGE_OF_MIND,
        request_date=date.today(),
        identity_verified=True,
        ownership_verified=True,
        required_details_verified=True,
        issue_verified=False,
    )


def evaluate_test_order(
    database_session: Session,
    customer: Customer,
    order: Order,
):
    return evaluate_refund_eligibility(
        database_session,
        customer=CustomerPolicyData.model_validate(
            customer
        ),
        order=OrderPolicyData.model_validate(order),
        request_context=create_request_context(
            customer_id=customer.customer_id,
            order_id=order.order_id,
        ),
    )


def test_get_customer_by_id(
    db_session: Session,
) -> None:
    customer, _ = add_customer_and_order(db_session)

    result = get_customer(
        db_session,
        customer_id=customer.customer_id,
    )

    assert result.status == ToolStatus.SUCCESS
    assert result.customer is not None
    assert (
        result.customer.customer_id
        == customer.customer_id
    )


def test_get_customer_by_email_is_case_insensitive(
    db_session: Session,
) -> None:
    customer, _ = add_customer_and_order(db_session)

    result = get_customer(
        db_session,
        email=customer.email.upper(),
    )

    assert result.status == ToolStatus.SUCCESS
    assert result.customer is not None
    assert result.customer.email == customer.email


def test_get_customer_requires_identifier(
    db_session: Session,
) -> None:
    result = get_customer(db_session)

    assert result.status == ToolStatus.ERROR
    assert (
        result.error_code
        == ToolErrorCode.INVALID_INPUT
    )


def test_get_order_verifies_valid_ownership(
    db_session: Session,
) -> None:
    customer, order = add_customer_and_order(db_session)

    result = get_order(
        db_session,
        order_id=order.order_id,
        customer_id=customer.customer_id,
    )

    assert result.status == ToolStatus.SUCCESS
    assert result.order is not None
    assert result.order.order_id == order.order_id


def test_get_order_rejects_ownership_mismatch(
    db_session: Session,
) -> None:
    _, order = add_customer_and_order(db_session)

    result = get_order(
        db_session,
        order_id=order.order_id,
        customer_id="CUST-DIFFERENT-999",
    )

    assert result.status == ToolStatus.ERROR
    assert (
        result.error_code
        == ToolErrorCode.ORDER_OWNERSHIP_MISMATCH
    )
    assert result.order is None
    assert "Tool Test Customer" not in (
        result.error_message or ""
    )


def test_get_refund_policy_returns_version_and_rules() -> None:
    result = get_refund_policy()

    assert result.status == ToolStatus.SUCCESS
    assert result.policy_version == "1.0"
    assert len(result.rule_codes) == 12
    assert "RP-001" in result.rule_codes
    assert "RP-012" in result.rule_codes
    assert result.markdown is not None
    assert "ResolveAI Refund Policy" in result.markdown


def test_evaluate_refund_eligibility_persists_approval(
    db_session: Session,
) -> None:
    customer, order = add_customer_and_order(db_session)

    result = evaluate_test_order(
        db_session,
        customer,
        order,
    )

    assert result.status == ToolStatus.SUCCESS
    assert result.policy_result is not None
    assert (
        result.policy_result.decision
        == PolicyDecision.APPROVED
    )
    assert result.refund_request_id is not None

    stored_request = db_session.get(
        RefundRequest,
        result.refund_request_id,
    )

    assert stored_request is not None
    assert (
        stored_request.decision
        == PolicyDecision.APPROVED
    )
    assert (
        stored_request.refundable_amount
        == Decimal("100.00")
    )


def test_issue_refund_requires_prior_approval(
    db_session: Session,
) -> None:
    _, order = add_customer_and_order(db_session)

    result = issue_refund(
        db_session,
        order_id=order.order_id,
        amount=Decimal("100.00"),
        idempotency_key="approval-required-key",
    )

    assert result.status == ToolStatus.ERROR
    assert (
        result.error_code
        == ToolErrorCode.APPROVAL_REQUIRED
    )


def test_issue_refund_rejects_amount_mismatch(
    db_session: Session,
) -> None:
    customer, order = add_customer_and_order(db_session)

    evaluation = evaluate_test_order(
        db_session,
        customer,
        order,
    )

    assert evaluation.status == ToolStatus.SUCCESS

    result = issue_refund(
        db_session,
        order_id=order.order_id,
        amount=Decimal("500.00"),
        idempotency_key="amount-mismatch-key",
    )

    assert result.status == ToolStatus.ERROR
    assert (
        result.error_code
        == ToolErrorCode.AMOUNT_MISMATCH
    )


def test_issue_refund_is_idempotent(
    db_session: Session,
) -> None:
    customer, order = add_customer_and_order(db_session)

    evaluation = evaluate_test_order(
        db_session,
        customer,
        order,
    )

    assert evaluation.status == ToolStatus.SUCCESS

    first_result = issue_refund(
        db_session,
        order_id=order.order_id,
        amount=Decimal("100.00"),
        idempotency_key="same-refund-key",
    )

    second_result = issue_refund(
        db_session,
        order_id=order.order_id,
        amount=Decimal("100.00"),
        idempotency_key="same-refund-key",
    )

    assert first_result.status == ToolStatus.SUCCESS
    assert first_result.refund_reference is not None
    assert first_result.idempotent_replay is False

    assert second_result.status == ToolStatus.SUCCESS
    assert (
        second_result.refund_reference
        == first_result.refund_reference
    )
    assert second_result.idempotent_replay is True

    stored_order = db_session.get(
        Order,
        order.order_id,
    )

    assert stored_order is not None
    assert (
        stored_order.refund_status
        == RefundStatus.FULL
    )


def test_new_key_cannot_refund_fully_refunded_order(
    db_session: Session,
) -> None:
    customer, order = add_customer_and_order(db_session)

    evaluate_test_order(
        db_session,
        customer,
        order,
    )

    first_result = issue_refund(
        db_session,
        order_id=order.order_id,
        amount=Decimal("100.00"),
        idempotency_key="first-refund-key",
    )

    assert first_result.status == ToolStatus.SUCCESS

    second_result = issue_refund(
        db_session,
        order_id=order.order_id,
        amount=Decimal("100.00"),
        idempotency_key="different-refund-key",
    )

    assert second_result.status == ToolStatus.ERROR
    assert (
        second_result.error_code
        == ToolErrorCode.ALREADY_REFUNDED
    )


def test_record_refund_denial_updates_order(
    db_session: Session,
) -> None:
    customer, order = add_customer_and_order(
        db_session,
        final_sale=True,
    )

    evaluation = evaluate_test_order(
        db_session,
        customer,
        order,
    )

    assert evaluation.policy_result is not None
    assert (
        evaluation.policy_result.decision
        == PolicyDecision.DENIED
    )

    result = record_refund_denial(
        db_session,
        order_id=order.order_id,
        rule_codes=(
            evaluation.policy_result.rule_codes
        ),
        reason=(
            evaluation.policy_result.reasons[0]
        ),
    )

    assert result.status == ToolStatus.SUCCESS
    assert result.refund_status == RefundStatus.DENIED
    assert "RP-003" in result.rule_codes

    stored_order = db_session.get(
        Order,
        order.order_id,
    )

    assert stored_order is not None
    assert (
        stored_order.refund_status
        == RefundStatus.DENIED
    )


def test_create_human_review_is_idempotent(
    db_session: Session,
) -> None:
    customer, order = add_customer_and_order(
        db_session,
        item_price=Decimal("600.00"),
    )

    evaluation = evaluate_test_order(
        db_session,
        customer,
        order,
    )

    assert evaluation.policy_result is not None
    assert (
        evaluation.policy_result.decision
        == PolicyDecision.ESCALATED
    )

    first_result = create_human_review(
        db_session,
        order_id=order.order_id,
        reason="Refund exceeds the automatic limit.",
    )

    second_result = create_human_review(
        db_session,
        order_id=order.order_id,
        reason="Refund exceeds the automatic limit.",
    )

    assert first_result.status == ToolStatus.SUCCESS
    assert first_result.case_id is not None
    assert first_result.review_status == ReviewStatus.OPEN
    assert first_result.idempotent_replay is False

    assert second_result.status == ToolStatus.SUCCESS
    assert second_result.case_id == first_result.case_id
    assert second_result.idempotent_replay is True

    case_count = db_session.scalar(
        select(func.count()).select_from(
            HumanReviewCase
        )
    )

    assert case_count == 1

    stored_order = db_session.get(
        Order,
        order.order_id,
    )

    assert stored_order is not None
    assert (
        stored_order.refund_status
        == RefundStatus.HUMAN_REVIEW
    )