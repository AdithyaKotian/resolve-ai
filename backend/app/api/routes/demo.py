from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas import DemoResetResponse
from app.seed import reset_demo_data


router = APIRouter(
    prefix="/demo",
    tags=["Demo Controls"],
)


@router.post(
    "/reset",
    response_model=DemoResetResponse,
    summary="Reset the ResolveAI demo environment",
)
def reset_demo_environment(
    database_session: Session = Depends(get_db),
) -> DemoResetResponse:
    """
    Clear operational activity and restore the original seed data.

    This endpoint is disabled in production.
    """

    if settings.app_env == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "The demo reset endpoint is disabled "
                "in production."
            ),
        )

    try:
        customer_count, order_count = (
            reset_demo_data(
                database_session
            )
        )

    except SQLAlchemyError as error:
        database_session.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "The demo environment could not "
                "be reset."
            ),
        ) from error

    return DemoResetResponse(
        message=(
            "ResolveAI demo environment reset successfully."
        ),
        customers=customer_count,
        orders=order_count,
        sessions=0,
        events=0,
    )