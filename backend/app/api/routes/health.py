from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import check_database_connection


router = APIRouter(tags=["System"])


class HealthResponse(BaseModel):
    """Response returned when the backend is healthy."""

    status: Literal["ok"]
    app_name: str
    version: str
    environment: str
    database: Literal["connected"]
    timestamp: datetime


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check backend health",
)
def health_check() -> HealthResponse:
    """Confirm that the API and database are available."""

    try:
        check_database_connection()
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The database is currently unavailable.",
        ) from error

    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        database="connected",
        timestamp=datetime.now(timezone.utc),
    )