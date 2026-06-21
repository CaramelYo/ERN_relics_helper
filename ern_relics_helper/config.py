from __future__ import annotations

import json
from pathlib import Path


DEFAULT_CONFIG = {
    "game": {
        "process_name": "",
        "window_title": "黑夜君臨",
    },
    "ocr": {
        "tesseract_cmd": "tesseract",
        "language": "chi_tra+eng",
        "psm": 6,
    },
    "regions": {
        "relic_kind": {"x": 0, "y": 0, "width": 0, "height": 0},
        "relic_terms": {"x": 0, "y": 0, "width": 0, "height": 0},
        "relic_grid": {"x": 0, "y": 0, "width": 0, "height": 0},
        "keep_marker": {"x": 0, "y": 0, "width": 0, "height": 0},
    },
    "marker_detection": {
        "enabled": False,
        "rgb": [255, 255, 255],
        "tolerance": 32,
        "minimum_ratio": 0.02,
    },
    "actions": {
        "move_next": [],
        "toggle_keep": [],
        "delete_relic": [],
    },
    "scan": {
        "max_relics": 0,
        "delay_seconds": 0.15,
        "stop_on_duplicate": True,
        "move_after_delete": False,
    },
    "scoring": {
        "keep_threshold": 0.5,
    },
}


def write_default_config(path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2), encoding="utf-8")


def load_config(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
