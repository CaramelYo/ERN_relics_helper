import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from ern_relics_helper.excel_io import read_relics, write_relics
from ern_relics_helper.models import Relic


class ExcelIoTests(unittest.TestCase):
    def test_read_relics_from_workbook(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "relics.xlsx"
            workbook = Workbook()
            sheet = workbook.active
            sheet.append(["unique_id", "保留標記", "遺物種類", "詞條1", "詞條2"])
            sheet.append(["abc", "是", "紅色", "生命力＋１", "力氣＋１"])
            workbook.save(path)

            relics = read_relics(path)

        self.assertEqual(len(relics), 1)
        self.assertEqual(relics[0].unique_id, "abc")
        self.assertTrue(relics[0].retained)
        self.assertEqual(relics[0].terms, ("生命力＋１", "力氣＋１"))

    def test_write_relics_creates_workbook(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.xlsx"
            write_relics(path, [Relic(unique_id="abc", retained=True, terms=("生命力＋１",), total_score=0.2)])

            self.assertTrue(path.exists())
            relics = read_relics(path)

        self.assertEqual(len(relics), 1)
        self.assertEqual(relics[0].unique_id, "abc")
        self.assertTrue(relics[0].retained)


if __name__ == "__main__":
    unittest.main()

