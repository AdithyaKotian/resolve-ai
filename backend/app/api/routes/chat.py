from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.graph import create_initial_state
from app.agent.tools import generate_identifier
from app.database import get_db
from app.models import (
    AgentSession,
    ChatMessage,
    Customer,
    PolicyDecision,
    SessionStatus,
)
from app.schemas import (
    AgentEventResponse,
    ChatRequest,
    ChatResponse,
    DecisionResult,
)
from app.services.event_service import (
    persist_trace_event,
)
from app.services.realtime import realtime_manager


router = APIRouter(
    prefix="/chat",
    tags=["Agent Chat"],
)


def build_conversation_input(
    messages: list[ChatMessage],
) -> str:
    """
    Combine recent customer messages so missing-information
    follow-ups keep their earlier context.
    """

    customer_messages = [
        message.content
        for message in messages
        if message.role == "user"
    ]

    return "\n".join(
        customer_messages[-8:]
    )


def normalize_final_decision(
    decision: Any,
) -> PolicyDecision | None:
    if isinstance(decision, PolicyDecision):
        return decision

    if isinstance(decision, str):
        try:
            return PolicyDecision(decision)
        except ValueError:
            return None

    return None


@router.post(
    "",
    response_model=ChatResponse,
    summary="Process one customer refund message",
)
async def process_chat_message(
    payload: ChatRequest,
    request: Request,
    database_session: Session = Depends(get_db),
) -> ChatResponse:
    customer = database_session.get(
        Customer,
        payload.customer_id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        )

    session_id = (
        payload.session_id
        or generate_identifier("SESSION")
    )

    agent_session = database_session.get(
        AgentSession,
        session_id,
    )

    if agent_session is None:
        agent_session = AgentSession(
            session_id=session_id,
            customer_id=payload.customer_id,
            order_id=payload.order_id,
            status=SessionStatus.ACTIVE,
        )

        database_session.add(agent_session)

    else:
        if (
            agent_session.customer_id
            != payload.customer_id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "The session belongs to a different "
                    "customer."
                ),
            )

        if (
            agent_session.status
            == SessionStatus.COMPLETED
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This refund session is already complete. "
                    "Start a new conversation."
                ),
            )

        agent_session.status = SessionStatus.ACTIVE

        if payload.order_id:
            agent_session.order_id = payload.order_id

    customer_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=payload.message,
    )

    database_session.add(customer_message)
    database_session.commit()

    conversation_messages = (
        database_session.scalars(
            select(ChatMessage)
            .where(
                ChatMessage.session_id
                == session_id
            )
            .order_by(
                ChatMessage.created_at.asc(),
                ChatMessage.message_id.asc(),
            )
        ).all()
    )

    combined_user_message = (
        build_conversation_input(
            conversation_messages
        )
    )

    initial_state = create_initial_state(
        session_id=session_id,
        customer_id=payload.customer_id,
        order_id=(
            payload.order_id
            or agent_session.order_id
        ),
        user_message=combined_user_message,
        simulate_transient_failure=(
            payload.simulate_transient_failure
        ),
    )

    refund_graph = (
        request.app.state.refund_graph
    )

    final_state: dict[str, Any] = dict(
        initial_state
    )

    persisted_trace_count = 0

    try:
        async for graph_state in refund_graph.astream(
            initial_state,
            stream_mode="values",
        ):
            final_state = dict(graph_state)

            complete_trace = final_state.get(
                "execution_trace",
                [],
            )

            new_trace_events = complete_trace[
                persisted_trace_count:
            ]

            for trace_event in new_trace_events:
                stored_event = persist_trace_event(
                    database_session,
                    session_id=session_id,
                    trace_event=trace_event,
                )

                database_session.commit()
                database_session.refresh(
                    stored_event
                )

                event_response = (
                    AgentEventResponse.model_validate(
                        stored_event
                    )
                )

                await realtime_manager.broadcast(
                    session_id,
                    {
                        "type": "AGENT_EVENT",
                        "session_id": session_id,
                        "event": event_response.model_dump(
                            mode="json"
                        ),
                    },
                )

            persisted_trace_count = len(
                complete_trace
            )

    except Exception as error:
        database_session.rollback()

        agent_session = database_session.get(
            AgentSession,
            session_id,
        )

        if agent_session is not None:
            agent_session.status = (
                SessionStatus.FAILED
            )
            agent_session.final_response = (
                "The refund workflow could not be "
                "completed."
            )

            database_session.add(
                ChatMessage(
                    session_id=session_id,
                    role="assistant",
                    content=(
                        "I’m sorry, but the refund workflow "
                        "could not be completed. No refund "
                        "has been issued."
                    ),
                )
            )

            database_session.commit()

        await realtime_manager.broadcast(
            session_id,
            {
                "type": "SESSION_ERROR",
                "session_id": session_id,
                "message": (
                    "The refund workflow could not be "
                    "completed."
                ),
            },
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "The refund workflow could not be "
                "completed."
            ),
        ) from error

    assistant_message = str(
        final_state.get("final_response")
        or (
            "The refund workflow could not produce "
            "a response."
        )
    )

    final_decision = normalize_final_decision(
        final_state.get("final_decision")
    )

    agent_session = database_session.get(
        AgentSession,
        session_id,
    )

    if agent_session is None:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="The agent session could not be saved.",
        )

    resolved_order_id = final_state.get(
        "order_id"
    )

    if isinstance(resolved_order_id, str):
        agent_session.order_id = (
            resolved_order_id
        )

    agent_session.final_decision = (
        final_decision
    )
    agent_session.final_response = (
        assistant_message
    )

    if final_decision is not None:
        agent_session.status = (
            SessionStatus.COMPLETED
        )
    elif final_state.get("error_code"):
        agent_session.status = SessionStatus.FAILED
    else:
        agent_session.status = SessionStatus.ACTIVE

    database_session.add(
        ChatMessage(
            session_id=session_id,
            role="assistant",
            content=assistant_message,
        )
    )

    database_session.commit()
    database_session.refresh(agent_session)

    policy_result = final_state.get(
        "policy_result"
    )

    decision_result: DecisionResult | None = None

    if (
        policy_result is not None
        and final_decision is not None
        and agent_session.order_id is not None
    ):
        decision_result = DecisionResult(
            decision=final_decision,
            order_id=agent_session.order_id,
            refundable_amount=(
                policy_result.refundable_amount
            ),
            rule_codes=list(
                policy_result.rule_codes
            ),
            reasons=list(
                policy_result.reasons
            ),
            refund_reference=final_state.get(
                "refund_reference"
            ),
            human_review_case_id=(
                final_state.get(
                    "human_review_case_id"
                )
            ),
            payment_method=(
                policy_result.refund_method
            ),
        )

    await realtime_manager.broadcast(
        session_id,
        {
            "type": "SESSION_UPDATED",
            "session_id": session_id,
            "status": agent_session.status.value,
            "final_decision": (
                final_decision.value
                if final_decision
                else None
            ),
        },
    )

    return ChatResponse(
        session_id=session_id,
        session_status=agent_session.status,
        assistant_message=assistant_message,
        decision_result=decision_result,
        retry_count=int(
            final_state.get(
                "total_retry_count",
                0,
            )
        ),
    )