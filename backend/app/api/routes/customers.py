from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer, Order
from app.schemas import (
    CustomerDetail,
    CustomerOrdersResponse,
    CustomerSummary,
    OrderSummary,
)


router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.get(
    "",
    response_model=list[CustomerSummary],
    summary="List demo CRM customers",
)
def list_customers(
    database_session: Session = Depends(get_db),
) -> list[CustomerSummary]:
    customers = database_session.scalars(
        select(Customer).order_by(
            Customer.full_name.asc()
        )
    ).all()

    return [
        CustomerSummary.model_validate(customer)
        for customer in customers
    ]


@router.get(
    "/{customer_id}",
    response_model=CustomerDetail,
    summary="Get one CRM customer",
)
def get_customer(
    customer_id: str,
    database_session: Session = Depends(get_db),
) -> CustomerDetail:
    customer = database_session.get(
        Customer,
        customer_id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        )

    return CustomerDetail.model_validate(
        customer
    )


@router.get(
    "/{customer_id}/orders",
    response_model=CustomerOrdersResponse,
    summary="List orders belonging to a customer",
)
def list_customer_orders(
    customer_id: str,
    database_session: Session = Depends(get_db),
) -> CustomerOrdersResponse:
    customer = database_session.get(
        Customer,
        customer_id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        )

    orders = database_session.scalars(
        select(Order)
        .where(
            Order.customer_id == customer_id
        )
        .order_by(
            Order.order_date.desc()
        )
    ).all()

    return CustomerOrdersResponse(
        customer=CustomerSummary.model_validate(
            customer
        ),
        orders=[
            OrderSummary.model_validate(order)
            for order in orders
        ],
    )