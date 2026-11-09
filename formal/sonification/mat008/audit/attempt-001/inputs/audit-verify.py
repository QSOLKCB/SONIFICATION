"""Check the explicitly required MAT008 audit evidence; never promote refinement."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEAN = HERE.parent / "lean"
PIN = "c7889e3c9468ef4354d45d41b467263a0b5dea02"
MODULES = {"Audit", "Mat008", "Mat008.RunOwnership"}
ALLOW = {"propext", "Quot.sound", "Classical.choice"}
MUTATIONS = {
    "drop_sticky_conflict": (1, "Lean rejected Mat008.RunOwnership"),
    "weaker_same_name_theorem": (3, "Lean rejected Audit"),
    "prohibited_data_assumption": (3, "Lean rejected Audit"),
    "unimported_module": (0, "module coverage mismatch"),
}


def load(path: Path):
    return json.loads(path.read_text())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def streams(root: Path, row: dict) -> None:
    for key in ("stdout", "stderr"):
        p = root / row[f"{key}_path"]
        assert p.is_file() and sha(p) == row[f"{key}_sha256"], p


def checker(root: Path, count: int, status: str) -> dict:
    result = load(root / "result.json")
    assert result["status"] == status
    assert len(result["commands"]) == count
    for index, command in enumerate(result["commands"]):
        assert command["stdout_path"] == f"{index:02d}.stdout"
        assert command["stderr_path"] == f"{index:02d}.stderr"
        assert command["timed_out"] is False
        assert command["exit_code"] == (1 if status == "FAIL" and index == count - 1 else 0)
        streams(root, command)
    if count:
        assert result["version_exit_code"] == 0
        assert (root / "version.stdout").read_bytes() == (
            b"Lean (version 4.19.0, x86_64-unknown-linux-gnu, commit 6caaee842e94, Release)\n"
        )
        assert (root / "version.stderr").read_bytes() == b""
    if status == "PASS":
        assert result["baseline_commit"] == PIN
        assert result["python_refinement"] == "OPEN"
        assert set(result["imported_modules"]) == MODULES
        assert result["declaration_count"] == 99
        assert (root / "declarations.json").is_file()
        assert (root / "toolchain-imports.json").is_file()
    return result


def negative(root: Path) -> dict:
    receipt = load(root / "result.json")
    rows = {r["mutation"]: r for r in receipt["results"]}
    assert receipt["status"] == "PASS" and len(receipt["results"]) == 4
    assert set(rows) == set(MUTATIONS)
    assert {p.name for p in root.iterdir() if p.is_dir()} == set(MUTATIONS)
    for name, (count, error) in MUTATIONS.items():
        case = root / name
        row = rows[name]
        assert row["exit_code"] == 1 and row["detected"] is True
        assert sha(case / "RunOwnership.lean") == row["source_sha256"]
        assert (case / "runner.stdout").is_file() and (case / "runner.stderr").is_file()
        verification = checker(case / "verification", count, "FAIL")
        assert verification["error"].startswith(error)
        logs = "".join((case / "verification" / f"{i:02d}.stdout").read_text() for i in range(count))
        if name == "prohibited_data_assumption":
            assert "unapproved transitive axiom sorryAx in Sonification.Mat008.prohibitedHelper" in logs
        if name == "weaker_same_name_theorem":
            assert "function expected at" in logs and "reused_run_blocks" in logs
        if name == "unimported_module":
            assert "Unimported.lean" in verification["error"]
        if name == "drop_sticky_conflict":
            assert "error:" in logs and "decide" in logs
            assert row["counterexample"]["exit_code"] == 0
            assert sha(case / "Counterexample.lean") == row["counterexample"]["source_sha256"]
            assert (case / "counterexample.stdout").read_bytes() == b""
            assert (case / "counterexample.stderr").read_bytes() == b""
    return receipt


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 audit/verify.py ATTEMPT_NAME")
    attempt = HERE / sys.argv[1]
    manifest = load(attempt / "input-manifest.json")
    assert manifest["proof_input_commit"] == PIN
    for name, item in manifest["input_files"].items():
        assert item["equal"] and item["sha256"] == item["committed_sha256"]
        assert sha(attempt / "inputs" / name) == item["sha256"]
    execution = load(attempt / "execution-index.json")
    assert execution["status"] == "PASS"
    commands = [execution["version"], *execution["direct_build"], *execution["independent_jobs"].values()]
    assert len(execution["direct_build"]) == 3
    assert set(execution["independent_jobs"]) == {
        "fresh-checker", "fresh-negative", "submitted-conformance", "independent-conformance", "targeted-tests"
    }
    for command in commands:
        assert command["exit_code"] == 0 and command["timed_out"] is False
        streams(attempt, command)
    direct = [
        json.loads(line.removeprefix("SONIFICATION_DECL "))
        for line in (attempt / "direct-02.stdout").read_text().splitlines()
        if line.startswith("SONIFICATION_DECL ")
    ]
    assert len(direct) == 99 and len({x["declaration"] for x in direct}) == 99
    assert sorted(x["declaration"] for x in direct) == load(LEAN / "expected-declarations.json")
    assert all(set(row["axioms"]) <= ALLOW for row in direct)
    statements = load(LEAN / "theorem-statements.json")
    observed = {row["declaration"]: row for row in direct}
    assert len(statements) == 10
    for statement in statements:
        assert observed[statement["declaration"]] == statement
    nominal_paths = [LEAN / "attempts/commit-bound-001", attempt / "fresh-checker"]
    nominal = [checker(p, 3, "PASS") for p in nominal_paths]
    for path, result in zip(nominal_paths, nominal, strict=True):
        assert result["input_sha256"] == {
            key: item["sha256"] for key, item in manifest["input_files"].items()
        }
        assert result["lean_executable"]["sha256"] == manifest["lean_binary_sha256"]
        assert load(path / "declarations.json") == direct
        for item in load(path / "toolchain-imports.json").values():
            assert sha(Path(item["path"])) == item["sha256"]
    negative_paths = [LEAN / "attempts/commit-bound-negative-001", attempt / "fresh-negative"]
    for path in negative_paths:
        negative(path)
    independent = load(attempt / "independent-conformance.stdout")
    assert independent["status"] == "PASS" and independent["cases"] == 1296
    assert independent["collision_cases"] == 834 and independent["noncollision_cases"] == 462
    assert independent["REFINEMENT_PROVED"] == "OPEN"
    finite = load(attempt / "submitted-conformance/receipt.json")
    assert finite["status"] == "FINITE_CONFORMANCE_PASS" and finite["exhaustive_generated_cases"] == 1296
    assert finite["REFINEMENT_PROVED"] == "OPEN" and finite["DIFFERENTIAL_TESTED"] == "PASS"
    assert finite["source_mutation_detected"] and finite["output_mutation_detected"]
    report = {
        "status": "AUDIT_ACCEPTED_FOR_DECLARED_PARTIAL_SCOPE",
        "proof_input_commit": PIN,
        "declaration_count": len(direct),
        "named_theorems": len(statements),
        "allowed_transitive_axioms": sorted(ALLOW),
        "required_nominal_receipts": [str(p.relative_to(HERE.parent)) for p in nominal_paths],
        "required_negative_receipts": [str(p.relative_to(HERE.parent)) for p in negative_paths],
        "mutation_count_per_run": 4,
        "finite_cases": 1296,
        "MODEL_PROVED": "PASS", "REFINEMENT_PROVED": "OPEN",
        "DIFFERENTIAL_TESTED": "PASS", "AUDIT_ACCEPTED": "PASS",
        "scope": "Ten named mathematical theorems and finite run-ownership observations only",
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
