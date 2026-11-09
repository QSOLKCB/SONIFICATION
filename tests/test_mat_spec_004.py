"""MAT-SPEC-004 exact table, phase gate, receipts and symbolic export tests.

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

from materials import mat_spec, mat_spec_003, mat_spec_004

ROOT = Path(__file__).resolve().parents[1]


class TemperatureMappingTests(unittest.TestCase):
    def test_exact_source_values_and_fraction_closure(self) -> None:
        raw = mat_spec.read_regular(ROOT / mat_spec_004.DATA_PATH)
        original = mat_spec_004.parse_source(raw)
        self.assertEqual(len(original), 8)
        self.assertEqual(original[0]["temperature_K"], "0.9")
        self.assertEqual(original[-1]["temperature_K"], "2.1")
        self.assertEqual(original[0]["normal_fraction"], "0.003")
        self.assertEqual(original[-1]["normal_fraction"], "0.741")
        self.assertEqual(
            [p["mutual_friction_alpha"] for p in original],
            ["0.0025", "0.011", "0.026", "0.051", "0.097", "0.160", "0.206", "0.48"],
        )
        for p in original:
            self.assertEqual(
                Fraction(p["normal_fraction"]) + Fraction(p["superfluid_fraction"]),
                1,
            )
            self.assertIsNone(p["superfluid_fraction_uncertainty"])
            self.assertIsNone(p["independent_phase_diagnostic"])

    def test_source_tamper_and_relabel_are_rejected(self) -> None:
        raw = mat_spec.read_regular(ROOT / mat_spec_004.DATA_PATH)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            mat_spec_004.parse_source(raw.replace(b"0.003", b"0.004"))
        rows = mat_spec_004.parse_source(raw)
        rows[0]["independent_phase_label"] = "He-I"
        with self.assertRaisesRegex(ValueError, "unrecognised phase evidence"):
            mat_spec_004.phase_admission(rows)

    def test_quantization_roundtrip_and_negative_reassociation(self) -> None:
        raw = mat_spec.read_regular(ROOT / mat_spec_004.DATA_PATH)
        mapped = mat_spec_004.map_temperature(mat_spec_004.parse_source(raw))
        audit = mat_spec_004.audit_temperature(mapped)
        self.assertEqual(audit["exact_mass_fraction_closure_checks"], 8)
        self.assertEqual(audit["exact_authored_frequency_roundtrips"], 8)
        self.assertEqual(audit["full_precision_fraction_values_distinct"], 8)
        self.assertEqual(audit["quantized_midi_unique_notes"], 6)
        self.assertEqual(audit["quantized_midi_colliding_pairs"], 3)
        self.assertEqual(audit["pairwise_source_comparisons"], 28)
        self.assertEqual(
            [p["quantized_midi_note"] for p in mapped], [67, 67, 67, 66, 64, 61, 58, 44]
        )
        self.assertEqual([p["rank_offset"] for p in mapped], [3, 2, 1, 0, -1, -2, -3, -4])
        self.assertFalse(
            mat_spec_004.is_strictly_decreasing(
                [Fraction(p["superfluid_fraction"]) for p in reversed(mapped)]
            )
        )

    def test_phase_gate_rejects_unverified_labels_and_results(self) -> None:
        rows = mat_spec_004.parse_source(
            mat_spec.read_regular(ROOT / mat_spec_004.DATA_PATH)
        )
        gate = mat_spec_004.phase_admission(rows)
        self.assertEqual(gate["status"], "BLOCKED_INSUFFICIENT_PHYSICAL_EVIDENCE")
        self.assertEqual(gate["observed_regimes"]["verified_He_I"], 0)
        self.assertIsNone(gate["phase_accuracy"])
        self.assertIsNone(gate["holdout_score"])
        self.assertFalse(gate["phase_classifier_trained"])
        self.assertFalse(gate["temperature_threshold_used_as_classifier"])
        self.assertIn("NO_INDEPENDENT_PHASE_DIAGNOSTIC", gate["reasons"])


class BundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = mat_spec_004.build_evidence(ROOT)
        cls.manifest = json.loads(cls.bundle["manifest.json"])

    def test_replay_and_parent_artifact_manifest(self) -> None:
        self.assertEqual(self.bundle, mat_spec_004.build_evidence(ROOT))
        self.assertEqual(set(self.bundle), mat_spec_004.OUTPUT_NAMES)
        self.assertEqual(self.manifest["profile"], "MAT-SPEC-004")
        self.assertEqual(self.manifest["parent_commit"], mat_spec_004.PARENT_COMMIT)
        self.assertEqual(
            self.manifest["source"]["sha256"], mat_spec_004.DATA_SHA256
        )
        for name, record in self.manifest["outputs"].items():
            self.assertEqual(mat_spec.sha256(self.bundle[name]), record["sha256"])
        self.assertIsNone(self.manifest["canonical_pcm_sha256"])
        self.assertIsNone(self.manifest["canonical_wav_sha256"])
        parent = mat_spec_003.build_evidence(ROOT)
        self.assertEqual(
            self.manifest["parent_artifacts"].keys(), parent.keys()
        )
        for name, record in self.manifest["parent_artifacts"].items():
            self.assertEqual(record["sha256"], mat_spec.sha256(parent[name]))
        if mat_spec_004.PARENT_V3_SHA256 is not None:
            self.assertEqual(
                {name: mat_spec.sha256(data) for name, data in parent.items()},
                mat_spec_004.PARENT_V3_SHA256,
            )

    def test_manifest_and_no_unsourced_phase_claims(self) -> None:
        data = json.loads(self.bundle["observations.json"])
        self.assertEqual(len(data["observations"]), 8)
        gate = json.loads(self.bundle["phase-gate.json"])
        self.assertFalse(gate["phase_classifier_trained"])
        self.assertEqual(gate["observed_regimes"]["verified_He_I"], 0)
        audit = json.loads(self.bundle["audit.json"])
        self.assertEqual(audit["quantized_midi_colliding_pairs"], 3)
        rows = list(csv.DictReader(io.StringIO(
            self.bundle["temperature-controls.csv"].decode()
        )))
        self.assertEqual(len(rows), 8)
        self.assertEqual(rows[0]["quantized_midi_note"], "67")

    def test_fail_on_metadata_and_parent_changes(self) -> None:
        original = mat_spec.read_regular

        def altered_meta(path: Path, limit: int = 1_048_576) -> bytes:
            raw = original(path, limit)
            if path.name == "temperature_table1_2022.source.json":
                return raw.replace(b'"licence"', b'"licence_edited"')
            return raw

        with (
            patch("materials.mat_spec_004.mat_spec.read_regular", side_effect=altered_meta),
            self.assertRaisesRegex(ValueError, "provenance or contract drift"),
        ):
            mat_spec_004.build_evidence(ROOT)
        original_parent = mat_spec_003.build_evidence(ROOT)
        extra = dict(original_parent)
        extra["injected.json"] = b"unexpected"
        with (
            patch("materials.mat_spec_004.mat_spec_003.build_evidence", return_value=extra),
            self.assertRaisesRegex(ValueError, "artifact membership"),
        ):
            mat_spec_004.build_evidence(ROOT)
        drifted = dict(original_parent)
        drifted["controls.json"] = b"changed"
        with (
            patch("materials.mat_spec_004.mat_spec_003.build_evidence", return_value=drifted),
            self.assertRaises(ValueError),
        ):
            mat_spec_004.build_evidence(ROOT)

    def test_symbolic_no_overwrite_symlink_and_bad_format(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            output = mat_spec_004.write_evidence(root, "dist/new", self.bundle)
            self.assertEqual({x.name for x in output.iterdir()}, mat_spec_004.OUTPUT_NAMES)
            with self.assertRaises(FileExistsError):
                mat_spec_004.write_evidence(root, "dist/new", self.bundle)
            outside = root / "outside"
            outside.mkdir()
            (root / "link").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(OSError):
                mat_spec_004.write_evidence(root, "link/evil", self.bundle)
            self.assertEqual(list(outside.iterdir()), [])
            for bad in ("", "../bad", "/abs", "x/../y", "x//y"):
                with self.assertRaises(ValueError):
                    mat_spec_004.write_evidence(root, bad, self.bundle)
            with self.assertRaises(ValueError):
                mat_spec_004.write_evidence(root, "bad", {"audio.wav": b"bad"})
        for args in (["--render-audio"], ["--format", "wav"]):
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/build_mat_spec_004.py"), *args],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 2)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX-only FIFO")
    def test_source_symlink_and_fifo_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            origin = ROOT / mat_spec_004.DATA_PATH
            link = root / "link.csv"
            link.symlink_to(origin)
            with self.assertRaises(OSError):
                mat_spec.read_regular(link)
            fifo = root / "special"
            os.mkfifo(fifo)
            with self.assertRaises(ValueError):
                mat_spec.read_regular(fifo)


if __name__ == "__main__":
    unittest.main()
