from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.models import (
    OrderStatus,
    PolicyDecision,
    ProductCondition,
    RefundStatus,
)


POLICY_VERSION = "1.0"


class RefundReason(str, Enum):
    """Customer-provided reason for requesting a refund."""

    CHANGE_OF_MIND = "CHANGE_OF_MIND"
    DAMAGED = "DAMAGED"
    DEFECTIVE = "DEFECTIVE"
    INCORRECT_ITEM = "INCORRECT_ITEM"


class CustomerPolicyData(BaseModel):
    """Customer fields required by the refund policy engine."""

    model_config = ConfigDict(from_attributes=True)

    customer_id: str
    fraud_review_flag: bool = False


class OrderPolicyData(BaseModel):
    """Order fields required by the refund policy engine."""

    model_config = ConfigDict(from_attributes=True)

    order_id: str
    customer_id: str
    product_category: str

    quantity: int = Field(gt=0)
    item_price: Decimal = Field(ge=Decimal("0.00"))
    shipping_amount: Decimal = Field(ge=Decimal("0.00"))

    delivery_date: date | None
    order_status: OrderStatus
    product_condition: ProductCondition

    final_sale: bool = False
    personalized: bool = False
    downloadable: bool = False
    hygiene_sensitive: bool = False

    payment_method: str
    refund_status: RefundStatus


class RefundRequestContext(BaseModel):
    """Verified context about the current refund request."""

    customer_id: str
    order_id: str
    requested_quantity: int = Field(gt=0)

    reason: RefundReason
    request_date: date = Field(default_factory=date.today)

    identity_verified: bool = True
    ownership_verified: bool = True
    required_details_verified: bool = True

    issue_verified: bool = False


class RefundPolicyResult(BaseModel):
    """Authoritative result returned by the policy engine."""

    policy_version: str = POLICY_VERSION
    decision: PolicyDecision

    rule_codes: list[str]
    reasons: list[str]

    refundable_amount: Decimal = Field(
        ge=Decimal("0.00"),
    )
    human_review_required: bool

    refund_method: str | None