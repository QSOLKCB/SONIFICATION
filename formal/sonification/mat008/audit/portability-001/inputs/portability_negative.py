"""Retain full-audit controls for a relocated, byte-identical Lean installation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERIFIER = HERE / "verify.py"
IMPORTS = HERE / "attempt-001/fresh-checker/toolchain-imports.json"
EXPECTED_BINARY = "92c3d35b5bfaa5e0fea413a775d504cf46cd95e1345df61c2274f76779e7e023"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def save_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def capture(out: Path, name: str, root: Path, expected_exit: int, diagnostic: str) -> dict:
    argv = [sys.executable, str(VERIFIER), "attempt-001", "--lean-root", str(root)]
    timed_out = False
    try:
        result = subprocess.run(argv, capture_output=True, timeout=60)
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        result = subprocess.CompletedProcess(argv, None, exc.stdout or b"", exc.stderr or b"")
    (out / f"{name}.stdout").write_bytes(result.stdout)
    (out / f"{name}.stderr").write_bytes(result.stderr)
    observed = (result.stdout + result.stderr).decode(errors="replace")
    record = {
        "name": name,
        "argv": argv,
        "exit_code": result.returncode,
        "expected_exit_code": expected_exit,
        "timed_out": timed_out,
        "expected_diagnostic": diagnostic,
        "stdout_sha256": digest(result.stdout),
        "stderr_sha256": digest(result.stderr),
        "status": "PASS" if result.returncode == expected_exit
        and not timed_out and diagnostic in observed else "FAIL",
    }
    save_json(out / f"{name}.json", record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_name", help="new append-only result directory")
    parser.add_argument("--lean-root", required=True, type=Path)
    args = parser.parse_args()
    if re.fullmatch(r"[A-Za-z0-9_-]+", args.output_name) is None:
        parser.error("output name must contain only letters, digits, underscore or hyphen")
    actual = args.lean_root
    if not actual.is_absolute() or actual != actual.resolve(strict=True):
        raise ValueError("--lean-root must be absolute and canonical")
    binary = actual / "bin/lean"
    if digest(binary.read_bytes()) != EXPECTED_BINARY:
        raise ValueError("selected Lean binary differs from accepted audit")
    imports = json.loads(IMPORTS.read_text())
    if len(imports) != 1303:
        raise ValueError("accepted import inventory changed")
    out = HERE / args.output_name
    out.mkdir(exist_ok=False)
    inputs = out / "inputs"
    inputs.mkdir()
    for source in (Path(__file__), VERIFIER):
        shutil.copyfile(source, inputs / source.name)
    with tempfile.TemporaryDirectory(prefix="mat008-relocated-", dir=HERE.parents[3]) as temp:
        relocated = Path(temp) / "other-home-lean"
        (relocated / "bin").mkdir(parents=True)
        os.link(binary, relocated / "bin/lean")
        for module in imports:
            relative = Path("lib/lean") / (module.replace(".", "/") + ".olean")
            target = relocated / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            os.link(actual / relative, target)
        results = [capture(
            out, "relocated_valid", relocated, 0,
            "AUDIT_ACCEPTED_FOR_DECLARED_PARTIAL_SCOPE",
        )]
        imported = relocated / "lib/lean/Init.olean"
        imported.unlink()
        imported.write_bytes(b"deliberately altered imported module\n")
        results.append(capture(
            out, "relocated_changed_import", relocated, 1,
            "local toolchain import digest mismatch: Init",
        ))
        installed_binary = relocated / "bin/lean"
        installed_binary.unlink()
        installed_binary.write_bytes(b"Lean (version 4.19.0, altered binary)\n")
        results.append(capture(
            out, "relocated_changed_binary", relocated, 1,
            "local Lean executable digest mismatch",
        ))
    report = {
        "status": "PASS" if all(row["status"] == "PASS" for row in results) else "FAIL",
        "scope": "Relocated accepted-toolchain binding and local-byte mutation detection only",
        "accepted_audit_sha256": digest((HERE / "attempt-001/AUDIT.json").read_bytes()),
        "import_manifest_sha256": digest(IMPORTS.read_bytes()),
        "selected_lean_binary_sha256": digest(binary.read_bytes()),
        "verifier_sha256": digest((inputs / "verify.py").read_bytes()),
        "runner_sha256": digest((inputs / "portability_negative.py").read_bytes()),
        "results": results,
        "REFINEMENT_PROVED": "OPEN",
    }
    save_json(out / "result.json", report)
    print(json.dumps({"status": report["status"], "cases": len(results)}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
