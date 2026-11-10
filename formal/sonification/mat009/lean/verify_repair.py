#!/usr/bin/env python3
"""Bind the retained suffix-axiom bypass and its repaired negative controls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE / "recovery/001-original-bypass"
CORRECTED = HERE / "recovery/005-negative-controls"
ORIGINAL_MANIFEST_SHA256 = "783d4d69de3fdfa810899143a3a2bf03f13e3bd3aa3eda935356763e404d8350"
CORRECTED_MANIFEST_SHA256 = "1e1efa7eb0d4aedc1e43f096cc2610a6bd2d733a69a1e0f35d91e78a86eae191"
MUTANT_SHA256 = "1b2e633163118f65974db85be1416ea44af7126d303f5864d5d1f993dc547b71"
OLD_SCANNER_SHA256 = "7aeabffbd65357e4ea41d773950bc7b52c892c5347b259f51d6a3831296aced8"
NEW_RUNNER_SHA256 = "9ee63fda2cd0a6e045c85a99ce28e20ea6f2d6d800e38ed5088ce9432acfeb48"
PROOF_COMMIT = "c562377308ebbb4694685076af12e79eefe0a479"
RUNNER_COMMIT = "e1091de3bce9502ad333c530c1d7b12eb143f6da"
CASES = {
    "drop_cross_conflict_stickiness",
    "drop_historical_campaign_membership",
    "weaken_final_leakage_theorem",
    "change_diagnostic_first_owner_update",
    "prohibited_project_axiom",
    "prohibited_sorry",
    "compiler_suffix_false_axiom",
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def manifest_files(base: Path, name: str, digest: str) -> dict[str, str]:
    require(base.is_dir() and not base.is_symlink(), f"missing evidence directory: {base}")
    path = base / name
    require(path.is_file() and not path.is_symlink() and sha(path.read_bytes()) == digest,
            f"changed evidence manifest: {base}")
    files = json.loads(path.read_text())["files_sha256"]
    observed = {str(p.relative_to(base)) for p in base.rglob("*") if p.is_file()}
    require(observed == set(files) | {name}, f"evidence file inventory changed: {base}")
    for relative, expected in files.items():
        member = Path(relative)
        require(not member.is_absolute() and ".." not in member.parts,
                f"invalid evidence path: {relative}")
        source = base / member
        require(source.is_file() and not source.is_symlink() and
                sha(source.read_bytes()) == expected,
                f"altered evidence file: {relative}")
    return files


def verify(original: Path = ORIGINAL, corrected: Path = CORRECTED) -> dict:
    manifest_files(original, "manifest.json", ORIGINAL_MANIFEST_SHA256)
    result = json.loads((original / "result.json").read_text())
    require(result["bypass_reproduced"] is True and
            result["retained_mutant_sha256"] == MUTANT_SHA256 and
            result["original_scanner_sha256"] == OLD_SCANNER_SHA256 and
            sha((original / "work/LeanAudit.lean").read_bytes()) == OLD_SCANNER_SHA256 and
            len(result["jobs"]) == 5 and
            all(job["exit_code"] == 0 for job in result["jobs"]),
            "original vulnerable gate did not accept the retained mutant")
    false_rows = result["false_declarations"]
    require({row["declaration"] for row in false_rows} == {
        "MAT009.auditor_false_cstage1", "MAT009.auditor_false_proof_cstage1"
    } and all(row["kind"] == "compiler_auxiliary" and row["type"] == "False"
              for row in false_rows), "original False declarations changed")

    manifest_files(corrected, "EVIDENCE_MANIFEST.json", CORRECTED_MANIFEST_SHA256)
    report = json.loads((corrected / "result.json").read_text())
    require(report["status"] == "PASS" and
            report["proof_input_commit"] == PROOF_COMMIT and
            report["negative_runner_commit"] == RUNNER_COMMIT and
            report["negative_runner_sha256"] == NEW_RUNNER_SHA256 and
            sha((HERE / "negative.py").read_bytes()) == NEW_RUNNER_SHA256 and
            report["REFINEMENT_PROVED"] == "OPEN" and
            {case["mutation"] for case in report["cases"]} == CASES and
            all(case["detected"] for case in report["cases"]),
            "repaired negative control set changed")
    for case in report["cases"]:
        name = case["mutation"]
        folder = corrected / name
        detail = json.loads((folder / "result.json").read_text())
        require(detail["detected"] is True and detail["mutation"] == name and
                detail["observed_failure_module"] ==
                detail["expected_failure_module"] == case["observed_failure_module"] and
                sha((folder / "mutant-source.lean.txt").read_bytes()) ==
                detail["mutant_sha256"], f"negative control changed: {name}")
        for index, job in enumerate(detail["commands"]):
            module = job["argv"][-1].removesuffix(".lean")
            label = f"build-{index:02d}-{module}"
            require(job["timed_out"] is False and
                    (job["exit_code"] == 0 if index + 1 < len(detail["commands"])
                     else job["exit_code"] != 0),
                    f"negative control exit changed: {name}/{label}")
            for stream in ("stdout", "stderr"):
                require(sha((folder / f"{label}.{stream}").read_bytes()) ==
                        job[f"{stream}_sha256"],
                        f"negative control log changed: {name}/{label}")
    suffix = json.loads((corrected / "compiler_suffix_false_axiom/result.json").read_text())
    log = (corrected / "compiler_suffix_false_axiom/build-04-LeanAudit.stdout").read_text()
    require(suffix["mutant_sha256"] == MUTANT_SHA256 and
            suffix["observed_failure_module"] == "LeanAudit" and
            suffix["expected_diagnostic_text"] in log and
            len(suffix["commands"]) == 5,
            "retained suffix-axiom bypass was not rejected by repaired gate")
    return {"status": "MAT009_SUFFIX_AXIOM_REPAIR_BOUND", "detected": len(CASES),
            "vulnerable_gate_accepted": True, "corrected_gate_rejected": True,
            "REFINEMENT_PROVED": "OPEN"}


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
