#!/usr/bin/env python3
"""Fresh-build the explicitly enumerated mathematical model and audit its trust.

This runner reports observed execution. It does not accept project claims or
establish Python implementation refinement. A baseline commit binds input hashes
to a separately reviewable Git object; omitting it is a development run.
"""

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
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODULES = ["Mat008.RunOwnership", "Mat008", "Audit"]
PROOF_FILES = [m.replace(".", "/") + ".lean" for m in MODULES]
INPUT_FILES = [
    *PROOF_FILES,
    "lean-toolchain",
    "lakefile.toml",
    "check.py",
    "expected-declarations.json",
    "negative.py",
    "theorem-statements.json",
]
THEOREMS = [
    "Sonification.Mat008.step_clear_before",
    "Sonification.Mat008.step_clear_same_owner",
    "Sonification.Mat008.step_covers",
    "Sonification.Mat008.scan_append",
    "Sonification.Mat008.scanFrom_append",
    "Sonification.Mat008.snoc_induction",
    "Sonification.Mat008.scan_clear_covers",
    "Sonification.Mat008.reused_run_blocks",
    "Sonification.Mat008.step_conflict_sticky",
    "Sonification.Mat008.nonvacuity",
]


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path, help="new directory; never overwritten")
    parser.add_argument("--baseline-commit", help="Git commit containing these exact proof inputs")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {
        "status": "INCOMPLETE",
        "started_utc": datetime.now(UTC).isoformat(),
        "assurance": "MATHEMATICAL_MODEL_ONLY",
        "python_refinement": "OPEN",
        "baseline_commit": args.baseline_commit,
        "commands": [],
    }
    try:
        actual = sorted(
            str(p.relative_to(HERE))
            for p in HERE.rglob("*.lean")
            if not ({"attempts", ".lake"} & set(p.relative_to(HERE).parts))
        )
        if actual != sorted(PROOF_FILES):
            raise ValueError(f"module coverage mismatch: {actual!r}")
        report["input_sha256"] = {p: digest((HERE / p).read_bytes()) for p in INPUT_FILES}
        if args.baseline_commit:
            if not re.fullmatch(r"[0-9a-f]{40}", args.baseline_commit):
                raise ValueError("baseline must be a full commit SHA")
            for p in INPUT_FILES:
                raw = subprocess.check_output(
                    [
                        "git",
                        "-C",
                        str(HERE),
                        "show",
                        f"{args.baseline_commit}:formal/sonification/mat008/lean/{p}",
                    ]
                )
                if digest(raw) != report["input_sha256"][p]:
                    raise ValueError(f"baseline input mismatch: {p}")
        expected = json.loads((HERE / "expected-declarations.json").read_text())
        lean = args.lean.resolve(strict=True)
        report["lean_executable"] = {"path": str(lean), "sha256": digest(lean.read_bytes())}
        version = subprocess.run([str(lean), "--version"], capture_output=True)
        (out / "version.stdout").write_bytes(version.stdout)
        (out / "version.stderr").write_bytes(version.stderr)
        report["version_exit_code"] = version.returncode
        report["version"] = version.stdout.decode().strip()
        if (
            version.returncode
            or report["version"]
            != "Lean (version 4.19.0, x86_64-unknown-linux-gnu, commit 6caaee842e94, Release)"
        ):
            raise ValueError("effective Lean version mismatch")
        if (HERE / "lean-toolchain").read_text() != "leanprover/lean4:v4.19.0\n":
            raise ValueError("effective toolchain configuration mismatch")
        with tempfile.TemporaryDirectory(prefix="sonification-lean-") as temp:
            build = Path(temp)
            for p in PROOF_FILES:
                (build / p).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(HERE / p, build / p)
            for i, module in enumerate(MODULES):
                p = module.replace(".", "/") + ".lean"
                argv = [str(lean), "-o", p.replace(".lean", ".olean"), p]
                timed_out = False
                try:
                    result = subprocess.run(
                        argv,
                        cwd=build,
                        env={**os.environ, "LEAN_PATH": str(build)},
                        capture_output=True,
                        timeout=180,
                    )
                except subprocess.TimeoutExpired as exc:
                    timed_out = True
                    result = subprocess.CompletedProcess(
                        argv, None, exc.stdout or b"", exc.stderr or b""
                    )
                stdout_path, stderr_path = f"{i:02d}.stdout", f"{i:02d}.stderr"
                (out / stdout_path).write_bytes(result.stdout)
                (out / stderr_path).write_bytes(result.stderr)
                report["commands"].append(
                    {
                        "argv": argv,
                        "working_directory": str(build),
                        "environment": {"LEAN_PATH": str(build)},
                        "exit_code": result.returncode,
                        "timed_out": timed_out,
                        "timeout_seconds": 180,
                        "stdout_path": stdout_path,
                        "stdout_sha256": digest(result.stdout),
                        "stderr_path": stderr_path,
                        "stderr_sha256": digest(result.stderr),
                    }
                )
                if timed_out:
                    raise ValueError(f"Lean timed out on {module}; original partial logs retained")
                if result.returncode:
                    raise ValueError(f"Lean rejected {module}; see original logs")
            audit_output = result.stdout.decode()
        declarations = [
            json.loads(line.removeprefix("SONIFICATION_DECL "))
            for line in audit_output.splitlines()
            if line.startswith("SONIFICATION_DECL ")
        ]
        if len(declarations) != len({d["declaration"] for d in declarations}):
            raise ValueError("duplicate observed declaration")
        observed = sorted(d["declaration"] for d in declarations)
        if observed != expected:
            raise ValueError("exact declaration inventory mismatch")
        imported = {
            line.removeprefix("SONIFICATION_MODULE ")
            for line in audit_output.splitlines()
            if line.startswith("SONIFICATION_MODULE ")
        }
        if imported != set(MODULES):
            raise ValueError("imported module coverage mismatch")
        named = sorted(d["declaration"] for d in declarations if d["declaration"] in THEOREMS)
        if named != sorted(THEOREMS):
            raise ValueError("named theorem inventory mismatch")
        imports = sorted(
            {
                line.removeprefix("SONIFICATION_IMPORT ")
                for line in audit_output.splitlines()
                if line.startswith("SONIFICATION_IMPORT ")
            }
        )
        closure = {}
        for module in imports:
            if module in MODULES:
                continue
            path = lean.parent.parent / "lib/lean" / (module.replace(".", "/") + ".olean")
            closure[module] = {"path": str(path), "sha256": digest(path.read_bytes())}
        (out / "toolchain-imports.json").write_text(
            json.dumps(closure, indent=2, sort_keys=True) + "\n"
        )
        (out / "declarations.json").write_text(
            json.dumps(declarations, indent=2, sort_keys=True) + "\n"
        )
        report.update(
            status="PASS",
            expected_theorems=sorted(THEOREMS),
            observed_theorems=named,
            declaration_count=len(declarations),
            imported_modules=sorted(imported),
            trust=(
                "Kernel and pinned Lean distribution, source-sensitive audit runner, OS execution; "
                "logical axioms disclosed per declaration. Compiler-only unsafe auxiliaries "
                "Compiler axioms are forbidden."
            ),
        )
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        report.update(status="FAIL", error=str(exc))
    (out / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "out": str(out), "error": report.get("error")}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
