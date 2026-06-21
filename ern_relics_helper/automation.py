from __future__ import annotations


class AutomationUnavailable(RuntimeError):
    pass


class GameAutomationAdapter:
    """Interface for the game-screen workflow.

    The data workflow is implemented now. Real screen capture, OCR, and input
    playback must plug in here so dangerous operations stay explicit.
    """

    def scan_current_relics(self):
        raise AutomationUnavailable("遊戲畫面辨識尚未接入 adapter，請先使用 Excel 匯入流程。")

    def apply_keep_list(self, relics):
        raise AutomationUnavailable("保留特定遺物需要遊戲操作 adapter，目前尚未啟用。")

    def delete_unkept(self):
        raise AutomationUnavailable("刪除遺物需要遊戲操作 adapter，目前尚未啟用。")

    def clear_keep_marks(self):
        raise AutomationUnavailable("移除保留標記需要遊戲操作 adapter，目前尚未啟用。")

