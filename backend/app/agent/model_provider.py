from __future__ import annotations

import re
from decimal import Decimal
from typing import Protocol

from openai import OpenAI, OpenAIError
from pydantic import BaseModel, Field

from app.agent.prompts import (
    FINAL_RESPONSE_SYSTEM_PROMPT,
    REQUEST_EXTRACTION_SYSTEM_PROMPT,
)
from app.config import settings
from app.models import PolicyDecision
from app.policy.types import RefundReason


class ModelProviderError(RuntimeError):
    """Safe wrapper for model-provider failures."""


class ParsedRefundRequest(BaseModel):
    """Structured information extracted from customer language."""

    order_id: str | None = None

    requested_quantity: int | None = Field(
        default=None,
        ge=1,
    )

    reason: RefundReason | None = None


class FinalResponseContext(BaseModel):
    """Authoritative information used to word the final response."""

    decision: PolicyDecision
    order_id: str

    refundable_amount: Decimal = Decimal("0.00")
    rule_codes: list[str]
    reasons: list[str]

    payment_method: str | None = None
    refund_reference: str | None = None
    human_review_case_id: str | None = None


class ModelProvider(Protocol):
    """Interface implemented by every model provider."""

    name: str

    def parse_request(
        self,
        user_message: str,
    ) -> ParsedRefundRequest:
        ...

    def generate_final_response(
        self,
        context: FinalResponseContext,
    ) -> str:
        ...


class DeterministicModelProvider:
    """
    Clearly labelled development fallback.

    It uses predictable keyword and regular-expression matching
    and must not be described as a real language model.
    """

    name = "deterministic-development-fallback"

    ORDER_PATTERN = re.compile(
        r"\bORD-[A-Z0-9-]+\b",
        re.IGNORECASE,
    )

    QUANTITY_PATTERN = re.compile(
        r"\b(\d+)\s*"
        r"(?:item|items|unit|units|piece|pieces)\b",
        re.IGNORECASE,
    )

    def parse_request(
        self,
        user_message: str,
    ) -> ParsedRefundRequest:
        normalized_message = user_message.strip()
        lowered_message = normalized_message.lower()

        order_match = self.ORDER_PATTERN.search(
            normalized_message
        )
        quantity_match = self.QUANTITY_PATTERN.search(
            normalized_message
        )

        reason: RefundReason | None = None

        if any(
            phrase in lowered_message
            for phrase in (
                "wrong item",
                "incorrect item",
                "different item",
                "item i did not order",
            )
        ):
            reason = RefundReason.INCORRECT_ITEM

        elif any(
            phrase in lowered_message
            for phrase in (
                "damaged",
                "cracked",
                "broken on arrival",
                "arrived broken",
            )
        ):
            reason = RefundReason.DAMAGED

        elif any(
            phrase in lowered_message
            for phrase in (
                "defective",
                "faulty",
                "not working",
                "doesn't work",
                "does not work",
            )
        ):
            reason = RefundReason.DEFECTIVE

        elif any(
            phrase in lowered_message
            for phrase in (
                "changed my mind",
                "change of mind",
                "do not want it",
                "don't want it",
                "no longer want",
            )
        ):
            reason = RefundReason.CHANGE_OF_MIND

        return ParsedRefundRequest(
            order_id=(
                order_match.group(0).upper()
                if order_match
                else None
            ),
            requested_quantity=(
                int(quantity_match.group(1))
                if quantity_match
                else None
            ),
            reason=reason,
        )

    def generate_final_response(
        self,
        context: FinalResponseContext,
    ) -> str:
        rule_text = ", ".join(context.rule_codes)
        explanation = " ".join(context.reasons)

        if context.decision == PolicyDecision.APPROVED:
            refund_reference_text = (
                f" Refund reference: "
                f"{context.refund_reference}."
                if context.refund_reference
                else ""
            )

            return (
                f"Your refund for order {context.order_id} "
                f"has been approved for "
                f"${context.refundable_amount:.2f}. "
                f"It will be returned to the original payment "
                f"method, {context.payment_method}. "
                f"Applicable policy rules: {rule_text}. "
                f"{explanation}"
                f"{refund_reference_text}"
            )

        if context.decision == PolicyDecision.DENIED:
            return (
                f"I’m sorry, but the refund request for order "
                f"{context.order_id} has been denied. "
                f"Applicable policy rules: {rule_text}. "
                f"{explanation}"
            )

        return (
            f"Your refund request for order "
            f"{context.order_id} requires human review. "
            f"No refund has been issued automatically. "
            f"Applicable policy rules: {rule_text}. "
            f"{explanation} "
            f"Review case: "
            f"{context.human_review_case_id or 'pending'}."
        )


class OpenAIModelProvider:
    """OpenAI implementation using structured request extraction."""

    name = "openai"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
    ) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def parse_request(
        self,
        user_message: str,
    ) -> ParsedRefundRequest:
        try:
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": (
                            REQUEST_EXTRACTION_SYSTEM_PROMPT
                        ),
                    },
                    {
                        "role": "user",
                        "content": user_message,
                    },
                ],
                text_format=ParsedRefundRequest,
            )
        except OpenAIError as error:
            raise ModelProviderError(
                "The configured language model is unavailable."
            ) from error

        parsed_response = response.output_parsed

        if parsed_response is None:
            raise ModelProviderError(
                "The language model returned no structured data."
            )

        return parsed_response

    def generate_final_response(
        self,
        context: FinalResponseContext,
    ) -> str:
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=FINAL_RESPONSE_SYSTEM_PROMPT,
                input=context.model_dump_json(),
            )
        except OpenAIError as error:
            raise ModelProviderError(
                "The configured language model is unavailable."
            ) from error

        generated_text = response.output_text.strip()

        if not generated_text:
            raise ModelProviderError(
                "The language model returned an empty response."
            )

        return generated_text


def create_model_provider() -> ModelProvider:
    """Create the configured model provider."""

    if (
        settings.llm_provider == "openai"
        and settings.openai_api_key
    ):
        return OpenAIModelProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )

    return DeterministicModelProvider()