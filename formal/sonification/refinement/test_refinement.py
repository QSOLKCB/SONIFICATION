"""Executable checks and defect mutations for the limited conformance adapter."""

from __future__ import annotations

import ast
import unittest
from fractions import Fraction
from pathlib import Path

from source_adapter import (
    EXPECTED,
    MODULE_SHA256,
    compile_production,
    digest,
    evaluate,
    extract,
    load_frozen,
    oracle,
    outcome,
)

ROOT = Path(__file__).resolve().parents[3]


def mutated_function(before: str, after: str):
    # This intentionally bypasses adapter acceptance only for mutant execution.
    # Mutants are never represented as the frozen production function.
    node = ast.parse(EXPECTED.replace(before, after)).body[0]
    return compile_production(node)


class FrozenClassifyConformance(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = load_frozen(ROOT)
        cls.node = extract(cls.raw)
        cls.production = staticmethod(compile_production(cls.node))

    def test_exact_source_pin(self) -> None:
        self.assertEqual(digest(self.raw), MODULE_SHA256)

    def test_touching_is_overlap(self) -> None:
        a, b = (Fraction(0), Fraction(1)), (Fraction(1), Fraction(2))
        self.assertEqual(self.production(a, b), "overlap")
        self.assertEqual(oracle(a, b), "overlap")
        self.assertEqual(evaluate(self.node, a, b), "overlap")

    def test_both_zero_intervals_are_overlap(self) -> None:
        pair = (Fraction(0), Fraction(0))
        self.assertEqual(self.production(pair, pair), "overlap")

    def test_arbitrary_precision_separation(self) -> None:
        huge = 2**4096
        a = (Fraction(huge), Fraction(huge))
        b = (Fraction(huge + 1), Fraction(huge + 1))
        self.assertEqual(self.production(a, b), "a_below_b")
        self.assertEqual(oracle(a, b), "a_below_b")

    def test_invalid_rejected_before_separation(self) -> None:
        a, b = (Fraction(1), Fraction(0)), (Fraction(2), Fraction(3))
        expected = ("ValueError", "invalid reported-fit interval")
        self.assertEqual(outcome(self.production, a, b), expected)
        self.assertEqual(outcome(oracle, a, b), expected)

    def test_missing_does_not_become_zero(self) -> None:
        zero = (Fraction(0), Fraction(0))
        # Observation of an out-of-domain input; no claim of a general missingness model.
        self.assertEqual(outcome(self.production, (None, Fraction(0)), zero)[0], "TypeError")

    def test_truncated_tuple_is_rejected(self) -> None:
        self.assertEqual(outcome(self.production, (), (Fraction(0), Fraction(1)))[0], "IndexError")

    def test_adapter_rejects_subclasses_and_lists(self) -> None:
        class CustomFraction(Fraction):
            pass

        pair = (Fraction(0), Fraction(1))
        for invalid in ([Fraction(0), Fraction(1)], (CustomFraction(0), Fraction(1))):
            with self.assertRaisesRegex(TypeError, "adapter domain"):
                evaluate(self.node, invalid, pair)

    def test_runtime_annotations_do_not_prevent_overridden_order(self) -> None:
        class FalseOrdering(Fraction):
            def __lt__(self, other):
                return False

        a = (FalseOrdering(0), FalseOrdering(0))
        b = (Fraction(1), Fraction(1))
        # A minimal counterexample to interpreting annotations as a runtime
        # guarantee of ordinary rational comparison semantics.
        self.assertEqual(self.production(a, b), "overlap")
        self.assertEqual(oracle(a, b), "a_below_b")
        with self.assertRaisesRegex(TypeError, "adapter domain"):
            evaluate(self.node, a, b)

    def test_changed_source_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            extract(self.raw + b"\n# changed production source\n")

    def test_ast_guard_rejects_changed_comparison_even_without_hash_check(self) -> None:
        with self.assertRaisesRegex(ValueError, "changed classify AST"):
            extract(self.raw.replace(b"if a[1] < b[0]:", b"if a[1] <= b[0]:"), enforce_pin=False)

    def test_ast_guard_rejects_prohibited_call_even_without_hash_check(self) -> None:
        changed = self.raw.replace(b'    return "overlap"\n', b'    return str("overlap")\n', 1)
        with self.assertRaisesRegex(ValueError, "changed classify AST"):
            extract(changed, enforce_pin=False)

    def test_weakening_interval_guard_is_rejected(self) -> None:
        changed = self.raw.replace(b"a[0] > a[1] or b[0] > b[1]", b"a[0] > a[1] and b[0] > b[1]")
        with self.assertRaisesRegex(ValueError, "changed classify AST"):
            extract(changed, enforce_pin=False)

    def test_comparison_mutant_detected_by_touching_case(self) -> None:
        mutant = mutated_function("if a[1] < b[0]:", "if a[1] <= b[0]:")
        a, b = (Fraction(0), Fraction(1)), (Fraction(1), Fraction(2))
        self.assertNotEqual(outcome(mutant, a, b), outcome(oracle, a, b))

    def test_exception_mutant_detected(self) -> None:
        mutant = mutated_function("a[0] > a[1] or b[0] > b[1]", "a[0] > a[1] and b[0] > b[1]")
        a, b = (Fraction(1), Fraction(0)), (Fraction(2), Fraction(3))
        self.assertNotEqual(outcome(mutant, a, b), outcome(oracle, a, b))

    def test_output_label_mutant_detected(self) -> None:
        mutant = mutated_function('return "a_below_b"', 'return "b_below_a"')
        a, b = (Fraction(0), Fraction(0)), (Fraction(1), Fraction(1))
        self.assertNotEqual(outcome(mutant, a, b), outcome(oracle, a, b))

    def test_altered_expected_numerical_result_is_detected(self) -> None:
        a, b = (Fraction(0), Fraction(1)), (Fraction(1), Fraction(2))
        counterfeit_expected = ("return", "a_below_b")
        self.assertNotEqual(outcome(self.production, a, b), counterfeit_expected)
        self.assertEqual(outcome(self.production, a, b), outcome(oracle, a, b))


if __name__ == "__main__":
    unittest.main(verbosity=2)
