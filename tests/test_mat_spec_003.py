"""MAT-SPEC-003 exact interval, synthetic negative control and replay gates.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

from materials import mat_spec, mat_spec_002, mat_spec_003

ROOT = Path(__file__).resolve().parents[1]


def row(q: str, energy: str | None, error: str = "0.1") -> dict:
    return {
        "q_inverse_angstrom": q,
        "energy_meV": energy,
        "reported_energy_error_meV": error if energy is not None else None,
        "status": "tabulated" if energy is not None else "missing",
    }


class ModeContractTests(unittest.TestCase):
    def test_exact_phonon_origin_slope_interval(self) -> None:
        measured = [row("1", "2", "0.1"), row("2", "4", "0.2")]
        got = mat_spec_003.mode_feature(measured, "phonon", ("1", "2"))
        self.assertEqual(got["status"], "COMPLETE")
        self.assertEqual(Fraction(got["nominal"]), 2)
        self.assertEqual(Fraction(got["lower"]), Fraction(19, 10))
        self.assertEqual(Fraction(got["upper"]), Fraction(21, 10))
        self.assertEqual(got["unit"], "meV*angstrom")
        self.assertIsNone(got["nominal_q_inverse_angstrom"])

    def test_maxon_bounds_and_candidate_q(self) -> None:
        measured = [
            row("1.0", "1", "0.1"),
            row("1.1", "4", "0.2"),
            row("1.2", "2", "0.1"),
        ]
        got = mat_spec_003.mode_feature(measured, "maxon", ("1.0", "1.2"))
        self.assertEqual(got["nominal"], "4")
        self.assertEqual(got["nominal_q_inverse_angstrom"], "1.1")
        self.assertEqual(Fraction(got["lower"]), Fraction(19, 5))
        self.assertEqual(Fraction(got["upper"]), Fraction(21, 5))
        self.assertEqual(got["candidate_q_inverse_angstrom"], ["1.1"])
        self.assertTrue(got["unique_extremum_certified"])
        self.assertTrue(got["nominal_q_interior"])

    def test_roton_interval_tie_and_boundary_uncertainty(self) -> None:
        measured = [
            row("1.7", "3", "1"),
            row("1.8", "1", "1"),
            row("1.9", "1", "1"),
            row("2.0", "3", "1"),
        ]
        got = mat_spec_003.mode_feature(measured, "roton", ("1.7", "2.0"))
        self.assertEqual(got["nominal_q_inverse_angstrom"], "1.8")
        self.assertEqual(got["lower"], "0")
        self.assertEqual(got["upper"], "2")
        self.assertEqual(
            got["candidate_q_inverse_angstrom"], ["1.7", "1.8", "1.9", "2.0"]
        )
        self.assertFalse(got["unique_extremum_certified"])

    def test_missing_blocks_comparison_and_unique_claim(self) -> None:
        rows = [row("1.0", "3"), row("1.1", None), row("1.2", "1")]
        got = mat_spec_003.mode_feature(rows, "maxon", ("1.0", "1.2"))
        self.assertEqual(got["status"], "PARTIAL")
        self.assertEqual(got["missing"], 1)
        self.assertFalse(got["unique_extremum_certified"])
        self.assertEqual(mat_spec_003.interval_decision(got, got), "INELIGIBLE")
        all_missing = mat_spec_003.mode_feature(
            [row("1.0", None)], "maxon", ("0.9", "1.1")
        )
        self.assertEqual(all_missing["status"], "MISSING")
        self.assertIsNone(all_missing["nominal"])

    def test_closed_interval_touch_and_strict_separation(self) -> None:
        a = {"status": "COMPLETE", "lower": "1", "upper": "2"}
        b = {"status": "COMPLETE", "lower": "2", "upper": "3"}
        self.assertEqual(mat_spec_003.interval_decision(a, b), "overlap")
        b["lower"] = "2.01"
        self.assertEqual(mat_spec_003.interval_decision(a, b), "a_below_b")
        self.assertEqual(mat_spec_003.interval_decision(b, a), "b_below_a")

    def test_synthetic_controls_scale_and_permutation(self) -> None:
        source = [row("1", "2", "0.1"), row("2", "4", "0.2")]
        doubled = [mat_spec_003.scale_observation(p, Fraction(2)) for p in source]
        first = mat_spec_003.mode_feature(source, "phonon", ("1", "2"))
        second = mat_spec_003.mode_feature(doubled, "phonon", ("1", "2"))
        self.assertEqual(Fraction(second["nominal"]), 2 * Fraction(first["nominal"]))
        self.assertEqual(Fraction(second["lower"]), 2 * Fraction(first["lower"]))
        inverted = [row("1", "4", "0.2"), row("2", "2", "0.1")]
        reverse = mat_spec_003.mode_feature(inverted, "phonon", ("1", "2"))
        self.assertNotEqual(first["nominal"], reverse["nominal"])
        with self.assertRaises(ValueError):
            mat_spec_003.scale_observation(source[0], Fraction(-1))

    def test_fail_closed_window_and_q_order(self) -> None:
        with self.assertRaises(ValueError):
            mat_spec_003.mode_feature([row("1", "2")], "roton", ("2", "1"))
        with self.assertRaises(ValueError):
            mat_spec_003.mode_feature([row("2", "2"), row("1", "2")], "roton", ("1", "2"))
        with self.assertRaises(ValueError):
            mat_spec_003.mode_feature([row("1", "2")], "unknown", ("0", "2"))


class RuntimeEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = mat_spec_003.build_evidence(ROOT)
        cls.manifest = json.loads(cls.bundle["manifest.json"])
        cls.features = json.loads(cls.bundle["feature-intervals.json"])
        cls.controls = json.loads(cls.bundle["controls.json"])

    def test_full_profile_and_pair_counts(self) -> None:
        self.assertEqual(set(self.bundle), mat_spec_003.OUTPUT_NAMES)
        rows = list(csv.DictReader(io.StringIO(self.bundle["features.csv"].decode())))
        pairs = list(
            csv.DictReader(io.StringIO(self.bundle["pressure-discrimination.csv"].decode()))
        )
        self.assertEqual(len(rows), 21)
        self.assertEqual(len(pairs), 63)
        self.assertEqual(
            {p["mode"] for p in pairs},
            {"phonon", "maxon", "roton"},
        )
        for mode in mat_spec_003.MODES:
            self.assertEqual(
                sum(self.controls["pressure_pair_interval_counts"][mode].values()), 21
            )
        self.assertEqual(self.controls["metamorphic_checks"]["factor_two_energy_and_error"], 21)
        for pressure in mat_spec.PRESSURES:
            self.assertEqual(set(self.features[pressure]), set(mat_spec_003.MODES))
        self.assertTrue(self.controls["no_sampled_audio_generated"])

    def test_merged_mat_spec_002_five_output_hash_pins(self) -> None:
        ancestor = mat_spec_002.build_evidence(ROOT)
        self.assertEqual(
            {name: mat_spec.sha256(raw) for name, raw in ancestor.items()},
            mat_spec_003.PARENT_V2_SHA256,
        )
        self.assertEqual(
            set(self.manifest["parent_v2_artifacts"]),
            set(mat_spec_003.PARENT_V2_SHA256),
        )

    def test_manifest_parent_receipts_and_replay(self) -> None:
        self.assertEqual(self.bundle, mat_spec_003.build_evidence(ROOT))
        self.assertEqual(self.manifest["profile"], mat_spec_003.PROFILE)
        for name, expected in self.manifest["outputs"].items():
            self.assertEqual(mat_spec.sha256(self.bundle[name]), expected["sha256"])
        self.assertEqual(self.manifest["source_sha256"], mat_spec.SOURCE_SHA256)
        self.assertEqual(
            self.manifest["frozen_v1_artifacts"], mat_spec_002.PARENT_ARTIFACT_SHA256
        )
        self.assertIsNone(self.manifest["canonical_pcm_sha256"])
        self.assertIsNone(self.manifest["canonical_wav_sha256"])
        self.assertEqual(
            self.controls["assurance"]["normal_superfluid_phase_classification"],
            "NOT_TESTED",
        )

    def test_contract_drift_and_parent_mutation_are_rejected(self) -> None:
        baseline = mat_spec_002.build_evidence(ROOT)
        alternate = {name: data for name, data in baseline.items()}
        alternate["audit.json"] = b"tampered"
        with (
            patch("materials.mat_spec_003.mat_spec_002.build_evidence", return_value=alternate),
            self.assertRaises(ValueError),
        ):
            mat_spec_003.build_evidence(ROOT)
        real_read = mat_spec.read_regular

        def fake_spec(path: Path, limit: int = 1_048_576) -> bytes:
            raw = real_read(path, limit)
            if path.name == "mat-spec-003.v0.1.json":
                return raw.replace(b'"version": "0.1.0"', b'"version": "0.9.9"')
            return raw

        with (
            patch("materials.mat_spec_003.mat_spec.read_regular", side_effect=fake_spec),
            self.assertRaisesRegex(ValueError, "frozen mode contract mismatch"),
        ):
            mat_spec_003.build_evidence(ROOT)

    def test_posthoc_core_is_explicit_and_primary_roton_failure_is_preserved(self) -> None:
        core = json.loads(self.bundle["coverage-core.json"])
        info = core["selection"]
        self.assertEqual(info["status"], "EXPLORATORY_POSTHOC_COVERAGE_SELECTED")
        self.assertFalse(info["pre_registered"])
        self.assertEqual(info["complete_roton_q_window"], ["1.860", "2.150"])
        self.assertEqual(info["complete_q_positions"], 146)
        self.assertEqual(len(info["q_inverse_angstrom"]), 146)
        self.assertTrue(info["all_pressure_observed"])
        self.assertEqual(
            self.controls["pressure_pair_interval_counts"]["roton"]["INELIGIBLE"], 21
        )
        self.assertEqual(
            self.controls["coverage_core_interval_counts"]["roton"]["INELIGIBLE"], 0
        )
        rows = list(csv.DictReader(io.StringIO(
            self.bundle["core-discrimination.csv"].decode()
        )))
        self.assertEqual(len(rows), 63)
        self.assertEqual(
            sum(self.controls["coverage_core_interval_counts"]["roton"].values()), 21
        )
        self.assertEqual(
            self.controls["metamorphic_checks"]["factor_two_coverage_core"], 21
        )
        self.assertEqual(
            self.controls["coverage_core_receiver"]["collision_audit"][
                "exact_common_scale"
            ]["complete_profiles"], 7
        )
        for pressure in mat_spec.PRESSURES:
            self.assertEqual(core["features"][pressure]["roton"]["status"], "COMPLETE")
        original = mat_spec.build_bundle(ROOT)
        indexed = mat_spec_002.index_observations(
            json.loads(original["observations.json"])["observations"]
        )
        changed = {p: [dict(row) for row in rows] for p, rows in indexed.items()}
        for row in changed["0"]:
            if row["q_inverse_angstrom"] == "1.860":
                row["status"] = "missing"
                break
        with self.assertRaisesRegex(ValueError, "coverage-core selection drift"):
            mat_spec_003.coverage_core_window(changed)

    def test_fresh_no_follow_output_and_audio_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            location = mat_spec_003.write_evidence(root, "dist/evidence", self.bundle)
            self.assertEqual({p.name for p in location.iterdir()}, mat_spec_003.OUTPUT_NAMES)
            with self.assertRaises(FileExistsError):
                mat_spec_003.write_evidence(root, "dist/evidence", self.bundle)
            external = root / "external"
            external.mkdir()
            (root / "link").symlink_to(external, target_is_directory=True)
            with self.assertRaises(OSError):
                mat_spec_003.write_evidence(root, "link/escape", self.bundle)
            self.assertEqual(list(external.iterdir()), [])
            for bad in ("", "a//b", "../escape", "/absolute", "a/../b"):
                with self.assertRaises(ValueError):
                    mat_spec_003.write_evidence(root, bad, self.bundle)
            with self.assertRaises(ValueError):
                mat_spec_003.write_evidence(root, "bad", {"noise.wav": b""})
        for args in (["--render-audio"], ["--format", "wav"]):
            run = subprocess.run(
                [sys.executable, str(ROOT / "scripts/build_mat_spec_003.py"), *args],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(run.returncode, 2)


if __name__ == "__main__":
    unittest.main()
