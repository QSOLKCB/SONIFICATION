"""SPARK-001 independent Python oracle tests. SPDX-License-Identifier: MPL-2.0"""
from __future__ import annotations

import unittest

from scripts.verify_spark_001 import interval_oracle, parse_oracle, vectors


class SparkReferenceTests(unittest.TestCase):
    def test_decimal_boundaries_and_invalid_input(self) -> None:
        for source, expected in (
            ("9999.99", "OK 999999"),
            ("-9999.99", "OK -999999"),
            ("-0.00", "OK 0"),
            ("00.00", "INVALID"),
            ("1e2", "INVALID"),
            ("10000.00", "INVALID"),
            ("NaN", "INVALID"),
            ("", "INVALID"),
        ):
            with self.subTest(source=source):
                self.assertEqual(parse_oracle(source), expected)

    def test_closed_intervals_and_zero_missinguess(self) -> None:
        self.assertEqual(interval_oracle(1, 0, 1, 1, 1, 2), "OVERLAP")
        self.assertEqual(interval_oracle(1, 0, 1, 1, 2, 3), "BELOW")
        self.assertEqual(interval_oracle(1, 2, 3, 1, 0, 1), "ABOVE")
        self.assertEqual(interval_oracle(0, 0, 0, 2, 0, 0), "MISSING")
        self.assertEqual(interval_oracle(2, 0, 0, 1, 0, 0), "OVERLAP")
        self.assertEqual(interval_oracle(2, 1, 1, 1, 0, 0), "INVALID")

    def test_fixed_seed_vectors_and_source_identities(self) -> None:
        result = vectors()
        self.assertEqual(result, vectors())
        self.assertGreater(len(result), 300)
        self.assertEqual(len([x for x in result if x[0].startswith("L ")]), 11)
        self.assertTrue(all(isinstance(z, str) for pair in result for z in pair))


if __name__ == "__main__":
    unittest.main()
