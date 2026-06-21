from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    AgentEvent,
    AgentSession,
    ChatMessage,
    PolicyDecision,
    RefundRequest,
)
from app.schemas import (
    AgentEventResponse,
    ChatMessageResponse,
    DecisionResult,
    SessionDetailResponse,
    SessionListResponse,
    SessionMetrics,
    SessionSummary,
)


router = APIRouter(
    prefix="/sessions",
    tags=["Agent Sessions"],
)


def build_session_summary(
    database_session: Session,
    agent_session: AgentSession,
) -> SessionSummary:
    event_count = (
        database_session.scalar(
            select(func.count())
            .select_from(AgentEvent)
            .where(
                AgentEvent.session_id
                == agent_session.session_id
            )
        )
        or 0
    )

    tool_failures = (
        database_session.scalar(
            select(func.count())
            .select_from(AgentEvent)
            .where(
                AgentEvent.session_id
                == agent_session.session_id,
                AgentEvent.event_type
                == "TOOL_FAILED",
            )
        )
        or 0
    )

    return SessionSummary(
        session_id=agent_session.session_id,
        customer_id=agent_session.customer_id,
        order_id=agent_session.order_id,
        status=agent_session.status,
        final_decision=(
            agent_session.final_decision
        ),
        created_at=agent_session.created_at,
        updated_at=agent_session.updated_at,
        event_count=int(event_count),
        tool_failures=int(tool_failures),
    )


def build_decision_result(
    refund_request: RefundRequest | None,
) -> DecisionResult | None:
    if (
        refund_request is None
        or refund_request.decision is None
    ):
        return None

    return DecisionResult(
        decision=refund_request.decision,
        order_id=refund_request.order_id,
        refundable_amount=(
            refund_request.refundable_amount
        ),
        rule_codes=list(
            refund_request.rule_codes
        ),
        reasons=list(
            refund_request.reasons
        ),
        refund_reference=(
            refund_request.refund_reference
        ),
        payment_method=None,
    )


@router.get(
    "",
    response_model=SessionListResponse,
    summary="List recent agent sessions",
)
def list_sessions(
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    database_session: Session = Depends(get_db),
) -> SessionListResponse:
    agent_sessions = database_session.scalars(
        select(AgentSession)
        .order_by(
            AgentSession.updated_at.desc()
        )
        .limit(limit)
    ).all()

    total_sessions = (
        database_session.scalar(
            select(func.count()).select_from(
                AgentSession
            )
        )
        or 0
    )

    approved_refunds = (
        database_session.scalar(
            select(func.count())
            .select_from(AgentSession)
            .where(
                AgentSession.final_decision
                == PolicyDecision.APPROVED
            )
        )
        or 0
    )

    denied_refunds = (
        database_session.scalar(
            select(func.count())
            .select_from(AgentSession)
            .where(
                AgentSession.final_decision
                == PolicyDecision.DENIED
            )
        )
        or 0
    )

    escalated_requests = (
        database_session.scalar(
            select(func.count())
            .select_from(AgentSession)
            .where(
                AgentSession.final_decision
                == PolicyDecision.ESCALATED
            )
        )
        or 0
    )

    tool_failures = (
        database_session.scalar(
            select(func.count())
            .select_from(AgentEvent)
            .where(
                AgentEvent.event_type
                == "TOOL_FAILED"
            )
        )
        or 0
    )

    return SessionListResponse(
        metrics=SessionMetrics(
            total_sessions=int(total_sessions),
            approved_refunds=int(
                approved_refunds
            ),
            denied_refunds=int(
                denied_refunds
            ),
            escalated_requests=int(
                escalated_requests
            ),
            tool_failures=int(tool_failures),
        ),
        sessions=[
            build_session_summary(
                database_session,
                agent_session,
            )
            for agent_session in agent_sessions
        ],
    )


@router.get(
    "/{session_id}",
    response_model=SessionDetailResponse,
    summary="Get one agent session",
)
def get_session(
    session_id: str,
    database_session: Session = Depends(get_db),
) -> SessionDetailResponse:
    agent_session = database_session.get(
        AgentSession,
        session_id,
    )

    if agent_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent session not found.",
        )

    messages = database_session.scalars(
        select(ChatMessage)
        .where(
            ChatMessage.session_id == session_id
        )
        .order_by(
            ChatMessage.created_at.asc(),
            ChatMessage.message_id.asc(),
        )
    ).all()

    latest_refund_request = (
        database_session.scalar(
            select(RefundRequest)
            .where(
                RefundRequest.session_id
                == session_id
            )
            .order_by(
                RefundRequest.created_at.desc()
            )
        )
    )

    return SessionDetailResponse(
        session=build_session_summary(
            database_session,
            agent_session,
        ),
        messages=[
            ChatMessageResponse.model_validate(
                message
            )
            for message in messages
        ],
        decision_result=build_decision_result(
            latest_refund_request
        ),
    )


@router.get(
    "/{session_id}/events",
    response_model=list[AgentEventResponse],
    summary="List structured execution events",
)
def list_session_events(
    session_id: str,
    database_session: Session = Depends(get_db),
) -> list[AgentEventResponse]:
    agent_session = database_session.get(
        AgentSession,
        session_id,
    )

    if agent_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent session not found.",
        )

    events = database_session.scalars(
        select(AgentEvent)
        .where(
            AgentEvent.session_id == session_id
        )
        .order_by(
            AgentEvent.timestamp.asc(),
            AgentEvent.event_id.asc(),
        )
    ).all()

    return [
        AgentEventResponse.model_validate(event)
        for event in events
    ]