#!/usr/bin/env python3
"""Independent isolated Lean mutations; never edit the candidate proof files."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PROOF = ROOT / "formal/sonification/mat009/lean"
OUT = Path(__file__).resolve().parent / "negative-probe-001"
LEAN = Path("/home/trent/.elan/toolchains/leanprover--lean4---v4.19.0/bin/lean")
MODULES = ("SplitModel", "DiagnosticFirstOwner", "TypedConsumer", "ExactTypes", "LeanAudit")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def mutate(name: str, source: str) -> str:
    if name == "weaken_final_leakage":
        start = source.index("theorem M009_R6_final_leakage_iff")
        end = source.index("\ndef noParent", start)
        return (
            source[:start]
            + "theorem M009_R6_final_leakage_iff : True := by trivial\n"
            + source[end:]
        )
    if name == "ordinary_false_axiom":
        return source.replace("\nend MAT009\n", "\naxiom auditor_false : False\n\nend MAT009\n")
    if name == "auxiliary_named_false_axiom":
        return source.replace(
            "\nend MAT009\n",
            "\naxiom auditor_false_cstage1 : False\n"
            "theorem auditor_false_proof_cstage1 : False := auditor_false_cstage1\n"
            "\nend MAT009\n",
        )
    raise AssertionError(name)


def run_case(name: str) -> dict:
    case = OUT / name
    case.mkdir()
    work = case / "work"
    work.mkdir()
    original = (PROOF / "SplitModel.lean").read_text()
    mutant = mutate(name, original)
    if mutant == original:
        raise AssertionError("empty mutation")
    for module in MODULES:
        raw = mutant if module == "SplitModel" else (PROOF / f"{module}.lean").read_text()
        (work / f"{module}.lean").write_text(raw)
    (case / "mutant-source.lean.txt").write_text(mutant)
    env = {**os.environ, "LEAN_PATH": str(work), "TMPDIR": str(work)}
    commands = []
    for number, module in enumerate(MODULES):
        argv = [str(LEAN), "--error=warning", "-o", str(work / f"{module}.olean"), f"{module}.lean"]
        result = subprocess.run(argv, cwd=work, env=env, capture_output=True, timeout=180)
        label = f"build-{number:02d}-{module}"
        (case / f"{label}.stdout").write_bytes(result.stdout)
        (case / f"{label}.stderr").write_bytes(result.stderr)
        commands.append(
            {
                "label": label,
                "argv": argv,
                "cwd": str(work),
                "exit_code": result.returncode,
                "stdout_sha256": sha(result.stdout),
                "stderr_sha256": sha(result.stderr),
            }
        )
        if result.returncode != 0:
            break
    observed = commands[-1]
    if name == "weaken_final_leakage":
        expected = observed["label"] == "build-02-TypedConsumer" and observed["exit_code"] != 0
    elif name == "ordinary_false_axiom":
        expected = observed["label"] == "build-04-LeanAudit" and observed["exit_code"] != 0
    else:
        expected = observed["label"] == "build-04-LeanAudit" and observed["exit_code"] == 0
    details = {}
    if name == "auxiliary_named_false_axiom" and expected:
        lines = (case / "build-04-LeanAudit.stdout").read_text().splitlines()
        rows = [
            json.loads(line.removeprefix("MAT009_DECL "))
            for line in lines
            if line.startswith("MAT009_DECL ")
        ]
        details["disguised_declarations"] = [
            row for row in rows if "auditor_false" in row["declaration"]
        ]
        expected = (
            expected
            and len(details["disguised_declarations"]) == 2
            and all(
                row["kind"] == "compiler_auxiliary" for row in details["disguised_declarations"]
            )
        )
        details["audit_summary"] = [line for line in lines if line.startswith("MAT009_AUDIT ")]
    report = {
        "mutation": name,
        "mutant_sha256": sha(mutant.encode()),
        "observed_last_job": observed["label"],
        "observed_exit_code": observed["exit_code"],
        "expected_observation": expected,
        "commands": commands,
        **details,
    }
    (case / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    OUT.mkdir(exist_ok=False)
    results = [
        run_case(name)
        for name in ("weaken_final_leakage", "ordinary_false_axiom", "auxiliary_named_false_axiom")
    ]
    report = {
        "status": "PASS" if all(x["expected_observation"] for x in results) else "FAIL",
        "source_candidate_unmodified": True,
        "lean_executable_sha256": sha(LEAN.read_bytes()),
        "results": [
            {
                key: x[key]
                for key in (
                    "mutation",
                    "mutant_sha256",
                    "observed_last_job",
                    "observed_exit_code",
                    "expected_observation",
                )
            }
            for x in results
        ],
    }
    (OUT / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
