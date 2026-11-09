"""Reject missing or changed files in the retained PR #42 audit evidence."""

from __future__ import annotations

import json
import shutil
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from formal.sonification.audit import verify

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "formal/sonification"


def isolated_audit(tmp_path: Path) -> Path:
    destination = tmp_path / "formal/sonification"
    audit = destination / "audit"
    audit.mkdir(parents=True)
    shutil.copytree(SOURCE / "audit/attempt-003", audit / "attempt-003")
    shutil.copy2(SOURCE / "audit/attempt-003.snapshot.json", audit)
    shutil.copy2(SOURCE / "audit/run.py", audit)
    report = json.loads((audit / "attempt-003/AUDIT.json").read_text())
    for name in report["proof_input_sha256"]:
        target = destination / "lean" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE / "lean" / name, target)
    return audit


def checked_main(audit: Path) -> int:
    with patch.object(verify, "HERE", audit), redirect_stdout(StringIO()):
        return verify.main()


def test_intact_retained_snapshot_matches_accepted_proof(tmp_path: Path) -> None:
    assert checked_main(isolated_audit(tmp_path)) == 0


def test_deleting_all_lean_checker_directories_fails_closed(tmp_path: Path) -> None:
    audit = isolated_audit(tmp_path)
    attempt = audit / "attempt-003"
    shutil.rmtree(attempt / "nominal-build")
    for name in verify.NEGATIVE_MUTATIONS:
        shutil.rmtree(attempt / name / "checker")
    with pytest.raises(ValueError, match="retained audit file inventory mismatch"):
        checked_main(audit)


def test_changed_accepted_theorem_statement_fails_closed(tmp_path: Path) -> None:
    audit = isolated_audit(tmp_path)
    report_path = audit / "attempt-003/AUDIT.json"
    report = json.loads(report_path.read_text())
    report["theorems"][0]["exact_observed_type"] = "False"
    report_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    with pytest.raises(ValueError, match=r"altered retained audit file: AUDIT\.json"):
        checked_main(audit)


@pytest.mark.parametrize(
    "relative,operation",
    [
        ("nominal-build/result.json", "replace"),
        ("nominal-build/declarations.json", "delete"),
        ("nominal-build/toolchain-imports.json", "replace"),
        ("false_theorem/checker/00.stdout", "delete"),
    ],
)
def test_changed_inner_proof_evidence_fails_closed(
    tmp_path: Path, relative: str, operation: str
) -> None:
    audit = isolated_audit(tmp_path)
    path = audit / "attempt-003" / relative
    if operation == "delete":
        path.unlink()
        expected = "retained audit file inventory mismatch"
    else:
        path.write_bytes(path.read_bytes() + b"\nchanged\n")
        expected = "altered retained audit file"
    with pytest.raises(ValueError, match=expected):
        checked_main(audit)


def test_extra_unreviewed_file_fails_closed(tmp_path: Path) -> None:
    audit = isolated_audit(tmp_path)
    (audit / "attempt-003/unreviewed.txt").write_text("extra\n")
    with pytest.raises(ValueError, match="retained audit file inventory mismatch"):
        checked_main(audit)


def test_manifest_rewrite_fails_pinned_identity(tmp_path: Path) -> None:
    audit = isolated_audit(tmp_path)
    manifest_path = audit / "attempt-003.snapshot.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["source_commit"] = "0" * 40
    manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    with pytest.raises(ValueError, match="retained audit snapshot manifest changed"):
        checked_main(audit)


def test_linked_attempt_root_or_manifest_fails_closed(tmp_path: Path) -> None:
    audit = isolated_audit(tmp_path)
    attempt = audit / "attempt-003"
    saved_attempt = audit / "attempt-copy"
    attempt.rename(saved_attempt)
    attempt.symlink_to(saved_attempt, target_is_directory=True)
    with pytest.raises(ValueError, match="linked retained audit root or manifest"):
        checked_main(audit)
    attempt.unlink()
    saved_attempt.rename(attempt)
    manifest = audit / "attempt-003.snapshot.json"
    saved_manifest = audit / "snapshot-copy.json"
    manifest.rename(saved_manifest)
    manifest.symlink_to(saved_manifest)
    with pytest.raises(ValueError, match="linked retained audit root or manifest"):
        checked_main(audit)
