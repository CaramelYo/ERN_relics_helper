import unittest

from ern_relics_helper.automation import parse_kind_text


class AutomationParsingTests(unittest.TestCase):
    def test_parse_kind_text_maps_color_to_relic_color_name(self):
        self.assertEqual(parse_kind_text("火燃遺物"), ("火燃", "一般"))
        self.assertEqual(parse_kind_text("水滴暗淡遺物"), ("水滴", "深夜"))
        self.assertEqual(parse_kind_text("光耀遺物"), ("光耀", "一般"))
        self.assertEqual(parse_kind_text("幽靜遺物"), ("幽靜", "一般"))

    def test_parse_kind_text_ignores_legacy_color_names(self):
        self.assertEqual(parse_kind_text("紅色遺物"), ("", "一般"))


if __name__ == "__main__":
    unittest.main()
