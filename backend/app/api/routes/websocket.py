from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy import select

from app.database import SessionLocal
from app.models import AgentEvent, AgentSession
from app.schemas import AgentEventResponse
from app.services.realtime import realtime_manager


router = APIRouter(
    tags=["Realtime"],
)


@router.websocket(
    "/ws/sessions/{session_id}"
)
async def session_event_websocket(
    websocket: WebSocket,
    session_id: str,
) -> None:
    await realtime_manager.connect(
        session_id,
        websocket,
    )

    try:
        with SessionLocal() as database_session:
            agent_session = database_session.get(
                AgentSession,
                session_id,
            )

            if agent_session is None:
                await websocket.send_json(
                    {
                        "type": "ERROR",
                        "message": (
                            "Agent session not found."
                        ),
                    }
                )

                await websocket.close(code=4404)

                realtime_manager.disconnect(
                    session_id,
                    websocket,
                )

                return

            stored_events = (
                database_session.scalars(
                    select(AgentEvent)
                    .where(
                        AgentEvent.session_id
                        == session_id
                    )
                    .order_by(
                        AgentEvent.timestamp.asc(),
                        AgentEvent.event_id.asc(),
                    )
                ).all()
            )

            history = [
                AgentEventResponse.model_validate(
                    event
                ).model_dump(mode="json")
                for event in stored_events
            ]

        await websocket.send_json(
            {
                "type": "SESSION_HISTORY",
                "session_id": session_id,
                "events": history,
            }
        )

        while True:
            client_message = (
                await websocket.receive_text()
            )

            if client_message.strip().lower() == "ping":
                await websocket.send_json(
                    {
                        "type": "PONG",
                        "session_id": session_id,
                    }
                )

    except WebSocketDisconnect:
        realtime_manager.disconnect(
            session_id,
            websocket,
        )

    except RuntimeError:
        realtime_manager.disconnect(
            session_id,
            websocket,
        )