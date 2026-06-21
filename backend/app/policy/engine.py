from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from app.models import (
    OrderStatus,
    PolicyDecision,
    ProductCondition,
    RefundStatus,
)
from app.policy.types import (
    CustomerPolicyData,
    OrderPolicyData,
    RefundPolicyResult,
    RefundReason,
    RefundRequestContext,
)


MONEY_QUANTUM = Decimal("0.01")
HIGH_VALUE_THRESHOLD = Decimal("500.00")

NON_REFUNDABLE_CATEGORIES = {
    "GIFT_CARD",
    "DOWNLOADABLE",
}


def round_money(amount: Decimal) -> Decimal:
    """Round monetary values to two decimal places."""

    return amount.quantize(
        MONEY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def normalize_category(category: str) -> str:
    """Convert category names into a predictable comparison format."""

    return (
        category.strip()
        .upper()
        .replace("-", "_")
        .replace(" ", "_")
    )


def unique_rule_codes(rule_codes: list[str]) -> list[str]:
    """Remove duplicate rule codes while preserving their order."""

    return list(dict.fromkeys(rule_codes))


def create_result(
    *,
    decision: PolicyDecision,
    rule_codes: list[str],
    reasons: list[str],
    refundable_amount: Decimal = Decimal("0.00"),
    human_review_required: bool = False,
    refund_method: str | None = None,
) -> RefundPolicyResult:
    """Create a consistently formatted policy result."""

    return RefundPolicyResult(
        decision=decision,
        rule_codes=unique_rule_codes(rule_codes),
        reasons=reasons,
        refundable_amount=round_money(refundable_amount),
        human_review_required=human_review_required,
        refund_method=refund_method,
    )


def issue_condition_matches_request(
    order: OrderPolicyData,
    request: RefundRequestContext,
) -> bool:
    """Check whether the verified issue matches the stored condition."""

    expected_conditions = {
        RefundReason.DAMAGED: ProductCondition.DAMAGED,
        RefundReason.DEFECTIVE: ProductCondition.DEFECTIVE,
        RefundReason.INCORRECT_ITEM: (
            ProductCondition.INCORRECT_ITEM
        ),
    }

    expected_condition = expected_conditions.get(
        request.reason
    )

    if expected_condition is None:
        return False

    return (
        request.issue_verified
        and order.product_condition == expected_condition
    )


def is_within_damage_exception_window(
    order: OrderPolicyData,
    request: RefundRequestContext,
) -> bool:
    """Check whether a verified issue was reported within seven days."""

    if order.delivery_date is None:
        return False

    days_since_delivery = (
        request.request_date - order.delivery_date
    ).days

    return (
        0 <= days_since_delivery <= 7
        and issue_condition_matches_request(order, request)
    )


def calculate_item_amount(
    order: OrderPolicyData,
    requested_quantity: int,
) -> Decimal:
    """Calculate the item value for the requested quantity."""

    return round_money(
        order.item_price * requested_quantity
    )


def calculate_candidate_refund_amount(
    order: OrderPolicyData,
    request: RefundRequestContext,
) -> Decimal:
    """Calculate the possible refund before the final decision."""

    item_amount = calculate_item_amount(
        order,
        request.requested_quantity,
    )

    if is_within_damage_exception_window(
        order,
        request,
    ):
        return round_money(
            item_amount + order.shipping_amount
        )

    return item_amount


def evaluate_refund_policy(
    customer: CustomerPolicyData,
    order: OrderPolicyData,
    request: RefundRequestContext,
) -> RefundPolicyResult:
    """
    Apply ResolveAI refund policy version 1.0.

    This function is the final authority for automatic refund
    approval, denial and escalation.
    """

    # Priority 1: Identity, ownership and required-data validation.
    identity_or_ownership_failed = (
        not request.identity_verified
        or not request.ownership_verified
        or not request.required_details_verified
        or request.customer_id != customer.customer_id
        or request.order_id != order.order_id
        or order.customer_id != customer.customer_id
    )

    if identity_or_ownership_failed:
        return create_result(
            decision=PolicyDecision.DENIED,
            rule_codes=["RP-011"],
            reasons=[
                (
                    "Customer identity, order ownership or required "
                    "order details could not be verified."
                ),
                (
                    "No refund can be processed until the provided "
                    "customer and order information matches."
                ),
            ],
        )

    # Priority 2: Duplicate refund protection.
    if order.refund_status == RefundStatus.FULL:
        return create_result(
            decision=PolicyDecision.DENIED,
            rule_codes=["RP-005"],
            reasons=[
                (
                    "The order has already been fully refunded and "
                    "cannot be refunded again."
                )
            ],
        )

    # Quantity is checked before amount calculation because an invalid
    # quantity must never be used to determine a refund value.
    if request.requested_quantity > order.quantity:
        return create_result(
            decision=PolicyDecision.DENIED,
            rule_codes=["RP-006"],
            reasons=[
                (
                    f"The requested quantity "
                    f"({request.requested_quantity}) exceeds the "
                    f"purchased quantity ({order.quantity})."
                )
            ],
        )

    candidate_refund_amount = (
        calculate_candidate_refund_amount(
            order,
            request,
        )
    )

    # Priority 3: Fraud and high-value requests require human review.
    escalation_codes: list[str] = []
    escalation_reasons: list[str] = []

    if customer.fraud_review_flag:
        escalation_codes.append("RP-010")
        escalation_reasons.append(
            (
                "The customer account is marked for fraud review, "
                "so the request requires a human decision."
            )
        )

    if candidate_refund_amount > HIGH_VALUE_THRESHOLD:
        escalation_codes.append("RP-009")
        escalation_reasons.append(
            (
                f"The candidate refund amount of "
                f"${candidate_refund_amount:.2f} exceeds the "
                "$500.00 automatic-refund limit."
            )
        )

    if escalation_codes:
        return create_result(
            decision=PolicyDecision.ESCALATED,
            rule_codes=escalation_codes,
            reasons=escalation_reasons,
            refundable_amount=candidate_refund_amount,
            human_review_required=True,
            refund_method=order.payment_method,
        )

    # Priority 4: Product restrictions.
    product_category = normalize_category(
        order.product_category
    )

    restriction_reasons: list[str] = []

    if order.final_sale:
        restriction_reasons.append(
            "The product was sold as a final-sale item."
        )

    if product_category == "GIFT_CARD":
        restriction_reasons.append(
            "Gift cards are non-refundable."
        )

    if (
        order.downloadable
        or product_category == "DOWNLOADABLE"
    ):
        restriction_reasons.append(
            "Downloadable products are non-refundable."
        )

    if order.personalized:
        restriction_reasons.append(
            "Personalized products are non-refundable."
        )

    if restriction_reasons:
        return create_result(
            decision=PolicyDecision.DENIED,
            rule_codes=["RP-003"],
            reasons=restriction_reasons,
        )

    if (
        order.hygiene_sensitive
        and order.product_condition
        == ProductCondition.OPENED
    ):
        return create_result(
            decision=PolicyDecision.DENIED,
            rule_codes=["RP-004"],
            reasons=[
                (
                    "The hygiene-sensitive product has been opened "
                    "and is therefore non-refundable."
                )
            ],
        )

    # Priority 5: Delivery status and return window.
    if order.order_status != OrderStatus.DELIVERED:
        return create_result(
            decision=PolicyDecision.DENIED,
            rule_codes=["RP-002"],
            reasons=[
                (
                    "The order has not reached DELIVERED status, "
                    "so a standard refund cannot be processed."
                )
            ],
        )

    if order.delivery_date is None:
        return create_result(
            decision=PolicyDecision.DENIED,
            rule_codes=["RP-011"],
            reasons=[
                (
                    "The delivery date is missing, so the return "
                    "window cannot be verified."
                )
            ],
        )

    days_since_delivery = (
        request.request_date - order.delivery_date
    ).days

    if days_since_delivery < 0:
        return create_result(
            decision=PolicyDecision.DENIED,
            rule_codes=["RP-011"],
            reasons=[
                (
                    "The recorded delivery date is later than the "
                    "refund-request date and cannot be verified."
                )
            ],
        )

    if days_since_delivery > 30:
        return create_result(
            decision=PolicyDecision.DENIED,
            rule_codes=["RP-001"],
            reasons=[
                (
                    f"The refund was requested "
                    f"{days_since_delivery} days after delivery, "
                    "which exceeds the 30-day return window."
                )
            ],
        )

    # Priority 6: Verified damage, defect or incorrect-item exception.
    if is_within_damage_exception_window(
        order,
        request,
    ):
        refundable_amount = round_money(
            calculate_item_amount(
                order,
                request.requested_quantity,
            )
            + order.shipping_amount
        )

        return create_result(
            decision=PolicyDecision.APPROVED,
            rule_codes=[
                "RP-002",
                "RP-006",
                "RP-008",
                "RP-012",
            ],
            reasons=[
                (
                    "The verified damaged, defective or incorrect "
                    "item was reported within seven days of "
                    "delivery."
                ),
                (
                    "The refund includes the eligible item amount "
                    "and original shipping charge."
                ),
                (
                    "The refund must return to the original "
                    f"payment method: {order.payment_method}."
                ),
            ],
            refundable_amount=refundable_amount,
            refund_method=order.payment_method,
        )

    # Priority 7: Standard return amount calculation.
    standard_refund_amount = calculate_item_amount(
        order,
        request.requested_quantity,
    )

    standard_reasons = [
        (
            "The request is within the 30-day return window and "
            "the product is eligible for a standard return."
        ),
        (
            "Original shipping charges are excluded from a "
            "standard change-of-mind refund."
        ),
        (
            "The refund must return to the original payment "
            f"method: {order.payment_method}."
        ),
    ]

    if request.reason in {
        RefundReason.DAMAGED,
        RefundReason.DEFECTIVE,
        RefundReason.INCORRECT_ITEM,
    }:
        standard_reasons.insert(
            1,
            (
                "The reported product issue was not eligible for "
                "the verified seven-day exception, so the request "
                "was evaluated under the standard return rules."
            ),
        )

    return create_result(
        decision=PolicyDecision.APPROVED,
        rule_codes=[
            "RP-001",
            "RP-002",
            "RP-006",
            "RP-007",
            "RP-012",
        ],
        reasons=standard_reasons,
        refundable_amount=standard_refund_amount,
        refund_method=order.payment_method,
    )