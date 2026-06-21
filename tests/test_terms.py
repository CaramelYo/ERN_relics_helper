import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from ern_relics_helper.terms import load_term_rules, write_term_rules


class TermRuleTests(unittest.TestCase):
    def test_load_term_rules_from_standard_workbook(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "terms.xlsx"
            workbook = Workbook()
            sheet = workbook.active
            sheet.append(["詞條", "詞條種類", "疊加", "邏輯判斷", "評分"])
            sheet.append(["生命力＋１", "能力值", "相同詞條可疊加", "強力", "0.2"])
            workbook.save(path)

            rules = load_term_rules(path)

        self.assertIn("生命力＋１", rules)
        self.assertEqual(rules["生命力＋１"].stack_state, "可疊加")
        self.assertEqual(rules["生命力＋１"].logic_tags, ("強力",))
        self.assertEqual(rules["生命力＋１"].score, 0.2)

    def test_write_term_rules_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "terms.xlsx"
            write_term_rules(path, {})
            self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
