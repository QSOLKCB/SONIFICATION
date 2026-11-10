#!/usr/bin/env python3
"""Fresh-build and audit the source-pinned MAT009 mathematical modules.

The receipt is about Lean model statements. It does not prove CPython source
refinement, physical source independence, or empirical classifier accuracy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MODULES = (
    "SplitModel", "DiagnosticFirstOwner", "TypedConsumer", "ExactTypes",
    "LeanAudit",
)
INPUTS = (*(f"{module}.lean" for module in MODULES),
    "PROOF_NOTES.md", "lean-toolchain", "check.py",
)
NAMED_THEOREMS = {
    *(f"MAT009.{name}" for name in (
        "M009_R1_initial", "M009_R2_assignment_overwrite",
        "M009_R3_cross_role_trigger", "M009_R4_stickiness",
        "M009_R5_final_set_intersection", "M009_R5_parent_union",
        "M009_R6_cross_trigger_in_finite_scan",
        "M009_R6_arbitrary_finite_scan", "M009_R6_latest_owner",
        "M009_R6_parent_reason_survives", "M009_R6_final_leakage_iff",
        "M009_R7_accepted_example", "M009_R7_rejected_example",
        "M009_R7_nonvacuous",
    )),
    "MAT009.Consumer.parent_reason_blocks_any_scan",
    "MAT009.Consumer.shared_campaign_blocks_any_scan",
    "MAT009.Diagnostic.register_first_owner",
    "MAT009.Diagnostic.register_new_owner",
    "MAT009.Diagnostic.register_other_identity",
    "MAT009.Diagnostic.register_preserves_existing",
    "MAT009.Diagnostic.scan_first_owner_sticky",
    "MAT009.Diagnostic.first_owner_not_last_writer",
}
PRINTED_AXIOMS = {
    *(f"MAT009.{name}" for name in (
        "M009_R1_initial", "M009_R2_assignment_overwrite",
        "M009_R3_cross_role_trigger", "M009_R4_stickiness",
        "M009_R5_final_set_intersection", "M009_R5_parent_union",
        "M009_R6_cross_trigger_in_finite_scan",
        "M009_R6_arbitrary_finite_scan", "M009_R6_latest_owner",
        "M009_R6_parent_reason_survives", "M009_R6_final_leakage_iff",
        "M009_R7_accepted_example", "M009_R7_rejected_example",
        "M009_R7_nonvacuous",
    )),
    "MAT009.Consumer.parent_reason_blocks_any_scan",
    "MAT009.Consumer.shared_campaign_blocks_any_scan",
    "MAT009.Diagnostic.scan_first_owner_sticky",
    "MAT009.Diagnostic.first_owner_not_last_writer",
}
ALLOWED_LOGICAL_AXIOMS = {"propext", "Quot.sound", "Classical.choice"}
VERSION = "Lean (version 4.19.0, x86_64-unknown-linux-gnu, commit 6caaee842e94, Release)"
PROHIBITED = re.compile(r"\b(?:sorry|admit|axiom|opaque|unsafe|partial)\b")
AXIOM_LINE = re.compile(
    r"^'([^']+)' (?:depends on axioms: \[([^]]*)\]|does not depend on any axioms)$"
)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def record_command(
    out: Path, label: str, argv: list[str], *, cwd: Path, env: dict[str, str],
    timeout: int = 180,
) -> tuple[int | None, bytes, bytes, bool]:
    timed_out = False
    try:
        run = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, timeout=timeout)
        code, stdout, stderr = run.returncode, run.stdout, run.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        code, stdout, stderr = None, exc.stdout or b"", exc.stderr or b""
    (out / f"{label}.stdout").write_bytes(stdout)
    (out / f"{label}.stderr").write_bytes(stderr)
    (out / f"{label}.json").write_text(json.dumps({
        "argv": argv,
        "cwd": str(cwd),
        "exit_code": code,
        "timed_out": timed_out,
        "timeout_seconds": timeout,
        "stdout_sha256": sha(stdout),
        "stderr_sha256": sha(stderr),
    }, indent=2, sort_keys=True) + "\n")
    return code, stdout, stderr, timed_out


def verify_baseline(commit: str) -> dict[str, str]:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("proof baseline must be a full Git commit SHA")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=ROOT, check=True, capture_output=True,
    )
    observed = {}
    for name in INPUTS:
        current = HERE / name
        if current.is_symlink() or not current.is_file():
            raise ValueError(f"missing ordinary proof input: {name}")
        raw = current.read_bytes()
        historical = subprocess.check_output(
            ["git", "show", f"{commit}:formal/sonification/mat009/lean/{name}"],
            cwd=ROOT,
        )
        if raw != historical:
            raise ValueError(f"stale proof input: {name}")
        observed[name] = sha(raw)
    actual_modules = {
        str(p.relative_to(HERE)) for p in HERE.rglob("*.lean")
        if ".lake" not in p.parts
    }
    if actual_modules != {f"{module}.lean" for module in MODULES}:
        raise ValueError(f"Lean source module coverage changed: {sorted(actual_modules)}")
    for module in MODULES[:-1]:
        if PROHIBITED.search((HERE / f"{module}.lean").read_text()):
            raise ValueError(f"prohibited proof shortcut in {module}")
    if (HERE / "lean-toolchain").read_text() != "leanprover/lean4:v4.19.0\n":
        raise ValueError("Lean toolchain declaration changed")
    return observed


def audit_output(raw: bytes, lean: Path, out: Path) -> dict:
    lines = raw.decode("utf-8").splitlines()
    modules = {line.removeprefix("MAT009_MODULE ") for line in lines
               if line.startswith("MAT009_MODULE ")}
    if modules != set(MODULES):
        raise ValueError(f"imported proof module coverage mismatch: {sorted(modules)}")
    summary = [line for line in lines if line.startswith("MAT009_AUDIT ")]
    if summary != ["MAT009_AUDIT declarations=351 theorems=95"]:
        raise ValueError("complete declaration/theorem inventory changed")
    declarations = [json.loads(line.removeprefix("MAT009_DECL ")) for line in lines
                    if line.startswith("MAT009_DECL ")]
    names = [row["declaration"] for row in declarations]
    if len(names) != 351 or len(set(names)) != 351:
        raise ValueError("duplicate or missing proof declaration")
    if sum(row["kind"] == "theorem" for row in declarations) != 95:
        raise ValueError("theorem declaration inventory changed")
    named = {row["declaration"] for row in declarations
             if row["kind"] == "theorem" and row["declaration"] in NAMED_THEOREMS}
    if named != NAMED_THEOREMS:
        raise ValueError(f"named intended theorem missing: {sorted(NAMED_THEOREMS - named)}")
    for row in declarations:
        if row["origin"] not in MODULES:
            raise ValueError(f"unexpected proof declaration origin: {row['origin']}")
        if row["kind"] != "compiler_auxiliary":
            if row["is_axiom"] or row["unsafe_definition"]:
                raise ValueError(f"logical declaration contains trusted code: {row['declaration']}")
            if not set(row["axioms"]) <= ALLOWED_LOGICAL_AXIOMS:
                raise ValueError(f"unapproved logical axiom: {row['declaration']}")
    (out / "declarations.json").write_text(
        json.dumps(declarations, indent=2, sort_keys=True) + "\n"
    )
    imports = {line.removeprefix("MAT009_IMPORT ") for line in lines
               if line.startswith("MAT009_IMPORT ")}
    if not {"SplitModel", "DiagnosticFirstOwner", "TypedConsumer", "ExactTypes"} <= imports:
        raise ValueError("project import dependency missing")
    toolchain_root = lean.parent.parent
    external = {}
    for module in sorted(imports - set(MODULES)):
        relative = Path("lib/lean") / (module.replace(".", "/") + ".olean")
        path = toolchain_root / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"missing toolchain import: {relative}")
        external[module] = {"relative_path": str(relative), "sha256": sha(path.read_bytes())}
    (out / "toolchain-imports.json").write_text(
        json.dumps(external, indent=2, sort_keys=True) + "\n"
    )
    types = {row["declaration"]: row["type"] for row in declarations
             if row["declaration"] in NAMED_THEOREMS}
    (out / "theorem-types.json").write_text(
        json.dumps(types, indent=2, sort_keys=True) + "\n"
    )
    return {
        "declaration_count": len(declarations),
        "theorem_declaration_count_including_generated": 95,
        "named_intended_theorems": sorted(named),
        "external_import_count": len(external),
        "logical_axioms": sorted(ALLOWED_LOGICAL_AXIOMS),
        "compiler_auxiliary_count": sum(row["kind"] == "compiler_auxiliary"
                                        for row in declarations),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean", required=True, type=Path)
    parser.add_argument("--baseline-commit", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {
        "status": "INCOMPLETE",
        "baseline_commit": args.baseline_commit,
        "started_utc": datetime.now(UTC).isoformat(),
        "MODEL_PROVED": "NOT_EXECUTED",
        "REFINEMENT_PROVED": "OPEN",
        "DIFFERENTIAL_TESTED": "NOT_EXECUTED",
        "AUDIT_ACCEPTED": "OPEN",
    }
    try:
        report["input_sha256"] = verify_baseline(args.baseline_commit)
        lean = args.lean.resolve(strict=True)
        report["lean_executable_sha256"] = sha(lean.read_bytes())
        code, stdout, _, timeout = record_command(
            out, "lean-version", [str(lean), "--version"], cwd=ROOT,
            env=os.environ.copy(), timeout=30,
        )
        if timeout or code != 0 or stdout.decode().strip() != VERSION:
            raise ValueError("pinned Lean version mismatch")
        report["lean_version"] = VERSION
        with tempfile.TemporaryDirectory(prefix="mat009-lean-build-") as temp:
            build = Path(temp)
            env = {**os.environ, "LEAN_PATH": str(build)}
            for number, module in enumerate(MODULES):
                argv = [
                    str(lean), "--error=warning", "-o",
                    str(build / f"{module}.olean"), str(HERE / f"{module}.lean"),
                ]
                code, stdout, _, timeout = record_command(
                    out, f"build-{number:02d}-{module}", argv, cwd=ROOT, env=env
                )
                if timeout or code != 0:
                    raise ValueError(f"Lean rejected or timed out on {module}")
                if module == "TypedConsumer":
                    found = {}
                    for line in stdout.decode().splitlines():
                        match = AXIOM_LINE.match(line)
                        if match:
                            found[match[1]] = (
                                set(a.strip() for a in match[2].split(","))
                                if match[2] else set()
                            )
                    if set(found) != PRINTED_AXIOMS:
                        raise ValueError("typed consumer axiom report coverage changed")
                    if any(not value <= ALLOWED_LOGICAL_AXIOMS for value in found.values()):
                        raise ValueError("typed consumer depends on unapproved axioms")
                    (out / "named-axioms.json").write_text(
                        json.dumps({key: sorted(value) for key, value in found.items()},
                                   indent=2, sort_keys=True) + "\n"
                    )
                if module == "LeanAudit":
                    report.update(audit_output(stdout, lean, out))
        report["status"] = "PASS"
        report["MODEL_PROVED"] = "PASS_FOR_SCOPED_MATHEMATICAL_MODEL"
    except (OSError, ValueError, subprocess.SubprocessError, UnicodeError) as exc:
        report["status"] = "FAIL"
        report["error"] = str(exc)
    report["completed_utc"] = datetime.now(UTC).isoformat()
    (out / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"], "out": str(out), "error": report.get("error"),
        "named_theorems": len(report.get("named_intended_theorems", [])),
    }, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
