import unittest

from ern_relics_helper.ocr import match_terms, normalize_ocr_lines


class OcrMatchingTests(unittest.TestCase):
    def test_normalize_ocr_lines_converts_fullwidth_to_halfwidth(self):
        lines = normalize_ocr_lines("　ＡＢＣ１２３，！？＋　\r\n")

        self.assertEqual(lines, ["ABC123,!?+"])

    def test_exact_term_match(self):
        terms = {"生命力＋１", "力氣＋１"}

        matched = match_terms("生命力＋１\n其他文字", terms)

        self.assertEqual(matched, ("生命力＋１",))

    def test_fullwidth_ocr_text_matches_halfwidth_term(self):
        terms = {"生命力+1", "力氣+1"}

        matched = match_terms("生命力＋１\n其他文字", terms)

        self.assertEqual(matched, ("生命力+1",))

    def test_fuzzy_term_match(self):
        terms = {"提升血量上限", "提升專注值上限"}

        matched = match_terms("提升血量上跟", terms)

        self.assertEqual(matched, ("提升血量上限",))


if __name__ == "__main__":
    unittest.main()
