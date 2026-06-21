from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass

from .models import Relic
from .ocr import marker_color_present, match_terms, run_tesseract
from .win32_api import Win32Error, activate_window, capture_window_region, find_window_by_title, run_action


class AutomationUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class AutomationReport:
    scanned: int = 0
    matched: int = 0
    actions: int = 0
    dry_run: bool = True


class GameAutomationAdapter:
    def __init__(self, config: dict, known_terms: set[str] | None = None, execute: bool = False):
        self.config = config
        self.known_terms = known_terms or set()
        self.execute = execute
        self.window = self._find_window()
        self.delay_seconds = float(config.get("scan", {}).get("delay_seconds", 0.15))

    def scan_current_relics(self) -> list[Relic]:
        max_relics = self._max_relics()
        relics: list[Relic] = []
        seen: set[str] = set()
        activate_window(self.window.hwnd)

        for index in range(max_relics):
            relic = self.scan_current_relic(index)
            if self.config.get("scan", {}).get("stop_on_duplicate", True) and relic.unique_id in seen:
                break
            seen.add(relic.unique_id)
            relics.append(relic)
            if index < max_relics - 1:
                self._run_configured_action("move_next")
        return relics

    def apply_keep_list(self, target_relics: list[Relic]) -> AutomationReport:
        max_relics = self._max_relics()
        target_keys = {relic_match_key(relic) for relic in target_relics}
        actions = 0
        activate_window(self.window.hwnd)

        for index in range(max_relics):
            current = self.scan_current_relic(index)
            if not current.retained and relic_match_key(current) in target_keys:
                actions += 1
                self._run_configured_action("toggle_keep")
            if index < max_relics - 1:
                self._run_configured_action("move_next")
        return AutomationReport(scanned=max_relics, matched=actions, actions=actions, dry_run=not self.execute)

    def delete_unkept(self) -> AutomationReport:
        max_relics = self._max_relics()
        actions = 0
        activate_window(self.window.hwnd)

        for index in range(max_relics):
            current = self.scan_current_relic(index)
            if not current.retained:
                actions += 1
                self._run_configured_action("delete_relic")
                if self.config.get("scan", {}).get("move_after_delete", False) and index < max_relics - 1:
                    self._run_configured_action("move_next")
            elif index < max_relics - 1:
                self._run_configured_action("move_next")
        return AutomationReport(scanned=max_relics, actions=actions, dry_run=not self.execute)

    def clear_keep_marks(self) -> AutomationReport:
        max_relics = self._max_relics()
        actions = 0
        activate_window(self.window.hwnd)

        for index in range(max_relics):
            current = self.scan_current_relic(index)
            if current.retained:
                actions += 1
                self._run_configured_action("toggle_keep")
            if index < max_relics - 1:
                self._run_configured_action("move_next")
        return AutomationReport(scanned=max_relics, actions=actions, dry_run=not self.execute)

    def scan_current_relic(self, index: int) -> Relic:
        regions = self.config.get("regions", {})
        kind_text = self._ocr_region("relic_kind")
        terms_text = self._ocr_region("relic_terms")
        terms = match_terms(terms_text, self.known_terms)
        retained = self._detect_keep_marker(regions)
        unique_id = relic_id(index, kind_text, terms)
        relic_type, color, mode = parse_kind_text(kind_text)
        return Relic(
            unique_id=unique_id,
            retained=retained,
            relic_type=relic_type,
            color=color,
            mode=mode,
            terms=terms,
            notes=(f"OCR種類={kind_text}",) if kind_text else (),
        )

    def _ocr_region(self, region_name: str) -> str:
        region = self.config.get("regions", {}).get(region_name, {})
        image = capture_window_region(self.window, region)
        ocr_config = self.config.get("ocr", {})
        return run_tesseract(
            image,
            tesseract_cmd=ocr_config.get("tesseract_cmd", "tesseract"),
            language=ocr_config.get("language", "chi_tra+eng"),
            psm=int(ocr_config.get("psm", 6)),
        )

    def _detect_keep_marker(self, regions: dict) -> bool:
        marker_config = self.config.get("marker_detection", {})
        if not marker_config.get("enabled", False):
            return False
        image = capture_window_region(self.window, regions.get("keep_marker", {}))
        return marker_color_present(
            image,
            rgb=marker_config.get("rgb", [255, 255, 255]),
            tolerance=int(marker_config.get("tolerance", 32)),
            minimum_ratio=float(marker_config.get("minimum_ratio", 0.02)),
        )

    def _run_configured_action(self, name: str) -> None:
        action = self.config.get("actions", {}).get(name, [])
        if not action:
            raise AutomationUnavailable(f"尚未設定 actions.{name}。")
        if not self.execute and name != "move_next":
            return
        run_action(action, self.window, self.delay_seconds)
        time.sleep(self.delay_seconds)

    def _find_window(self):
        title = self.config.get("game", {}).get("window_title", "")
        if not title:
            raise AutomationUnavailable("config.game.window_title 尚未設定。")
        try:
            return find_window_by_title(title)
        except Win32Error as error:
            raise AutomationUnavailable(str(error)) from error

    def _max_relics(self) -> int:
        max_relics = int(self.config.get("scan", {}).get("max_relics", 0))
        if max_relics <= 0:
            raise AutomationUnavailable("config.scan.max_relics 必須大於 0。")
        return max_relics


def relic_id(index: int, kind_text: str, terms: tuple[str, ...]) -> str:
    digest = hashlib.sha1("|".join((kind_text, *terms)).encode("utf-8")).hexdigest()[:10]
    return f"relic-{index + 1:04d}-{digest}"


def relic_match_key(relic: Relic) -> tuple[str, tuple[str, ...]]:
    return (relic.relic_type, tuple(sorted(relic.terms)))


def parse_kind_text(text: str) -> tuple[str, str, str]:
    normalized = " ".join(text.split())
    color = ""
    for candidate in ("紅", "藍", "綠", "黃", "紫", "白", "黑"):
        if candidate in normalized:
            color = candidate
            break
    mode = "深夜" if "深夜" in normalized else ("一般" if normalized else "")
    return normalized, color, mode

