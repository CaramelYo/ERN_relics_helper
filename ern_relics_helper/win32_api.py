from __future__ import annotations

import ctypes
import time
from ctypes import wintypes
from dataclasses import dataclass

from PIL import ImageGrab


user32 = ctypes.windll.user32


@dataclass(frozen=True)
class WindowInfo:
    hwnd: int
    title: str
    rect: tuple[int, int, int, int]


class Win32Error(RuntimeError):
    pass


def find_window_by_title(title_contains: str) -> WindowInfo:
    matches = [
        window for window in list_windows()
        if title_contains.lower() in window.title.lower()
    ]
    if not matches:
        raise Win32Error(f"找不到標題包含「{title_contains}」的視窗。")
    return matches[0]


def list_windows() -> list[WindowInfo]:
    matches: list[WindowInfo] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def callback(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        matches.append(WindowInfo(hwnd=int(hwnd), title=title, rect=(rect.left, rect.top, rect.right, rect.bottom)))
        return True

    user32.EnumWindows(callback, 0)
    return matches


def activate_window(hwnd: int) -> None:
    user32.ShowWindow(hwnd, 5)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.1)


def capture_window_region(window: WindowInfo, region: dict) -> object:
    left, top, _right, _bottom = window.rect
    x = int(region.get("x", 0))
    y = int(region.get("y", 0))
    width = int(region.get("width", 0))
    height = int(region.get("height", 0))
    if width <= 0 or height <= 0:
        raise Win32Error("截圖區域尚未設定 width/height。")
    bbox = (left + x, top + y, left + x + width, top + y + height)
    return ImageGrab.grab(bbox=bbox)


def send_key(key: str, duration: float = 0.02) -> None:
    virtual_key = virtual_key_code(key)
    keybd_event(virtual_key, 0)
    time.sleep(duration)
    keybd_event(virtual_key, 2)


def click(x: int, y: int) -> None:
    user32.SetCursorPos(int(x), int(y))
    mouse_event(0x0002)
    time.sleep(0.02)
    mouse_event(0x0004)


def run_action(action: list[dict], window: WindowInfo, delay_seconds: float) -> None:
    for step in action:
        kind = step.get("type", "key")
        if kind == "key":
            send_key(str(step["key"]), float(step.get("duration", 0.02)))
        elif kind == "click":
            left, top, _right, _bottom = window.rect
            click(left + int(step["x"]), top + int(step["y"]))
        elif kind == "wait":
            time.sleep(float(step.get("seconds", delay_seconds)))
        else:
            raise Win32Error(f"不支援的操作類型：{kind}")
        time.sleep(delay_seconds)


def virtual_key_code(key: str) -> int:
    key = key.strip().upper()
    aliases = {
        "ENTER": 0x0D,
        "RETURN": 0x0D,
        "ESC": 0x1B,
        "ESCAPE": 0x1B,
        "SPACE": 0x20,
        "TAB": 0x09,
        "UP": 0x26,
        "DOWN": 0x28,
        "LEFT": 0x25,
        "RIGHT": 0x27,
        "BACKSPACE": 0x08,
        "DELETE": 0x2E,
    }
    if key in aliases:
        return aliases[key]
    if len(key) == 1:
        code = user32.VkKeyScanW(ord(key))
        if code == -1:
            raise Win32Error(f"無法轉換按鍵：{key}")
        return code & 0xFF
    if key.startswith("F") and key[1:].isdigit():
        number = int(key[1:])
        if 1 <= number <= 24:
            return 0x70 + number - 1
    raise Win32Error(f"不支援的按鍵：{key}")


def keybd_event(vk: int, flags: int) -> None:
    user32.keybd_event(vk, 0, flags, 0)


def mouse_event(flags: int) -> None:
    user32.mouse_event(flags, 0, 0, 0, 0)
