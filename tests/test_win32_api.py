import ctypes
import unittest
from unittest.mock import patch

from ern_relics_helper import win32_api


class FakeUser32:
    def MapVirtualKeyW(self, virtual_key, _map_type):
        return {0x27: 0x4D}.get(virtual_key, 0)


class Win32ApiTests(unittest.TestCase):
    def test_input_struct_matches_windows_size(self):
        expected_size = 40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28

        self.assertEqual(ctypes.sizeof(win32_api.INPUT), expected_size)

    def test_send_key_uses_extended_scan_code_for_arrow_keys(self):
        fake_user32 = FakeUser32()

        with (
            patch.object(win32_api, "user32", fake_user32),
            patch.object(win32_api, "keybd_event") as keybd_event,
        ):
            win32_api.send_key("RIGHT", duration=0)

        self.assertEqual(
            [call.args for call in keybd_event.call_args_list],
            [
                (0, 0x4D, win32_api.KEYEVENTF_SCANCODE | win32_api.KEYEVENTF_EXTENDEDKEY),
                (
                    0,
                    0x4D,
                    win32_api.KEYEVENTF_SCANCODE | win32_api.KEYEVENTF_EXTENDEDKEY | win32_api.KEYEVENTF_KEYUP,
                ),
            ],
        )


if __name__ == "__main__":
    unittest.main()
