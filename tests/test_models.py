import unittest

from ern_relics_helper.models import normalize_relic_color, normalize_text


class ModelNormalizationTests(unittest.TestCase):
    def test_normalize_text_converts_fullwidth_to_halfwidth(self):
        self.assertEqual(normalize_text("　ＡＢＣ１２３，！？＋　"), "ABC123,!?+")

    def test_normalize_relic_color_maps_legacy_color_names(self):
        self.assertEqual(normalize_relic_color("紅"), "火燃")
        self.assertEqual(normalize_relic_color("藍色"), "水滴")
        self.assertEqual(normalize_relic_color("黃"), "光耀")
        self.assertEqual(normalize_relic_color("綠色"), "幽靜")


if __name__ == "__main__":
    unittest.main()
