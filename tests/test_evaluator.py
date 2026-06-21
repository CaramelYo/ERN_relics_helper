import unittest

from ern_relics_helper.evaluator import evaluate_relics
from ern_relics_helper.models import NON_STACKABLE, STACKABLE, Relic, TermRule


class EvaluatorTests(unittest.TestCase):
    def test_score_threshold_marks_unretained_relic(self):
        rules = {
            "強攻": TermRule(term="強攻", score=0.4),
            "生命": TermRule(term="生命", score=0.2),
        }
        relics = [Relic(unique_id="a", terms=("強攻", "生命"))]

        evaluated, newly_retained = evaluate_relics(relics, rules, keep_threshold=0.5)

        self.assertTrue(evaluated[0].retained)
        self.assertTrue(evaluated[0].newly_retained)
        self.assertEqual(evaluated[0].total_score, 0.6)
        self.assertEqual([relic.unique_id for relic in newly_retained], ["a"])

    def test_non_stack_power_keeps_highest_scored_relic_only(self):
        rules = {
            "稀有強力": TermRule(term="稀有強力", stack_state=NON_STACKABLE, logic_tags=("強力",), score=0.1),
            "補分": TermRule(term="補分", score=0.3),
        }
        relics = [
            Relic(unique_id="low", terms=("稀有強力",)),
            Relic(unique_id="high", terms=("稀有強力", "補分")),
        ]

        evaluated, newly_retained = evaluate_relics(relics, rules, keep_threshold=0.9)

        by_id = {relic.unique_id: relic for relic in evaluated}
        self.assertFalse(by_id["low"].retained)
        self.assertTrue(by_id["high"].retained)
        self.assertEqual([relic.unique_id for relic in newly_retained], ["high"])

    def test_stackable_power_keeps_top_three(self):
        rules = {
            "可疊強力": TermRule(term="可疊強力", stack_state=STACKABLE, logic_tags=("強力",), score=0.1),
            "補分1": TermRule(term="補分1", score=0.1),
            "補分2": TermRule(term="補分2", score=0.2),
            "補分3": TermRule(term="補分3", score=0.3),
            "補分4": TermRule(term="補分4", score=0.4),
        }
        relics = [
            Relic(unique_id="r1", terms=("可疊強力", "補分1")),
            Relic(unique_id="r2", terms=("可疊強力", "補分2")),
            Relic(unique_id="r3", terms=("可疊強力", "補分3")),
            Relic(unique_id="r4", terms=("可疊強力", "補分4")),
        ]

        evaluated, newly_retained = evaluate_relics(relics, rules, keep_threshold=0.9)

        kept = {relic.unique_id for relic in evaluated if relic.retained}
        self.assertEqual(kept, {"r2", "r3", "r4"})
        self.assertEqual(len(newly_retained), 3)


if __name__ == "__main__":
    unittest.main()

