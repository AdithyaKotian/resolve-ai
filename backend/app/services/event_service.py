from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from sqlalchemy.orm import Session

from app.models import AgentEvent, PolicyDecision


def parse_event_timestamp(
    timestamp_value: Any,
) -> datetime:
    """Convert a trace timestamp into a UTC datetime."""

    if isinstance(timestamp_value, datetime):
        return timestamp_value

    if isinstance(timestamp_value, str):
        try:
            parsed_timestamp = datetime.fromisoformat(
                timestamp_value
            )

            if parsed_timestamp.tzinfo is None:
                return parsed_timestamp.replace(
                    tzinfo=timezone.utc
                )

            return parsed_timestamp

        except ValueError:
            pass

    return datetime.now(timezone.utc)


def parse_policy_decision(
    decision_value: Any,
) -> PolicyDecision | None:
    """Safely convert an event decision into its enum."""

    if isinstance(decision_value, PolicyDecision):
        return decision_value

    if isinstance(decision_value, str):
        try:
            return PolicyDecision(decision_value)
        except ValueError:
            return None

    return None


def persist_trace_event(
    database_session: Session,
    *,
    session_id: str,
    trace_event: Mapping[str, Any],
) -> AgentEvent:
    """Save one safe LangGraph trace event."""

    stored_event = AgentEvent(
        session_id=session_id,
        timestamp=parse_event_timestamp(
            trace_event.get("timestamp")
        ),
        event_type=str(
            trace_event.get(
                "event_type",
                "UNKNOWN_EVENT",
            )
        ),
        graph_node=trace_event.get("graph_node"),
        tool_name=trace_event.get("tool_name"),
        sanitized_input=trace_event.get(
            "input_summary"
        ),
        tool_output_summary=trace_event.get(
            "output_summary"
        ),
        matched_policy_rule_codes=list(
            trace_event.get("rule_codes") or []
        ),
        decision=parse_policy_decision(
            trace_event.get("decision")
        ),
        execution_status=str(
            trace_event.get(
                "execution_status",
                "UNKNOWN",
            )
        ),
        latency_ms=trace_event.get("latency_ms"),
        retry_count=int(
            trace_event.get("retry_count") or 0
        ),
        error_message=trace_event.get(
            "error_message"
        ),
    )

    database_session.add(stored_event)
    database_session.flush()

    return stored_event