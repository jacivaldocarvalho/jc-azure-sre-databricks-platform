"""Deterministic fallback for AI-based summarization.

Used when Azure OpenAI is not available. Produces a structured summary
that mirrors the shape and intent of the AI-generated output, so the
downstream pipeline can be developed, tested, and demonstrated without
a provisioned model.

This is not a simulation of the model output. It is a template-based
generator that extracts the same signals from the data that a model
would use, expressed in a fixed format.
"""

from datetime import date
from typing import Any

from src.utils.logging import get_logger

logger = get_logger(__name__)

MONTHS_PT = {
    1: "janeiro",
    2: "fevereiro",
    3: "março",
    4: "abril",
    5: "maio",
    6: "junho",
    7: "julho",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "dezembro",
}


def generate_fallback_summary(
    monthly_data: list[dict[str, Any]],
    series_list: list[str],
    start_date: date,
    end_date: date,
) -> str:
    """Generate a deterministic summary from monthly aggregates.

    Args:
        monthly_data: List of dicts with keys: series, year_month,
            mean_value, min_value, max_value.
        series_list: Names of the series included.
        start_date: Start of the period.
        end_date: End of the period.

    Returns:
        A structured summary as a string.
    """
    logger.info("Generating fallback summary (Azure OpenAI not enabled).")

    # Group by series
    by_series: dict[str, list[dict[str, Any]]] = {}
    for row in monthly_data:
        series = row["series"]
        by_series.setdefault(series, []).append(row)

    paragraphs: list[str] = []

    # Opening paragraph
    period_desc = (
        f"{MONTHS_PT[start_date.month]} de {start_date.year} a "
        f"{MONTHS_PT[end_date.month]} de {end_date.year}"
    )
    paragraphs.append(
        f"Resumo executivo dos indicadores econômicos brasileiros no período "
        f"de {period_desc}. Foram analisadas as séries: "
        f"{', '.join(series_list).upper()}."
    )

    # Per-series analysis
    for series_name in series_list:
        rows = by_series.get(series_name, [])
        if not rows:
            continue

        rows_sorted = sorted(rows, key=lambda r: r["year_month"])
        first = rows_sorted[0]
        last = rows_sorted[-1]

        mean_overall = sum(r["mean_value"] for r in rows_sorted) / len(rows_sorted)
        min_val = min(r["min_value"] for r in rows_sorted)
        max_val = max(r["max_value"] for r in rows_sorted)

        trend = "estabilidade"
        if last["mean_value"] > first["mean_value"] * 1.05:
            trend = "elevação"
        elif last["mean_value"] < first["mean_value"] * 0.95:
            trend = "redução"

        paragraphs.append(
            f"{series_name.upper()}: iniciou o período em "
            f"{first['mean_value']:.4f} e encerrou em {last['mean_value']:.4f} "
            f"({trend}). A média do período foi {mean_overall:.4f}, com mínima "
            f"de {min_val:.4f} e máxima de {max_val:.4f}. Foram analisados "
            f"{len(rows_sorted)} meses de dados."
        )

    # Closing paragraph
    paragraphs.append(
        "Este resumo foi gerado por um gerador determinístico, pois o serviço "
        "de Azure OpenAI não está habilitado no ambiente atual. Quando o "
        "serviço estiver disponível, o resumo será gerado por um modelo de "
        "linguagem com análise contextual mais rica."
    )

    return "\n\n".join(paragraphs)