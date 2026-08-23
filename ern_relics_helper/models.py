from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field, replace
from typing import Iterable


STACKABLE = "可疊加"
TIER_STACKABLE = "不同級別可疊加"
NON_STACKABLE = "不可疊加"
RELIC_COLOR_ALIASES = {
    "紅": "火燃",
    "紅色": "火燃",
    "火燃": "火燃",
    "藍": "水滴",
    "藍色": "水滴",
    "水滴": "水滴",
    "黃": "光耀",
    "黃色": "光耀",
    "光耀": "光耀",
    "綠": "幽靜",
    "綠色": "幽靜",
    "幽靜": "幽靜",
}


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    return unicodedata.normalize("NFKC", str(value)).strip()


def normalize_relic_color(value: object) -> str:
    text = normalize_text(value)
    return RELIC_COLOR_ALIASES.get(text, text)


def normalize_stack_state(value: object) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    if "不同" in text and "疊加" in text:
        return TIER_STACKABLE
    if "不可" in text or "不會" in text or "無法" in text:
        return NON_STACKABLE
    if "可疊加" in text or "相同" in text:
        return STACKABLE
    return text


def parse_tags(value: object) -> tuple[str, ...]:
    # text = normalize_text(value)
    # if not text:
    #     return ()
    # separators = [";", "；", ",", "，", "、", "\n", "|", "/"]
    # parts = [text]
    # for sep in separators:
    #     parts = [piece for part in parts for piece in part.split(sep)]
    # return tuple(dict.fromkeys(part.strip() for part in parts if part.strip()))
    return normalize_text(value)


def parse_score(value: object, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        score = float(value)
    except (TypeError, ValueError):
        return default
    return max(-1.0, min(1.0, score))


def parse_bool(value: object) -> bool:
    text = normalize_text(value).lower()
    return text in {"1", "true", "yes", "y", "是", "有", "保留", "已保留", "v", "ok"}


@dataclass(frozen=True)
class TermRule:
    term: str
    # category: str = ""
    stack_state: str = ""
    # logic_tags: tuple[str, ...] = ()
    logic_tags: str = ""
    score: float = 0.0

    def has_tag(self, *needles: str) -> bool:
        # haystack = " ".join((self.term, self.category, self.stack_state, *self.logic_tags))
        haystack = " ".join((self.term, self.stack_state, self.logic_tags))
        return any(needle and needle in haystack for needle in needles)


@dataclass(frozen=True)
class Relic:
    unique_id: str
    retained: bool = False
    # relic_type: str = ""
    color: str = ""
    mode: str = ""
    # terms: tuple[str, ...] = ()
    terms: tuple[TermRule, ...] = ()
    total_score: float = 0.0
    newly_retained: bool = False
    # either keep_reasons or notes
    keep_reasons: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def with_score(self, rules: dict[str, TermRule]) -> "Relic":
        total = sum(rules.get(term, TermRule(term=term)).score for term in self.terms)
        return replace(self, total_score=round(total, 4))

    def mark_retained(self, reason: str, note: str = "") -> "Relic":
        reasons = append_unique(self.keep_reasons, reason)
        notes = append_unique(self.notes, note) if note else self.notes
        return replace(
            self,
            retained=True,
            newly_retained=(not self.retained) or self.newly_retained,
            keep_reasons=reasons,
            notes=notes,
        )


def append_unique(values: Iterable[str], value: str) -> tuple[str, ...]:
    result = [item for item in values if item]
    if value and value not in result:
        result.append(value)
    return tuple(result)
