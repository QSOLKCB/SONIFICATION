"""Fail CI when the retained SONIFICATION model proof or audit input goes stale."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from formal.sonification.audit import model_verify

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "formal/sonification/audit/model_verify.py"


def test_retained_model_proof_audit_binding() -> None:
    completed = subprocess.run(
        [sys.executable, str(VERIFIER)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert '"status": "MODEL_AUDIT_BINDING_MATCH"' in completed.stdout


def _copy_bound_audit(tmp_path: Path) -> Path:
    source = ROOT / "formal/sonification"
    destination = tmp_path / "formal/sonification"
    audit = destination / "audit"
    audit.mkdir(parents=True)
    shutil.copytree(source / "audit/attempt-004-model", audit / "attempt-004-model")
    shutil.copy2(source / "audit/model_run.py", audit / "model_run.py")
    report = json.loads((audit / "attempt-004-model/AUDIT.json").read_text())
    for name in report["proof_input_sha256"]:
        target = destination / "lean" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / "lean" / name, target)
    return audit


@pytest.mark.parametrize("remove_all", [False, True])
def test_missing_recorded_execution_receipts_fail_closed(
    tmp_path: Path, remove_all: bool
) -> None:
    audit = _copy_bound_audit(tmp_path)
    attempt = audit / "attempt-004-model"
    receipts = sorted(attempt.rglob("execution.json"))
    assert len(receipts) == 9
    with patch.object(model_verify, "HERE", audit), redirect_stdout(StringIO()):
        assert model_verify.main() == 0
        for receipt in receipts if remove_all else receipts[:1]:
            shutil.rmtree(receipt.parent)
        with pytest.raises(ValueError, match="missing or unexpected audit execution receipts"):
            model_verify.main()


def test_missing_checker_result_fails_closed(tmp_path: Path) -> None:
    audit = _copy_bound_audit(tmp_path)
    shutil.rmtree(audit / "attempt-004-model/false_theorem/checker")
    with (
        patch.object(model_verify, "HERE", audit),
        redirect_stdout(StringIO()),
        pytest.raises(ValueError, match="missing or unexpected audit checker results"),
    ):
        model_verify.main()


def test_extra_execution_receipt_fails_closed(tmp_path: Path) -> None:
    audit = _copy_bound_audit(tmp_path)
    attempt = audit / "attempt-004-model"
    extra = attempt / "unexpected/command"
    extra.mkdir(parents=True)
    shutil.copy2(attempt / "nominal-command/execution.json", extra / "execution.json")
    with (
        patch.object(model_verify, "HERE", audit),
        redirect_stdout(StringIO()),
        pytest.raises(ValueError, match="missing or unexpected audit execution receipts"),
    ):
        model_verify.main()


def test_changed_child_log_and_matching_child_hash_fail_root_binding(tmp_path: Path) -> None:
    audit = _copy_bound_audit(tmp_path)
    command_dir = audit / "attempt-004-model/nominal-command"
    altered = b"tampered command output\n"
    (command_dir / "stdout.log").write_bytes(altered)
    receipt = command_dir / "execution.json"
    child = json.loads(receipt.read_text())
    child["stdout_sha256"] = hashlib.sha256(altered).hexdigest()
    receipt.write_text(json.dumps(child, sort_keys=True, indent=2) + "\n")
    with (
        patch.object(model_verify, "HERE", audit),
        redirect_stdout(StringIO()),
        pytest.raises(ValueError, match="audit execution mismatch"),
    ):
        model_verify.main()


def test_checker_command_inventory_cannot_be_cleared(tmp_path: Path) -> None:
    audit = _copy_bound_audit(tmp_path)
    nominal_dir = audit / "attempt-004-model/nominal-build"
    result_path = nominal_dir / "result.json"
    result = json.loads(result_path.read_text())
    assert len(result["commands"]) == 4
    for command in result["commands"]:
        for stream in ("stdout", "stderr"):
            (nominal_dir / command[stream + "_path"]).unlink()
    result["commands"] = []
    result_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    with (
        patch.object(model_verify, "HERE", audit),
        redirect_stdout(StringIO()),
        pytest.raises(ValueError, match="altered checker result"),
    ):
        model_verify.main()


def test_checker_version_stderr_is_required(tmp_path: Path) -> None:
    audit = _copy_bound_audit(tmp_path)
    (audit / "attempt-004-model/nominal-build/version.stderr").unlink()
    with (
        patch.object(model_verify, "HERE", audit),
        redirect_stdout(StringIO()),
        pytest.raises(FileNotFoundError, match=r"version\.stderr"),
    ):
        model_verify.main()


def test_checker_version_stdout_bytes_are_bound(tmp_path: Path) -> None:
    audit = _copy_bound_audit(tmp_path)
    version = audit / "attempt-004-model/nominal-build/version.stdout"
    version.write_bytes(b"\n" + version.read_bytes())
    with (
        patch.object(model_verify, "HERE", audit),
        redirect_stdout(StringIO()),
        pytest.raises(ValueError, match="altered checker version output"),
    ):
        model_verify.main()


def test_joint_child_and_root_report_tamper_fails_pinned_report(tmp_path: Path) -> None:
    audit = _copy_bound_audit(tmp_path)
    attempt = audit / "attempt-004-model"
    command_dir = attempt / "nominal-command"
    altered = b"tampered command output\n"
    (command_dir / "stdout.log").write_bytes(altered)
    child_path = command_dir / "execution.json"
    child = json.loads(child_path.read_text())
    child["stdout_sha256"] = hashlib.sha256(altered).hexdigest()
    child_path.write_text(json.dumps(child, sort_keys=True, indent=2) + "\n")
    root_path = attempt / "AUDIT.json"
    report = json.loads(root_path.read_text())
    report["checks"][0]["stdout_sha256"] = child["stdout_sha256"]
    root_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    with (
        patch.object(model_verify, "HERE", audit),
        redirect_stdout(StringIO()),
        pytest.raises(ValueError, match="recorded independent audit report changed"),
    ):
        model_verify.main()
