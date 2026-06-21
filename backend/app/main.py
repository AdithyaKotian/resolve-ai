from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.config import settings
from app.database import check_database_connection, engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Run startup and shutdown operations for the application."""

    check_database_connection()

    yield

    engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="AI customer-support agent for e-commerce refund requests.",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    health_router,
    prefix=settings.api_prefix,
)


@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    """Return useful links for developers running the backend locally."""

    return {
        "message": "ResolveAI backend is running.",
        "health": f"{settings.api_prefix}/health",
        "documentation": "/docs",
    }