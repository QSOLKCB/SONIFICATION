"""Finite, source-pinned MAT-SPEC-008 run-ownership checks.

This executes frozen function bodies and an independent pairwise oracle.  It
does not prove correspondence to CPython or the full packet validator.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import itertools
import json
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

TAG = "mat-spec-008-v0.1.0"
TAG_OBJECT = "a02088e3c68addb41c9c7145694c0f566e84f87f"
COMMIT = "b4247877dd471e2e9d4986c86bdc1f11b14e43f8"
TREE = "eb19f2e06a502442f621a73be1e5696c2fa25a65"
PATH = "materials/mat_spec_008.py"
MODULE_SHA256 = "e56563235d87da43293bc46661b077660538b476d2bb340a1d208cc59aaa5f08"
FUNCTIONS = ("_identity", "_decimal", "validate_future_measurement_packet")
REUSE_REASON = "REUSED_ORIGINAL_RUN_ACROSS_CAMPAIGNS"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        timeout=30,
    ).stdout


def frozen_source(root: Path) -> bytes:
    for ref, expected in (
        (f"refs/tags/{TAG}", TAG_OBJECT),
        (f"{TAG}^{{commit}}", COMMIT),
        (f"{TAG}^{{tree}}", TREE),
    ):
        actual = git(root, "rev-parse", ref).decode("ascii").strip()
        if actual != expected:
            raise ValueError(f"frozen Git identity mismatch: {ref}")
    raw = git(root, "show", f"{COMMIT}:{PATH}")
    if sha256(raw) != MODULE_SHA256:
        raise ValueError("frozen MAT-SPEC-008 source SHA-256 mismatch")
    return raw


def compile_frozen_slice(raw: bytes) -> tuple[Any, dict[str, str]]:
    if sha256(raw) != MODULE_SHA256:
        raise ValueError("frozen MAT-SPEC-008 source SHA-256 mismatch")
    module = ast.parse(raw.decode("utf-8"), filename=f"{COMMIT}:{PATH}")
    selected: list[ast.FunctionDef] = []
    for name in FUNCTIONS:
        matches = [
            node
            for node in module.body
            if isinstance(node, ast.FunctionDef) and node.name == name
        ]
        if len(matches) != 1 or matches[0].decorator_list:
            raise ValueError(f"expected one undecorated top-level {name} function")
        selected.append(matches[0])
    namespace: dict[str, Any] = {"re": re, "Fraction": Fraction}
    isolated = ast.Module(body=selected, type_ignores=[])
    code = compile(isolated, f"{COMMIT}:{PATH}", "exec", dont_inherit=True)
    exec(code, namespace)
    lines = raw.splitlines(keepends=True)
    spans = {
        node.name: sha256(b"".join(lines[node.lineno - 1 : node.end_lineno]))
        for node in selected
    }
    return namespace["validate_future_measurement_packet"], spans


def row(index: int, campaign: str, run: str) -> dict[str, Any]:
    """Construct exact built-in values in the finite-test input domain."""
    return {
        "campaign_id": campaign,
        "lab_family_id": "LAB_A" if campaign == "CAMP_A" else "LAB_B",
        "original_run_id": run,
        "source_document_id": f"DOC_{index}",
        "row_id": f"ROW_{index}",
        "phase": "HE_I" if index % 2 == 0 else "HE_II",
        "source_type": "ORIGINAL_EXPERIMENTAL_RECORD",
        "synthetic_fixture": False,
        "diagnostic_basis": "INDEPENDENT_NON_TEMPERATURE_DIAGNOSTIC",
        "measurement_value": "1",
        "measurement_sigma": "0.1",
        "diagnostic_sigma": "0.1",
        "source_sha256": chr(ord("a") + index) * 64,
        "pressure_condition": "HE4_SVP",
    }


def pairwise_reuse(records: list[dict[str, Any]]) -> bool:
    """Independent finite oracle: compare every unordered pair of parsed IDs."""
    return any(
        left["original_run_id"] == right["original_run_id"]
        and left["campaign_id"] != right["campaign_id"]
        for left, right in itertools.combinations(records, 2)
    )


def check_case(validate: Any, records: list[dict[str, Any]]) -> None:
    observed = validate(records)
    expected = pairwise_reuse(records)
    if (REUSE_REASON in observed["reasons"]) != expected:
        raise AssertionError("run-reuse reason disagrees with pairwise oracle")
    if expected and observed["status"] != "BLOCKED":
        raise AssertionError("reused run did not block structural eligibility")
    if observed["physical_evidence_admitted"] is not False:
        raise AssertionError("physical evidence was admitted")
    if observed["independence_authenticated"] is not False:
        raise AssertionError("independence was authenticated")


def two_campaign_fixture() -> list[dict[str, Any]]:
    """A structural pass with two campaigns and both phases in each."""
    baseline = [
        row(0, "CAMP_A", "RUN_A"),
        row(1, "CAMP_A", "RUN_A"),
        row(2, "CAMP_B", "RUN_B"),
        row(3, "CAMP_B", "RUN_B"),
    ]
    for pair in (baseline[:2], baseline[2:]):
        pair[1]["source_document_id"] = pair[0]["source_document_id"]
        pair[1]["source_sha256"] = pair[0]["source_sha256"]
    return baseline


def verify(root: Path) -> dict[str, Any]:
    raw = frozen_source(root)
    validate, spans = compile_frozen_slice(raw)
    baseline = two_campaign_fixture()
    check_case(validate, baseline)
    if validate(baseline)["status"] != "STRUCTURAL_ONLY_UNAUTHENTICATED":
        raise AssertionError("complete nonreused fixture was rejected")
    collision = [dict(item) for item in baseline]
    for item in collision[2:]:
        item["original_run_id"] = "RUN_A"
    check_case(validate, collision)

    cases = 0
    for campaigns in itertools.product(("CAMP_A", "CAMP_B"), repeat=4):
        for runs in itertools.product(("RUN_A", "RUN_B", "RUN_C"), repeat=4):
            records = [row(i, campaigns[i], runs[i]) for i in range(4)]
            check_case(validate, records)
            cases += 1

    def defective(records: list[dict[str, Any]]) -> dict[str, Any]:
        result = validate(records)
        result["reasons"] = [r for r in result["reasons"] if r != REUSE_REASON]
        return result

    mutation_detected = False
    try:
        check_case(defective, collision)
    except AssertionError:
        mutation_detected = True
    if not mutation_detected:
        raise AssertionError("negative output mutation escaped oracle")
    drift_detected = False
    try:
        compile_frozen_slice(raw + b"\n# altered frozen source\n")
    except ValueError:
        drift_detected = True
    if not drift_detected:
        raise AssertionError("source mutation escaped SHA-256 pin")

    empty = validate([])
    if empty["status"] != "BLOCKED" or "heldout_accuracy" in empty:
        raise AssertionError("empty-packet boundary changed")
    synthetic_numeric = [dict(item) for item in baseline]
    synthetic_numeric[0]["synthetic_fixture"] = 1
    numeric_result = validate(synthetic_numeric)
    if numeric_result["status"] != "STRUCTURAL_ONLY_UNAUTHENTICATED":
        raise AssertionError("exact-True synthetic flag boundary changed")
    if numeric_result["physical_evidence_admitted"] is not False:
        raise AssertionError("structural pass was promoted to physical evidence")

    return {
        "status": "FINITE_CONFORMANCE_PASS",
        "claim_scope": "exact built-in dict and str rows in generated finite cases",
        "MODEL_PROVED": "OPEN",
        "REFINEMENT_PROVED": "OPEN",
        "DIFFERENTIAL_TESTED": "PASS",
        "AUDIT_ACCEPTED": "OPEN",
        "tag": TAG,
        "tag_object": TAG_OBJECT,
        "source_commit": COMMIT,
        "source_tree": TREE,
        "module_sha256": MODULE_SHA256,
        "function_span_sha256": spans,
        "exhaustive_generated_cases": cases,
        "named_fixture_cases": 2,
        "source_mutation_detected": drift_detected,
        "output_mutation_detected": mutation_detected,
        "empty_report_omits_heldout_accuracy": True,
        "numeric_one_synthetic_flag_structurally_passes": True,
        "python": sys.version,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    receipt = verify(root)
    output = json.dumps(receipt, sort_keys=True, indent=2) + "\n"
    if args.out is not None:
        args.out.mkdir(parents=True, exist_ok=False)
        (args.out / "receipt.json").write_text(output, encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "cases": receipt["exhaustive_generated_cases"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
