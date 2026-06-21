from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.database import SessionLocal, init_database
from app.models import (
    Customer,
    MembershipTier,
    Order,
    OrderStatus,
    ProductCondition,
    RefundStatus,
    AgentEvent,
    AgentSession,
    ChatMessage,
    HumanReviewCase,
    RefundRequest,
)


def days_ago(number_of_days: int) -> date:
    return date.today() - timedelta(days=number_of_days)


def datetime_days_ago(number_of_days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=number_of_days)


def calculate_total(
    item_price: str,
    quantity: int,
    shipping_amount: str,
) -> Decimal:
    return (
        Decimal(item_price) * quantity
        + Decimal(shipping_amount)
    ).quantize(Decimal("0.01"))


def customer_records() -> list[dict[str, Any]]:
    return [
        {
            "customer_id": "CUST-VALID-001",
            "full_name": "Maya Rao",
            "email": "maya.rao@example.com",
            "phone": "+1-202-555-0101",
            "address_line": "114 Cedar Avenue",
            "city": "Seattle",
            "state": "Washington",
            "postal_code": "98101",
            "country": "United States",
            "membership_tier": MembershipTier.GOLD,
            "account_created_at": datetime_days_ago(820),
            "fraud_review_flag": False,
        },
        {
            "customer_id": "CUST-LATE-002",
            "full_name": "Noah Bennett",
            "email": "noah.bennett@example.com",
            "phone": "+1-202-555-0102",
            "address_line": "22 Willow Street",
            "city": "Austin",
            "state": "Texas",
            "postal_code": "73301",
            "country": "United States",
            "membership_tier": MembershipTier.SILVER,
            "account_created_at": datetime_days_ago(610),
            "fraud_review_flag": False,
        },
        {
            "customer_id": "CUST-FINAL-003",
            "full_name": "Aisha Khan",
            "email": "aisha.khan@example.com",
            "phone": "+1-202-555-0103",
            "address_line": "78 Lakeview Drive",
            "city": "Chicago",
            "state": "Illinois",
            "postal_code": "60601",
            "country": "United States",
            "membership_tier": MembershipTier.STANDARD,
            "account_created_at": datetime_days_ago(420),
            "fraud_review_flag": False,
        },
        {
            "customer_id": "CUST-HYGIENE-004",
            "full_name": "Liam Carter",
            "email": "liam.carter@example.com",
            "phone": "+1-202-555-0104",
            "address_line": "905 Maple Lane",
            "city": "Denver",
            "state": "Colorado",
            "postal_code": "80201",
            "country": "United States",
            "membership_tier": MembershipTier.GOLD,
            "account_created_at": datetime_days_ago(730),
            "fraud_review_flag": False,
        },
        {
            "customer_id": "CUST-REFUNDED-005",
            "full_name": "Sofia Martin",
            "email": "sofia.martin@example.com",
            "phone": "+1-202-555-0105",
            "address_line": "48 Orchard Road",
            "city": "Boston",
            "state": "Massachusetts",
            "postal_code": "02108",
            "country": "United States",
            "membership_tier": MembershipTier.PLATINUM,
            "account_created_at": datetime_days_ago(1200),
            "fraud_review_flag": False,
        },
        {
            "customer_id": "CUST-HIGHVALUE-006",
            "full_name": "Ethan Brooks",
            "email": "ethan.brooks@example.com",
            "phone": "+1-202-555-0106",
            "address_line": "360 Pine Street",
            "city": "San Francisco",
            "state": "California",
            "postal_code": "94102",
            "country": "United States",
            "membership_tier": MembershipTier.GOLD,
            "account_created_at": datetime_days_ago(900),
            "fraud_review_flag": False,
        },
        {
            "customer_id": "CUST-FRAUD-007",
            "full_name": "Zara Ali",
            "email": "zara.ali@example.com",
            "phone": "+1-202-555-0107",
            "address_line": "71 River Court",
            "city": "Phoenix",
            "state": "Arizona",
            "postal_code": "85001",
            "country": "United States",
            "membership_tier": MembershipTier.STANDARD,
            "account_created_at": datetime_days_ago(145),
            "fraud_review_flag": True,
        },
        {
            "customer_id": "CUST-DAMAGE-008",
            "full_name": "Arjun Mehta",
            "email": "arjun.mehta@example.com",
            "phone": "+1-202-555-0108",
            "address_line": "500 Sunrise Boulevard",
            "city": "Portland",
            "state": "Oregon",
            "postal_code": "97201",
            "country": "United States",
            "membership_tier": MembershipTier.SILVER,
            "account_created_at": datetime_days_ago(500),
            "fraud_review_flag": False,
        },
        {
            "customer_id": "CUST-OWNER-A-009",
            "full_name": "Priya Nair",
            "email": "priya.nair@example.com",
            "phone": "+1-202-555-0109",
            "address_line": "63 Birch Terrace",
            "city": "Atlanta",
            "state": "Georgia",
            "postal_code": "30301",
            "country": "United States",
            "membership_tier": MembershipTier.STANDARD,
            "account_created_at": datetime_days_ago(250),
            "fraud_review_flag": False,
        },
        {
            "customer_id": "CUST-OWNER-B-010",
            "full_name": "Daniel Kim",
            "email": "daniel.kim@example.com",
            "phone": "+1-202-555-0110",
            "address_line": "810 Franklin Avenue",
            "city": "New York",
            "state": "New York",
            "postal_code": "10001",
            "country": "United States",
            "membership_tier": MembershipTier.GOLD,
            "account_created_at": datetime_days_ago(960),
            "fraud_review_flag": False,
        },
        {
            "customer_id": "CUST-GIFT-011",
            "full_name": "Elena Garcia",
            "email": "elena.garcia@example.com",
            "phone": "+1-202-555-0111",
            "address_line": "27 Palm Avenue",
            "city": "Miami",
            "state": "Florida",
            "postal_code": "33101",
            "country": "United States",
            "membership_tier": MembershipTier.SILVER,
            "account_created_at": datetime_days_ago(340),
            "fraud_review_flag": False,
        },
        {
            "customer_id": "CUST-DIGITAL-012",
            "full_name": "Marcus Lee",
            "email": "marcus.lee@example.com",
            "phone": "+1-202-555-0112",
            "address_line": "91 Harbor Street",
            "city": "Baltimore",
            "state": "Maryland",
            "postal_code": "21201",
            "country": "United States",
            "membership_tier": MembershipTier.STANDARD,
            "account_created_at": datetime_days_ago(180),
            "fraud_review_flag": False,
        },
        {
            "customer_id": "CUST-PERSONAL-013",
            "full_name": "Nia Johnson",
            "email": "nia.johnson@example.com",
            "phone": "+1-202-555-0113",
            "address_line": "415 Garden Way",
            "city": "Charlotte",
            "state": "North Carolina",
            "postal_code": "28201",
            "country": "United States",
            "membership_tier": MembershipTier.GOLD,
            "account_created_at": datetime_days_ago(700),
            "fraud_review_flag": False,
        },
        {
            "customer_id": "CUST-DELIVERY-014",
            "full_name": "Oliver Smith",
            "email": "oliver.smith@example.com",
            "phone": "+1-202-555-0114",
            "address_line": "12 Highland Road",
            "city": "Columbus",
            "state": "Ohio",
            "postal_code": "43004",
            "country": "United States",
            "membership_tier": MembershipTier.STANDARD,
            "account_created_at": datetime_days_ago(110),
            "fraud_review_flag": False,
        },
        {
            "customer_id": "CUST-EXTRA-015",
            "full_name": "Kavya Shetty",
            "email": "kavya.shetty@example.com",
            "phone": "+1-202-555-0115",
            "address_line": "205 Meadow Circle",
            "city": "Dallas",
            "state": "Texas",
            "postal_code": "75001",
            "country": "United States",
            "membership_tier": MembershipTier.PLATINUM,
            "account_created_at": datetime_days_ago(1500),
            "fraud_review_flag": False,
        },
    ]


def build_order(
    *,
    order_id: str,
    customer_id: str,
    product_name: str,
    product_category: str,
    quantity: int,
    item_price: str,
    shipping_amount: str,
    order_days_ago: int,
    delivery_days_ago: int | None,
    order_status: OrderStatus,
    product_condition: ProductCondition,
    payment_method: str,
    refund_status: RefundStatus = RefundStatus.NONE,
    final_sale: bool = False,
    personalized: bool = False,
    downloadable: bool = False,
    hygiene_sensitive: bool = False,
) -> dict[str, Any]:
    return {
        "order_id": order_id,
        "customer_id": customer_id,
        "product_name": product_name,
        "product_category": product_category,
        "quantity": quantity,
        "item_price": Decimal(item_price),
        "shipping_amount": Decimal(shipping_amount),
        "total_amount": calculate_total(
            item_price,
            quantity,
            shipping_amount,
        ),
        "order_date": days_ago(order_days_ago),
        "delivery_date": (
            days_ago(delivery_days_ago)
            if delivery_days_ago is not None
            else None
        ),
        "order_status": order_status,
        "product_condition": product_condition,
        "final_sale": final_sale,
        "personalized": personalized,
        "downloadable": downloadable,
        "hygiene_sensitive": hygiene_sensitive,
        "payment_method": payment_method,
        "refund_status": refund_status,
    }


def order_records() -> list[dict[str, Any]]:
    return [
        build_order(
            order_id="ORD-VALID-1001",
            customer_id="CUST-VALID-001",
            product_name="Wireless Mechanical Keyboard",
            product_category="ELECTRONICS",
            quantity=1,
            item_price="129.99",
            shipping_amount="9.99",
            order_days_ago=15,
            delivery_days_ago=10,
            order_status=OrderStatus.DELIVERED,
            product_condition=ProductCondition.UNOPENED,
            payment_method="Visa ending in 4242",
        ),
        build_order(
            order_id="ORD-LATE-1002",
            customer_id="CUST-LATE-002",
            product_name="Canvas Travel Backpack",
            product_category="BAGS",
            quantity=1,
            item_price="84.00",
            shipping_amount="7.50",
            order_days_ago=55,
            delivery_days_ago=45,
            order_status=OrderStatus.DELIVERED,
            product_condition=ProductCondition.UNOPENED,
            payment_method="Mastercard ending in 1881",
        ),
        build_order(
            order_id="ORD-FINAL-1003",
            customer_id="CUST-FINAL-003",
            product_name="Limited Edition Running Shoes",
            product_category="FOOTWEAR",
            quantity=1,
            item_price="149.00",
            shipping_amount="8.99",
            order_days_ago=12,
            delivery_days_ago=8,
            order_status=OrderStatus.DELIVERED,
            product_condition=ProductCondition.UNOPENED,
            payment_method="Visa ending in 7654",
            final_sale=True,
        ),
        build_order(
            order_id="ORD-HYGIENE-1004",
            customer_id="CUST-HYGIENE-004",
            product_name="Electric Grooming Kit",
            product_category="HYGIENE",
            quantity=1,
            item_price="79.99",
            shipping_amount="6.99",
            order_days_ago=10,
            delivery_days_ago=6,
            order_status=OrderStatus.DELIVERED,
            product_condition=ProductCondition.OPENED,
            payment_method="American Express ending in 3005",
            hygiene_sensitive=True,
        ),
        build_order(
            order_id="ORD-REFUNDED-1005",
            customer_id="CUST-REFUNDED-005",
            product_name="Smart Fitness Watch",
            product_category="ELECTRONICS",
            quantity=1,
            item_price="219.00",
            shipping_amount="0.00",
            order_days_ago=18,
            delivery_days_ago=12,
            order_status=OrderStatus.DELIVERED,
            product_condition=ProductCondition.UNOPENED,
            payment_method="Visa ending in 9001",
            refund_status=RefundStatus.FULL,
        ),
        build_order(
            order_id="ORD-HIGHVALUE-1006",
            customer_id="CUST-HIGHVALUE-006",
            product_name="Professional Laptop",
            product_category="ELECTRONICS",
            quantity=1,
            item_price="899.00",
            shipping_amount="19.99",
            order_days_ago=9,
            delivery_days_ago=5,
            order_status=OrderStatus.DELIVERED,
            product_condition=ProductCondition.UNOPENED,
            payment_method="Mastercard ending in 6006",
        ),
        build_order(
            order_id="ORD-FRAUD-1007",
            customer_id="CUST-FRAUD-007",
            product_name="Noise Cancelling Headphones",
            product_category="ELECTRONICS",
            quantity=1,
            item_price="249.00",
            shipping_amount="9.00",
            order_days_ago=11,
            delivery_days_ago=7,
            order_status=OrderStatus.DELIVERED,
            product_condition=ProductCondition.UNOPENED,
            payment_method="Visa ending in 0707",
        ),
        build_order(
            order_id="ORD-DAMAGE-1008",
            customer_id="CUST-DAMAGE-008",
            product_name="27-inch Computer Monitor",
            product_category="ELECTRONICS",
            quantity=1,
            item_price="329.00",
            shipping_amount="15.00",
            order_days_ago=7,
            delivery_days_ago=3,
            order_status=OrderStatus.DELIVERED,
            product_condition=ProductCondition.DAMAGED,
            payment_method="Mastercard ending in 8080",
        ),
        build_order(
            order_id="ORD-PRIYA-1009",
            customer_id="CUST-OWNER-A-009",
            product_name="Ceramic Table Lamp",
            product_category="HOME",
            quantity=1,
            item_price="54.00",
            shipping_amount="6.00",
            order_days_ago=13,
            delivery_days_ago=9,
            order_status=OrderStatus.DELIVERED,
            product_condition=ProductCondition.UNOPENED,
            payment_method="Visa ending in 1009",
        ),
        build_order(
            order_id="ORD-OWNER-1010",
            customer_id="CUST-OWNER-B-010",
            product_name="Portable Bluetooth Speaker",
            product_category="ELECTRONICS",
            quantity=1,
            item_price="99.00",
            shipping_amount="5.99",
            order_days_ago=8,
            delivery_days_ago=4,
            order_status=OrderStatus.DELIVERED,
            product_condition=ProductCondition.UNOPENED,
            payment_method="Visa ending in 1010",
        ),
        build_order(
            order_id="ORD-GIFT-1011",
            customer_id="CUST-GIFT-011",
            product_name="Resolve Shop Gift Card",
            product_category="GIFT_CARD",
            quantity=1,
            item_price="100.00",
            shipping_amount="0.00",
            order_days_ago=6,
            delivery_days_ago=6,
            order_status=OrderStatus.DELIVERED,
            product_condition=ProductCondition.UNOPENED,
            payment_method="Mastercard ending in 1111",
        ),
        build_order(
            order_id="ORD-DIGITAL-1012",
            customer_id="CUST-DIGITAL-012",
            product_name="Digital Photography Course",
            product_category="DOWNLOADABLE",
            quantity=1,
            item_price="65.00",
            shipping_amount="0.00",
            order_days_ago=5,
            delivery_days_ago=5,
            order_status=OrderStatus.DELIVERED,
            product_condition=ProductCondition.OPENED,
            payment_method="Visa ending in 1212",
            downloadable=True,
        ),
        build_order(
            order_id="ORD-PERSONAL-1013",
            customer_id="CUST-PERSONAL-013",
            product_name="Engraved Silver Bracelet",
            product_category="JEWELLERY",
            quantity=1,
            item_price="139.00",
            shipping_amount="8.00",
            order_days_ago=14,
            delivery_days_ago=8,
            order_status=OrderStatus.DELIVERED,
            product_condition=ProductCondition.UNOPENED,
            payment_method="American Express ending in 1313",
            personalized=True,
        ),
        build_order(
            order_id="ORD-SHIPPED-1014",
            customer_id="CUST-DELIVERY-014",
            product_name="Standing Desk Mat",
            product_category="OFFICE",
            quantity=1,
            item_price="59.00",
            shipping_amount="7.00",
            order_days_ago=4,
            delivery_days_ago=None,
            order_status=OrderStatus.SHIPPED,
            product_condition=ProductCondition.UNOPENED,
            payment_method="Visa ending in 1414",
        ),
        build_order(
            order_id="ORD-EXTRA-1015",
            customer_id="CUST-EXTRA-015",
            product_name="Premium Coffee Maker",
            product_category="KITCHEN",
            quantity=1,
            item_price="189.00",
            shipping_amount="12.00",
            order_days_ago=17,
            delivery_days_ago=11,
            order_status=OrderStatus.DELIVERED,
            product_condition=ProductCondition.UNOPENED,
            payment_method="Mastercard ending in 1515",
        ),
        build_order(
            order_id="ORD-INCORRECT-1016",
            customer_id="CUST-VALID-001",
            product_name="USB-C Docking Station",
            product_category="ELECTRONICS",
            quantity=1,
            item_price="159.00",
            shipping_amount="8.00",
            order_days_ago=6,
            delivery_days_ago=2,
            order_status=OrderStatus.DELIVERED,
            product_condition=ProductCondition.INCORRECT_ITEM,
            payment_method="Visa ending in 4242",
        ),
        build_order(
            order_id="ORD-DEFECTIVE-1017",
            customer_id="CUST-DAMAGE-008",
            product_name="Smart Home Camera",
            product_category="ELECTRONICS",
            quantity=1,
            item_price="119.00",
            shipping_amount="7.00",
            order_days_ago=8,
            delivery_days_ago=4,
            order_status=OrderStatus.DELIVERED,
            product_condition=ProductCondition.DEFECTIVE,
            payment_method="Mastercard ending in 8080",
        ),
        build_order(
            order_id="ORD-BOUNDARY30-1018",
            customer_id="CUST-LATE-002",
            product_name="Wool Throw Blanket",
            product_category="HOME",
            quantity=1,
            item_price="72.00",
            shipping_amount="6.00",
            order_days_ago=37,
            delivery_days_ago=30,
            order_status=OrderStatus.DELIVERED,
            product_condition=ProductCondition.UNOPENED,
            payment_method="Mastercard ending in 1881",
        ),
        build_order(
            order_id="ORD-CANCELLED-1019",
            customer_id="CUST-DELIVERY-014",
            product_name="Ergonomic Office Chair",
            product_category="OFFICE",
            quantity=1,
            item_price="279.00",
            shipping_amount="20.00",
            order_days_ago=6,
            delivery_days_ago=None,
            order_status=OrderStatus.CANCELLED,
            product_condition=ProductCondition.UNOPENED,
            payment_method="Visa ending in 1414",
        ),
        build_order(
            order_id="ORD-EXACT500-1020",
            customer_id="CUST-EXTRA-015",
            product_name="Damaged Studio Microphone Bundle",
            product_category="ELECTRONICS",
            quantity=1,
            item_price="480.00",
            shipping_amount="20.00",
            order_days_ago=6,
            delivery_days_ago=2,
            order_status=OrderStatus.DELIVERED,
            product_condition=ProductCondition.DAMAGED,
            payment_method="Mastercard ending in 1515",
        ),
        build_order(
            order_id="ORD-DAY31-1021",
            customer_id="CUST-LATE-002",
            product_name="Leather Notebook Cover",
            product_category="STATIONERY",
            quantity=1,
            item_price="46.00",
            shipping_amount="5.00",
            order_days_ago=40,
            delivery_days_ago=31,
            order_status=OrderStatus.DELIVERED,
            product_condition=ProductCondition.UNOPENED,
            payment_method="Mastercard ending in 1881",
        ),
        build_order(
            order_id="ORD-MULTI-1022",
            customer_id="CUST-EXTRA-015",
            product_name="Cotton T-Shirt Pack",
            product_category="APPAREL",
            quantity=3,
            item_price="25.00",
            shipping_amount="6.00",
            order_days_ago=12,
            delivery_days_ago=7,
            order_status=OrderStatus.DELIVERED,
            product_condition=ProductCondition.UNOPENED,
            payment_method="Mastercard ending in 1515",
        ),
    ]


def update_or_create(
    database_session: Session,
    model: type[Customer] | type[Order],
    primary_key: str,
    values: dict[str, Any],
) -> None:
    existing_record = database_session.get(model, primary_key)

    if existing_record is None:
        database_session.add(model(**values))
        return

    for field_name, field_value in values.items():
        setattr(existing_record, field_name, field_value)


def seed_demo_records(
    database_session: Session,
) -> tuple[int, int]:
    """
    Insert or update the deterministic demo customers and orders.

    The session is injected so this function can be reused by the
    command-line seed process, tests, and the demo-reset API.
    """

    customers = customer_records()
    orders = order_records()

    order_counts = Counter(
        order["customer_id"]
        for order in orders
    )

    previous_refund_counts = Counter(
        order["customer_id"]
        for order in orders
        if order["refund_status"] in {
            RefundStatus.FULL,
            RefundStatus.PARTIAL,
        }
    )

    for customer in customers:
        customer["total_orders"] = order_counts[
            customer["customer_id"]
        ]
        customer["previous_refunds"] = (
            previous_refund_counts[
                customer["customer_id"]
            ]
        )

        update_or_create(
            database_session,
            Customer,
            customer["customer_id"],
            customer,
        )

    database_session.flush()

    for order in orders:
        update_or_create(
            database_session,
            Order,
            order["order_id"],
            order,
        )

    database_session.commit()

    return len(customers), len(orders)


def reset_demo_data(
    database_session: Session,
) -> tuple[int, int]:
    """
    Delete operational activity and restore the original demo data.

    The deletion order respects the foreign-key relationships between
    review cases, events, messages, refund requests, sessions, orders,
    and customers.
    """

    database_session.execute(
        delete(HumanReviewCase)
    )
    database_session.execute(
        delete(AgentEvent)
    )
    database_session.execute(
        delete(ChatMessage)
    )
    database_session.execute(
        delete(RefundRequest)
    )
    database_session.execute(
        delete(AgentSession)
    )
    database_session.execute(
        delete(Order)
    )
    database_session.execute(
        delete(Customer)
    )

    database_session.flush()

    return seed_demo_records(
        database_session
    )


def seed_database() -> None:
    """Create tables and seed the development database."""

    init_database()

    with SessionLocal() as database_session:
        customer_count, order_count = (
            seed_demo_records(
                database_session
            )
        )

    print(
        "ResolveAI demo database seeded successfully."
    )
    print(
        f"Customers in seed dataset: {customer_count}"
    )
    print(
        f"Orders in seed dataset: {order_count}"
    )


if __name__ == "__main__":
    seed_database()
