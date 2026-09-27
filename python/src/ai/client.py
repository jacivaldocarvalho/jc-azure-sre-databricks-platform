"""Abstraction over AI model invocation.

Provides a single entry point for the summarizer, which decides at
runtime between:

    - Azure OpenAI (when AZURE_OPENAI_ENABLED=true and the endpoint is set)
    - Deterministic fallback (when not enabled)

The choice is controlled by environment variables so the same code
runs in both modes without modification.
"""

import os
from dataclasses import dataclass
from typing import Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AIResponse:
    """Result of an AI invocation."""

    text: str
    model: str
    input_tokens: int
    output_tokens: int
    is_fallback: bool


def is_ai_enabled() -> bool:
    """Return True if Azure OpenAI is enabled and configured."""
    if os.getenv("AZURE_OPENAI_ENABLED", "false").lower() != "true":
        return False

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    if not endpoint:
        logger.warning(
            "AZURE_OPENAI_ENABLED is true but AZURE_OPENAI_ENDPOINT is not set."
        )
        return False

    return True


def invoke_ai(
    system_prompt: str,
    user_prompt: str,
    deployment_name: Optional[str] = None,
) -> AIResponse:
    """Invoke the configured AI model.

    If Azure OpenAI is enabled, this calls the deployed model. Otherwise,
    it returns an empty response that the caller should replace with a
    fallback.

    Args:
        system_prompt: System prompt.
        user_prompt: User prompt.
        deployment_name: Name of the model deployment. Defaults to
            the AZURE_OPENAI_DEPLOYMENT environment variable.

    Returns:
        AIResponse with the model's response, or an empty AIResponse
        with is_fallback=True when AI is not enabled.
    """
    if not is_ai_enabled():
        return AIResponse(
            text="",
            model="fallback",
            input_tokens=0,
            output_tokens=0,
            is_fallback=True,
        )

    # Azure OpenAI invocation (only reached when enabled)
    from openai import AzureOpenAI
    from src.utils.credentials import get_azure_credential

    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
    deployment = deployment_name or os.getenv(
        "AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"
    )

    credential = get_azure_credential()
    token = credential.get_token("https://cognitiveservices.azure.com/.default")

    client = AzureOpenAI(
        azure_endpoint=endpoint,
        azure_ad_token=token.token,
        api_version="2024-08-01-preview",
    )

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=800,
    )

    return AIResponse(
        text=response.choices[0].message.content or "",
        model=deployment,
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
        is_fallback=False,
    )
