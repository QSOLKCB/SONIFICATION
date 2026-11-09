"""Exercise receipt-integrity failures in isolated copies, preserving raw logs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
AUDIT_SHA256 = "34eef078032bfb168faec6ba3bfe82cbf7e6bdc0412fe56820bc2bf2e26665d8"
ROOTS = (
    "audit/attempt-001",
    "lean/attempts/commit-bound-001",
    "lean/attempts/commit-bound-negative-001",
)
NESTED_LOG = (
    "audit/attempt-001/fresh-negative/prohibited_data_assumption/verification/02.stderr"
)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def fixture(work: Path) -> None:
    for root in ROOTS:
        shutil.copytree(BASE / root, work / root, symlinks=True)
    shutil.copyfile(HERE / "verify.py", work / "audit/verify.py")
    inputs = json.loads((HERE / "attempt-001/input-manifest.json").read_text())
    for name in inputs["input_files"]:
        target = work / "lean" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(BASE / "lean" / name, target)


def mutate(name: str, work: Path, case: Path) -> str:
    manifest = work / "audit/attempt-001/AUDIT.json"
    if name in {"changed_accepted_theorem_type", "promoted_refinement"}:
        audit = json.loads(manifest.read_text())
        if name == "changed_accepted_theorem_type":
            audit["claims"][0]["type"] = "True"
        else:
            audit["assurance"]["REFINEMENT_PROVED"] = "PASS"
            audit["claims"][0]["assurance"]["REFINEMENT_PROVED"] = "PASS"
        write_json(manifest, audit)
        shutil.copyfile(manifest, case / "mutated-AUDIT.json")
        return "accepted audit SHA-256 mismatch"
    if name == "deleted_nested_log":
        (work / NESTED_LOG).unlink()
        return "evidence membership mismatch"
    if name in {"deleted_postcommit_receipt", "deleted_all_postcommit_receipts"}:
        shutil.rmtree(work / ROOTS[1])
        if name == "deleted_all_postcommit_receipts":
            shutil.rmtree(work / ROOTS[2])
        return "required evidence root missing"
    if name == "extra_file":
        (work / "audit/attempt-001/unrecorded.json").write_text("{}\n")
        return "evidence membership mismatch"
    if name == "extra_empty_directory":
        (work / "audit/attempt-001/unrecorded-empty-directory").mkdir()
        return "evidence directory membership mismatch"
    if name in {"symlink_audit_root", "symlink_postcommit_root"}:
        path = work / ROOTS[0 if name == "symlink_audit_root" else 1]
        backing = work / "unbound-root-backing"
        path.rename(backing)
        path.symlink_to(backing, target_is_directory=True)
        return "symlink path rejected"
    if name in {"symlink_manifest", "symlink_individual_log"}:
        path = manifest if name == "symlink_manifest" else work / NESTED_LOG
        backing = work / "unbound-file-backing"
        path.rename(backing)
        path.symlink_to(backing)
        return "symlink path rejected" if name == "symlink_manifest" else "symlink evidence rejected"
    if name == "joint_log_and_manifest_tamper":
        log = work / NESTED_LOG
        log.write_bytes(b"jointly altered execution evidence\n")
        audit = json.loads(manifest.read_text())
        audit["evidence_files"][NESTED_LOG] = {
            "sha256": digest(log.read_bytes()), "bytes": log.stat().st_size,
        }
        write_json(manifest, audit)
        shutil.copyfile(manifest, case / "mutated-AUDIT.json")
        shutil.copyfile(log, case / "mutated-child-log")
        return "accepted audit SHA-256 mismatch"
    if name == "changed_current_theorem_statement":
        path = work / "lean/theorem-statements.json"
        statements = json.loads(path.read_text())
        statements[0]["type"] = "True"
        write_json(path, statements)
        shutil.copyfile(path, case / "mutated-theorem-statements.json")
        return "current proof input mismatch"
    if name == "optimized_python":
        return "optimized Python is rejected"
    if name != "baseline":
        raise ValueError(name)
    return "AUDIT_ACCEPTED_FOR_DECLARED_PARTIAL_SCOPE"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_name", help="new append-only result directory")
    parser.add_argument("--lean-root", required=True, type=Path)
    args = parser.parse_args()
    if re.fullmatch(r"[A-Za-z0-9_-]+", args.output_name) is None:
        parser.error("output name must contain only letters, digits, underscore or hyphen")
    out = HERE / args.output_name
    out.mkdir(exist_ok=False)
    original = (HERE / "attempt-001/AUDIT.json").read_bytes()
    if digest(original) != AUDIT_SHA256:
        raise ValueError("accepted source AUDIT.json changed before mutation execution")
    inputs = out / "inputs"
    inputs.mkdir()
    for name in ("verify.py", "binder_negative.py"):
        shutil.copyfile(HERE / name, inputs / name)
    cases = [
        "baseline", "changed_accepted_theorem_type", "promoted_refinement",
        "deleted_nested_log", "deleted_postcommit_receipt", "deleted_all_postcommit_receipts",
        "extra_file", "extra_empty_directory", "symlink_audit_root",
        "symlink_postcommit_root", "symlink_manifest", "symlink_individual_log",
        "joint_log_and_manifest_tamper", "changed_current_theorem_statement", "optimized_python",
    ]
    results = []
    for name in cases:
        case = out / name
        case.mkdir()
        with tempfile.TemporaryDirectory(prefix="mat008-binder-mutation-") as temp:
            work = Path(temp)
            fixture(work)
            expected_message = mutate(name, work, case)
            argv = [sys.executable]
            if name == "optimized_python":
                argv.append("-O")
            argv.extend([
                str(work / "audit/verify.py"), "attempt-001",
                "--lean-root", str(args.lean_root),
            ])
            timed_out = False
            try:
                run = subprocess.run(argv, cwd=work, capture_output=True, timeout=60)
            except subprocess.TimeoutExpired as exc:
                timed_out = True
                run = subprocess.CompletedProcess(argv, None, exc.stdout or b"", exc.stderr or b"")
            (case / "stdout").write_bytes(run.stdout)
            (case / "stderr").write_bytes(run.stderr)
            expected_exit = 0 if name == "baseline" else 1
            matched = expected_message in (run.stdout + run.stderr).decode(errors="replace")
            record = {
                "case": name, "argv": argv, "cwd": str(work),
                "exit_code": run.returncode, "expected_exit_code": expected_exit,
                "timed_out": timed_out, "expected_diagnostic": expected_message,
                "stdout_sha256": digest(run.stdout), "stderr_sha256": digest(run.stderr),
                "status": "PASS" if run.returncode == expected_exit and matched and not timed_out else "FAIL",
            }
            write_json(case / "command.json", record)
            results.append(record)
    unchanged = (HERE / "attempt-001/AUDIT.json").read_bytes() == original
    report = {
        "status": "PASS" if unchanged and all(r["status"] == "PASS" for r in results) else "FAIL",
        "scope": "Evidence-binder integrity only; no new Lean proof or Python refinement",
        "accepted_audit_sha256": AUDIT_SHA256,
        "accepted_audit_unchanged": unchanged,
        "verifier_sha256": digest((inputs / "verify.py").read_bytes()),
        "runner_sha256": digest((inputs / "binder_negative.py").read_bytes()),
        "python_executable": sys.executable, "python_version": sys.version,
        "baseline_cases": 1, "negative_cases": len(results) - 1,
        "results": results,
        "REFINEMENT_PROVED": "OPEN",
        "limitations": [
            "Checks static artifacts with trusted OS execution, not concurrent adversarial replacement.",
            "Reviewed verifier code and the independent audit digest pin remain trusted inputs.",
            "Content binding is not a signature or experimental-source authentication.",
        ],
    }
    write_json(out / "result.json", report)
    print(json.dumps({"status": report["status"], "baseline": 1, "negative": len(results) - 1}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
