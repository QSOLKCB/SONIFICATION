"""Check the explicitly required MAT008 audit evidence; never promote refinement."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath

HERE = Path(os.path.abspath(__file__)).parent
LEAN = HERE.parent / "lean"
PIN = "c7889e3c9468ef4354d45d41b467263a0b5dea02"
ACCEPTED_AUDIT_SHA256 = "34eef078032bfb168faec6ba3bfe82cbf7e6bdc0412fe56820bc2bf2e26665d8"
EVIDENCE_COUNT = 161
EVIDENCE_ROOTS = (
    "audit/attempt-001",
    "lean/attempts/commit-bound-001",
    "lean/attempts/commit-bound-negative-001",
)
ASSURANCE = {
    "MODEL_PROVED": "PASS",
    "REFINEMENT_PROVED": "OPEN",
    "DIFFERENTIAL_TESTED": "PASS",
    "AUDIT_ACCEPTED": "PASS",
}
THEOREM_FIELDS = {"unsafe_definition", "type", "origin", "kind", "declaration", "axioms"}
MODULES = {"Audit", "Mat008", "Mat008.RunOwnership"}
ALLOW = {"propext", "Quot.sound", "Classical.choice"}
MUTATIONS = {
    "drop_sticky_conflict": (1, "Lean rejected Mat008.RunOwnership"),
    "weaker_same_name_theorem": (3, "Lean rejected Audit"),
    "prohibited_data_assumption": (3, "Lean rejected Audit"),
    "unimported_module": (0, "module coverage mismatch"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def reject_symlinks(path: Path) -> None:
    absolute = Path(os.path.abspath(path))
    for part in reversed([absolute, *absolute.parents]):
        require(not part.is_symlink(), f"symlink path rejected: {part}")


def read(path: Path) -> bytes:
    reject_symlinks(path)
    require(path.is_file(), f"required regular file missing: {path}")
    return path.read_bytes()


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, f"duplicate JSON key: {key}")
        value[key] = item
    return value


def load(path: Path):
    return json.loads(read(path), object_pairs_hook=unique_object)


def sha(path: Path) -> str:
    return hashlib.sha256(read(path)).hexdigest()


def inventory_tree(root: Path) -> tuple[set[str], set[str]]:
    reject_symlinks(root)
    require(root.is_dir(), f"required evidence root missing: {root}")
    files, directories = set(), set()
    pending = [root]
    while pending:
        directory = pending.pop()
        directories.add(directory.relative_to(HERE.parent).as_posix())
        with os.scandir(directory) as entries:
            for entry in entries:
                path = Path(entry.path)
                require(not entry.is_symlink(), f"symlink evidence rejected: {path}")
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                else:
                    require(entry.is_file(follow_symlinks=False), f"special evidence file rejected: {path}")
                    files.add(path.relative_to(HERE.parent).as_posix())
    return files, directories


def accepted_audit(attempt: Path) -> dict:
    # The reviewed digest is independent of the mutable manifest. A new execution
    # needs a new reviewed receipt and pin; copying a PASS report cannot accept it.
    raw = read(attempt / "AUDIT.json")
    require(hashlib.sha256(raw).hexdigest() == ACCEPTED_AUDIT_SHA256,
            "accepted audit SHA-256 mismatch")
    audit = json.loads(raw, object_pairs_hook=unique_object)
    require(audit["proof_input_commit"] == PIN, "accepted audit proof commit mismatch")
    require(audit["audit_outcome"] == "PASS", "accepted audit outcome mismatch")
    require(audit["assurance"] == ASSURANCE, "accepted audit assurance mismatch")
    expected = audit["evidence_files"]
    require(isinstance(expected, dict) and len(expected) == EVIDENCE_COUNT,
            "accepted evidence inventory must contain exactly 161 files")
    for name, item in expected.items():
        path = PurePosixPath(name)
        require(not path.is_absolute() and ".." not in path.parts and path.as_posix() == name,
                f"noncanonical evidence path: {name}")
        require(any(path.is_relative_to(PurePosixPath(root)) for root in EVIDENCE_ROOTS),
                f"evidence path outside accepted roots: {name}")
        require(set(item) == {"sha256", "bytes"}, f"invalid evidence metadata: {name}")
        require(type(item["bytes"]) is int and item["bytes"] >= 0,
                f"invalid evidence size: {name}")
        require(isinstance(item["sha256"], str) and re.fullmatch("[0-9a-f]{64}", item["sha256"]) is not None,
                f"invalid evidence digest: {name}")
    actual_files, actual_directories = set(), set()
    for root in EVIDENCE_ROOTS:
        files, directories = inventory_tree(HERE.parent / root)
        actual_files.update(files)
        actual_directories.update(directories)
    manifest_name = "audit/attempt-001/AUDIT.json"
    require(actual_files == set(expected) | {manifest_name},
            f"evidence membership mismatch; missing={sorted(set(expected) - actual_files)}; "
            f"extra={sorted(actual_files - set(expected) - {manifest_name})}")
    expected_directories = set()
    for name in actual_files:
        path = PurePosixPath(name).parent
        while any(path == PurePosixPath(root) or path.is_relative_to(PurePosixPath(root))
                  for root in EVIDENCE_ROOTS):
            expected_directories.add(path.as_posix())
            path = path.parent
    require(actual_directories == expected_directories, "evidence directory membership mismatch")
    for name, item in expected.items():
        data = read(HERE.parent / name)
        require(len(data) == item["bytes"], f"evidence size mismatch: {name}")
        require(hashlib.sha256(data).hexdigest() == item["sha256"], f"evidence digest mismatch: {name}")
    return audit


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
    if not __debug__:
        raise ValueError("optimized Python is rejected; assertions must remain enabled")
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 audit/verify.py ATTEMPT_NAME")
    require(sys.argv[1] == "attempt-001", "only the independently pinned attempt-001 is accepted")
    reject_symlinks(Path(os.path.abspath(__file__)))
    attempt = HERE / sys.argv[1]
    audit = accepted_audit(attempt)
    manifest = load(attempt / "input-manifest.json")
    assert manifest["proof_input_commit"] == PIN
    for name, item in manifest["input_files"].items():
        assert item["equal"] and item["sha256"] == item["committed_sha256"]
        assert sha(attempt / "inputs" / name) == item["sha256"]
        require(sha(LEAN / name) == item["sha256"], f"current proof input mismatch: {name}")
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
    claims = audit["claims"]
    require(len(claims) == 10 and len({r["declaration"] for r in claims}) == 10,
            "accepted theorem inventory mismatch")
    require({r["declaration"] for r in claims} == {r["declaration"] for r in statements},
            "accepted and checker theorem sets differ")
    for claim in claims:
        row = {key: claim[key] for key in THEOREM_FIELDS}
        require(observed[claim["declaration"]] == row,
                f"accepted theorem row mismatch: {claim['declaration']}")
        dimensions = {
            **ASSURANCE,
            "DIFFERENTIAL_TESTED": (
                "PASS" if claim["declaration"] == "Sonification.Mat008.reused_run_blocks"
                else "NOT_EXECUTED"
            ),
        }
        require(claim["assurance"] == dimensions,
                f"accepted theorem assurance mismatch: {claim['declaration']}")
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
        "accepted_audit_sha256": ACCEPTED_AUDIT_SHA256,
        "exact_evidence_files": EVIDENCE_COUNT,
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
    try:
        main()
    except (AssertionError, KeyError, OSError, TypeError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc), "error_type": type(exc).__name__}))
        raise SystemExit(1) from None
