from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """Manage local WebSocket connections by agent session."""

    def __init__(self) -> None:
        self._connections: dict[
            str,
            list[WebSocket],
        ] = defaultdict(list)

    async def connect(
        self,
        session_id: str,
        websocket: WebSocket,
    ) -> None:
        await websocket.accept()

        self._connections[session_id].append(
            websocket
        )

    def disconnect(
        self,
        session_id: str,
        websocket: WebSocket,
    ) -> None:
        session_connections = self._connections.get(
            session_id,
            [],
        )

        if websocket in session_connections:
            session_connections.remove(websocket)

        if not session_connections:
            self._connections.pop(
                session_id,
                None,
            )

    async def broadcast(
        self,
        session_id: str,
        payload: dict[str, Any],
    ) -> None:
        disconnected_connections: list[
            WebSocket
        ] = []

        for websocket in list(
            self._connections.get(session_id, [])
        ):
            try:
                await websocket.send_json(payload)
            except RuntimeError:
                disconnected_connections.append(
                    websocket
                )

        for websocket in disconnected_connections:
            self.disconnect(
                session_id,
                websocket,
            )


realtime_manager = ConnectionManager()