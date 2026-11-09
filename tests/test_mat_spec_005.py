"""MAT-SPEC-005: exact cross-lambda reference, missingness and witness gates.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import csv
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

from materials import mat_spec, mat_spec_004, mat_spec_005

ROOT = Path(__file__).resolve().parents[1]


class SourceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = mat_spec.read_regular(ROOT / mat_spec_005.DATA_PATH)
        cls.rows = mat_spec_005.parse_reference(cls.raw)
        cls.mapped = mat_spec_005.map_receivers(cls.rows)

    def test_printed_reference_values_and_boundary(self) -> None:
        self.assertEqual(len(self.rows), 14)
        self.assertEqual(
            [r["temperature_regime_context"] for r in self.rows].count("CONTEXT_HE_II"),
            9,
        )
        self.assertEqual(
            [r["temperature_regime_context"] for r in self.rows].count("CONTEXT_HE_I"),
            4,
        )
        by_t = {r["temperature_K"]: r for r in self.rows}
        self.assertEqual(by_t["2.1767"]["first_sound_m_per_s"], "2.175E+2")
        self.assertEqual(by_t["2.1769"]["first_sound_m_per_s"], "2.178E+2")
        self.assertEqual(by_t["2.1767"]["heat_capacity_J_per_mol_K"], "6.640E+1")
        self.assertEqual(by_t["2.1769"]["heat_capacity_J_per_mol_K"], "4.569E+1")
        self.assertEqual(by_t["2.1768"]["second_sound_m_per_s"], "0.000E+0")
        self.assertEqual(by_t["2.1768"]["heat_capacity_status"], "LAMBDA_UNDEFINED")
        self.assertIsNone(by_t["2.1768"]["heat_capacity_J_per_mol_K"])
        for t in ("2.1769", "2.1770", "2.1800", "2.2000"):
            self.assertIsNone(by_t[t]["second_sound_m_per_s"])
            self.assertEqual(
                by_t[t]["second_sound_status"], "OUTSIDE_RECOMMENDED_DOMAIN"
            )
        self.assertEqual(by_t["2.1800"]["heat_capacity_status"], "NOT_TABULATED_AT_SELECTED_T")

    def test_source_byte_tamper_and_context_injection_fail(self) -> None:
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            mat_spec_005.parse_reference(self.raw.replace(b"9.809E-1", b"9.808E-1"))
        mutable = [dict(row) for row in self.rows]
        mutable[-1]["independent_row_phase_witness"] = "invented"
        with self.assertRaisesRegex(ValueError, "forged phase"):
            mat_spec_005.evidence_gate(mutable)
        with self.assertRaises(ValueError):
            mat_spec_005._strict_number("NaN")
        with self.assertRaises(ValueError):
            mat_spec_005._strict_number("-0.1")
        for invalid in ("1/2", " 2.1", "0x10", "Infinity"):
            with self.assertRaises(ValueError):
                mat_spec_005._strict_number(invalid)
        corrupted = [dict(row) for row in self.rows]
        corrupted[0]["data_kind"] = "raw_measurement"
        with self.assertRaisesRegex(ValueError, "forged phase"):
            mat_spec_005.evidence_gate(corrupted)
        corrupted = [dict(row) for row in self.rows]
        corrupted[0]["reported_measurement_uncertainty"] = {
            name: ("0.01" if name == "first_sound_m_per_s" else None)
            for name in mat_spec_005.SOURCE_PROPERTIES
        }
        with self.assertRaisesRegex(ValueError, "forged phase"):
            mat_spec_005.evidence_gate(corrupted)
        corrupted = [dict(row) for row in self.rows]
        corrupted[0]["temperature_regime_context"] = "CONTEXT_HE_I"
        with self.assertRaisesRegex(ValueError, "forged phase"):
            mat_spec_005.evidence_gate(corrupted)

    def test_zero_second_sound_distinct_from_out_of_domain(self) -> None:
        u2 = [r for r in self.mapped if r["property"] == "second_sound_m_per_s"]
        self.assertEqual(len(u2), 14)
        self.assertEqual(sum(r["missing_not_zero"] for r in u2), 4)
        self.assertEqual(sum(r["zero_unpitched"] for r in u2), 1)
        boundary = next(r for r in u2 if r["temperature_K"] == "2.1768")
        self.assertEqual(boundary["frequency_target_Hz"], "0")
        self.assertIsNone(boundary["nearest_midi_note"])
        for r in u2:
            if Fraction(r["temperature_K"]) > mat_spec_005.LAMBDA:
                self.assertIsNone(r["frequency_target_Hz"])
                self.assertIsNone(r["nearest_midi_note"])

    def test_near_transition_differences_and_no_significance(self) -> None:
        crossed = mat_spec_005.crossing_reference(self.rows, self.mapped)
        self.assertEqual(
            Fraction(crossed["first_sound_difference_above_minus_below_m_per_s"]),
            Fraction(3, 10),
        )
        self.assertEqual(
            Fraction(crossed["heat_capacity_difference_above_minus_below_J_per_mol_K"]),
            Fraction(-2071, 100),
        )
        self.assertEqual(crossed["second_sound_below_m_per_s"], "9.809E-1")
        self.assertIsNone(crossed["second_sound_above"])
        self.assertEqual(
            crossed["physical_significance_test"],
            "NOT_PERFORMED_NO_REPORTED_PER_ROW_ERRORS",
        )

    def test_exact_roundtrips_and_reassociation_negative_control(self) -> None:
        result = mat_spec_005.audit(self.rows, self.mapped)
        self.assertEqual(result["exact_fraction_target_roundtrip_checks"], 36)
        self.assertEqual(
            [result["source_property_counts"][n]["tabulated"] for n in mat_spec_005.SCALES],
            [14, 10, 12],
        )
        u1 = result["source_property_counts"]["first_sound_m_per_s"]
        self.assertEqual(u1["unique_symbolic_midi_notes"], 1)
        self.assertEqual(u1["colliding_row_pairs_after_midi"], 91)
        u2 = result["source_property_counts"]["second_sound_m_per_s"]
        self.assertEqual(u2["unique_symbolic_midi_notes"], 9)
        self.assertEqual(u2["unpitched_true_zero"], 1)
        self.assertEqual(u2["unique_controls_including_unpitched"], 10)
        heat = result["source_property_counts"]["heat_capacity_J_per_mol_K"]
        self.assertEqual(heat["unique_symbolic_midi_notes"], 8)
        first = [row for row in self.mapped if row["property"] == "first_sound_m_per_s"]
        moved = [dict(row) for row in first]
        moved[8]["frequency_target_Hz"], moved[10]["frequency_target_Hz"] = (
            moved[10]["frequency_target_Hz"], moved[8]["frequency_target_Hz"]
        )
        self.assertEqual(
            sorted(x["frequency_target_Hz"] for x in first),
            sorted(x["frequency_target_Hz"] for x in moved),
        )
        self.assertNotEqual(
            [x["frequency_target_Hz"] for x in first],
            [x["frequency_target_Hz"] for x in moved],
        )


class EvidenceBundles(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = mat_spec_005.build_evidence(ROOT)
        cls.manifest = json.loads(cls.artifacts["manifest.json"])
        cls.audit = json.loads(cls.artifacts["audit.json"])
        cls.phase = json.loads(cls.artifacts["phase-gate.json"])

    def test_receipts_and_deterministic_replay(self) -> None:
        self.assertEqual(set(self.artifacts), mat_spec_005.OUTPUT_NAMES)
        self.assertEqual(self.artifacts, mat_spec_005.build_evidence(ROOT))
        self.assertEqual(self.manifest["source"]["sha256"], mat_spec_005.DATA_SHA256)
        self.assertEqual(self.manifest["parent_commit"], mat_spec_005.PARENT_COMMIT)
        self.assertEqual(
            set(self.manifest["parent_v4_artifacts"]),
            set(mat_spec_005.PARENT_V4_SHA256),
        )
        self.assertIsNone(self.manifest["canonical_pcm_sha256"])
        self.assertIsNone(self.manifest["canonical_wav_sha256"])
        parent = mat_spec_004.build_evidence(ROOT)
        self.assertEqual(set(parent), set(self.manifest["parent_v4_artifacts"]))
        for name, digest in self.manifest["outputs"].items():
            self.assertEqual(mat_spec.sha256(self.artifacts[name]), digest["sha256"])
        for name, digest in self.manifest["parent_v4_artifacts"].items():
            self.assertEqual(mat_spec.sha256(parent[name]), digest["sha256"])

    def test_refuses_phase_classifier_without_independent_witness(self) -> None:
        self.assertEqual(self.phase["cross_transition_reference"], "REPLAY_VERIFIED")
        crossing = json.loads(self.artifacts["crossing.json"])
        self.assertEqual(crossing["contextual_lambda_K"], "2.1768")
        self.assertEqual(
            crossing["receiver_notes_below_above"]["first_sound_m_per_s"], [69, 69]
        )
        self.assertEqual(
            crossing["receiver_notes_below_above"]["heat_capacity_J_per_mol_K"],
            [84, 78],
        )
        self.assertEqual(
            self.phase["independent_phase_witness"],
            "BLOCKED_INSUFFICIENT_INDEPENDENCE_AND_UNCERTAINTY",
        )
        self.assertEqual(self.phase["observations"]["context_He_I"], 4)
        self.assertEqual(self.phase["observations"]["context_He_II"], 9)
        self.assertIsNone(self.phase["heldout_phase_accuracy"])
        self.assertFalse(self.phase["phase_classifier_trained"])
        self.assertIn(
            "NO_SOURCE_SEPARATED_PREREGISTERED_HELD_OUT_EXPERIMENT",
            self.phase["missing_evidence"],
        )
        events = list(csv.DictReader(io.StringIO(
            self.artifacts["receiver-controls.csv"].decode("ascii")
        )))
        self.assertEqual(len(events), 42)

    def test_parent_forgery_and_contract_drift_fail(self) -> None:
        parent = mat_spec_004.build_evidence(ROOT)
        extras = dict(parent)
        extras["extra.json"] = b"noise"
        with (
            patch("materials.mat_spec_005.mat_spec_004.build_evidence", return_value=extras),
            self.assertRaisesRegex(ValueError, "membership"),
        ):
            mat_spec_005.build_evidence(ROOT)
        changed = dict(parent)
        changed["phase-gate.json"] = b"forged"
        with (
            patch("materials.mat_spec_005.mat_spec_004.build_evidence", return_value=changed),
            self.assertRaises(ValueError),
        ):
            mat_spec_005.build_evidence(ROOT)
        normal_reader = mat_spec.read_regular

        def changed_spec(path: Path, limit: int = 1_048_576) -> bytes:
            raw = normal_reader(path, limit)
            if path.name == "mat-spec-005.v0.1.json":
                return raw.replace(b'"sample_count": 14', b'"sample_count": 13')
            return raw

        with (
            patch("materials.mat_spec_005.mat_spec.read_regular", side_effect=changed_spec),
            self.assertRaisesRegex(ValueError, "specification"),
        ):
            mat_spec_005.build_evidence(ROOT)

    def test_safe_symbolic_export_and_audio_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = mat_spec_005.write_evidence(root, "dist/new", self.artifacts)
            self.assertEqual({p.name for p in target.iterdir()}, mat_spec_005.OUTPUT_NAMES)
            with self.assertRaises(FileExistsError):
                mat_spec_005.write_evidence(root, "dist/new", self.artifacts)
            outside = root / "outside"
            outside.mkdir()
            (root / "alias").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(OSError):
                mat_spec_005.write_evidence(root, "alias/escape", self.artifacts)
            self.assertEqual(list(outside.iterdir()), [])
            for bad in ("", "..", "../escape", "/absolute", "a//b", "a/../b"):
                with self.assertRaises(ValueError):
                    mat_spec_005.write_evidence(root, bad, self.artifacts)
            with self.assertRaises(ValueError):
                mat_spec_005.write_evidence(root, "bad", {"audio.wav": b"raw"})
        for args in (["--render-audio"], ["--format", "wav"]):
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts/build_mat_spec_005.py"), *args],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(proc.returncode, 2)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX only")
    def test_special_source_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            actual = ROOT / mat_spec_005.DATA_PATH
            (root / "link").symlink_to(actual)
            with self.assertRaises(OSError):
                mat_spec.read_regular(root / "link")
            os.mkfifo(root / "fifo")
            with self.assertRaises(ValueError):
                mat_spec.read_regular(root / "fifo")


if __name__ == "__main__":
    unittest.main()
