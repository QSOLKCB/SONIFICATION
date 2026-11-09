"""Bind the retained finite-conformance receipt to current test inputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECEIPT = HERE / "receipts" / "conformance-002"
EXPECTED_INPUTS = frozenset({"conformance.py", "capture.py"})
EXPECTED_SOURCE = {
    "source_commit": "b4247877dd471e2e9d4986c86bdc1f11b14e43f8",
    "source_tree": "eb19f2e06a502442f621a73be1e5696c2fa25a65",
    "tag_object": "a02088e3c68addb41c9c7145694c0f566e84f87f",
    "module_sha256": "e56563235d87da43293bc46661b077660538b476d2bb340a1d208cc59aaa5f08",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify() -> dict:
    execution = json.loads((RECEIPT / "execution.json").read_text())
    result = json.loads((RECEIPT / "result" / "receipt.json").read_text())
    if execution["exit_code"] != 0 or result["status"] != "FINITE_CONFORMANCE_PASS":
        raise ValueError("finite-conformance execution did not pass")
    if result["REFINEMENT_PROVED"] != "OPEN" or result["AUDIT_ACCEPTED"] != "OPEN":
        raise ValueError("finite receipt overstates formal assurance")
    if result["exhaustive_generated_cases"] != 1296:
        raise ValueError("finite case inventory changed")
    if frozenset(execution["input_sha256"]) != EXPECTED_INPUTS:
        raise ValueError("finite-conformance input inventory changed")
    if any(result[key] != expected for key, expected in EXPECTED_SOURCE.items()):
        raise ValueError("frozen source binding changed")
    if not result["source_mutation_detected"] or not result["output_mutation_detected"]:
        raise ValueError("finite negative controls did not detect defects")
    for name, expected in execution["input_sha256"].items():
        if digest(HERE / name) != expected:
            raise ValueError(f"stale finite-conformance input: {name}")
    for stream in ("stdout", "stderr"):
        if digest(RECEIPT / (stream + ".log")) != execution[stream + "_sha256"]:
            raise ValueError(f"altered {stream} log")
    if digest(RECEIPT / "result" / "receipt.json") != execution["receipt_sha256"]:
        raise ValueError("altered finite-conformance result")
    return {"status": "FINITE_RECEIPT_BINDING_MATCH", "cases": 1296, "refinement": "OPEN"}


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
