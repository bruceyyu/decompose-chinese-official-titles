"""Assign Qing ranks to already-separated title components.

Lower is more senior: 1a=1, 1b=1.5, ..., 9b=9.5; unranked=10.
An absent or unmatched component returns None, never 10. Noble titles are
outside this lookup. See data/office_ranks.csv for mappings and provenance.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

__all__ = ["office_rank", "component_rank"]


def _load_ranks() -> dict[str, float]:
    ranks = {}
    path = Path(__file__).parent / "data/office_ranks.csv"
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            name, rank = row["office"], float(row["rank"])
            if not name or name in ranks or not (1 <= rank <= 10) or rank * 2 != int(rank * 2):
                raise ValueError(f"Invalid or duplicate office-rank entry: {name!r}")
            ranks[name] = rank
    return ranks


_RANKS = _load_ranks()
_KEYS = tuple(sorted(_RANKS, key=lambda key: (-len(key), key)))
_NUMBERS = dict(zip("頭一二三四五六七八九", (1, 1, 2, 3, 4, 5, 6, 7, 8, 9)))
_GRADE = re.compile(r"(正|從)?([頭一二三四五六七八九])品")
_LEADING_GRADE = re.compile(r"^(正|從)?([頭一二三四五六七八九])品(?!銜)")
_GLYPHS = str.maketrans({"衞": "衛", "閘": "牐", "闸": "牐", "馹": "驛", "驲": "驛"})
_PREFIXES = (
    "欽加", "欽賞", "賞加", "請旨", "後加", "暫加", "敘加", "升加", "欽命",
    "欽授", "欽賜", "賞授", "賞", "加", "署", "原", "兼", "管", "前",
)
_SUFFIXES = ("升銜", "職銜", "官銜", "用銜", "銜", "職", "官", "用")
_QUALIFICATION_PREFIXES = ("在任候補", "在任候選", "候補", "候選", "候用", "學習", "署理", "署任")


def _clean(text: str) -> str:
    """Fold limited spelling/OCR variants, not arbitrary fuzzy matches."""
    text = re.sub(r"[？?]+", "", text).translate(_GLYPHS).strip()
    text = re.sub(r"侯([補選用])", r"候\1", text)
    if text.startswith("督察院"):
        text = "都察院" + text[3:]
    if text.endswith("禦史"):
        text = text[:-2] + "御史"
    # Do not replace 禦 globally: 防禦 is a legitimate office spelling.
    return text


def _strip_affixes(text: str, prefixes=(), suffixes=()) -> str:
    previous = None
    while text != previous:
        previous = text
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):]
        for suffix in suffixes:
            if text.endswith(suffix):
                text = text[:-len(suffix)]
    return text.strip()


def _grade_value(match) -> float | None:
    if match is None:
        return None
    return float(_NUMBERS[match[2]]) + (0.5 if match[1] == "從" else 0)


def office_rank(office: str | None, departments=(), full_title: str | None = None) -> float | None:
    """Resolve the rank of a duty/base office using its institutional context.

    Prefer explicit office grades, then the most specific registered name
    supplied by the department hierarchy or original title. Only exact or
    suffix matches are allowed; an interior office substring is insufficient.
    This function does not decide which component represents the duty office.
    """
    if not isinstance(office, str) or not (office := _clean(office)):
        return None
    if office == "未入流":
        return 10.0
    if office in _RANKS and _GRADE.search(office):
        return _RANKS[office]
    explicit = _grade_value(_LEADING_GRADE.match(office))
    if explicit is not None:
        return explicit

    # 筆帖式 spans several grades. Only an adjacent substantive grade counts:
    # 六品銜八品筆帖式 -> 8; 六品銜筆帖式 has no recoverable office grade.
    if office.endswith("筆帖式"):
        for context in (office, full_title):
            if isinstance(context, str):
                match = re.search(_GRADE.pattern + "筆帖式", _clean(context))
                if match:
                    return _grade_value(match)
        # Register-compatible convention, not a universal historical grade.
        return 10.0

    elements = [_clean(item) for item in (departments or ()) if isinstance(item, str) and item.strip()]
    full = "".join(elements) + office
    candidates = {office, full}
    for index, element in enumerate(elements):
        candidates.add(element + office)
        candidates.add("".join(elements[:index + 1]) + office)
    if isinstance(full_title, str):
        title = _clean(full_title)
        candidates.update(key for key in _KEYS
                          if len(key) > len(office) and key.endswith(office) and key in title)
    best = next((key for key in _KEYS if key in candidates), None)

    # Department-qualified suffixes can resolve abbreviated office components.
    # A province name alone must not create a false suffix (貴州學正 ≠ 州學正).
    suffix_candidates = {full}
    for index in range(1, len(elements)):
        suffix_candidates.add("".join(elements[:index + 1]) + office)
        suffix_candidates.add(elements[index] + office)
    suffix = next((key for key in _KEYS if len(key) >= 2
                   and any(text.endswith(key) for text in suffix_candidates)), None)
    if suffix is not None and (best is None or len(suffix) > len(best)):
        best = suffix
    return _RANKS[best] if best is not None else None


def component_rank(value, full_title: str | None = None) -> float | None:
    """Rank an additional-title or eligibility component, not an entire title.

    For a list, return the most senior mapped rank within that component.
    Do not use this function to combine offices, eligibility, and honors.
    Bare X品 is treated as Xa; 從X品 retains the b distinction.
    """
    if isinstance(value, (list, tuple, set)):
        ranks = [component_rank(item, full_title) for item in value]
        return min((rank for rank in ranks if rank is not None), default=None)
    if not isinstance(value, str) or not (text := _clean(value)):
        return None
    text = _strip_affixes(text, prefixes=_QUALIFICATION_PREFIXES)
    rank = office_rank(text, full_title=full_title or value)
    if rank is not None:
        return rank

    # An additional title may wrap an office name (欽加…銜) or state a grade.
    suffix_stripped = _strip_affixes(text, suffixes=_SUFFIXES)
    if suffix_stripped in _RANKS:
        return _RANKS[suffix_stripped]
    explicit = _grade_value(_GRADE.search(suffix_stripped or text))
    if explicit is not None:
        return explicit
    normalized = _strip_affixes(text, _PREFIXES, _SUFFIXES)
    if normalized in _RANKS:
        return _RANKS[normalized]
    key = next((key for key in _KEYS if key in normalized), None)
    return _RANKS[key] if key is not None else None
