#!/usr/bin/env python3
"""Assemble the independent MAT009 checkpoint audit from retained raw logs."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
AUDIT = Path(__file__).resolve().parent
OUT = AUDIT / "report.json"
LEAN = "/home/trent/.elan/toolchains/leanprover--lean4---v4.19.0/bin/lean"
PROOF_COMMIT = "a09aab6572fb9c3875d5f2940bdb17ec55c358d5"
SOURCE_COMMIT = "0758a96360726aafbb07abed34620eda178407ae"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def obj(relative: str) -> dict:
    return json.loads((AUDIT / relative).read_text())


def local_log(label: str, argv: list[str], exit_code: int, *, env: dict | None = None) -> dict:
    stdout = AUDIT / f"{label}.stdout"
    stderr = AUDIT / f"{label}.stderr"
    assert stdout.is_file() and stderr.is_file()
    return {
        "label": label,
        "argv": argv,
        "cwd": str(ROOT),
        "env_overrides": env or {},
        "exit_code": exit_code,
        "stdout": str(stdout.relative_to(ROOT)),
        "stderr": str(stderr.relative_to(ROOT)),
        "stdout_sha256": sha(stdout),
        "stderr_sha256": sha(stderr),
    }


def main() -> int:
    fresh = obj("independent-replay-001/result.json")
    checker = obj("checker-replay-001/result.json")
    negatives = obj("negative-probe-001/result.json")
    verification = obj("verification-probe-002/result.json")
    archived = obj("archive-integrity-001.json")
    finite = obj("independent-cpython-001.json")
    full_path = ROOT / "formal/sonification/evidence/mat009-full-pytest-001/receipt.json"
    full = json.loads(full_path.read_text())
    assert all(x["status"] == "PASS" for x in (fresh, checker, negatives, verification, archived))
    assert finite["status"] == "PASS_FOR_LISTED_CASES_ONLY"
    assert full["exit_code"] == 0

    negative_details = {}
    for row in negatives["results"]:
        name = row["mutation"]
        detail = obj(f"negative-probe-001/{name}/result.json")
        negative_details[name] = {
            "mutant_sha256": row["mutant_sha256"],
            "last_job": row["observed_last_job"],
            "exit_code": row["observed_exit_code"],
            "expected_observation": row["expected_observation"],
            "jobs": detail["commands"],
            "raw_log_directory": f"formal/sonification/mat009/audit/negative-probe-001/{name}",
        }
    disguised = obj("negative-probe-001/auxiliary_named_false_axiom/result.json")
    count_gate_error = (AUDIT / "count_gate.stderr").read_text()
    assert "complete declaration/theorem inventory changed" in count_gate_error

    nominal_commands = [
        local_log(
            "nominal-source-binding",
            ["python3", "-B", "formal/sonification/mat009/source/source_bind.py"],
            0,
            env={"PYTHONDONTWRITEBYTECODE": "1"},
        ),
        local_log(
            "nominal-source-receipts",
            ["python3", "-B", "formal/sonification/mat009/verify_evidence.py"],
            0,
            env={"PYTHONDONTWRITEBYTECODE": "1"},
        ),
        local_log(
            "nominal-lean-receipt",
            ["python3", "-B", "formal/sonification/mat009/lean/verify.py"],
            0,
            env={"PYTHONDONTWRITEBYTECODE": "1"},
        ),
        local_log(
            "nominal-negative-receipt",
            ["python3", "-B", "formal/sonification/mat009/lean/verify_negative.py"],
            0,
            env={"PYTHONDONTWRITEBYTECODE": "1"},
        ),
        local_log(
            "nominal-finite",
            [
                "python3",
                "-B",
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests",
                "-p",
                "test_sonification_formal_mat009_split.py",
                "-q",
            ],
            0,
            env={"PYTHONDONTWRITEBYTECODE": "1"},
        ),
    ]
    own_commands = [
        local_log(
            "checker-replay-001",
            [
                "python3",
                "-B",
                "formal/sonification/mat009/lean/check.py",
                "--lean",
                LEAN,
                "--baseline-commit",
                PROOF_COMMIT,
                "--out",
                "formal/sonification/mat009/audit/checker-replay-001",
            ],
            0,
            env={"PYTHONDONTWRITEBYTECODE": "1", "TMPDIR": str(AUDIT)},
        ),
        local_log(
            "independent_replay",
            ["python3", "-B", "formal/sonification/mat009/audit/independent_replay.py"],
            0,
            env={"PYTHONDONTWRITEBYTECODE": "1"},
        ),
        local_log(
            "negative_probe",
            ["python3", "-B", "formal/sonification/mat009/audit/negative_probe.py"],
            0,
            env={"PYTHONDONTWRITEBYTECODE": "1"},
        ),
        local_log(
            "verification_probe_002",
            ["python3", "-B", "formal/sonification/mat009/audit/verification_probe.py"],
            0,
            env={"PYTHONDONTWRITEBYTECODE": "1"},
        ),
        local_log(
            "independent_cpython",
            ["python3", "-B", "formal/sonification/mat009/audit/independent_cpython.py"],
            0,
            env={"PYTHONDONTWRITEBYTECODE": "1"},
        ),
        local_log(
            "archive_integrity",
            ["python3", "-B", "formal/sonification/mat009/audit/archive_integrity.py"],
            0,
            env={"PYTHONDONTWRITEBYTECODE": "1"},
        ),
        local_log(
            "count_gate",
            ["python3", "-B", "formal/sonification/mat009/audit/count_gate_driver.py"],
            1,
            env={"PYTHONDONTWRITEBYTECODE": "1"},
        ),
    ]
    report = {
        "schema": "sonification-mat009-independent-audit-v1",
        "target": "MAT-009-VERIFY-001",
        "candidate_commit": "94a357284408e6bc24cfb9b2d49e9d4144791042",
        "observed_head_after_additional_full_pytest_receipt": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_identity": {
            "tag": "mat-spec-009-v0.1.0",
            "tag_object": "ad99d9e52f9ede423a4fb9d6a622624e32955263",
            "commit": SOURCE_COMMIT,
            "tree": "a6a03e1227e666680d656b886201ee9dde9de32d",
            "mat009_blob": "c447f0ce76b91acf458221390ac4261166145a0b",
            "mat009_sha256": fresh["source_sha256"]["materials/mat_spec_009.py"],
            "direct_mat008_blob": "3117adbc3739c834f8203d5d2dd2b80d6caf862b",
            "direct_mat008_sha256": fresh["source_sha256"]["materials/mat_spec_008.py"],
        },
        "proof_identity": {
            "proof_input_commit": PROOF_COMMIT,
            "module_sha256": fresh["proof_sha256"],
            "all_proof_input_sha256": checker["input_sha256"],
            "lean_executable_sha256": fresh["lean_executable_sha256"],
            "toolchain_imports_verified": archived["toolchain_import_count"],
        },
        "verdicts": {
            "exact_model": "PASS",
            "finite": "PASS",
            "source_binding": "PASS",
            "cpython_refinement": "OPEN",
            "audit": "FAIL",
        },
        "model_scope": {
            "eligible_rows_only": True,
            "arbitrary_parent_reason_set": True,
            "arbitrary_finite_eligible_row_list": True,
            "exact_typed_consumer_compiled": True,
            "named_theorems_independently_queried": fresh["independently_queried_named_theorems"],
            "logical_violations_in_nominal_declarations": fresh["logical_violations"],
            "declarations": fresh["declaration_count"],
            "theorems_including_generated": fresh["theorem_count_including_generated"],
            "compiler_auxiliaries": fresh["compiler_auxiliary_count"],
            "compiler_generated_axioms_in_nominal_inventory": fresh["compiler_auxiliary_axioms"],
            "nonvacuity": "R7 supplies both structural and blocked model witnesses",
            "false_or_weakened_named_theorem_found": False,
        },
        "finite_scope": {
            "focused_unittest_methods": 18,
            "four_row_role_campaign_lab_assignments": 4096,
            "independent_counterexamples": finite,
            "archived_negative_cases_verified": len(archived["negative_cases"]),
            "frozen_synthetic_controls": finite["synthetic_control_count"],
            "full_pytest_receipt": {
                "argv": full["argv"],
                "cwd": full["cwd"],
                "checkout_commit": full["checkout_commit"],
                "exit_code": full["exit_code"],
                "stdout_sha256": full["stdout_sha256"],
                "stderr_sha256": full["stderr_sha256"],
                "summary": archived["full_pytest_reported"],
                "explicit_input_count": len(full["inputs"]),
            },
        },
        "retained_evidence": {
            "nominal_manifest_sha256": archived["nominal_manifest_sha256"],
            "nominal_files_verified": archived["nominal_file_count"],
            "nominal_audit_stdout_matches_fresh_replay": True,
            "negative_manifest_sha256": archived["negative_manifest_sha256"],
            "negative_files_verified": archived["negative_file_count"],
            "failed_development_attempts_retained": archived[
                "failed_development_attempts_retained"
            ],
            "source_receipts_verified": archived["source_receipts"],
            "receipt_deletion_controls_detected": sum(
                x["expected_rejection"]
                for x in verification["results"]
                if x["label"].startswith("missing-")
            ),
            "receipt_verifier_fail_open_found": False,
        },
        "scientific_boundary": {
            "physical_evidence_admitted": False,
            "independence_authenticated": False,
            "heldout_accuracy": None,
            "classifier_accuracy_proved": False,
            "empirical_validation": "OPEN",
            "receipt_digests_are_syntactic_assertions_only": True,
        },
        "finding": {
            "id": "MAT009-AUDIT-001",
            "status": "CONFIRMED",
            "component": "formal/sonification/mat009/lean/LeanAudit.lean:37",
            "description": (
                "The audit labels declarations as compiler auxiliaries from "
                "user-controllable name suffixes and exempts that class from "
                "project-axiom and transitive-axiom checks."
            ),
            "minimal_mutation": [
                "axiom auditor_false_cstage1 : False",
                "theorem auditor_false_proof_cstage1 : False := auditor_false_cstage1",
            ],
            "mutant_splitmodel_sha256": negative_details["auxiliary_named_false_axiom"][
                "mutant_sha256"
            ],
            "lean_audit_exit_code": negative_details["auxiliary_named_false_axiom"]["exit_code"],
            "audit_summary": disguised["audit_summary"],
            "logged_false_declarations": disguised["disguised_declarations"],
            "ordinary_axiom_control_exit_code": negative_details["ordinary_false_axiom"][
                "exit_code"
            ],
            "integrated_checker_mutation_exit_code": next(
                x["exit_code"]
                for x in verification["results"]
                if x["label"] == "mutated-proof-checker"
            ),
            "integrated_checker_error": obj("verification-probe-002/checker-result/result.json")[
                "error"
            ],
            "fixed_count_gate_mutation_exit_code": 1,
            "fixed_count_gate_error": "complete declaration/theorem inventory changed",
            "current_named_theorem_axiom_impact": "NONE_OBSERVED",
            "boundary": (
                "Current proof-source commit and fixed declaration counts reject "
                "this changed input; "
                "the standalone Lean audit gate is unsafe for future rebaselines."
            ),
        },
        "executions": {
            "nominal_verifiers_and_finite": nominal_commands,
            "own_top_level": own_commands,
            "fresh_lean_jobs": fresh["commands"],
            "isolated_lean_mutation_jobs": negative_details,
            "source_and_receipt_negative_jobs": verification["results"],
            "raw_logs_root": "formal/sonification/mat009/audit",
        },
        "failed_audit_harness_attempt": {
            "exit_code": 1,
            "cause": (
                "Audit drivers initially lacked the repository import path; "
                "three receipt deletions still rejected."
            ),
            "raw_log": "formal/sonification/mat009/audit/verification_probe.stdout",
            "detail": "formal/sonification/mat009/audit/verification-probe-001/result.json",
            "accepted_negative_replay": "verification-probe-002",
        },
        "limitations": [
            "No theorem establishes source-to-model or CPython refinement for MAT009 and MAT008.",
            (
                "R7's two-row structural witness is a model witness only; MAT009 "
                "requires both phases in each source split."
            ),
            (
                "The Lean row model omits child skip guards, parent implementation, "
                "phases, receipts, diagnostics, and other child reasons."
            ),
            (
                "Finite tests and archived execution receipts cover listed cases only; "
                "the full pytest receipt lists no explicit inputs."
            ),
            (
                "Python subclass equality, hashing, dict methods, and exceptions "
                "escape the exact built-in refinement domain."
            ),
            (
                "All candidate identities and digests are self-declared. No physical "
                "independence, prospective registration, or accuracy is authenticated."
            ),
        ],
        "auditor_file_scope": "formal/sonification/mat009/audit/**",
        "production_files_modified_by_auditor": False,
        "auditor_committed_or_pushed": False,
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "audit": report["verdicts"]["audit"],
                "finding": report["finding"]["id"],
                "report": str(OUT),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
