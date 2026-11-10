#!/usr/bin/env python3
"""Bind all retained MAT009 Lean mutation attempts, including failures."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_ARCHIVE = HERE / "negative"
MANIFEST_SHA256 = "6d99b5c41017d87922ffd01f3b34eccab692806ca38b760299371cbcc0d0750b"
BASELINE = "a09aab6572fb9c3875d5f2940bdb17ec55c358d5"
RUNNER_COMMIT = "5620029fb724ac41827a0c41c4c677b9594464f3"
EXPECTED_CASES = {
    "drop_cross_conflict_stickiness",
    "drop_historical_campaign_membership",
    "weaken_final_leakage_theorem",
    "change_diagnostic_first_owner_update",
    "prohibited_project_axiom",
    "prohibited_sorry",
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify(archive: Path = DEFAULT_ARCHIVE) -> dict:
    path = archive / "ARCHIVE_MANIFEST.json"
    require(path.is_file() and not path.is_symlink(), "missing negative archive manifest")
    raw = path.read_bytes()
    require(sha(raw) == MANIFEST_SHA256, "negative archive manifest changed")
    manifest = json.loads(raw)
    require(manifest["schema"] == "sonification-mat009-lean-negative-archive-v1" and
            manifest["nominal_proof_input_commit"] == BASELINE and
            manifest["accepted_attempt"] == "003" and
            manifest["accepted_case_count"] == 6 and
            manifest["prior_failed_attempts"] == ["001", "002"],
            "negative archive identity changed")
    files = manifest["files_sha256"]
    observed = {str(p.relative_to(archive)) for p in archive.rglob("*") if p.is_file()}
    require(observed == set(files) | {"ARCHIVE_MANIFEST.json"},
            "negative archive file inventory changed")
    for name, digest in files.items():
        member = archive / name
        require(member.is_file() and not member.is_symlink() and
                sha(member.read_bytes()) == digest, f"altered negative evidence: {name}")

    prior1 = json.loads((archive / "001/result.json").read_text())
    prior2 = json.loads((archive / "002/result.json").read_text())
    require(prior1["status"] == "FAILED_DEVELOPMENT_ATTEMPT" and
            prior1["exit_code"] != 0, "first failed attempt was rewritten")
    require(prior2["status"] == "FAIL" and
            sum(case["detected"] for case in prior2["cases"]) == 4,
            "second failed attempt was rewritten")

    report = json.loads((archive / "003/result.json").read_text())
    require(report["status"] == "PASS" and
            report["proof_input_commit"] == BASELINE and
            report["negative_runner_commit"] == RUNNER_COMMIT and
            report["negative_runner_sha256"] == sha((HERE / "negative.py").read_bytes()) and
            report["REFINEMENT_PROVED"] == "OPEN",
            "accepted negative execution identity changed")
    require({row["mutation"] for row in report["cases"]} == EXPECTED_CASES and
            len(report["cases"]) == len(EXPECTED_CASES) and
            all(row["detected"] for row in report["cases"]),
            "negative control coverage or result changed")
    for summary in report["cases"]:
        case = archive / "003" / summary["mutation"]
        detail = json.loads((case / "result.json").read_text())
        require(detail["detected"] is True and
                detail["mutation"] == summary["mutation"] and
                detail["expected_failure_module"] ==
                detail["observed_failure_module"] == summary["observed_failure_module"],
                f"negative case did not detect intended failure: {summary['mutation']}")
        require(sha((case / "mutant-source.lean.txt").read_bytes()) ==
                detail["mutant_sha256"],
                f"mutated proof source changed: {summary['mutation']}")
        for index, job in enumerate(detail["commands"]):
            module = job["argv"][-1].removesuffix(".lean")
            label = f"build-{index:02d}-{module}"
            for stream in ("stdout", "stderr"):
                require(sha((case / f"{label}.{stream}").read_bytes()) ==
                        job[f"{stream}_sha256"],
                        f"negative command stream changed: {summary['mutation']}/{label}")
            require(job["timed_out"] is False and
                    (job["exit_code"] == 0 if index + 1 < len(detail["commands"])
                     else job["exit_code"] != 0),
                    f"negative command exit changed: {summary['mutation']}/{label}")
        module = detail["observed_failure_module"]
        label = f"build-{len(detail['commands']) - 1:02d}-{module}"
        output = ((case / f"{label}.stdout").read_text() +
                  (case / f"{label}.stderr").read_text())
        require(detail["expected_diagnostic_text"] in output,
                f"negative case failed for an unrelated reason: {summary['mutation']}")
    return {"status": "MAT009_NEGATIVE_EVIDENCE_BOUND", "detected": 6,
            "failed_development_attempts_retained": 2,
            "REFINEMENT_PROVED": "OPEN"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    args = parser.parse_args()
    print(json.dumps(verify(args.archive), sort_keys=True))
