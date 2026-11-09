"""Bind the append-only MAT008 audit CLI fix controls to exact retained bytes."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
MANIFEST_SHA256 = "423964376918eb3c56188a8a17d7709f891698beb394d5b47f36c1bc58e77b31"
ROOTS = ("binder-hardening-002", "portability-002")
EXPECTED_FILES = 65
EXPECTED_BINDER_CASES = {
    "baseline", "changed_accepted_theorem_type", "promoted_refinement",
    "deleted_nested_log", "deleted_postcommit_receipt", "deleted_all_postcommit_receipts",
    "extra_file", "extra_empty_directory", "symlink_audit_root", "symlink_postcommit_root",
    "symlink_manifest", "symlink_individual_log", "joint_log_and_manifest_tamper",
    "changed_current_theorem_statement", "optimized_python",
}
EXPECTED_PORTABILITY_CASES = {
    "relocated_valid", "relocated_changed_import", "relocated_changed_binary",
}
ACCEPTED_AUDIT_SHA256 = "34eef078032bfb168faec6ba3bfe82cbf7e6bdc0412fe56820bc2bf2e26665d8"
RUNNER_SHA256 = "7c9e67d4e8dec118ab80163442fe876e84f0ff978b6461d3703367a3badfc25d"
CLI_TEST_SHA256 = "d6fd93c1a6857950d063dd1b3f311546b3f46acb63c9b922c717a17998e16075"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read(path: Path) -> bytes:
    require(path.is_file(), f"missing evidence file: {path}")
    for item in (path, *path.parents):
        require(not item.is_symlink(), f"linked evidence path: {item}")
    return path.read_bytes()


def load(path: Path):
    return json.loads(read(path), object_pairs_hook=unique_pairs)


def inventory(root: Path) -> tuple[set[str], set[str]]:
    for item in (root, *root.parents):
        require(not item.is_symlink(), f"linked evidence root: {item}")
    require(root.is_dir(), f"missing evidence root: {root}")
    files, directories = set(), set()
    pending = [root]
    while pending:
        directory = pending.pop()
        directories.add(directory.relative_to(HERE).as_posix())
        with os.scandir(directory) as entries:
            for entry in entries:
                path = Path(entry.path)
                require(not entry.is_symlink(), f"linked evidence entry: {path}")
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                else:
                    require(entry.is_file(follow_symlinks=False),
                            f"special evidence entry: {path}")
                    files.add(path.relative_to(HERE).as_posix())
    return files, directories


def verify() -> dict:
    raw = read(HERE / "hotfix-snapshot.json")
    require(digest(raw) == MANIFEST_SHA256, "hotfix snapshot SHA-256 mismatch")
    manifest = json.loads(raw, object_pairs_hook=unique_pairs)
    require(manifest["roots"] == list(ROOTS), "hotfix evidence roots changed")
    expected = manifest["files"]
    require(isinstance(expected, list) and len(expected) == EXPECTED_FILES,
            "hotfix file inventory changed")
    names = []
    for item in expected:
        require(set(item) == {"path", "bytes", "sha256"}, "invalid hotfix file record")
        name = item["path"]
        require(isinstance(name, str), "hotfix evidence path is not a string")
        path = PurePosixPath(name)
        require(bool(path.parts) and not path.is_absolute()
                and ".." not in path.parts and path.as_posix() == name
                and path.parts[0] in ROOTS,
                f"noncanonical hotfix evidence path: {name}")
        require(type(item["bytes"]) is int and item["bytes"] >= 0,
                f"invalid hotfix byte count: {name}")
        require(isinstance(item["sha256"], str)
                and re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is not None,
                f"invalid hotfix digest: {name}")
        names.append(name)
    require(len(names) == len(set(names)), "duplicate hotfix evidence path")
    files, directories = set(), set()
    for root in ROOTS:
        found_files, found_dirs = inventory(HERE / root)
        files.update(found_files)
        directories.update(found_dirs)
    require(files == set(names), "hotfix evidence file membership mismatch")
    expected_directories = set(ROOTS)
    for name in names:
        parent = PurePosixPath(name).parent
        while parent.parts and parent.parts[0] in ROOTS:
            expected_directories.add(parent.as_posix())
            parent = parent.parent
    require(directories == expected_directories,
            "hotfix evidence directory membership mismatch")
    for item in expected:
        data = read(HERE / item["path"])
        require(len(data) == item["bytes"], f"hotfix evidence size mismatch: {item['path']}")
        require(digest(data) == item["sha256"],
                f"hotfix evidence digest mismatch: {item['path']}")

    accepted_sha = digest(read(HERE / "attempt-001/AUDIT.json"))
    require(accepted_sha == ACCEPTED_AUDIT_SHA256, "accepted audit changed")
    require(digest(read(HERE / "run.py")) == RUNNER_SHA256,
            "current audit runner source mismatch")
    cli_test = HERE.parents[3] / "tests/test_sonification_formal_mat008_audit_cli.py"
    require(digest(read(cli_test)) == CLI_TEST_SHA256,
            "current audit CLI test source mismatch")
    verifier_sha = digest(read(HERE / "verify.py"))
    binder = load(HERE / "binder-hardening-002/result.json")
    portable = load(HERE / "portability-002/result.json")
    require(binder["status"] == portable["status"] == "PASS", "hotfix control failed")
    require(binder["verifier_sha256"] == portable["verifier_sha256"] == verifier_sha,
            "hotfix verifier source mismatch")
    require(binder["runner_sha256"] == digest(read(HERE / "binder_negative.py")),
            "binder control source mismatch")
    require(portable["runner_sha256"] == digest(read(HERE / "portability_negative.py")),
            "portability control source mismatch")
    require(binder["accepted_audit_sha256"] == portable["accepted_audit_sha256"]
            == accepted_sha, "hotfix accepted-audit identity mismatch")
    require(portable["import_manifest_sha256"] == digest(
        read(HERE / "attempt-001/fresh-checker/toolchain-imports.json")
    ), "hotfix import manifest identity mismatch")
    require({r["case"] for r in binder["results"]} == EXPECTED_BINDER_CASES
            and len(binder["results"]) == 15, "binder case inventory mismatch")
    require({r["name"] for r in portable["results"]} == EXPECTED_PORTABILITY_CASES
            and len(portable["results"]) == 3, "portability case inventory mismatch")
    for row in binder["results"]:
        name = row["case"]
        expected_exit = 0 if name == "baseline" else 1
        require(row["status"] == "PASS" and row["exit_code"] == expected_exit
                and row["timed_out"] is False, f"binder case failed: {name}")
        for stream in ("stdout", "stderr"):
            actual = digest(read(HERE / "binder-hardening-002" / name / stream))
            require(actual == row[f"{stream}_sha256"],
                    f"binder case stream mismatch: {name}/{stream}")
    for row in portable["results"]:
        name = row["name"]
        expected_exit = 0 if name == "relocated_valid" else 1
        require(row["status"] == "PASS" and row["exit_code"] == expected_exit
                and row["timed_out"] is False, f"portability case failed: {name}")
        for stream in ("stdout", "stderr"):
            actual = digest(read(HERE / "portability-002" / f"{name}.{stream}"))
            require(actual == row[f"{stream}_sha256"],
                    f"portability case stream mismatch: {name}/{stream}")
    require(binder["REFINEMENT_PROVED"] == portable["REFINEMENT_PROVED"] == "OPEN",
            "hotfix receipt promotes refinement")
    return {
        "status": "HOTFIX_RECEIPTS_MATCH",
        "evidence_files": EXPECTED_FILES,
        "binder_cases": 15,
        "portability_cases": 3,
        "refinement": "OPEN",
    }


if __name__ == "__main__":
    try:
        print(json.dumps(verify(), sort_keys=True))
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}))
        raise SystemExit(1) from None
