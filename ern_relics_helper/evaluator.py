from __future__ import annotations

from dataclasses import replace

from .models import NON_STACKABLE, STACKABLE, TIER_STACKABLE, Relic, TermRule


def evaluate_relics(
    relics: list[Relic],
    rules: dict[str, TermRule],
    keep_threshold: float = 0.5,
) -> tuple[list[Relic], list[Relic]]:
    scored = [relic.with_score(rules) for relic in relics]
    by_id = {relic.unique_id: relic for relic in scored}

    apply_best_for_rules(by_id, rules, lambda rule: rule.has_tag("特定武器"))
    apply_best_for_rules(
        by_id,
        rules,
        lambda rule: rule.stack_state == NON_STACKABLE and rule.has_tag("強力", "特定強力", "不可疊加強力"),
    )
    apply_best_for_rules(
        by_id,
        rules,
        lambda rule: rule.stack_state == TIER_STACKABLE and rule.has_tag("強力", "特定強力", "不同級別可疊加強力"),
    )
    apply_top_for_rules(
        by_id,
        rules,
        lambda rule: rule.stack_state == STACKABLE and rule.has_tag("強力", "特定強力", "可疊加強力"),
        limit=3,
    )
    apply_score_threshold(by_id, keep_threshold)

    evaluated = [by_id[relic.unique_id] for relic in scored]
    newly_retained = [relic for relic in evaluated if relic.newly_retained]
    return evaluated, newly_retained


def apply_best_for_rules(by_id: dict[str, Relic], rules: dict[str, TermRule], predicate) -> None:
    for rule in rules.values():
        if not predicate(rule):
            continue
        matches = relics_with_term(by_id.values(), rule.term)
        if not matches:
            continue
        winner = max(matches, key=lambda relic: relic.total_score)
        by_id[winner.unique_id] = winner.mark_retained(
            reason=f"{rule.term} 最高評分",
            note=f"{rule.term}: 最高評分者",
        )


def apply_top_for_rules(by_id: dict[str, Relic], rules: dict[str, TermRule], predicate, limit: int) -> None:
    for rule in rules.values():
        if not predicate(rule):
            continue
        matches = sorted(relics_with_term(by_id.values(), rule.term), key=lambda relic: relic.total_score, reverse=True)
        for rank, relic in enumerate(matches[:limit], start=1):
            by_id[relic.unique_id] = relic.mark_retained(
                reason=f"{rule.term} 評分第 {rank} 名",
                note=f"{rule.term}: 評分第 {rank} 名",
            )


def apply_score_threshold(by_id: dict[str, Relic], keep_threshold: float) -> None:
    for relic in list(by_id.values()):
        if not relic.retained and relic.total_score > keep_threshold:
            by_id[relic.unique_id] = relic.mark_retained(
                reason=f"總評分高於 {keep_threshold}",
                note="總評分門檻新增保留",
            )


def relics_with_term(relics, term: str) -> list[Relic]:
    return [relic for relic in relics if term in relic.terms]


def clear_keep_marks(relics: list[Relic]) -> list[Relic]:
    return [replace(relic, retained=False, newly_retained=False, keep_reasons=(), notes=()) for relic in relics]

