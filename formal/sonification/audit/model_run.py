#!/usr/bin/env python3
"""Independent math-only audit; no dependency on later refinement artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FORMAL = ROOT / "formal/sonification"
LEAN = FORMAL / "lean"
LEANC = Path("/home/trent/.elan/toolchains/leanprover--lean4---v4.19.0/bin/lean")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def execute(argv: list[str], out: Path, *, expected_zero: bool) -> dict:
    out.mkdir(parents=True, exist_ok=False)
    completed = subprocess.run(argv, cwd=ROOT, capture_output=True, check=False, timeout=240)
    (out / "stdout.log").write_bytes(completed.stdout)
    (out / "stderr.log").write_bytes(completed.stderr)
    record = {
        "argv": argv,
        "cwd": str(ROOT),
        "exit_code": completed.returncode,
        "stdout_sha256": sha(completed.stdout),
        "stderr_sha256": sha(completed.stderr),
        "expected_zero": expected_zero,
        "detected_as_expected": (completed.returncode == 0) == expected_zero,
    }
    (out / "execution.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    runner_source = Path(__file__).read_bytes()
    (out / "audit-runner.py.source").write_bytes(runner_source)
    base_files = [
        "check.py",
        "Audit.lean",
        "Sonification.lean",
        "Sonification/Intervals.lean",
        "Sonification/OrderedIntervals.lean",
        "lean-toolchain",
        "lakefile.toml",
        "expected-declarations.json",
        "theorem-statements.json",
    ]
    snapshot = out / "inputs"
    for name in base_files:
        dest = snapshot / (name + ".source")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((LEAN / name).read_bytes())
    initial = {name: sha((LEAN / name).read_bytes()) for name in base_files}
    checks = []
    checks.append(
        execute(
            [
                sys.executable,
                str(LEAN / "check.py"),
                "--lean",
                str(LEANC),
                "--out",
                str(out / "nominal-build"),
            ],
            out / "nominal-command",
            expected_zero=True,
        )
    )
    mutations = [
        "false_theorem",
        "weaker_theorem",
        "hidden_data_sorry",
        "custom_axiom",
        "unimported_nested_module",
        "missing_import",
        "empty_zero_exit_report",
        "missing_expected_inventory",
    ]
    for mutation in mutations:
        with tempfile.TemporaryDirectory(prefix="sonification-independent-audit-") as temp:
            target = Path(temp)
            for name in base_files:
                dest = target / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes((snapshot / (name + ".source")).read_bytes())
            proof = target / "Sonification/Intervals.lean"
            text = proof.read_text()
            if mutation == "false_theorem":
                text = text.replace(
                    "classify ⟨0, 1⟩ ⟨2, 3⟩ = some .below", "classify ⟨0, 1⟩ ⟨2, 3⟩ = some .above"
                )
                proof.write_text(text)
            elif mutation == "weaker_theorem":
                text, count = re.subn(
                    r"theorem box_valid.*?(?=theorem touching)",
                    "theorem box_valid (center error : Int) (he : 0 ≤ error) : "
                    "True := by trivial\n\n",
                    text,
                    flags=re.S,
                )
                if count != 1:
                    raise ValueError("mutation locator mismatch")
                proof.write_text(text)
            elif mutation == "hidden_data_sorry":
                proof.write_text(
                    text.replace(
                        "end Sonification",
                        "namespace Unrelated\ndef hidden : Nat := by sorry\n"
                        "end Unrelated\nend Sonification",
                    )
                )
            elif mutation == "custom_axiom":
                proof.write_text(
                    text.replace(
                        "end Sonification", "axiom adversarialAssumption : False\nend Sonification"
                    )
                )
            elif mutation == "unimported_nested_module":
                nested = target / "Sonification/Nested/Excluded.lean"
                nested.parent.mkdir(parents=True)
                nested.write_text(
                    "namespace Unrelated\ntheorem broken : False := by trivial\nend Unrelated\n"
                )
            elif mutation == "missing_import":
                (target / "Sonification.lean").write_text("import Sonification.Intervals\n")
            elif mutation == "missing_expected_inventory":
                (target / "expected-declarations.json").unlink()
            executable = LEANC
            if mutation == "empty_zero_exit_report":
                executable = target / "fake-lean"
                executable.write_text(
                    "#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then printf '%s\\n' "
                    "'Lean (version 4.19.0, x86_64-unknown-linux-gnu, "
                    "commit 6caaee842e94, Release)'; fi\nexit 0\n"
                )
                executable.chmod(0o755)
            mutation_inputs = out / mutation / "mutated-inputs"
            for path in sorted(target.rglob("*")):
                if path.is_file():
                    dest = mutation_inputs / (str(path.relative_to(target)) + ".source")
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(path.read_bytes())
            record = execute(
                [
                    sys.executable,
                    str(target / "check.py"),
                    "--lean",
                    str(executable),
                    "--out",
                    str(out / mutation / "checker"),
                ],
                out / mutation / "command",
                expected_zero=False,
            )
            record["mutation"] = mutation
            checks.append(record)
    # Bind directly to historical Git; no production import or refinement adapter.
    frozen_commit = "b97348ff8fcf3f57764dec21a8914f153f96a745"
    frozen_tag = "8b933a5ab09b8e76afe4c8e169e089f251e23314"
    module_sha256 = "2e363adea6c781ab68aec69d2ee5c7d712fc5e46346ae5be21d8cf3e929781c6"
    for locator, expected in [
        ("refs/tags/mat-spec-007-v0.1.0", frozen_tag),
        (f"{frozen_tag}^{{commit}}", frozen_commit),
    ]:
        actual = subprocess.check_output(["git", "rev-parse", locator], cwd=ROOT, text=True)
        if actual.strip() != expected:
            raise ValueError(f"frozen Git identity mismatch: {locator}")
    raw = subprocess.check_output(
        ["git", "show", f"{frozen_commit}:materials/mat_spec_007.py"], cwd=ROOT
    )
    if sha(raw) != module_sha256:
        raise ValueError("frozen production module mismatch")
    (out / "frozen-production.py.source").write_bytes(raw)
    mutation_observations = {
        "frozen_source_identity_matches": sha(raw) == module_sha256,
        "changed_source_bytes_fail_fixed_pin": sha(raw + b"\n# mutation\n") != module_sha256,
    }
    (out / "source-observations.json").write_text(
        json.dumps(mutation_observations, indent=2) + "\n"
    )
    proof_result = json.loads((out / "nominal-build/result.json").read_text())
    declarations = json.loads((out / "nominal-build/declarations.json").read_text())
    expected_statements = json.loads((LEAN / "theorem-statements.json").read_text())
    intended = {row["declaration"]: row for row in expected_statements}
    observed = {row["declaration"]: row for row in declarations}
    theorem_reviews = []
    for name, expected in sorted(intended.items()):
        actual = observed[name]
        theorem_reviews.append(
            {
                "declaration": name,
                "exact_observed_type": actual["type"],
                "axioms": actual["axioms"],
                "MODEL_PROVED": "PASS" if actual == expected else "FAILED",
                "REFINEMENT_PROVED": "OPEN",
                "DIFFERENTIAL_TESTED": "NOT_EXECUTED",
                "AUDIT_ACCEPTED": "PASS" if actual == expected else "FAILED",
                "scope": "Mathematical statement only; no production correspondence",
            }
        )
    current_inputs_match = all(
        sha((LEAN / name).read_bytes()) == digest for name, digest in initial.items()
    )
    report = {
        "schema": "qsol.sonification-formal-001.independent-audit/v1",
        "target_commit": "8c62517138e3b86a4672d8969e190b747f81c398",
        "frozen_mat007_commit": frozen_commit,
        "frozen_mat007_tag_object": frozen_tag,
        "frozen_module_sha256": module_sha256,
        "scope": "MATHEMATICAL_MODEL_ONLY; finite conformance NOT_EXECUTED",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "audit_runner_sha256": sha(runner_source),
        "auditor": "independent_auditor subagent; inspected actual sources and reexecuted commands",
        "proof_input_sha256": initial,
        "inputs_stable_during_audit": current_inputs_match,
        "nominal_proof_result": proof_result["status"],
        "checks": checks,
        "negative_observations": mutation_observations,
        "theorems": theorem_reviews,
        "trust": [
            "Lean 4.19.0 kernel and pinned standard library",
            "propext, Quot.sound, Classical.choice as disclosed per theorem",
            "Unsafe compiler-only auxiliaries may contain lcProof/lcUnreachable; "
            "never safe theorem dependencies",
            "Source-sensitive checker and audit metaprogram; CPython, Git, OS and SHA-256",
            "No independent authentication of Lean distribution origin",
        ],
        "open_obligations": [
            "CPython semantics correspondence and Fraction refinement",
            "Rational instantiation of the generic OrderSpec",
            "Whole-program production caller/dependency closure",
            "Owner review of intended scientific specification",
        ],
        "status": "PASS"
        if all(c["detected_as_expected"] for c in checks)
        and all(mutation_observations.values())
        and current_inputs_match
        and all(t["AUDIT_ACCEPTED"] == "PASS" for t in theorem_reviews)
        else "FAIL",
    }
    (out / "AUDIT.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps({"status": report["status"], "out": str(out), "theorems": len(theorem_reviews)})
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
