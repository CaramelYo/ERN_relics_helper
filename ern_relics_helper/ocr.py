from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageOps


class OcrError(RuntimeError):
    pass


def run_tesseract(image: Image.Image, tesseract_cmd: str, language: str, psm: int = 6) -> str:
    prepared = prepare_for_ocr(image)
    with tempfile.TemporaryDirectory() as tmp:
        input_path = Path(tmp) / "ocr.png"
        output_base = Path(tmp) / "ocr"
        prepared.save(input_path)
        command = [
            tesseract_cmd,
            str(input_path),
            str(output_base),
            "-l",
            language,
            "--psm",
            str(psm),
        ]
        try:
            completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=30)
        except FileNotFoundError as error:
            raise OcrError("找不到 Tesseract 執行檔，請在 config 的 ocr.tesseract_cmd 設定完整路徑。") from error
        if completed.returncode != 0:
            raise OcrError(completed.stderr.strip() or "Tesseract OCR 執行失敗。")
        return (output_base.with_suffix(".txt")).read_text(encoding="utf-8").strip()


def prepare_for_ocr(image: Image.Image) -> Image.Image:
    grayscale = ImageOps.grayscale(image)
    width, height = grayscale.size
    if width < 900:
        scale = max(2, round(900 / max(width, 1)))
        grayscale = grayscale.resize((width * scale, height * scale))
    return ImageOps.autocontrast(grayscale)


def normalize_ocr_lines(text: str) -> list[str]:
    return [line.strip() for line in text.replace("\r", "\n").split("\n") if line.strip()]


def match_terms(ocr_text: str, known_terms: set[str], limit: int = 6) -> tuple[str, ...]:
    lines = normalize_ocr_lines(ocr_text)
    matched: list[str] = []
    for term in sorted(known_terms, key=len, reverse=True):
        if term and term in ocr_text and term not in matched:
            matched.append(term)
        if len(matched) >= limit:
            return tuple(matched)
    for line in lines:
        best = best_fuzzy_term(line, known_terms)
        if best and best not in matched:
            matched.append(best)
        if len(matched) >= limit:
            break
    return tuple(matched)


def best_fuzzy_term(text: str, known_terms: set[str]) -> str:
    normalized = compact(text)
    if not normalized:
        return ""
    best_term = ""
    best_score = 0.0
    for term in known_terms:
        score = similarity(normalized, compact(term))
        if score > best_score:
            best_term = term
            best_score = score
    return best_term if best_score >= 0.72 else ""


def compact(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace())


def similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        for j, right_char in enumerate(right, start=1):
            current.append(
                min(
                    current[j - 1] + 1,
                    previous[j] + 1,
                    previous[j - 1] + (left_char != right_char),
                )
            )
        previous = current
    distance = previous[-1]
    return 1.0 - distance / max(len(left), len(right))


def marker_color_present(image: Image.Image, rgb: list[int], tolerance: int, minimum_ratio: float) -> bool:
    target = tuple(int(channel) for channel in rgb[:3])
    pixels = image.convert("RGB").getdata()
    total = 0
    matched = 0
    for pixel in pixels:
        total += 1
        if all(abs(pixel[index] - target[index]) <= tolerance for index in range(3)):
            matched += 1
    return total > 0 and (matched / total) >= minimum_ratio
