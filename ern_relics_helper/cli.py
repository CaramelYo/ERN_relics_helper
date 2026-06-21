from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .automation import AutomationUnavailable, GameAutomationAdapter
from .config import load_config, write_default_config
from .evaluator import clear_keep_marks, evaluate_relics
from .excel_io import read_relics, write_relic_template, write_relics
from .terms import load_term_rules, write_term_rules


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except AutomationUnavailable as error:
        print(str(error), file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ern-relics", description="黑夜君臨遺物管理工具")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_config = subparsers.add_parser("init-config", help="建立初始設定檔")
    init_config.add_argument("--output", default="config/relic-helper.json")
    init_config.set_defaults(func=cmd_init_config)

    build_terms = subparsers.add_parser("build-terms", help="從來源 Excel 建立標準遺物詞條對照表")
    build_terms.add_argument("--source", required=True)
    build_terms.add_argument("--output", default="outputs/relic_terms_table/遺物詞條對照表.xlsx")
    build_terms.set_defaults(func=cmd_build_terms)

    template = subparsers.add_parser("create-relic-template", help="建立 5.1.2 遺物清單 Excel 範本")
    template.add_argument("--output", default="outputs/scan/當前遺物清單.xlsx")
    template.set_defaults(func=cmd_create_relic_template)

    evaluate = subparsers.add_parser("evaluate", help="評估多餘遺物並匯出兩份 Excel")
    evaluate.add_argument("--relics", required=True, help="5.1.2 產生的遺物清單 Excel")
    evaluate.add_argument("--terms", default="outputs/relic_terms_table/遺物詞條對照表.xlsx")
    evaluate.add_argument("--output-all", default="outputs/evaluation/所有遺物狀態.xlsx")
    evaluate.add_argument("--output-new", default="outputs/evaluation/新增保留遺物.xlsx")
    evaluate.add_argument("--threshold", type=float, default=None)
    evaluate.set_defaults(func=cmd_evaluate)

    clear_marks = subparsers.add_parser("clear-marks-file", help="從 Excel 檔案移除所有保留標記")
    clear_marks.add_argument("--relics", required=True)
    clear_marks.add_argument("--output", default="outputs/evaluation/移除保留標記後.xlsx")
    clear_marks.set_defaults(func=cmd_clear_marks_file)

    for name, help_text, func in [
        ("scan-game", "整理當前遊戲遺物並匯出 Excel", cmd_scan_game),
        ("apply-keep", "依 Excel 在遊戲中保留特定遺物", cmd_apply_keep),
        ("delete-unkept", "刪除遊戲中未有保留標記的遺物", cmd_delete_unkept),
        ("clear-keeps-game", "移除遊戲中所有保留標記", cmd_clear_keeps_game),
    ]:
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("--config", default="config/relic-helper.json")
        command.set_defaults(func=func)
        if name == "scan-game":
            command.add_argument("--output", default="outputs/scan/當前遺物清單.xlsx")
        if name == "apply-keep":
            command.add_argument("--input", required=True)

    return parser


def cmd_init_config(args) -> int:
    write_default_config(args.output)
    print(f"已建立設定檔：{Path(args.output).resolve()}")
    return 0


def cmd_build_terms(args) -> int:
    rules = load_term_rules(args.source)
    write_term_rules(args.output, rules)
    print(f"已匯出 {len(rules)} 筆詞條規則：{Path(args.output).resolve()}")
    return 0


def cmd_create_relic_template(args) -> int:
    write_relic_template(args.output)
    print(f"已建立遺物清單範本：{Path(args.output).resolve()}")
    return 0


def cmd_evaluate(args) -> int:
    threshold = args.threshold
    if threshold is None and Path("config/relic-helper.json").exists():
        threshold = load_config("config/relic-helper.json").get("scoring", {}).get("keep_threshold")
    if threshold is None:
        threshold = 0.5

    rules = load_term_rules(args.terms)
    relics = read_relics(args.relics)
    evaluated, newly_retained = evaluate_relics(relics, rules, keep_threshold=threshold)
    write_relics(args.output_all, evaluated)
    write_relics(args.output_new, newly_retained)
    print(f"已匯出所有遺物狀態：{Path(args.output_all).resolve()}")
    print(f"已匯出新增保留遺物：{Path(args.output_new).resolve()}")
    return 0


def cmd_clear_marks_file(args) -> int:
    relics = read_relics(args.relics)
    write_relics(args.output, clear_keep_marks(relics))
    print(f"已匯出移除保留標記後檔案：{Path(args.output).resolve()}")
    return 0


def cmd_scan_game(args) -> int:
    load_config(args.config)
    adapter = GameAutomationAdapter()
    relics = adapter.scan_current_relics()
    write_relics(args.output, relics)
    return 0


def cmd_apply_keep(args) -> int:
    load_config(args.config)
    relics = read_relics(args.input)
    GameAutomationAdapter().apply_keep_list(relics)
    return 0


def cmd_delete_unkept(args) -> int:
    load_config(args.config)
    GameAutomationAdapter().delete_unkept()
    return 0


def cmd_clear_keeps_game(args) -> int:
    load_config(args.config)
    GameAutomationAdapter().clear_keep_marks()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
