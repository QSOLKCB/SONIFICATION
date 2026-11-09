#!/usr/bin/env python3
"""Run auditable mathematical-model mutations; never modify production inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = "Mat008/RunOwnership.lean"
FILES = [
    SOURCE,
    "Mat008.lean",
    "Audit.lean",
    "lean-toolchain",
    "lakefile.toml",
    "check.py",
    "expected-declarations.json",
    "negative.py",
    "theorem-statements.json",
]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    model = (HERE / SOURCE).read_text()
    weak_start = model.index("theorem reused_run_blocks")
    weak_end = model.index("theorem step_conflict_sticky")
    mutations = {
        "drop_sticky_conflict": model.replace(
            "s.conflict || differentOwner s row", "differentOwner s row"
        ),
        "weaker_same_name_theorem": (
            model[:weak_start]
            + "theorem reused_run_blocks : True := by trivial\n\n"
            + model[weak_end:]
        ),
        "prohibited_data_assumption": model.replace(
            "end Sonification.Mat008",
            "def prohibitedHelper : Nat := by sorry\n\nend Sonification.Mat008",
        ),
        "unimported_module": model,
    }
    results = []
    for name, mutant in mutations.items():
        case = out / name
        case.mkdir()
        with tempfile.TemporaryDirectory(prefix="mat008-mutant-") as temp:
            work = Path(temp)
            for path in FILES:
                (work / path).parent.mkdir(exist_ok=True, parents=True)
                shutil.copyfile(HERE / path, work / path)
            (work / SOURCE).write_text(mutant)
            (case / "RunOwnership.lean").write_text(mutant)
            if name == "unimported_module":
                (work / "Unimported.lean").write_text("theorem unimported : False := by trivial\n")
            argv = [
                sys.executable,
                str(work / "check.py"),
                "--lean",
                str(args.lean.resolve()),
                "--out",
                str(case / "verification"),
            ]
            result = subprocess.run(argv, capture_output=True, timeout=180)
            (case / "runner.stdout").write_bytes(result.stdout)
            (case / "runner.stderr").write_bytes(result.stderr)
            verification = json.loads((case / "verification/result.json").read_text())
            expected_errors = {
                "drop_sticky_conflict": "Lean rejected Mat008.RunOwnership",
                "weaker_same_name_theorem": "Lean rejected Audit",
                "prohibited_data_assumption": "Lean rejected Audit",
                "unimported_module": "module coverage mismatch",
            }
            expected_error = expected_errors[name]
            error_matches = verification.get("error", "").startswith(expected_error)
            logs = "".join(p.read_text() for p in (case / "verification").glob("*.stdout"))
            if name == "prohibited_data_assumption":
                error_matches = error_matches and "unapproved transitive axiom sorryAx" in logs
            if name == "weaker_same_name_theorem":
                error_matches = error_matches and "reused_run_blocks" in logs
            row = {
                "mutation": name,
                "argv": argv,
                "exit_code": result.returncode,
                "source_sha256": sha(mutant.encode()),
                "expected": expected_error,
                "observed_error": verification.get("error"),
                "detected": result.returncode != 0 and error_matches,
            }
            if name == "drop_sticky_conflict":
                # Kernel-check the changed model's actual counterexample result.
                witness = (
                    mutant[: mutant.index("theorem step_clear_before")]
                    + """
 theorem sticky_defect_counterexample :
     (scan [⟨"A", "RUN"⟩, ⟨"B", "RUN"⟩, ⟨"B", "OTHER"⟩]).conflict = false := by
   decide
 end Sonification.Mat008
"""
                )
                (work / "Counterexample.lean").write_text(witness)
                (case / "Counterexample.lean").write_text(witness)
                argv2 = [str(args.lean.resolve()), "Counterexample.lean"]
                r2 = subprocess.run(
                    argv2,
                    cwd=work,
                    capture_output=True,
                    env={**os.environ, "LEAN_PATH": str(work)},
                    timeout=180,
                )
                (case / "counterexample.stdout").write_bytes(r2.stdout)
                (case / "counterexample.stderr").write_bytes(r2.stderr)
                row["counterexample"] = {
                    "argv": argv2,
                    "exit_code": r2.returncode,
                    "statement": "Mutant clears A/B collision after an independent row.",
                    "source_sha256": sha(witness.encode()),
                }
                row["detected"] = row["detected"] and r2.returncode == 0
            results.append(row)
    status = "PASS" if all(row["detected"] for row in results) else "FAIL"
    (out / "result.json").write_text(
        json.dumps(
            {
                "status": status,
                "scope": "Negative controls for mathematical model only; no Python refinement.",
                "results": results,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                "status": status,
                "detected": sum(r["detected"] for r in results),
                "total": len(results),
            }
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
