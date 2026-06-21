from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.models import (
    MembershipTier,
    OrderStatus,
    ProductCondition,
    RefundStatus,
    ReviewStatus,
)
from app.policy.types import RefundPolicyResult


class ToolStatus(str, Enum):
    """Standard status returned by every backend tool."""

    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class ToolErrorCode(str, Enum):
    """Safe error codes returned without exposing internal details."""

    INVALID_INPUT = "INVALID_INPUT"

    CUSTOMER_NOT_FOUND = "CUSTOMER_NOT_FOUND"
    CUSTOMER_IDENTIFIER_MISMATCH = (
        "CUSTOMER_IDENTIFIER_MISMATCH"
    )

    ORDER_NOT_FOUND = "ORDER_NOT_FOUND"
    ORDER_OWNERSHIP_MISMATCH = (
        "ORDER_OWNERSHIP_MISMATCH"
    )

    POLICY_FILE_UNAVAILABLE = (
        "POLICY_FILE_UNAVAILABLE"
    )

    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    ALREADY_REFUNDED = "ALREADY_REFUNDED"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"

    DENIAL_RECORD_NOT_FOUND = (
        "DENIAL_RECORD_NOT_FOUND"
    )
    ESCALATION_RECORD_NOT_FOUND = (
        "ESCALATION_RECORD_NOT_FOUND"
    )

    DATABASE_ERROR = "DATABASE_ERROR"


class ToolResultBase(BaseModel):
    """Common fields returned by all tools."""

    status: ToolStatus
    error_code: ToolErrorCode | None = None
    error_message: str | None = None


class CustomerRecord(BaseModel):
    """Customer data returned by the CRM lookup tool."""

    model_config = ConfigDict(from_attributes=True)

    customer_id: str
    full_name: str
    email: str
    phone: str

    address_line: str
    city: str
    state: str
    postal_code: str
    country: str

    membership_tier: MembershipTier
    account_created_at: datetime
    fraud_review_flag: bool
    total_orders: int
    previous_refunds: int


class CustomerLookupResult(ToolResultBase):
    """Result returned by get_customer."""

    customer: CustomerRecord | None = None


class OrderRecord(BaseModel):
    """Order data returned after ownership verification."""

    model_config = ConfigDict(from_attributes=True)

    order_id: str
    customer_id: str

    product_name: str
    product_category: str
    quantity: int

    item_price: Decimal
    shipping_amount: Decimal
    total_amount: Decimal

    order_date: date
    delivery_date: date | None
    order_status: OrderStatus
    product_condition: ProductCondition

    final_sale: bool
    personalized: bool
    downloadable: bool
    hygiene_sensitive: bool

    payment_method: str
    refund_status: RefundStatus


class OrderLookupResult(ToolResultBase):
    """Result returned by get_order."""

    order: OrderRecord | None = None


class RefundPolicyDocumentResult(ToolResultBase):
    """Human-readable policy document and rule metadata."""

    policy_version: str | None = None
    rule_codes: list[str] = Field(
        default_factory=list,
    )
    markdown: str | None = None


class PolicyEvaluationToolResult(ToolResultBase):
    """Persisted result of deterministic policy evaluation."""

    refund_request_id: str | None = None
    policy_result: RefundPolicyResult | None = None


class RefundExecutionResult(ToolResultBase):
    """Result returned by the refund execution tool."""

    refund_request_id: str | None = None
    order_id: str | None = None
    refund_reference: str | None = None

    amount: Decimal | None = None
    payment_method: str | None = None
    refund_status: RefundStatus | None = None

    idempotent_replay: bool = False


class DenialRecordResult(ToolResultBase):
    """Result returned after storing a refund denial."""

    refund_request_id: str | None = None
    order_id: str | None = None

    rule_codes: list[str] = Field(
        default_factory=list,
    )
    reason: str | None = None
    refund_status: RefundStatus | None = None


class HumanReviewCreationResult(ToolResultBase):
    """Result returned after creating a human-review case."""

    case_id: str | None = None
    refund_request_id: str | None = None
    order_id: str | None = None

    review_status: ReviewStatus | None = None
    idempotent_replay: bool = False