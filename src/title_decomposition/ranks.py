"""Keep the ranks of decomposed institutional components separate."""
from __future__ import annotations

import math
from typing import Any

from title_ranks import component_rank, office_rank


def _values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return [str(value).strip()] if str(value).strip() else []


def _number(value: Any) -> float | None:
    return float(value) if value is not None and math.isfinite(float(value)) else None


def rank_label(value: float | None) -> str | None:
    if value is None:
        return None
    if value == 10:
        return "unranked"
    if not (1 <= value <= 9.5) or value * 2 != int(value * 2):
        raise ValueError(f"Not a Qing rank on the documented scale: {value}")
    return f"{int(value)}{'a' if float(value).is_integer() else 'b'}"


def rank_record(value: dict) -> dict:
    record = dict(value)
    title = record.get("original_title", "")
    depts = [item for field in ("local_department", "central_department", "military_department")
             for item in _values(record.get(field))]
    current = _number(office_rank(record.get("duty_office"), departments=depts, full_title=title))
    base = _number(office_rank(record.get("base_office"), departments=depts, full_title=title))
    # A ranked substantive base post can stand
    # in when the current deputation is outside the nine-rank scale. Preserve
    # raw current/base values so unranked (10) is never confused with unknown.
    base_used = (current is None or current == 10) and base is not None and base < 10
    office = base if base_used else current
    source = "base_office" if base_used else "duty_office" if current is not None else None
    ranks = {
        "office_rank": office,
        "duty_office_rank": current,
        "base_office_rank": base,
        "additional_title_rank": _number(component_rank(
            record.get("additional_title", []), full_title=title)),
        "eligibility_rank": _number(component_rank(
            record.get("qualification_title"), full_title=title)),
    }
    return {"ranks": ranks, "rank_labels": {key: rank_label(rank) for key, rank in ranks.items()},
            "office_rank_source": source}

