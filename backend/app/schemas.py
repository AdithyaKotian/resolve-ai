from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.models import (
    MembershipTier,
    OrderStatus,
    PolicyDecision,
    ProductCondition,
    RefundStatus,
    SessionStatus,
)


class CustomerSummary(BaseModel):
    """Customer information needed by the demo selector."""

    model_config = ConfigDict(from_attributes=True)

    customer_id: str
    full_name: str
    email: str
    membership_tier: MembershipTier
    fraud_review_flag: bool
    total_orders: int
    previous_refunds: int


class CustomerDetail(CustomerSummary):
    """Complete fictional CRM profile."""

    phone: str
    address_line: str
    city: str
    state: str
    postal_code: str
    country: str
    account_created_at: datetime


class OrderSummary(BaseModel):
    """Order information exposed to the customer demo interface."""

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
    refund_status: RefundStatus

    final_sale: bool
    personalized: bool
    downloadable: bool
    hygiene_sensitive: bool

    payment_method: str


class CustomerOrdersResponse(BaseModel):
    customer: CustomerSummary
    orders: list[OrderSummary]


class ChatRequest(BaseModel):
    """Input accepted by the customer chat endpoint."""

    session_id: str | None = Field(
        default=None,
        max_length=80,
    )

    customer_id: str = Field(
        min_length=1,
        max_length=40,
    )

    order_id: str | None = Field(
        default=None,
        max_length=40,
    )

    message: str = Field(
        min_length=1,
        max_length=2000,
    )

    simulate_transient_failure: bool = False

    @field_validator(
        "session_id",
        "customer_id",
        "order_id",
        "message",
        mode="before",
    )
    @classmethod
    def strip_text(
        cls,
        value: Any,
    ) -> Any:
        if isinstance(value, str):
            cleaned_value = value.strip()
            return cleaned_value or None

        return value


class DecisionResult(BaseModel):
    """Structured refund decision displayed by the frontend."""

    decision: PolicyDecision
    order_id: str

    refundable_amount: Decimal
    rule_codes: list[str]
    reasons: list[str]

    refund_reference: str | None = None
    human_review_case_id: str | None = None
    payment_method: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    session_status: SessionStatus

    assistant_message: str
    decision_result: DecisionResult | None = None

    retry_count: int = 0


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: int
    session_id: str
    role: str
    content: str
    created_at: datetime


class AgentEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: int
    session_id: str
    timestamp: datetime

    event_type: str
    graph_node: str | None
    tool_name: str | None

    sanitized_input: dict[str, Any] | None
    tool_output_summary: dict[str, Any] | None
    matched_policy_rule_codes: list[str]

    decision: PolicyDecision | None
    execution_status: str

    latency_ms: int | None
    retry_count: int
    error_message: str | None


class SessionSummary(BaseModel):
    session_id: str

    customer_id: str | None
    order_id: str | None

    status: SessionStatus
    final_decision: PolicyDecision | None

    created_at: datetime
    updated_at: datetime

    event_count: int
    tool_failures: int


class SessionMetrics(BaseModel):
    total_sessions: int
    approved_refunds: int
    denied_refunds: int
    escalated_requests: int
    tool_failures: int


class SessionListResponse(BaseModel):
    metrics: SessionMetrics
    sessions: list[SessionSummary]


class SessionDetailResponse(BaseModel):
    session: SessionSummary
    messages: list[ChatMessageResponse]
    decision_result: DecisionResult | None

class DemoResetResponse(BaseModel):
    """Result returned after restoring the demo environment."""

    message: str
    customers: int
    orders: int
    sessions: int
    events: int