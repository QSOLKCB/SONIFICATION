#!/usr/bin/env python3
"""Negative controls for abstract state correspondence, never CPython proofs."""

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
SOURCE = "Refine/MapReason.lean"
FILES = [
    SOURCE,
    "Refine.lean",
    "Audit.lean",
    "lean-toolchain",
    "lakefile.toml",
    "check.py",
    "negative.py",
    "expected-declarations.json",
    "expected-theorems.json",
    "theorem-statements.json",
]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def weaken(model: str, name: str, following: str) -> str:
    start = model.index("theorem " + name)
    end = model.index("theorem " + following, start)
    return model[:start] + f"theorem {name} : True := by trivial\n\n" + model[end:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument(
        "--accepted-model", type=Path, default=HERE.parents[1] / "lean/Mat008/RunOwnership.lean"
    )
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    original = (HERE / SOURCE).read_text()
    operations = """[GateInstruction.testExistingOwner, GateInstruction.insertReasonIfMismatch,
    GateInstruction.overwriteOwner]"""
    reordered = """[GateInstruction.overwriteOwner, GateInstruction.testExistingOwner,
    GateInstruction.insertReasonIfMismatch]"""
    mutations = {
        "update_before_test": original.replace(operations, reordered),
        "reason_erasure": original.replace(
            "if foundMismatch then insert s.reasons reuseReason else s.reasons",
            "if foundMismatch then insert s.reasons reuseReason else (fun _ => false)",
        ),
        "weaker_r4_theorem": weaken(original, "r4_reason_iff", "new_reason_iff_mismatch"),
        "weaker_r7_theorem": weaken(
            original, "r7_collision_reason", "preexisting_reason_counterexample"
        ),
        "prohibited_data_assumption": original.replace(
            "end Sonification.Mat008.AbstractPy",
            "noncomputable def prohibitedData : Nat := by sorry\n\n"
            "end Sonification.Mat008.AbstractPy",
        ),
        "unimported_module": original,
        "changed_accepted_model": original,
    }
    results = []
    for name, mutant in mutations.items():
        case = out / name
        case.mkdir()
        with tempfile.TemporaryDirectory(prefix="mat008-refine-mutant-") as temp:
            temp_root = Path(temp)
            work = temp_root / "project"
            work.mkdir()
            for filename in FILES:
                target = work / filename
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(HERE / filename, target)
            (work / SOURCE).write_text(mutant)
            (case / "MapReason.lean").write_text(mutant)
            dependency = temp_root / "accepted-model.lean"
            dependency.write_bytes(args.accepted_model.read_bytes())
            if name == "changed_accepted_model":
                dependency.write_bytes(dependency.read_bytes() + b"\n-- mutated dependency\n")
            if name == "unimported_module":
                (work / "Unimported.lean").write_text("theorem missing : False := by trivial\n")
            argv = [
                sys.executable,
                str(work / "check.py"),
                "--lean",
                str(args.lean.resolve()),
                "--accepted-model",
                str(dependency),
                "--out",
                str(case / "verification"),
            ]
            result = subprocess.run(argv, capture_output=True, timeout=180)
            (case / "runner.stdout").write_bytes(result.stdout)
            (case / "runner.stderr").write_bytes(result.stderr)
            verification = json.loads((case / "verification/result.json").read_text())
            expected_errors = {
                "update_before_test": (2, "Lean rejected Refine.MapReason"),
                "reason_erasure": (2, "Lean rejected Refine.MapReason"),
                "weaker_r4_theorem": (4, "Lean rejected Audit"),
                "weaker_r7_theorem": (4, "Lean rejected Audit"),
                "prohibited_data_assumption": (4, "Lean rejected Audit"),
                "unimported_module": (0, "module coverage mismatch"),
                "changed_accepted_model": (0, "accepted mathematical dependency source mismatch"),
            }
            count, expected = expected_errors[name]
            logs = "".join(p.read_text() for p in (case / "verification").glob("*.stdout"))
            detected = (
                result.returncode == 1
                and verification.get("error", "").startswith(expected)
                and len(verification["commands"]) == count
            )
            if name == "prohibited_data_assumption":
                detected = detected and "unapproved transitive axiom sorryAx" in logs
            if name == "weaker_r4_theorem":
                detected = detected and "r4_reason_iff" in logs
            if name == "weaker_r7_theorem":
                detected = detected and "r7_collision_reason" in logs
            row = {
                "mutation": name,
                "argv": argv,
                "exit_code": result.returncode,
                "source_sha256": sha(mutant.encode()),
                "expected_error": expected,
                "observed_error": verification.get("error"),
                "detected": detected,
            }
            if name == "reason_erasure":
                witness = (
                    mutant[: mutant.index("theorem instruction_program_correspondence")]
                    + """
 theorem erasure_counterexample :
     let s : PyState := ⟨fun _ => none, fun _ => true⟩
     (pyStep s ⟨"C", "R"⟩).reasons reuseReason = false := by rfl
 end Sonification.Mat008.AbstractPy
"""
                )
                (case / "Counterexample.lean").write_text(witness)
                counter = temp_root / "counterexample"
                (counter / "Mat008").mkdir(parents=True)
                (counter / "Mat008/RunOwnership.lean").write_bytes(args.accepted_model.read_bytes())
                (counter / "Counterexample.lean").write_text(witness)
                commands = []
                for filename in ["Mat008/RunOwnership.lean", "Counterexample.lean"]:
                    cmd = [
                        str(args.lean.resolve()),
                        "-o",
                        filename.replace(".lean", ".olean"),
                        filename,
                    ]
                    run = subprocess.run(
                        cmd,
                        cwd=counter,
                        env={**os.environ, "LEAN_PATH": str(counter)},
                        capture_output=True,
                        timeout=180,
                    )
                    i = len(commands)
                    (case / f"counterexample-{i}.stdout").write_bytes(run.stdout)
                    (case / f"counterexample-{i}.stderr").write_bytes(run.stderr)
                    commands.append(
                        {
                            "argv": cmd,
                            "working_directory": str(counter),
                            "exit_code": run.returncode,
                        }
                    )
                    if run.returncode:
                        break
                row["counterexample"] = {
                    "commands": commands,
                    "source_sha256": sha(witness.encode()),
                    "statement": "Mutant removes a preexisting reason on a collision-free row.",
                }
                row["detected"] = (
                    row["detected"]
                    and len(commands) == 2
                    and all(c["exit_code"] == 0 for c in commands)
                )
            results.append(row)
    status = "PASS" if all(r["detected"] for r in results) else "FAIL"
    (out / "result.json").write_text(
        json.dumps(
            {
                "status": status,
                "scope": "Abstract state correspondence only; CPython refinement OPEN.",
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
