#!/usr/bin/env python3
"""Retain isolated MAT010 Phase A proof and trust-gate mutations."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from check import HERE, LEAN_SHA256, MODULES, sha, source_inventory, verify_baseline


def replace_once(source: str, before: str, after: str) -> str:
    if source.count(before) != 1:
        raise ValueError(f"non-unique mutation anchor: {before[:60]!r}")
    return source.replace(before, after, 1)


def variants() -> dict[str, tuple[str, str, str, str]]:
    model = (HERE / "ArchiveModel.lean").read_text()
    weak_start = model.index("theorem M010_A4_unique_logical_paths")
    weak_end = model.index("\nprivate theorem", weak_start)
    weakened = (
        model[:weak_start] +
        "theorem M010_A4_unique_logical_paths {claims : List Claim}\n"
        "    {snapshots : List Snapshot} {out : List Artifact}\n"
        "    (_h : validate claims snapshots = some out) : True := by trivial\n" +
        model[weak_end:]
    )

    def add_axiom(name: str) -> str:
        return replace_once(
            model, "\nend MAT010.Archive\n",
            f"\naxiom {name} : False\n"
            f"theorem {name}_proof : False := {name}\n\n"
            "end MAT010.Archive\n",
        )

    return {
        "weaken_named_theorem": (
            "ArchiveModel", weakened, "ArchiveConsumer",
            "M010_A4_unique_logical_paths",
        ),
        "prohibited_project_axiom": (
            "ArchiveModel", add_axiom("fabricated_physical_admission"),
            "LeanAudit", "project axiom declaration",
        ),
        "compiler_suffix_false_axiom_cstage1": (
            "ArchiveModel", add_axiom("audit_false_cstage1"),
            "LeanAudit", "project axiom declaration MAT010.Archive.audit_false_cstage1",
        ),
        "compiler_suffix_false_axiom_cstage2": (
            "ArchiveModel", add_axiom("audit_false_cstage2"),
            "LeanAudit", "project axiom declaration MAT010.Archive.audit_false_cstage2",
        ),
        "prohibited_sorry": (
            "ArchiveModel",
            replace_once(model, "\nend MAT010.Archive\n",
                         "\ndef hidden_unproved : Nat := by sorry\n\n"
                         "end MAT010.Archive\n"),
            "LeanAudit", "unapproved transitive axiom sorryAx",
        ),
    }


def run_build_case(out: Path, name: str, variant: tuple, lean: Path) -> dict:
    target, mutant, expected_module, expected_text = variant
    case = out / name
    case.mkdir()
    (case / "mutant-source.lean.txt").write_text(mutant)
    commands = []
    with tempfile.TemporaryDirectory(prefix=f"mat010-negative-{name}-") as temp:
        work = Path(temp)
        for module in MODULES:
            original = (HERE / f"{module}.lean").read_text()
            (work / f"{module}.lean").write_text(
                mutant if module == target else original
            )
        (work / "lean-toolchain").write_bytes((HERE / "lean-toolchain").read_bytes())
        env = {**os.environ, "LEAN_PATH": str(work)}
        for index, module in enumerate(MODULES):
            argv = [str(lean), "--error=warning", "-o",
                    str(work / f"{module}.olean"), f"{module}.lean"]
            timed_out = False
            try:
                run = subprocess.run(argv, cwd=work, env=env,
                                     capture_output=True, timeout=180)
                code, stdout, stderr = run.returncode, run.stdout, run.stderr
            except subprocess.TimeoutExpired as exc:
                timed_out = True
                code, stdout, stderr = None, exc.stdout or b"", exc.stderr or b""
            label = f"build-{index:02d}-{module}"
            (case / f"{label}.stdout").write_bytes(stdout)
            (case / f"{label}.stderr").write_bytes(stderr)
            commands.append({
                "argv": argv, "cwd": str(work), "exit_code": code,
                "timed_out": timed_out, "stdout_sha256": sha(stdout),
                "stderr_sha256": sha(stderr),
            })
            if code != 0 or timed_out:
                diagnostic = (stdout + stderr).decode("utf-8", errors="replace")
                detected = (module == expected_module and not timed_out and
                            expected_text in diagnostic)
                break
        else:
            module, detected = "NONE", False
    result = {
        "mutation": name, "target_module": target,
        "mutant_sha256": sha(mutant.encode()),
        "expected_failure_module": expected_module,
        "observed_failure_module": module,
        "expected_diagnostic_text": expected_text,
        "detected": detected, "commands": commands,
    }
    (case / "result.json").write_text(json.dumps(result, indent=2,
                                                  sort_keys=True) + "\n")
    return result


def run_unimported_case(out: Path) -> dict:
    name = "unimported_failing_module"
    case = out / name
    case.mkdir()
    bad = "theorem hidden_false : False := by trivial\n"
    (case / "Hidden.lean").write_text(bad)
    with tempfile.TemporaryDirectory(prefix="mat010-negative-unimported-") as temp:
        work = Path(temp)
        for module in MODULES:
            (work / f"{module}.lean").write_bytes(
                (HERE / f"{module}.lean").read_bytes()
            )
        (work / "Hidden.lean").write_text(bad)
        try:
            source_inventory(work)
        except ValueError as exc:
            diagnostic = str(exc)
        else:
            diagnostic = "accepted unimported module"
    detected = "unexpected Lean module inventory" in diagnostic
    (case / "inventory-diagnostic.txt").write_text(diagnostic + "\n")
    result = {
        "mutation": name, "mutant_sha256": sha(bad.encode()),
        "expected_failure_module": "source_inventory",
        "observed_failure_module": "source_inventory" if detected else "NONE",
        "expected_diagnostic_text": "unexpected Lean module inventory",
        "detected": detected, "commands": [],
    }
    (case / "result.json").write_text(json.dumps(result, indent=2,
                                                  sort_keys=True) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean", required=True, type=Path)
    parser.add_argument("--baseline-commit", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {"status": "INCOMPLETE", "proof_input_commit": args.baseline_commit}
    try:
        report["proof_input_sha256"] = verify_baseline(args.baseline_commit)
        lean = args.lean.resolve(strict=True)
        if sha(lean.read_bytes()) != LEAN_SHA256:
            raise ValueError("negative controls require pinned Lean executable")
        cases = [run_build_case(out, name, variant, lean)
                 for name, variant in variants().items()]
        cases.append(run_unimported_case(out))
        report.update({
            "status": "PASS" if all(row["detected"] for row in cases) else "FAIL",
            "negative_runner_sha256": sha(Path(__file__).read_bytes()),
            "lean_executable_sha256": sha(lean.read_bytes()),
            "cases": [{key: row[key] for key in (
                "mutation", "detected", "expected_failure_module",
                "observed_failure_module", "mutant_sha256"
            )} for row in cases],
            "REFINEMENT_PROVED": "OPEN",
        })
    except (OSError, ValueError, subprocess.SubprocessError, UnicodeError,
            KeyError, TypeError) as exc:
        report["status"] = "FAIL"
        report["error"] = str(exc)
    (out / "result.json").write_text(json.dumps(report, indent=2,
                                                 sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"], "detected": sum(
            row["detected"] for row in report.get("cases", [])
        ), "total": len(report.get("cases", [])), "out": str(out),
        "error": report.get("error"),
    }, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
