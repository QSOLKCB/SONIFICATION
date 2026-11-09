"""Fail-closed integrity tests for SONIFICATION independent-audit receipts."""

from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from formal.sonification.audit.verify import (
    EXPECTED_EXECUTION_DIRS,
    verify_execution_receipts,
)

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "formal/sonification/audit/attempt-003"
REPORT = json.loads((ORIGINAL / "AUDIT.json").read_text(encoding="utf-8"))


def copy_receipts(destination: Path) -> None:
    for location in EXPECTED_EXECUTION_DIRS:
        source = ORIGINAL / location
        target = destination / location
        target.mkdir(parents=True, exist_ok=False)
        for name in ("execution.json", "stdout.log", "stderr.log"):
            shutil.copyfile(source / name, target / name)


class HistoricalAuditReceiptTests(unittest.TestCase):
    def test_original_execution_inventory_matches_report(self) -> None:
        verify_execution_receipts(ORIGINAL, REPORT["checks"])
        self.assertEqual(len(EXPECTED_EXECUTION_DIRS), 12)

    def test_removing_finite_conformance_and_refinement_evidence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copy_receipts(root)
            shutil.rmtree(root / "finite-conformance")
            shutil.rmtree(root / "refinement-tests")
            with self.assertRaisesRegex(ValueError, "execution receipt inventory mismatch"):
                verify_execution_receipts(root, REPORT["checks"])

    def test_removing_nominal_execution_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copy_receipts(root)
            shutil.rmtree(root / "nominal-command")
            with self.assertRaisesRegex(ValueError, "execution receipt inventory mismatch"):
                verify_execution_receipts(root, REPORT["checks"])

    def test_unexpected_execution_receipt_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copy_receipts(root)
            extra = root / "unrecorded"
            extra.mkdir()
            shutil.copyfile(root / "nominal-command/execution.json", extra / "execution.json")
            with self.assertRaisesRegex(ValueError, "execution receipt inventory mismatch"):
                verify_execution_receipts(root, REPORT["checks"])

    def test_altered_command_record_fails_even_with_intact_logs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copy_receipts(root)
            path = root / "finite-conformance/execution.json"
            record = json.loads(path.read_text(encoding="utf-8"))
            record["argv"] = ["/usr/bin/false"]
            path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "execution receipt disagrees"):
                verify_execution_receipts(root, REPORT["checks"])

    def test_modified_audit_binding_fails_even_with_intact_receipt(self) -> None:
        checks = copy.deepcopy(REPORT["checks"])
        checks[-2]["stdout_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "execution receipt disagrees"):
            verify_execution_receipts(ORIGINAL, checks)

    def test_reordered_or_relabelled_audit_checks_fail(self) -> None:
        checks = copy.deepcopy(REPORT["checks"])
        checks[1], checks[2] = checks[2], checks[1]
        with self.assertRaisesRegex(ValueError, "unexpected audit check identity"):
            verify_execution_receipts(ORIGINAL, checks)

    def test_missing_or_modified_stream_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copy_receipts(root)
            path = root / "refinement-tests/stderr.log"
            path.write_bytes(path.read_bytes() + b"tamper")
            with self.assertRaisesRegex(ValueError, "altered command stream"):
                verify_execution_receipts(root, REPORT["checks"])
            path.unlink()
            with self.assertRaisesRegex(ValueError, "missing or linked command stream"):
                verify_execution_receipts(root, REPORT["checks"])


if __name__ == "__main__":
    unittest.main()
