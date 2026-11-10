#!/usr/bin/env python3
"""Independent MAT009 audit runner; all generated files stay under audit/."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
AUDIT = Path(__file__).resolve().parent
PROOF = ROOT / "formal/sonification/mat009/lean"
OUT = AUDIT / "independent-replay-001"
LEAN = Path("/home/trent/.elan/toolchains/leanprover--lean4---v4.19.0/bin/lean")
PROOF_COMMIT = "a09aab6572fb9c3875d5f2940bdb17ec55c358d5"
SOURCE_COMMIT = "0758a96360726aafbb07abed34620eda178407ae"
MODULES = ("SplitModel", "DiagnosticFirstOwner", "TypedConsumer", "ExactTypes", "LeanAudit")
ALLOWED = {"propext", "Quot.sound", "Classical.choice"}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_show(commit: str, relative: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{relative}"], cwd=ROOT)


def run(label: str, argv: list[str], cwd: Path, env: dict[str, str]) -> dict:
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, timeout=180)
    (OUT / f"{label}.stdout").write_bytes(result.stdout)
    (OUT / f"{label}.stderr").write_bytes(result.stderr)
    return {
        "label": label,
        "argv": argv,
        "cwd": str(cwd),
        "exit_code": result.returncode,
        "stdout_sha256": sha(result.stdout),
        "stderr_sha256": sha(result.stderr),
    }


def main() -> int:
    OUT.mkdir(exist_ok=False)
    work = OUT / "work"
    work.mkdir()
    source_inputs = {}
    for relative, commit in (
        ("materials/mat_spec_009.py", SOURCE_COMMIT),
        ("materials/mat_spec_008.py", SOURCE_COMMIT),
    ):
        raw = (ROOT / relative).read_bytes()
        if raw != git_show(commit, relative):
            raise AssertionError(f"frozen source drift: {relative}")
        source_inputs[relative] = sha(raw)
    proof_inputs = {}
    for module in MODULES:
        relative = f"formal/sonification/mat009/lean/{module}.lean"
        raw = (ROOT / relative).read_bytes()
        if raw != git_show(PROOF_COMMIT, relative):
            raise AssertionError(f"proof input drift: {relative}")
        (work / f"{module}.lean").write_bytes(raw)
        proof_inputs[relative] = sha(raw)
    env = {**os.environ, "LEAN_PATH": str(work), "TMPDIR": str(work)}
    commands = [run("lean-version", [str(LEAN), "--version"], work, env)]
    for number, module in enumerate(MODULES):
        commands.append(
            run(
                f"build-{number:02d}-{module}",
                [
                    str(LEAN),
                    "--error=warning",
                    "-o",
                    str(work / f"{module}.olean"),
                    f"{module}.lean",
                ],
                work,
                env,
            )
        )
    if any(command["exit_code"] != 0 for command in commands):
        raise AssertionError("fresh Lean build failed")

    lines = (OUT / "build-04-LeanAudit.stdout").read_text().splitlines()
    modules = {
        line.removeprefix("MAT009_MODULE ") for line in lines if line.startswith("MAT009_MODULE ")
    }
    declarations = [
        json.loads(line.removeprefix("MAT009_DECL "))
        for line in lines
        if line.startswith("MAT009_DECL ")
    ]
    if modules != set(MODULES) or len(declarations) != 351:
        raise AssertionError("fresh module or declaration inventory differs")
    if len({row["declaration"] for row in declarations}) != len(declarations):
        raise AssertionError("duplicate declaration")
    logical_violations = [
        row["declaration"]
        for row in declarations
        if row["kind"] != "compiler_auxiliary"
        and (row["is_axiom"] or row["unsafe_definition"] or set(row["axioms"]) - ALLOWED)
    ]
    if logical_violations:
        raise AssertionError(f"logical violations: {logical_violations}")

    named_theorems = (
        "MAT009.M009_R1_initial",
        "MAT009.M009_R2_assignment_overwrite",
        "MAT009.M009_R3_cross_role_trigger",
        "MAT009.M009_R4_stickiness",
        "MAT009.M009_R5_final_set_intersection",
        "MAT009.M009_R5_parent_union",
        "MAT009.M009_R6_cross_trigger_in_finite_scan",
        "MAT009.M009_R6_arbitrary_finite_scan",
        "MAT009.M009_R6_latest_owner",
        "MAT009.M009_R6_parent_reason_survives",
        "MAT009.M009_R6_final_leakage_iff",
        "MAT009.M009_R7_accepted_example",
        "MAT009.M009_R7_rejected_example",
        "MAT009.M009_R7_nonvacuous",
        "MAT009.Consumer.parent_reason_blocks_any_scan",
        "MAT009.Consumer.shared_campaign_blocks_any_scan",
        "MAT009.Diagnostic.register_first_owner",
        "MAT009.Diagnostic.register_new_owner",
        "MAT009.Diagnostic.register_other_identity",
        "MAT009.Diagnostic.register_preserves_existing",
        "MAT009.Diagnostic.scan_first_owner_sticky",
        "MAT009.Diagnostic.first_owner_not_last_writer",
    )
    (work / "IndependentAxioms.lean").write_text(
        "import ExactTypes\n" + "\n".join(f"#print axioms {name}" for name in named_theorems) + "\n"
    )
    commands.append(
        run(
            "independent-axioms",
            [str(LEAN), "--error=warning", "IndependentAxioms.lean"],
            work,
            env,
        )
    )
    if commands[-1]["exit_code"] != 0:
        raise AssertionError("independent theorem axiom query failed")
    text = (OUT / "independent-axioms.stdout").read_text()
    printed = {}
    pattern = re.compile(
        r"^'([^']+)' (?:depends on axioms: \[([^]]*)\]|does not depend on any axioms)$"
    )
    for line in text.splitlines():
        match = pattern.match(line)
        if match:
            printed[match[1]] = sorted(
                set(map(str.strip, match[2].split(","))) if match[2] else set()
            )
    if set(printed) != set(named_theorems) or any(set(xs) - ALLOWED for xs in printed.values()):
        raise AssertionError("independent theorem axiom result differs")
    (OUT / "independent-axioms.json").write_text(
        json.dumps(printed, indent=2, sort_keys=True) + "\n"
    )

    auxiliary_axioms = [
        row for row in declarations if row["kind"] == "compiler_auxiliary" and row["is_axiom"]
    ]
    report = {
        "status": "PASS",
        "source_commit": SOURCE_COMMIT,
        "proof_commit": PROOF_COMMIT,
        "source_sha256": source_inputs,
        "proof_sha256": proof_inputs,
        "lean_executable_sha256": sha(LEAN.read_bytes()),
        "commands": commands,
        "module_count": len(modules),
        "declaration_count": len(declarations),
        "theorem_count_including_generated": sum(row["kind"] == "theorem" for row in declarations),
        "compiler_auxiliary_count": sum(
            row["kind"] == "compiler_auxiliary" for row in declarations
        ),
        "compiler_auxiliary_axioms": [row["declaration"] for row in auxiliary_axioms],
        "logical_violations": logical_violations,
        "independently_queried_named_theorems": len(printed),
        "allowed_logical_axioms": sorted(ALLOWED),
        "cpython_refinement": "OPEN",
    }
    (OUT / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {"status": "PASS", "declarations": len(declarations), "named_theorems": len(printed)},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
