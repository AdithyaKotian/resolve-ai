from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.graph import build_refund_graph
from app.api.routes.chat import router as chat_router
from app.api.routes.customers import (
    router as customers_router,
)
from app.api.routes.health import router as health_router
from app.api.routes.sessions import (
    router as sessions_router,
)
from app.api.routes.websocket import (
    router as websocket_router,
)
from app.config import settings
from app.database import (
    check_database_connection,
    engine,
    init_database,
)


@asynccontextmanager
async def lifespan(
    application: FastAPI,
) -> AsyncIterator[None]:
    """Initialize local resources and release them at shutdown."""

    init_database()
    check_database_connection()

    application.state.refund_graph = (
        build_refund_graph()
    )

    yield

    engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description=(
        "AI customer-support agent for e-commerce "
        "refund requests."
    ),
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_origin,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    health_router,
    prefix=settings.api_prefix,
)

app.include_router(
    customers_router,
    prefix=settings.api_prefix,
)

app.include_router(
    chat_router,
    prefix=settings.api_prefix,
)

app.include_router(
    sessions_router,
    prefix=settings.api_prefix,
)

app.include_router(websocket_router)


@app.get(
    "/",
    tags=["System"],
)
def root() -> dict[str, str]:
    """Return useful local development links."""

    return {
        "message": (
            "ResolveAI backend is running."
        ),
        "health": (
            f"{settings.api_prefix}/health"
        ),
        "documentation": "/docs",
        "customer_api": (
            f"{settings.api_prefix}/customers"
        ),
        "chat_api": (
            f"{settings.api_prefix}/chat"
        ),
        "sessions_api": (
            f"{settings.api_prefix}/sessions"
        ),
    }