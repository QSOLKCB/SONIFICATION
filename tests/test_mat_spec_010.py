"""MAT-SPEC-010: terminal claim, source and archive integrity gates.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from materials import mat_spec, mat_spec_009, mat_spec_010

ROOT = Path(__file__).resolve().parents[1]


class ClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parent = mat_spec_009.build_evidence(ROOT)
        cls.bundle = mat_spec_010.build_evidence(ROOT)
        cls.manifest = json.loads(cls.bundle["manifest.json"])
        cls.archive = json.loads(cls.bundle["archive-index.json"])

    def test_chain_replayed_and_parent_hashes_are_exact(self) -> None:
        self.assertEqual(set(self.bundle), mat_spec_010.OUTPUT_NAMES)
        self.assertEqual(len(self.manifest["parent_artifacts"]), 7)
        parent_hashes = {
            name: mat_spec.sha256(raw) for name, raw in self.parent.items()
        }
        if mat_spec_010.PARENT_V9_SHA256 is not None:
            self.assertEqual(parent_hashes, mat_spec_010.PARENT_V9_SHA256)
        for name, record in self.manifest["parent_artifacts"].items():
            self.assertEqual(parent_hashes[name], record["sha256"])
        self.assertEqual(self.manifest["parent_commit"], mat_spec_010.PARENT_COMMIT)
        self.assertIsNone(self.manifest["new_doi"])
        self.assertIsNone(self.manifest["canonical_pcm_sha256"])
        self.assertIsNone(self.manifest["canonical_wav_sha256"])
        self.assertFalse(self.manifest["audio_generated"])

    def test_all_logical_ancestor_outputs_are_indexed_not_invented(self) -> None:
        records = self.archive["ancestor_artifacts"]
        self.assertEqual(self.archive["status"], "REPLAYABLE_INDEX_NOT_AN_EXTERNAL_ARCHIVE")
        self.assertEqual(self.archive["profiles_indexed"], list(mat_spec_010.STAGES))
        self.assertEqual(self.archive["ancestor_artifact_count"], len(records))
        self.assertEqual(
            len(records),
            sum(len(record[2]) for record in mat_spec_010.ancestor_artifact_maps(
                {name: mat_spec.sha256(data) for name, data in self.parent.items()}
            )),
        )
        self.assertEqual(
            len({record["logical_path"] for record in records}), len(records)
        )
        self.assertTrue(all(
            record["content_in_this_manifest"] == "HASH_ONLY_REBUILD_REQUIRED"
            for record in records
        ))
        self.assertEqual(sum(x["logical_path"].endswith(".mid") for x in records), 2)
        self.assertTrue(all(
            x["stage"] == "MAT-SPEC-001"
            for x in records if x["logical_path"].endswith(".mid")
        ))
        self.assertFalse(self.archive["external_archive_in_this_build"])
        self.assertIsNone(self.archive["external_doi"])
        self.assertIsNone(self.archive["archive_release_tag"])

    def test_all_declared_inputs_are_sha256_indexed(self) -> None:
        records = self.archive["repository_files"]
        self.assertEqual(len(records), self.archive["repository_file_count"])
        by_path = {record["path"]: record for record in records}
        self.assertEqual(len(by_path), len(records))
        self.assertIn("AGENTS.md", by_path)
        self.assertIn(".github/workflows/tests.yml", by_path)
        self.assertIn("docs/MAT_SPEC_010_HANDOFF.md", by_path)
        self.assertIn("materials/mat_spec_010.py", by_path)
        self.assertIn("tests/test_mat_spec_010.py", by_path)
        self.assertIn("data/materials/helium4/DispersionAllPressures.txt", by_path)
        self.assertIn(
            "data/materials/helium4/lipa_chui_1984_excerpt.csv", by_path
        )
        for record in records:
            raw = mat_spec.read_regular(ROOT / record["path"])
            self.assertEqual(record["sha256"], mat_spec.sha256(raw))
            self.assertEqual(record["bytes"], len(raw))
            self.assertTrue(record["materialized_in_repository"])

    def test_claims_and_final_closed_science_boundary(self) -> None:
        claims = json.loads(self.bundle["claims.json"])
        sources = json.loads(self.bundle["source-inventory.json"])
        gate = json.loads(self.bundle["closure-gate.json"])
        handoff = json.loads(self.bundle["handoff.json"])
        audit = json.loads(self.bundle["audit.json"])
        self.assertEqual(len(claims["stages"]), 9)
        self.assertEqual(len(sources["source_stages"]), 9)
        self.assertEqual(gate["numbered_profiles"], 10)
        self.assertEqual(gate["predecessor_profiles_replayed"], 9)
        self.assertEqual(
            gate["status"],
            "NUMBERED_SERIES_CLOSED_AT_010_WITH_OPEN_SCIENTIFIC_GATES",
        )
        self.assertFalse(gate["mat_spec_011_allowed"])
        self.assertFalse(gate["real_classifier_trained"])
        self.assertIsNone(gate["real_heldout_accuracy"])
        self.assertFalse(gate["external_research_archive_deposited"])
        self.assertIsNone(gate["new_doi_assigned"])
        self.assertFalse(gate["formal_proof_executed_in_this_profile"])
        self.assertEqual(gate["synthetic_negative_controls_passed"], 14)
        self.assertEqual(handoff["research_profile_series"], "CLOSED_AT_MAT_SPEC_010")
        self.assertEqual(len(handoff["next_projects"]), 2)
        self.assertEqual(handoff["next_projects"][0]["status"], "NOT_STARTED")
        self.assertIsNone(handoff["next_projects"][0]["proof_result"])
        self.assertFalse(handoff["new_mat_spec_profiles_permitted"])
        self.assertEqual(audit["synthetic_controls_replayed"], 14)
        self.assertTrue(audit["stage_010_final"])
        self.assertIsNone(audit["real_phase_classifier_accuracy"])

    def test_complete_bundle_byte_replay_and_internal_receipts(self) -> None:
        with patch(
            "materials.mat_spec_010.mat_spec_009.build_evidence",
            return_value=self.parent,
        ):
            self.assertEqual(mat_spec_010.build_evidence(ROOT), self.bundle)
        for name, rec in self.manifest["outputs"].items():
            self.assertEqual(rec["sha256"], mat_spec.sha256(self.bundle[name]))
            self.assertEqual(rec["bytes"], len(self.bundle[name]))

    def test_synthetic_or_invalid_physical_promotion_blocked(self) -> None:
        split, audit, source_gate = mat_spec_010.verify_parent(self.parent)
        fake_split = dict(split)
        fake_split["holdout_accuracy"] = "1.0"
        with self.assertRaisesRegex(ValueError, "physical admission invariant"):
            mat_spec_010.science_closure(fake_split, audit, source_gate)
        fake_gate = dict(source_gate)
        fake_gate["physical_evidence_admitted"] = True
        with self.assertRaisesRegex(ValueError, "physical admission invariant"):
            mat_spec_010.science_closure(split, audit, fake_gate)
        changed = dict(self.parent)
        source = json.loads(changed["source-gate.json"])
        source["independent_measurement_pairs"] = 2
        changed["source-gate.json"] = mat_spec.canonical_json(source)
        # Altered evidence must fail the ancestor's signed output receipt
        # before a new physical interpretation could even be considered.
        with self.assertRaises(ValueError):
            mat_spec_010.verify_parent(changed)

    def test_no_eleventh_profile_or_claim_evidence_laundering(self) -> None:
        existing = mat_spec_010.ancestor_artifact_maps({
            name: mat_spec.sha256(raw) for name, raw in self.parent.items()
        })
        changed = deepcopy(mat_spec_010.EXPECTED_CLAIMS)
        changed["stages"][0]["profile"] = "MAT-SPEC-011"
        with self.assertRaisesRegex(ValueError, "missing, repeated"):
            mat_spec_010.validate_archive_membership(changed, existing)
        changed = deepcopy(mat_spec_010.EXPECTED_CLAIMS)
        changed["stages"][5]["evidence_file"] = "invented-discovery.json"
        with self.assertRaisesRegex(ValueError, "invalid frozen"):
            mat_spec_010.validate_archive_membership(changed, existing)
        corrupted = list(existing)
        corrupted[0] = (
            corrupted[0][0], corrupted[0][1],
            dict(corrupted[0][2], **{"synthesized.wav": "a" * 64}),
        )
        with self.assertRaisesRegex(ValueError, "malformed ancestor"):
            mat_spec_010.validate_archive_membership(
                mat_spec_010.EXPECTED_CLAIMS, corrupted
            )

    def test_frozen_registry_and_ancestor_mutation_blocked(self) -> None:
        native = mat_spec.read_regular

        def changed(path: Path, limit: int = 1_048_576) -> bytes:
            data = native(path, limit)
            if path.name == "mat_spec_010_claim_registry.json":
                return data.replace(b"MAT-SPEC-001", b"MAT-SPEC-011", 1)
            return data

        with (
            patch(
                "materials.mat_spec_010.mat_spec_009.build_evidence",
                return_value=self.parent,
            ),
            patch("materials.mat_spec_010.mat_spec.read_regular", side_effect=changed),
            self.assertRaisesRegex(ValueError, "scientific contract drift"),
        ):
            mat_spec_010.build_evidence(ROOT)
        modified = dict(self.parent)
        modified["extra.json"] = b"surprise"
        with self.assertRaisesRegex(ValueError, "file membership"):
            mat_spec_010.verify_parent(modified)
        modified = dict(self.parent)
        modified["manifest.json"] = b"wrong"
        with self.assertRaises(ValueError):
            mat_spec_010.verify_parent(modified)

    def test_exclusive_symbolic_export_no_follow_and_no_rendered_audio(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dest = mat_spec_010.write_evidence(root, "dist/closing", self.bundle)
            self.assertEqual({p.name for p in dest.iterdir()}, mat_spec_010.OUTPUT_NAMES)
            with self.assertRaises(FileExistsError):
                mat_spec_010.write_evidence(root, "dist/closing", self.bundle)
            outside = root / "outside"
            outside.mkdir()
            (root / "link").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(OSError):
                mat_spec_010.write_evidence(root, "link/misroute", self.bundle)
            self.assertEqual(list(outside.iterdir()), [])
            for bad in ("", "../escape", "/absolute", "..", "a//b", "a/../b"):
                with self.subTest(bad=bad), self.assertRaises(ValueError):
                    mat_spec_010.write_evidence(root, bad, self.bundle)
            with self.assertRaises(ValueError):
                mat_spec_010.write_evidence(root, "audio", {"sound.wav": b""})
            with self.assertRaises(ValueError):
                mat_spec_010.write_evidence(root, "audio", {"midi.mid": b""})
        for args in (["--render-audio"], ["--format", "wav"]):
            process = subprocess.run(
                [sys.executable, str(ROOT / "scripts/build_mat_spec_010.py"), *args],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(process.returncode, 2)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX only")
    def test_symlink_and_fifo_input_cannot_be_archived(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "linked").symlink_to(ROOT / mat_spec_010.CLAIMS_PATH)
            with self.assertRaises(OSError):
                mat_spec.read_regular(root / "linked")
            os.mkfifo(root / "fifo")
            with self.assertRaises(ValueError):
                mat_spec.read_regular(root / "fifo")


if __name__ == "__main__":
    unittest.main()
