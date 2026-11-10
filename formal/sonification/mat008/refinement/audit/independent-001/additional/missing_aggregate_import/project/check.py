#!/usr/bin/env python3
"""Fresh-build the explicitly enumerated mathematical model and audit its trust.

This runner reports observed execution. It does not accept project claims or
establish CPython or frozen-source implementation refinement. A baseline commit binds input hashes
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
DEPENDENCY_FILE = "Mat008/RunOwnership.lean"
DEPENDENCY_COMMIT = "ac1408cf0c459d79c3d0552287812a15ce644f0d"
DEPENDENCY_SHA256 = "653f4638568e4e461176cca7659360737f3ac2632152163602c789fd65ead201"
LEAN_SHA256 = "92c3d35b5bfaa5e0fea413a775d504cf46cd95e1345df61c2274f76779e7e023"
MODULES = ["Mat008.RunOwnership", "Refine.MapReason", "Refine", "Audit"]
PROOF_FILES = [m.replace(".", "/") + ".lean" for m in MODULES]
OWN_PROOF_FILES = [p for p in PROOF_FILES if p != DEPENDENCY_FILE]
INPUT_FILES = [
    *OWN_PROOF_FILES,
    "lean-toolchain",
    "lakefile.toml",
    "check.py",
    "expected-declarations.json",
    "expected-theorems.json",
    "theorem-statements.json",
    "negative.py",
]
THEOREMS = json.loads((HERE / "expected-theorems.json").read_text())


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path, help="new directory; never overwritten")
    parser.add_argument(
        "--accepted-model", type=Path, default=HERE.parents[1] / "lean/Mat008/RunOwnership.lean"
    )
    parser.add_argument("--baseline-commit", help="Git commit containing these exact proof inputs")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {
        "status": "INCOMPLETE",
        "started_utc": datetime.now(UTC).isoformat(),
        "assurance": "ABSTRACT_STATE_CORRESPONDENCE_ONLY",
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
        if actual != sorted(OWN_PROOF_FILES):
            raise ValueError(f"module coverage mismatch: {actual!r}")
        if not THEOREMS or len(THEOREMS) != len(set(THEOREMS)):
            raise ValueError("empty or duplicate intended theorem inventory")
        dependency = args.accepted_model.read_bytes()
        if digest(dependency) != DEPENDENCY_SHA256:
            raise ValueError("accepted mathematical dependency source mismatch")
        report["accepted_mathematical_dependency"] = {
            "source_commit": DEPENDENCY_COMMIT,
            "path": str(args.accepted_model.resolve()),
            "sha256": digest(dependency),
            "module": "Mat008.RunOwnership",
        }
        report["REFINEMENT_PROVED"] = "OPEN"
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
                        f"{args.baseline_commit}:formal/sonification/mat008/refinement/lean/{p}",
                    ]
                )
                if digest(raw) != report["input_sha256"][p]:
                    raise ValueError(f"baseline input mismatch: {p}")
        expected = json.loads((HERE / "expected-declarations.json").read_text())
        lean = args.lean.resolve(strict=True)
        report["lean_executable"] = {"path": str(lean), "sha256": digest(lean.read_bytes())}
        if report["lean_executable"]["sha256"] != LEAN_SHA256:
            raise ValueError("effective Lean executable digest mismatch")
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
                if p == DEPENDENCY_FILE:
                    (build / p).write_bytes(dependency)
                else:
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
            json.loads(line.removeprefix("MAT008_REFINE_DECL "))
            for line in audit_output.splitlines()
            if line.startswith("MAT008_REFINE_DECL ")
        ]
        if len(declarations) != len({d["declaration"] for d in declarations}):
            raise ValueError("duplicate observed declaration")
        observed = sorted(d["declaration"] for d in declarations)
        if observed != expected:
            raise ValueError("exact declaration inventory mismatch")
        imported = {
            line.removeprefix("MAT008_REFINE_MODULE ")
            for line in audit_output.splitlines()
            if line.startswith("MAT008_REFINE_MODULE ")
        }
        if imported != set(MODULES):
            raise ValueError("imported module coverage mismatch")
        named = sorted(d["declaration"] for d in declarations if d["declaration"] in THEOREMS)
        if named != sorted(THEOREMS):
            raise ValueError("named theorem inventory mismatch")
        statements = json.loads((HERE / "theorem-statements.json").read_text())
        if sorted(d["declaration"] for d in statements) != sorted(THEOREMS):
            raise ValueError("exact intended statement inventory mismatch")
        observed_rows = {d["declaration"]: d for d in declarations}
        if any(observed_rows[d["declaration"]] != d for d in statements):
            raise ValueError("exact observed theorem statement or axiom mismatch")
        imports = sorted(
            {
                line.removeprefix("MAT008_REFINE_IMPORT ")
                for line in audit_output.splitlines()
                if line.startswith("MAT008_REFINE_IMPORT ")
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
                "logical axioms disclosed per declaration; compiler axioms are forbidden."
            ),
        )
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        report.update(status="FAIL", error=str(exc))
    (out / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "out": str(out), "error": report.get("error")}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
