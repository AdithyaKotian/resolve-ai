from __future__ import annotations

from app.agent.state import AgentState
from app.models import PolicyDecision


def retry_is_available(
    state: AgentState,
) -> bool:
    """Return whether another retry is allowed."""

    return (
        state.get("transient_error", False)
        and state.get("retry_count", 0)
        < state.get("max_retries", 2)
    )


def route_after_understanding(
    state: AgentState,
) -> str:
    if state.get("error_code"):
        return "generate_final_response"

    if state.get("missing_fields"):
        return "ask_customer"

    return "fetch_customer"


def route_after_customer_lookup(
    state: AgentState,
) -> str:
    if state.get("error_code"):
        if retry_is_available(state):
            return "retry_tool"

        return "generate_final_response"

    return "fetch_order"


def route_after_order_lookup(
    state: AgentState,
) -> str:
    if state.get("error_code"):
        if retry_is_available(state):
            return "retry_tool"

        return "generate_final_response"

    if state.get("missing_fields"):
        return "ask_customer"

    return "load_policy"


def route_after_policy_load(
    state: AgentState,
) -> str:
    if state.get("error_code"):
        if retry_is_available(state):
            return "retry_tool"

        return "generate_final_response"

    return "evaluate_refund_policy"


def route_after_policy_evaluation(
    state: AgentState,
) -> str:
    if state.get("error_code"):
        if retry_is_available(state):
            return "retry_tool"

        return "generate_final_response"

    policy_result = state.get("policy_result")

    if policy_result is None:
        return "generate_final_response"

    if (
        policy_result.decision
        == PolicyDecision.APPROVED
    ):
        return "execute_refund"

    if (
        policy_result.decision
        == PolicyDecision.DENIED
    ):
        return "record_denial"

    return "create_human_review"


def route_after_action(
    state: AgentState,
) -> str:
    if state.get("error_code"):
        if retry_is_available(state):
            return "retry_tool"

    return "generate_final_response"


def route_after_retry(
    state: AgentState,
) -> str:
    retryable_nodes = {
        "fetch_customer",
        "fetch_order",
        "load_policy",
        "evaluate_refund_policy",
        "execute_refund",
        "record_denial",
        "create_human_review",
    }

    failed_node = state.get("last_failed_node")

    if failed_node in retryable_nodes:
        return failed_node

    return "generate_final_response"