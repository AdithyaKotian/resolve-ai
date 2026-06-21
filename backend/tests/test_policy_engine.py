from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from app.models import (
    OrderStatus,
    PolicyDecision,
    ProductCondition,
    RefundStatus,
)
from app.policy.engine import evaluate_refund_policy
from app.policy.types import (
    CustomerPolicyData,
    OrderPolicyData,
    RefundReason,
    RefundRequestContext,
)


def create_customer(
    **overrides: Any,
) -> CustomerPolicyData:
    values: dict[str, Any] = {
        "customer_id": "CUST-TEST-001",
        "fraud_review_flag": False,
    }
    values.update(overrides)

    return CustomerPolicyData(**values)


def create_order(
    **overrides: Any,
) -> OrderPolicyData:
    values: dict[str, Any] = {
        "order_id": "ORD-TEST-001",
        "customer_id": "CUST-TEST-001",
        "product_category": "ELECTRONICS",
        "quantity": 1,
        "item_price": Decimal("100.00"),
        "shipping_amount": Decimal("10.00"),
        "delivery_date": date.today() - timedelta(days=10),
        "order_status": OrderStatus.DELIVERED,
        "product_condition": ProductCondition.UNOPENED,
        "final_sale": False,
        "personalized": False,
        "downloadable": False,
        "hygiene_sensitive": False,
        "payment_method": "Visa ending in 4242",
        "refund_status": RefundStatus.NONE,
    }
    values.update(overrides)

    return OrderPolicyData(**values)


def create_request(
    **overrides: Any,
) -> RefundRequestContext:
    values: dict[str, Any] = {
        "customer_id": "CUST-TEST-001",
        "order_id": "ORD-TEST-001",
        "requested_quantity": 1,
        "reason": RefundReason.CHANGE_OF_MIND,
        "request_date": date.today(),
        "identity_verified": True,
        "ownership_verified": True,
        "required_details_verified": True,
        "issue_verified": False,
    }
    values.update(overrides)

    return RefundRequestContext(**values)


def test_valid_standard_refund_is_approved() -> None:
    result = evaluate_refund_policy(
        create_customer(),
        create_order(
            item_price=Decimal("129.99"),
            shipping_amount=Decimal("9.99"),
        ),
        create_request(),
    )

    assert result.decision == PolicyDecision.APPROVED
    assert result.refundable_amount == Decimal("129.99")
    assert "RP-007" in result.rule_codes
    assert "RP-012" in result.rule_codes


def test_refund_outside_thirty_days_is_denied() -> None:
    result = evaluate_refund_policy(
        create_customer(),
        create_order(
            delivery_date=(
                date.today() - timedelta(days=31)
            )
        ),
        create_request(),
    )

    assert result.decision == PolicyDecision.DENIED
    assert result.refundable_amount == Decimal("0.00")
    assert result.rule_codes == ["RP-001"]


def test_final_sale_product_is_denied() -> None:
    result = evaluate_refund_policy(
        create_customer(),
        create_order(final_sale=True),
        create_request(),
    )

    assert result.decision == PolicyDecision.DENIED
    assert result.rule_codes == ["RP-003"]


def test_opened_hygiene_product_is_denied() -> None:
    result = evaluate_refund_policy(
        create_customer(),
        create_order(
            product_category="HYGIENE",
            product_condition=ProductCondition.OPENED,
            hygiene_sensitive=True,
        ),
        create_request(),
    )

    assert result.decision == PolicyDecision.DENIED
    assert result.rule_codes == ["RP-004"]


def test_fully_refunded_order_is_denied() -> None:
    result = evaluate_refund_policy(
        create_customer(),
        create_order(
            refund_status=RefundStatus.FULL,
        ),
        create_request(),
    )

    assert result.decision == PolicyDecision.DENIED
    assert result.rule_codes == ["RP-005"]


def test_requested_quantity_above_purchase_is_denied() -> None:
    result = evaluate_refund_policy(
        create_customer(),
        create_order(quantity=2),
        create_request(requested_quantity=3),
    )

    assert result.decision == PolicyDecision.DENIED
    assert result.rule_codes == ["RP-006"]


def test_high_value_refund_is_escalated() -> None:
    result = evaluate_refund_policy(
        create_customer(),
        create_order(
            item_price=Decimal("899.00"),
        ),
        create_request(),
    )

    assert result.decision == PolicyDecision.ESCALATED
    assert result.human_review_required is True
    assert result.refundable_amount == Decimal("899.00")
    assert "RP-009" in result.rule_codes


def test_fraud_flagged_customer_is_escalated() -> None:
    result = evaluate_refund_policy(
        create_customer(fraud_review_flag=True),
        create_order(),
        create_request(),
    )

    assert result.decision == PolicyDecision.ESCALATED
    assert result.human_review_required is True
    assert "RP-010" in result.rule_codes


def test_verified_damaged_item_within_seven_days_is_approved() -> None:
    result = evaluate_refund_policy(
        create_customer(),
        create_order(
            item_price=Decimal("329.00"),
            shipping_amount=Decimal("15.00"),
            delivery_date=(
                date.today() - timedelta(days=3)
            ),
            product_condition=ProductCondition.DAMAGED,
        ),
        create_request(
            reason=RefundReason.DAMAGED,
            issue_verified=True,
        ),
    )

    assert result.decision == PolicyDecision.APPROVED
    assert result.refundable_amount == Decimal("344.00")
    assert "RP-008" in result.rule_codes


def test_order_ownership_mismatch_is_denied() -> None:
    result = evaluate_refund_policy(
        create_customer(
            customer_id="CUST-OWNER-A",
        ),
        create_order(
            customer_id="CUST-OWNER-B",
        ),
        create_request(
            customer_id="CUST-OWNER-A",
            ownership_verified=False,
        ),
    )

    assert result.decision == PolicyDecision.DENIED
    assert result.rule_codes == ["RP-011"]


def test_order_not_delivered_is_denied() -> None:
    result = evaluate_refund_policy(
        create_customer(),
        create_order(
            delivery_date=None,
            order_status=OrderStatus.SHIPPED,
        ),
        create_request(),
    )

    assert result.decision == PolicyDecision.DENIED
    assert result.rule_codes == ["RP-002"]


def test_exactly_five_hundred_dollars_is_not_escalated() -> None:
    result = evaluate_refund_policy(
        create_customer(),
        create_order(
            item_price=Decimal("480.00"),
            shipping_amount=Decimal("20.00"),
            delivery_date=(
                date.today() - timedelta(days=2)
            ),
            product_condition=ProductCondition.DAMAGED,
        ),
        create_request(
            reason=RefundReason.DAMAGED,
            issue_verified=True,
        ),
    )

    assert result.decision == PolicyDecision.APPROVED
    assert result.refundable_amount == Decimal("500.00")
    assert "RP-009" not in result.rule_codes