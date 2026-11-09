"""Source-pinned finite interval-construction conformance; refinement remains OPEN."""

from __future__ import annotations

import ast
import re
import sys
import unittest
from fractions import Fraction
from pathlib import Path

from source_adapter import COMMIT, PATH, digest, load_frozen, outcome

ROOT = Path(__file__).resolve().parents[3]
EXPECTED_DECIMAL = """def decimal(text: str, *, positive: bool = False) -> Fraction:
    if not isinstance(text, str) or not re.fullmatch(
        r"-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?", text
    ):
        raise ValueError("invalid reported fit decimal")
    value = Fraction(text)
    if positive and value <= 0:
        raise ValueError("expected positive reported fit or error")
    return value
"""
EXPECTED_INTERVAL = """def interval(row: dict, field: str) -> tuple[Fraction, Fraction]:
    if field not in {"alpha", "amplitude_ratio"}:
        raise ValueError("unexpected fitted quantity")
    center = decimal(row[field])
    err = decimal(row[field + "_reported_error"], positive=True)
    return center - err, center + err
"""
TEXTS = (
    "0",
    "-0",
    "1",
    "-1",
    "0.1",
    "-0.1",
    "1.00",
    "2.125",
    "-12.500",
    "",
    "00",
    "01",
    "+1",
    "1.",
    ".1",
    "1e2",
    "1/2",
    " 1",
    "1 ",
    "nan",
    "\u0661",
)


def oracle_decimal(text: str, *, positive: bool = False) -> Fraction:
    # An independently authored grammar recognizer, without re or Fraction(text).
    if type(text) is not str:
        raise ValueError("invalid reported fit decimal")
    sign, unsigned = (-1, text[1:]) if text.startswith("-") else (1, text)
    parts = unsigned.split(".")
    if not 1 <= len(parts) <= 2:
        raise ValueError("invalid reported fit decimal")
    integer = parts[0]
    if not integer or any(c not in "0123456789" for c in integer):
        raise ValueError("invalid reported fit decimal")
    if len(integer) > 1 and integer[0] == "0":
        raise ValueError("invalid reported fit decimal")
    fractional = parts[1] if len(parts) == 2 else ""
    if len(parts) == 2 and (not fractional or any(c not in "0123456789" for c in fractional)):
        raise ValueError("invalid reported fit decimal")
    coefficient = 0
    for c in integer + fractional:
        coefficient = 10 * coefficient + ord(c) - ord("0")
    numerator = sign * coefficient
    if positive and numerator <= 0:
        raise ValueError("expected positive reported fit or error")
    return Fraction(numerator, 10 ** len(fractional))


def oracle_interval(row: dict, field: str) -> tuple[Fraction, Fraction]:
    if field not in ("alpha", "amplitude_ratio"):
        raise ValueError("unexpected fitted quantity")
    center = oracle_decimal(row[field])
    error = oracle_decimal(row[field + "_reported_error"], positive=True)
    # Integer numerator construction is independent of Fraction +/- operators.
    denominator = center.denominator * error.denominator
    center_num = center.numerator * error.denominator
    error_num = error.numerator * center.denominator
    return (
        Fraction(center_num - error_num, denominator),
        Fraction(center_num + error_num, denominator),
    )


def load_functions(raw: bytes) -> dict:
    nodes = ast.parse(raw.decode("utf-8")).body
    selected = []
    for name, expected_text in (("decimal", EXPECTED_DECIMAL), ("interval", EXPECTED_INTERVAL)):
        found = [n for n in nodes if isinstance(n, ast.FunctionDef) and n.name == name]
        if len(found) != 1 or ast.dump(found[0]) != ast.dump(ast.parse(expected_text).body[0]):
            raise ValueError(f"changed or unsupported {name} AST")
        selected.append(found[0])
    scope = {"Fraction": Fraction, "re": re}
    exec(compile(ast.Module(body=selected, type_ignores=[]), f"{COMMIT}:{PATH}", "exec"), scope)
    return scope


class FrozenIntervalConformance(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = load_frozen(ROOT)
        cls.functions = load_functions(cls.raw)

    def test_decimal_domain_42_cases(self) -> None:
        observed = 0
        for text in TEXTS:
            for positive in (False, True):
                with self.subTest(text=text, positive=positive):
                    self.assertEqual(
                        outcome(
                            lambda t, p: self.functions["decimal"](t, positive=p), text, positive
                        ),
                        outcome(lambda t, p: oracle_decimal(t, positive=p), text, positive),
                    )
                    observed += 1
        self.assertEqual(observed, 42)

    def test_interval_domain_882_cases(self) -> None:
        observed = 0
        for field in ("alpha", "amplitude_ratio"):
            for center in TEXTS:
                for error in TEXTS:
                    row = {field: center, field + "_reported_error": error}
                    with self.subTest(field=field, center=center, error=error):
                        self.assertEqual(
                            outcome(self.functions["interval"], row, field),
                            outcome(oracle_interval, row, field),
                        )
                        observed += 1
        self.assertEqual(observed, 882)

    def test_missing_center_and_error_preserve_keyerror(self) -> None:
        for row in ({}, {"alpha": "1"}):
            self.assertEqual(
                outcome(self.functions["interval"], row, "alpha"),
                outcome(oracle_interval, row, "alpha"),
            )
            self.assertEqual(outcome(self.functions["interval"], row, "alpha")[0], "KeyError")

    def test_unsupported_field_rejected_before_missing_keys(self) -> None:
        self.assertEqual(
            outcome(self.functions["interval"], {}, "pressure"),
            ("ValueError", "unexpected fitted quantity"),
        )

    def test_measured_zero_center_is_valid_positive_error_required(self) -> None:
        self.assertEqual(
            self.functions["interval"]({"alpha": "0", "alpha_reported_error": "0.1"}, "alpha"),
            (Fraction(-1, 10), Fraction(1, 10)),
        )
        self.assertEqual(
            outcome(
                self.functions["interval"], {"alpha": "1", "alpha_reported_error": "0"}, "alpha"
            ),
            ("ValueError", "expected positive reported fit or error"),
        )

    def test_missing_value_not_numeric_zero(self) -> None:
        self.assertEqual(
            outcome(
                self.functions["interval"], {"alpha": None, "alpha_reported_error": "1"}, "alpha"
            ),
            ("ValueError", "invalid reported fit decimal"),
        )

    def test_interval_arithmetic_mutation_rejected(self) -> None:
        mutant = self.raw.replace(
            b"return center - err, center + err", b"return center + err, center + err"
        )
        self.assertNotEqual(digest(mutant), digest(self.raw))
        with self.assertRaisesRegex(ValueError, "interval AST"):
            load_functions(mutant)

    def test_decimal_guard_mutation_rejected(self) -> None:
        mutant = self.raw.replace(b"if positive and value <= 0:", b"if positive and value < 0:")
        with self.assertRaisesRegex(ValueError, "decimal AST"):
            load_functions(mutant)

    def test_long_decimal_acceptance_has_runtime_digit_bound(self) -> None:
        # A grammar-only all-length theorem would ignore CPython's configured
        # integer string-conversion bound. No global interpreter setting changes.
        limit = sys.get_int_max_str_digits()
        if not limit:
            self.skipTest("this interpreter disables the decimal conversion digit bound")
        text = "1" * (limit + 1)
        self.assertGreater(oracle_decimal(text).numerator, 0)
        with self.assertRaises(ValueError):
            self.functions["decimal"](text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
