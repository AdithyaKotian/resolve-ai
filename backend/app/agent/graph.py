from __future__ import annotations

from typing import Callable

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.agent.model_provider import (
    ModelProvider,
    create_model_provider,
)
from app.agent.nodes import (
    AgentToolset,
    RefundGraphNodes,
)
from app.agent.routing import (
    route_after_action,
    route_after_customer_lookup,
    route_after_order_lookup,
    route_after_policy_evaluation,
    route_after_policy_load,
    route_after_retry,
    route_after_understanding,
)
from app.agent.state import AgentState
from app.config import settings
from app.database import SessionLocal


def build_refund_graph(
    *,
    session_factory: Callable[
        [],
        Session,
    ] = SessionLocal,
    model_provider: ModelProvider | None = None,
    toolset: AgentToolset | None = None,
):
    """Build and compile the ResolveAI refund graph."""

    selected_provider = (
        model_provider or create_model_provider()
    )
    selected_toolset = toolset or AgentToolset()

    nodes = RefundGraphNodes(
        session_factory=session_factory,
        model_provider=selected_provider,
        toolset=selected_toolset,
    )

    builder = StateGraph(AgentState)

    builder.add_node(
        "understand_request",
        nodes.understand_request,
    )
    builder.add_node(
        "ask_customer",
        nodes.ask_customer,
    )
    builder.add_node(
        "fetch_customer",
        nodes.fetch_customer,
    )
    builder.add_node(
        "fetch_order",
        nodes.fetch_order,
    )
    builder.add_node(
        "load_policy",
        nodes.load_policy,
    )
    builder.add_node(
        "evaluate_refund_policy",
        nodes.evaluate_refund_policy,
    )
    builder.add_node(
        "execute_refund",
        nodes.execute_refund,
    )
    builder.add_node(
        "record_denial",
        nodes.record_denial,
    )
    builder.add_node(
        "create_human_review",
        nodes.create_human_review,
    )
    builder.add_node(
        "retry_tool",
        nodes.retry_tool,
    )
    builder.add_node(
        "generate_final_response",
        nodes.generate_final_response,
    )

    builder.add_edge(
        START,
        "understand_request",
    )

    builder.add_conditional_edges(
        "understand_request",
        route_after_understanding,
        {
            "ask_customer": "ask_customer",
            "fetch_customer": "fetch_customer",
            "generate_final_response": (
                "generate_final_response"
            ),
        },
    )

    builder.add_conditional_edges(
        "fetch_customer",
        route_after_customer_lookup,
        {
            "fetch_order": "fetch_order",
            "retry_tool": "retry_tool",
            "generate_final_response": (
                "generate_final_response"
            ),
        },
    )

    builder.add_conditional_edges(
        "fetch_order",
        route_after_order_lookup,
        {
            "ask_customer": "ask_customer",
            "load_policy": "load_policy",
            "retry_tool": "retry_tool",
            "generate_final_response": (
                "generate_final_response"
            ),
        },
    )

    builder.add_conditional_edges(
        "load_policy",
        route_after_policy_load,
        {
            "evaluate_refund_policy": (
                "evaluate_refund_policy"
            ),
            "retry_tool": "retry_tool",
            "generate_final_response": (
                "generate_final_response"
            ),
        },
    )

    builder.add_conditional_edges(
        "evaluate_refund_policy",
        route_after_policy_evaluation,
        {
            "execute_refund": "execute_refund",
            "record_denial": "record_denial",
            "create_human_review": (
                "create_human_review"
            ),
            "retry_tool": "retry_tool",
            "generate_final_response": (
                "generate_final_response"
            ),
        },
    )

    for action_node in (
        "execute_refund",
        "record_denial",
        "create_human_review",
    ):
        builder.add_conditional_edges(
            action_node,
            route_after_action,
            {
                "retry_tool": "retry_tool",
                "generate_final_response": (
                    "generate_final_response"
                ),
            },
        )

    builder.add_conditional_edges(
        "retry_tool",
        route_after_retry,
        {
            "fetch_customer": "fetch_customer",
            "fetch_order": "fetch_order",
            "load_policy": "load_policy",
            "evaluate_refund_policy": (
                "evaluate_refund_policy"
            ),
            "execute_refund": "execute_refund",
            "record_denial": "record_denial",
            "create_human_review": (
                "create_human_review"
            ),
            "generate_final_response": (
                "generate_final_response"
            ),
        },
    )

    builder.add_edge(
        "ask_customer",
        END,
    )
    builder.add_edge(
        "generate_final_response",
        END,
    )

    return builder.compile()


def create_initial_state(
    *,
    session_id: str,
    user_message: str,
    customer_id: str | None = None,
    order_id: str | None = None,
    simulate_transient_failure: bool = False,
) -> AgentState:
    """Create a clean state for one graph execution."""

    return AgentState(
        session_id=session_id,
        customer_id=customer_id,
        order_id=order_id,
        user_message=user_message,
        conversation_messages=[
            {
                "role": "user",
                "content": user_message,
            }
        ],
        execution_trace=[],
        missing_fields=[],
        policy_rule_codes=[],
        retry_count=0,
        total_retry_count=0,
        max_retries=settings.max_tool_retries,
        transient_error=False,
        simulate_transient_failure=(
            simulate_transient_failure
        ),
        simulated_failure_consumed=False,
        model_provider_name="unresolved",
    )