#!/usr/bin/env python3
"""Bind retained MAT010 source and finite execution files to committed inputs.

This verifies archive integrity. It does not replay CPython or prove refinement.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RECEIPTS = HERE / "receipts"
INPUT_COMMIT = "1d07f94d03cd871c6d2a17c870f367b3e4d5a4a1"
MANIFESTS = {
    "source-001": "5c492e731aa53565ee59b6501831d34654689959f70963b916402ef935623ea6",
    "finite-001": "8dc1d00f4a1bfb9a88d60415cf42fb33dcc0242addc279c7b0f5a9075dbb066d",
}
COUNTEREXAMPLES = {
    "subclass_duplicate_commit_text",
    "subclass_hidden_evidence_iteration",
    "subclass_mid_suffix_override",
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify(base: Path = RECEIPTS) -> dict:
    subprocess.run(["git", "merge-base", "--is-ancestor", INPUT_COMMIT, "HEAD"],
                   cwd=ROOT, check=True, capture_output=True, timeout=30)
    reports = {}
    for name, expected_manifest_sha in MANIFESTS.items():
        folder = base / name
        require(folder.is_dir() and not folder.is_symlink(),
                f"missing ordinary receipt directory: {name}")
        manifest_file = folder / "EVIDENCE_MANIFEST.json"
        require(manifest_file.is_file() and not manifest_file.is_symlink() and
                sha(manifest_file.read_bytes()) == expected_manifest_sha,
                f"changed evidence manifest: {name}")
        manifest = json.loads(manifest_file.read_text())
        require(manifest["schema"] == "sonification-mat010-execution-files/v1" and
                manifest["label"] == name and
                manifest["input_commit"] == INPUT_COMMIT,
                f"changed receipt identity: {name}")
        files = manifest["files_sha256"]
        observed = {str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file()}
        require(observed == set(files) | {manifest_file.name},
                f"receipt file inventory changed: {name}")
        for relative, digest in files.items():
            path = Path(relative)
            require(not path.is_absolute() and ".." not in path.parts,
                    f"invalid receipt member: {relative}")
            member = folder / path
            require(member.is_file() and not member.is_symlink() and
                    sha(member.read_bytes()) == digest,
                    f"altered receipt file: {name}/{relative}")
        receipt = json.loads((folder / "receipt.json").read_text())
        require(receipt["schema"] == "sonification-mat010-execution-receipt/v1" and
                receipt["label"] == name and
                receipt["input_commit"] == INPUT_COMMIT and
                receipt["exit_code"] == 0 and
                receipt["REFINEMENT_PROVED"] == "OPEN" and
                receipt["cwd"].endswith("sonification-formal-001-mat010-closure"),
                f"execution receipt changed: {name}")
        for stream in ("stdout", "stderr"):
            require(sha((folder / f"{stream}.log").read_bytes()) ==
                    receipt[f"{stream}_sha256"],
                    f"altered execution stream: {name}/{stream}")
        require(receipt["frozen_source_sha256"] ==
                "e062474d4435e769f8c6c8407bc44ad89cfb2dfa04677b820c3a035d604a9056",
                f"frozen source identity changed: {name}")
        for relative, digest in receipt["inputs_sha256"].items():
            path = ROOT / relative
            require(path.is_file() and not path.is_symlink() and
                    sha(path.read_bytes()) == digest,
                    f"stale verification input: {relative}")
            historical = subprocess.check_output(
                ["git", "show", f"{INPUT_COMMIT}:{relative}"], cwd=ROOT,
                timeout=30,
            )
            require(sha(historical) == digest,
                    f"input commit mismatch: {relative}")
        reports[name] = receipt
    source = json.loads((base / "source-001/stdout.log").read_text())
    require(source["status"] == "SOURCE_SYNTAX_MATCH" and
            source["REFINEMENT_PROVED"] == "OPEN" and
            source["functions"] == 5,
            "source binder result changed")
    finite = json.loads((base / "finite-001/result/result.json").read_text())
    summary = json.loads((base / "finite-001/stdout.log").read_text())
    require(finite["status"] == summary["status"] ==
            "PASS_WITH_BOUNDARY_COUNTEREXAMPLES" and
            finite["case_count"] == summary["case_count"] == 28 and
            finite["exact_builtin_passed"] == summary["exact_builtin_passed"] == 23 and
            set(finite["boundary_counterexamples"]) ==
            set(summary["boundary_counterexamples"]) == COUNTEREXAMPLES and
            finite["REFINEMENT_PROVED"] == "OPEN",
            "finite conformance result changed")
    require(len(reports) == 2, "receipt coverage changed")
    return {
        "status": "MAT010_SOURCE_FINITE_RECEIPTS_BOUND",
        "receipt_count": len(reports), "finite_cases": finite["case_count"],
        "boundary_counterexamples": sorted(COUNTEREXAMPLES),
        "REFINEMENT_PROVED": "OPEN",
    }


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
