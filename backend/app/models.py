from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""

    return datetime.now(timezone.utc)


class MembershipTier(str, Enum):
    STANDARD = "STANDARD"
    SILVER = "SILVER"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"


class OrderStatus(str, Enum):
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class ProductCondition(str, Enum):
    UNOPENED = "UNOPENED"
    OPENED = "OPENED"
    DAMAGED = "DAMAGED"
    DEFECTIVE = "DEFECTIVE"
    INCORRECT_ITEM = "INCORRECT_ITEM"


class RefundStatus(str, Enum):
    NONE = "NONE"
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    FULL = "FULL"
    DENIED = "DENIED"
    HUMAN_REVIEW = "HUMAN_REVIEW"


class PolicyDecision(str, Enum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    ESCALATED = "ESCALATED"


class SessionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ReviewStatus(str, Enum):
    OPEN = "OPEN"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    CLOSED = "CLOSED"


class Customer(Base):
    """A fictional CRM customer profile."""

    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(
        String(40),
        primary_key=True,
    )
    full_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    phone: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    address_line: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    postal_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="United States",
    )

    membership_tier: Mapped[MembershipTier] = mapped_column(
        SqlEnum(MembershipTier, native_enum=False),
        nullable=False,
        default=MembershipTier.STANDARD,
    )
    account_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    fraud_review_flag: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    total_orders: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    previous_refunds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    orders: Mapped[list["Order"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
    )


class Order(Base):
    """An e-commerce order belonging to one customer."""

    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(
        String(40),
        primary_key=True,
    )
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.customer_id"),
        index=True,
        nullable=False,
    )

    product_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    product_category: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    item_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    shipping_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    order_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    order_status: Mapped[OrderStatus] = mapped_column(
        SqlEnum(OrderStatus, native_enum=False),
        nullable=False,
    )
    product_condition: Mapped[ProductCondition] = mapped_column(
        SqlEnum(ProductCondition, native_enum=False),
        nullable=False,
    )

    final_sale: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    personalized: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    downloadable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    hygiene_sensitive: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    payment_method: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    refund_status: Mapped[RefundStatus] = mapped_column(
        SqlEnum(RefundStatus, native_enum=False),
        nullable=False,
        default=RefundStatus.NONE,
    )

    customer: Mapped[Customer] = relationship(
        back_populates="orders",
    )
    refund_requests: Mapped[list["RefundRequest"]] = relationship(
        back_populates="order",
    )


class AgentSession(Base):
    """One customer conversation handled by the refund agent."""

    __tablename__ = "agent_sessions"

    session_id: Mapped[str] = mapped_column(
        String(80),
        primary_key=True,
    )
    customer_id: Mapped[str | None] = mapped_column(
        ForeignKey("customers.customer_id"),
        nullable=True,
        index=True,
    )
    order_id: Mapped[str | None] = mapped_column(
        ForeignKey("orders.order_id"),
        nullable=True,
        index=True,
    )

    status: Mapped[SessionStatus] = mapped_column(
        SqlEnum(SessionStatus, native_enum=False),
        nullable=False,
        default=SessionStatus.ACTIVE,
    )
    final_decision: Mapped[PolicyDecision | None] = mapped_column(
        SqlEnum(PolicyDecision, native_enum=False),
        nullable=True,
    )
    final_response: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class RefundRequest(Base):
    """A refund request and the authoritative policy result."""

    __tablename__ = "refund_requests"

    refund_request_id: Mapped[str] = mapped_column(
        String(80),
        primary_key=True,
    )
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("agent_sessions.session_id"),
        nullable=True,
        index=True,
    )
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.customer_id"),
        nullable=False,
        index=True,
    )
    order_id: Mapped[str] = mapped_column(
        ForeignKey("orders.order_id"),
        nullable=False,
        index=True,
    )

    request_reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    requested_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    decision: Mapped[PolicyDecision | None] = mapped_column(
        SqlEnum(PolicyDecision, native_enum=False),
        nullable=True,
    )
    rule_codes: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    reasons: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    refundable_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    human_review_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    idempotency_key: Mapped[str | None] = mapped_column(
        String(120),
        unique=True,
        nullable=True,
    )
    refund_reference: Mapped[str | None] = mapped_column(
        String(120),
        unique=True,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    order: Mapped[Order] = relationship(
        back_populates="refund_requests",
    )


class AgentEvent(Base):
    """A safe structured execution event for the admin dashboard."""

    __tablename__ = "agent_events"

    event_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    session_id: Mapped[str] = mapped_column(
        ForeignKey("agent_sessions.session_id"),
        nullable=False,
        index=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    event_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )
    graph_node: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    tool_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    sanitized_input: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    tool_output_summary: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    matched_policy_rule_codes: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    decision: Mapped[PolicyDecision | None] = mapped_column(
        SqlEnum(PolicyDecision, native_enum=False),
        nullable=True,
    )
    execution_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


class HumanReviewCase(Base):
    """A refund request that requires a human decision."""

    __tablename__ = "human_review_cases"

    case_id: Mapped[str] = mapped_column(
        String(80),
        primary_key=True,
    )
    refund_request_id: Mapped[str | None] = mapped_column(
        ForeignKey("refund_requests.refund_request_id"),
        nullable=True,
        index=True,
    )
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.customer_id"),
        nullable=False,
        index=True,
    )
    order_id: Mapped[str] = mapped_column(
        ForeignKey("orders.order_id"),
        nullable=False,
        index=True,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[ReviewStatus] = mapped_column(
        SqlEnum(ReviewStatus, native_enum=False),
        nullable=False,
        default=ReviewStatus.OPEN,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )