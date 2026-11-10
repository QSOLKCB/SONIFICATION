#!/usr/bin/env python3
"""Run isolated MAT009 theorem and trust mutations, retaining original logs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASELINE = "a09aab6572fb9c3875d5f2940bdb17ec55c358d5"
MODULES = ("SplitModel", "DiagnosticFirstOwner", "TypedConsumer", "ExactTypes", "LeanAudit")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def replace_once(source: str, before: str, after: str) -> str:
    if source.count(before) != 1:
        raise ValueError(f"mutation anchor is not unique: {before[:60]!r}")
    return source.replace(before, after, 1)


def variants() -> dict[str, tuple[str, str, str, str]]:
    split = (HERE / "SplitModel.lean").read_text()
    diagnostic = (HERE / "DiagnosticFirstOwner.lean").read_text()
    weak_start = split.index("theorem M009_R6_final_leakage_iff")
    weak_end = split.index("\ndef noParent", weak_start)
    weak = (split[:weak_start] +
            "theorem M009_R6_final_leakage_iff : True := by trivial\n" +
            split[weak_end:])
    return {
        "drop_cross_conflict_stickiness": (
            "SplitModel",
            replace_once(split, "crossed := s.crossed \u2228\n    ∃ previous : Role,",
                         "crossed :=\n    ∃ previous : Role,"),
            "SplitModel", "unsolved goals",
        ),
        "drop_historical_campaign_membership": (
            "SplitModel",
            replace_once(split,
                         "campaigns := fun role key =>\n    s.campaigns role key \u2228 "
                         "(role = row.role ∧ key = row.campaign)",
                         "campaigns := fun role key =>\n    "
                         "(role = row.role ∧ key = row.campaign)"),
            "SplitModel", "unsolved goals",
        ),
        "weaken_final_leakage_theorem": (
            "SplitModel", weak, "TypedConsumer", "M009_R6_final_leakage_iff",
        ),
        "change_diagnostic_first_owner_update": (
            "DiagnosticFirstOwner",
            replace_once(diagnostic, "| some first => some first",
                         "| some first => some candidate"),
            "DiagnosticFirstOwner", "unsolved goals",
        ),
        "prohibited_project_axiom": (
            "SplitModel",
            replace_once(split, "\nend MAT009\n",
                         "\naxiom fabricated_physical_admission : False\n\nend MAT009\n"),
            "LeanAudit", "project axiom declaration",
        ),
        "prohibited_sorry": (
            "SplitModel",
            replace_once(split, "\nend MAT009\n",
                         "\ndef hidden_unproved : Nat := by sorry\n\nend MAT009\n"),
            "SplitModel", "sorry",
        ),
    }


def run_case(
    out: Path, name: str, mutation: tuple[str, str, str, str], lean: Path,
) -> dict:
    target, mutant, expected_module, expected_text = mutation
    case = out / name
    case.mkdir()
    (case / "mutant-source.lean.txt").write_text(mutant)
    commands = []
    with tempfile.TemporaryDirectory(prefix=f"mat009-{name}-") as temp:
        work = Path(temp)
        for module in MODULES:
            raw = (HERE / f"{module}.lean").read_text()
            (work / f"{module}.lean").write_text(mutant if module == target else raw)
        env = {**os.environ, "LEAN_PATH": str(work)}
        for index, module in enumerate(MODULES):
            argv = [str(lean), "--error=warning", "-o",
                    str(work / f"{module}.olean"), f"{module}.lean"]
            timed_out = False
            try:
                result = subprocess.run(argv, cwd=work, env=env,
                                        capture_output=True, timeout=180)
                code, stdout, stderr = result.returncode, result.stdout, result.stderr
            except subprocess.TimeoutExpired as exc:
                timed_out = True
                code, stdout, stderr = None, exc.stdout or b"", exc.stderr or b""
            label = f"build-{index:02d}-{module}"
            (case / f"{label}.stdout").write_bytes(stdout)
            (case / f"{label}.stderr").write_bytes(stderr)
            commands.append({
                "argv": argv, "exit_code": code, "timed_out": timed_out,
                "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr),
            })
            if code != 0 or timed_out:
                diagnostic = (stdout + stderr).decode("utf-8", errors="replace")
                detected = (module == expected_module and not timed_out and
                            expected_text in diagnostic)
                break
        else:
            module, diagnostic, detected = "NONE", "no failure", False
    row = {
        "mutation": name,
        "target_module": target,
        "mutant_sha256": sha(mutant.encode()),
        "expected_failure_module": expected_module,
        "observed_failure_module": module,
        "expected_diagnostic_text": expected_text,
        "detected": detected,
        "commands": commands,
    }
    (case / "result.json").write_text(json.dumps(row, indent=2, sort_keys=True) + "\n")
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    lean = args.lean.resolve(strict=True)
    nominal = json.loads((HERE / "attempts/002/result.json").read_text())
    if sha(lean.read_bytes()) != nominal["lean_executable_sha256"]:
        raise ValueError("negative controls require the nominal Lean executable")
    for module in MODULES:
        path = f"formal/sonification/mat009/lean/{module}.lean"
        historical = subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], cwd=ROOT)
        if historical != (HERE / f"{module}.lean").read_bytes():
            raise ValueError(f"proof source drift before mutation: {module}")
    results = [run_case(out, name, mutation, lean)
               for name, mutation in variants().items()]
    status = "PASS" if all(row["detected"] for row in results) else "FAIL"
    report = {
        "status": status,
        "proof_input_commit": BASELINE,
        "negative_runner_sha256": sha(Path(__file__).read_bytes()),
        "negative_runner_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "lean_executable_sha256": sha(lean.read_bytes()),
        "scope": "negative controls for mathematical proof and trust checker only",
        "REFINEMENT_PROVED": "OPEN",
        "cases": [{"mutation": row["mutation"], "detected": row["detected"],
                   "expected_failure_module": row["expected_failure_module"],
                   "observed_failure_module": row["observed_failure_module"]}
                  for row in results],
    }
    (out / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": status, "detected": sum(r["detected"] for r in results),
                      "total": len(results), "out": str(out)}, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
