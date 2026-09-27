"""Executive summary generation from monthly economic aggregates.

Uses Azure OpenAI when enabled, falls back to a deterministic generator
when not. The output has the same shape in both cases.
"""

import json
from datetime import date
from typing import Any

from src.ai.client import AIResponse, invoke_ai, is_ai_enabled
from src.ai.fallback import generate_fallback_summary
from src.ai.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from src.utils.logging import get_logger

logger = get_logger(__name__)


def generate_summary(
    monthly_data: list[dict[str, Any]],
    series_list: list[str],
    start_date: date,
    end_date: date,
) -> AIResponse:
    """Generate an executive summary from monthly aggregates.

    Args:
        monthly_data: List of dicts with monthly aggregates.
        series_list: Names of the series included.
        start_date: Start of the period.
        end_date: End of the period.

    Returns:
        AIResponse with the summary text and metadata.
    """
    if not is_ai_enabled():
        logger.info("Azure OpenAI is not enabled. Using fallback generator.")
        text = generate_fallback_summary(
            monthly_data=monthly_data,
            series_list=series_list,
            start_date=start_date,
            end_date=end_date,
        )
        return AIResponse(
            text=text,
            model="fallback",
            input_tokens=0,
            output_tokens=len(text.split()),
            is_fallback=True,
        )

    logger.info("Azure OpenAI is enabled. Invoking model.")
    user_prompt = USER_PROMPT_TEMPLATE.format(
        data_json=json.dumps(monthly_data[:50], ensure_ascii=False, default=str),
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        series_list=", ".join(series_list),
    )

    return invoke_ai(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )
