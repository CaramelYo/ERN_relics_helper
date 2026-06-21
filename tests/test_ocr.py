import unittest

from ern_relics_helper.ocr import match_terms


class OcrMatchingTests(unittest.TestCase):
    def test_exact_term_match(self):
        terms = {"生命力＋１", "力氣＋１"}

        matched = match_terms("生命力＋１\n其他文字", terms)

        self.assertEqual(matched, ("生命力＋１",))

    def test_fuzzy_term_match(self):
        terms = {"提升血量上限", "提升專注值上限"}

        matched = match_terms("提升血量上跟", terms)

        self.assertEqual(matched, ("提升血量上限",))


if __name__ == "__main__":
    unittest.main()
