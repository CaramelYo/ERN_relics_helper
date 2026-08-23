from __future__ import annotations

import ctypes
import time
from ctypes import wintypes
from dataclasses import dataclass

from PIL import ImageGrab


user32 = ctypes.WinDLL("user32", use_last_error=True)

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
INPUT_KEYBOARD = 1
MAPVK_VK_TO_VSC = 0
EXTENDED_KEY_CODES = {
    0x21,  # PAGEUP
    0x22,  # PAGEDOWN
    0x23,  # END
    0x24,  # HOME
    0x25,  # LEFT
    0x26,  # UP
    0x27,  # RIGHT
    0x28,  # DOWN
    0x2D,  # INSERT
    0x2E,  # DELETE
}

ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _anonymous_ = ("input",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("input", INPUT_UNION),
    ]


user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
user32.SendInput.restype = wintypes.UINT


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


def get_window_rect(hwnd: int) -> tuple[int, int, int, int]:
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise Win32Error("無法取得視窗位置。")
    return (rect.left, rect.top, rect.right, rect.bottom)


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
        matches.append(WindowInfo(hwnd=int(hwnd), title=title, rect=get_window_rect(hwnd)))
        return True

    user32.EnumWindows(callback, 0)
    return matches


def activate_window(hwnd: int) -> None:
    user32.ShowWindow(hwnd, 5)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.1)
    if int(user32.GetForegroundWindow()) != int(hwnd):
        raise Win32Error("無法將遊戲視窗切到前景，請確認視窗未最小化，且程式權限不低於遊戲權限。")


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
    scan_code = user32.MapVirtualKeyW(virtual_key, MAPVK_VK_TO_VSC)
    flags = KEYEVENTF_SCANCODE
    if virtual_key in EXTENDED_KEY_CODES:
        flags |= KEYEVENTF_EXTENDEDKEY
    keybd_event(0, scan_code, flags)
    time.sleep(duration)
    keybd_event(0, scan_code, flags | KEYEVENTF_KEYUP)


def click(x: int, y: int) -> None:
    user32.SetCursorPos(int(x), int(y))
    mouse_event(0x0002)
    time.sleep(0.02)
    mouse_event(0x0004)


def run_action(action: list[dict], window: WindowInfo, delay_seconds: float) -> None:
    activate_window(window.hwnd)
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


def keybd_event(vk: int, scan_code: int, flags: int) -> None:
    input_event = INPUT()
    input_event.type = INPUT_KEYBOARD
    input_event.ki = KEYBDINPUT(vk, scan_code, flags, 0, 0)
    sent = user32.SendInput(1, ctypes.byref(input_event), ctypes.sizeof(INPUT))
    if sent != 1:
        error_code = ctypes.get_last_error()
        error_message = ctypes.FormatError(error_code).strip() if error_code else "Windows 未提供錯誤碼。"
        raise Win32Error(f"無法送出鍵盤輸入：SendInput 回傳 {sent}，last_error={error_code}，{error_message}")


def mouse_event(flags: int) -> None:
    user32.mouse_event(flags, 0, 0, 0, 0)
