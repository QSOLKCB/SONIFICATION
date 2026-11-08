"""MAT-SPEC-002 conservation, metamorphism, receipts and boundary tests.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import csv
import io
import json
import tempfile
import unittest
from fractions import Fraction
from itertools import combinations
from pathlib import Path

from materials.mat_spec import PRESSURES, build_bundle, sha256
from materials.mat_spec_002 import (
    OUTPUT_NAMES, SAMPLE_COUNTS, audit_pairs, build_evidence, index_observations,
    interval_relation, uniform_indices, write_evidence,
)

ROOT = Path(__file__).resolve().parents[1]


def point(energy: str, error: str = "0.1") -> dict:
    return {"status": "tabulated", "energy_meV": energy, "reported_energy_error_meV": error}


class IntervalTests(unittest.TestCase):
    def test_closed_intervals_and_missing_are_not_zero(self) -> None:
        self.assertEqual(interval_relation(point("1"), point("1.2")), "overlap")
        self.assertEqual(interval_relation(point("1"), point("1.200001")), "a_below_b")
        self.assertEqual(interval_relation(point("1.200001"), point("1")), "b_below_a")
        self.assertEqual(interval_relation(point("1"), point("1.05")), "overlap")
        self.assertEqual(interval_relation({"status": "missing"}, point("1")), "missing")
        with self.assertRaises(ValueError):
            interval_relation(point("1", "-1"), point("2"))
        with self.assertRaises(ValueError):
            interval_relation({"status": "invalid"}, point("1"))

    def test_exact_floor_sampling_and_invalid_bounds(self) -> None:
        self.assertEqual(uniform_indices(1050, 6), (0, 175, 350, 525, 700, 875))
        for count in SAMPLE_COUNTS:
            indices = uniform_indices(1050, count)
            self.assertEqual(len(indices), len(set(indices)))
            self.assertEqual(indices[0], 0)
            self.assertTrue(all(0 <= i < 1050 for i in indices))
        for args in ((0, 1), (5, 6), (5, 0), (True, 1), (6, False)):
            with self.assertRaises(ValueError):
                uniform_indices(*args)


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.original = build_bundle(ROOT)
        cls.outputs = build_evidence(ROOT)
        cls.manifest = json.loads(cls.outputs["manifest.json"])
        cls.audit = json.loads(cls.outputs["audit.json"])
        cls.sampling = json.loads(cls.outputs["sampling.json"])
        cls.obs = json.loads(cls.original["observations.json"])["observations"]

    def test_complete_count_conservation_and_source_identity(self) -> None:
        rows = list(csv.DictReader(io.StringIO(self.outputs["pressure-pairs.csv"].decode())))
        self.assertEqual(len(rows), 21)
        totals = self.audit["full_grid"]
        self.assertEqual(totals["total_q_pressure_pairs"], 21 * 1050)
        self.assertEqual(
            sum(totals[s] for s in ("a_below_b", "b_below_a", "overlap", "missing")),
            21 * 1050,
        )
        self.assertEqual(
            totals["comparable"],
            totals["a_below_b"] + totals["b_below_a"] + totals["overlap"],
        )
        self.assertEqual(totals["positive_scale_and_reversal_checks"], totals["comparable"])
        self.assertEqual(
            sum(int(row["missing"]) + int(row["comparable"]) for row in rows),
            21 * 1050,
        )
        self.assertEqual(self.manifest["profile"], "MAT-SPEC-002")
        self.assertEqual(self.manifest["source_sha256"], "15a56ccdd2f681de0e1d3d1517dc4641732dbef4e2d6153591154cc4b039b50a")

    def test_tile_parity_with_one_block_and_odd_block(self) -> None:
        indexed = index_observations(self.obs)
        original_rows, original_total = audit_pairs(indexed, 128)
        for tile in (1, 137, 1050):
            alternate_rows, alternate_total = audit_pairs(indexed, tile)
            self.assertEqual(alternate_rows, original_rows)
            self.assertEqual(
                {k: v for k, v in alternate_total.items() if k != "tile_size"},
                {k: v for k, v in original_total.items() if k != "tile_size"},
            )
        with self.assertRaises(ValueError):
            audit_pairs(indexed, 0)

    def test_sampling_exposes_missingness_and_receiver_collisions(self) -> None:
        self.assertEqual([item["sample_count"] for item in self.sampling], list(SAMPLE_COUNTS))
        for item in self.sampling:
            self.assertEqual(len(item["indices"]), item["sample_count"])
            self.assertEqual(
                item["metadata_lane_mod_3"], [i % 3 for i in range(item["sample_count"])]
            )
            self.assertEqual(
                len(item["complete_pressures_bar"]) + len(item["incomplete_pressures_bar"]),
                7,
            )
            self.assertEqual(
                item["comparable_pressure_pairs"],
                len(list(combinations(item["complete_pressures_bar"], 2))),
            )
            self.assertGreaterEqual(item["missing_selected_cells"], 0)
        self.assertNotEqual(self.sampling[0]["indices"], [0, 175, 475, 725, 875, 975])

    def test_replay_manifest_and_original_byte_identity(self) -> None:
        self.assertEqual(self.outputs, build_evidence(ROOT))
        self.assertEqual(set(self.outputs), OUTPUT_NAMES)
        self.assertEqual(
            self.manifest["parent_manifest_sha256"], sha256(self.original["manifest.json"])
        )
        for name, receipt in self.manifest["parent_artifacts"].items():
            self.assertEqual(sha256(self.original[name]), receipt["sha256"])
        for name, receipt in self.manifest["outputs"].items():
            self.assertEqual(sha256(self.outputs[name]), receipt["sha256"])
        self.assertIsNone(self.manifest["canonical_pcm_sha256"])
        self.assertIsNone(self.manifest["canonical_wav_sha256"])
        self.assertEqual(self.audit["assurance"]["phase_classification"], "NOT_TESTED")

    def test_safe_symbolic_export(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dst = write_evidence(root, "dist/new", self.outputs)
            self.assertEqual({p.name for p in dst.iterdir()}, OUTPUT_NAMES)
            with self.assertRaises(FileExistsError):
                write_evidence(root, "dist/new", self.outputs)
            outside = root / "outside"
            outside.mkdir()
            (root / "link").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(OSError):
                write_evidence(root, "link/escape", self.outputs)
            self.assertEqual(list(outside.iterdir()), [])
            for invalid in ("", "../escape", "/absolute", "a/../b", "a//b"):
                with self.assertRaises(ValueError):
                    write_evidence(root, invalid, self.outputs)
            with self.assertRaises(ValueError):
                write_evidence(root, "audio", {"music.wav": b""})


if __name__ == "__main__":
    unittest.main()
