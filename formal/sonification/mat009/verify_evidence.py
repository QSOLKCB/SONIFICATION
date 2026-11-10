"""Bind the retained MAT009 source and finite receipts to the source checkpoint.

This checks archive integrity and local test inputs. It does not turn finite
execution into a proof of CPython semantics or authenticate physical evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "formal/sonification/evidence"
SOURCE_CHECKPOINT = "38b5f9e99a5ce3f267c004362acf00ac0dc11342"
SOURCE_BINDING = "formal/sonification/mat009/source/SOURCE_BINDING.json"
SOURCE_BINDER = "formal/sonification/mat009/source/source_bind.py"
FINITE_TEST = "tests/test_sonification_formal_mat009_split.py"
FROZEN_TEST = "tests/test_mat_spec_009.py"

# The SHA-256 values pin the reviewed receipt files, including their recorded
# commands, input hashes, original stream hashes, tool identities and status.
RECEIPTS = {
    "mat009-source-bind-001": {
        "sha256": "e3c3793f25532f540ba20b79729c5f20ede2398470ed2ffa8d75705cb93c5606",
        "worktree_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "argv": ["python3", SOURCE_BINDER],
        "inputs": {SOURCE_BINDER, SOURCE_BINDING},
    },
    "mat009-finite-001": {
        "sha256": "b86b0b4ee2119ff0afffbd6ec575d9f2f3304fe6aaaa90cf3d6c43cae50f05e9",
        "worktree_sha256": "36528314ce41776bf58b80e489e1b96af92c4a086b413864f5ba6904070acf25",
        "argv": [
            "python3", "-m", "unittest", "discover", "-s", "tests", "-p",
            "test_sonification_formal_mat009_split.py", "-q",
        ],
        "inputs": {SOURCE_BINDING, FINITE_TEST},
    },
    "mat009-ruff-source-001": {
        "sha256": "efe30f79371ca762ac498a06e7e49c7b330b644d6b8bcb2cfbc37a7e60c0b4fd",
        "worktree_sha256": "009b0dc9d39fc77af691d2724fde7be97ecf743dccd838871db42cdef903121e",
        "argv": [
            "uv", "run", "--no-project", "--offline", "--with", "ruff", "ruff",
            "check", SOURCE_BINDER, FINITE_TEST,
        ],
        "inputs": {SOURCE_BINDER, FINITE_TEST},
    },
    "mat009-pytest-001": {
        "sha256": "cd00d1ebda66b847432194d9b53ffa22060bfa518c6c6b99dc9e63ea1fe0996f",
        "worktree_sha256": "19b35e6445bc6c3fdde34ea5f92c17eda4e94231263247d37c28ba7f1d61459e",
        "argv": ["python3", "-m", "pytest", "-q", FINITE_TEST, FROZEN_TEST],
        "inputs": {SOURCE_BINDING, FINITE_TEST, FROZEN_TEST},
    },
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def verify(evidence: Path = EVIDENCE) -> dict:
    """Reject missing, changed, failed or input-stale mandatory receipts."""
    for name, expected in RECEIPTS.items():
        directory = evidence / name
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError(f"missing ordinary receipt directory: {name}")
        required = {
            "receipt.json", "stdout.log", "stderr.log", "worktree-status.txt",
            "tracked-diff.patch",
        }
        if {p.name for p in directory.iterdir()} != required:
            raise ValueError(f"receipt file inventory changed: {name}")
        for member in required:
            if (directory / member).is_symlink() or not (directory / member).is_file():
                raise ValueError(f"missing ordinary receipt file: {name}/{member}")
        raw = (directory / "receipt.json").read_bytes()
        if sha(raw) != expected["sha256"]:
            raise ValueError(f"receipt changed: {name}")
        receipt = json.loads(raw)
        if (
            receipt.get("schema") != "qsol.sonification-formal-001.execution/v1"
            or receipt.get("checkout_commit") != SOURCE_CHECKPOINT
            or receipt.get("argv") != expected["argv"]
            or receipt.get("exit_code") != 0
            or set(receipt.get("inputs", {})) != expected["inputs"]
        ):
            raise ValueError(f"execution identity or outcome changed: {name}")
        for stream in ("stdout", "stderr"):
            if sha((directory / f"{stream}.log").read_bytes()) != receipt[f"{stream}_sha256"]:
                raise ValueError(f"recorded {stream} changed: {name}")
        if sha((directory / "worktree-status.txt").read_bytes()) != expected["worktree_sha256"]:
            raise ValueError(f"recorded worktree status changed: {name}")
        if (directory / "tracked-diff.patch").read_bytes():
            raise ValueError(f"recorded tracked input diff is nonempty: {name}")
        for relative, digest in receipt["inputs"].items():
            current = ROOT / relative
            if current.is_symlink() or not current.is_file() or sha(current.read_bytes()) != digest:
                raise ValueError(f"current test input changed: {relative}")
            historical = subprocess.check_output(
                ["git", "show", f"{SOURCE_CHECKPOINT}:{relative}"], cwd=ROOT
            )
            if sha(historical) != digest:
                raise ValueError(f"checkpoint test input changed: {relative}")

    binding_output = (evidence / "mat009-source-bind-001/stdout.log").read_text()
    binding = json.loads(binding_output)
    if (
        binding.get("status") != "SOURCE_SYNTAX_MATCH"
        or binding.get("refinement_to_cpython") != "OPEN"
        or binding.get("commit") != "0758a96360726aafbb07abed34620eda178407ae"
        or binding.get("target_sha256")
        != "a68089df7d1901fb7c17ffc2889b844b3573024aec4b66348f9c2ef71930c690"
    ):
        raise ValueError("frozen source binder output changed")
    if "Ran 18 tests" not in (evidence / "mat009-finite-001/stderr.log").read_text():
        raise ValueError("finite test summary missing")
    if "35 passed, 36 subtests passed" not in (
        evidence / "mat009-pytest-001/stdout.log"
    ).read_text():
        raise ValueError("targeted pytest summary missing")
    return {
        "status": "MAT009_SOURCE_FINITE_RECEIPTS_BOUND",
        "receipt_count": len(RECEIPTS),
        "REFINEMENT_PROVED": "OPEN",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=EVIDENCE)
    args = parser.parse_args()
    print(json.dumps(verify(args.evidence), sort_keys=True))
