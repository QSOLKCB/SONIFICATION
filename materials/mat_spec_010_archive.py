"""Deterministic external archive for the frozen MAT-SPEC-001--010 chain.

SPDX-License-Identifier: MPL-2.0

This publication workflow is intentionally separate from the frozen
MAT-SPEC-010 logical archive index.  It resolves the immutable annotated tag,
extracts that exact Git tree, executes the original builders and tests, and
then materializes every indexed artifact as bytes in a deterministic ZIP.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import stat
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

PROFILE = "MAT-SPEC-010"
VERSION = "0.1.0"
SOURCE_TAG = "mat-spec-010-v0.1.0"
SOURCE_COMMIT = "9d12c6a5098f4edba972bb6b1067555d8f48f693"
SOURCE_REPOSITORY = "https://github.com/QSOLKCB/SONIFICATION"
ARCHIVE_NAME = "MAT-SPEC-010-v0.1.0-research-archive.zip"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
PROHIBITED_AUDIO_SUFFIXES = {
    ".wav", ".pcm", ".aiff", ".aif", ".flac", ".mp3", ".ogg", ".opus",
}

STAGE_BUILDERS = {
    1: "scripts/build_mat_spec.py",
    **{n: f"scripts/build_mat_spec_{n:03d}.py" for n in range(2, 11)},
}

EVIDENCE_CATEGORIES = {
    "published-measurements": (
        "data/materials/helium4/DispersionAllPressures.txt",
        "data/materials/helium4/source.json",
        "data/materials/helium4/lipa_chui_1984_excerpt.csv",
        "data/materials/helium4/lipa_chui_1984.source.json",
    ),
    "model-inputs": (
        "data/materials/helium4/temperature_table1_2022.csv",
        "data/materials/helium4/temperature_table1_2022.source.json",
    ),
    "evaluated-reference": (
        "data/materials/helium4/nist_svp_lambda_reference_1998.csv",
        "data/materials/helium4/nist_svp_lambda_reference_1998.source.json",
    ),
    "fitted-values": (
        "data/materials/helium4/mat_spec_007_svp_fit_summaries.csv",
        "data/materials/helium4/mat_spec_007_svp_fit_summaries.source.json",
    ),
    "source-attribution": (
        "data/materials/helium4/mat_spec_006_source_inventory.json",
        "data/materials/helium4/mat_spec_008_source_catalogue.json",
        "data/materials/helium4/mat_spec_010_source_inventory.json",
        "data/materials/helium4/mat_spec_010_claim_registry.json",
    ),
}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("ascii")


def _run(
    argv: list[str], *, cwd: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[bytes]:
    complete_env = os.environ.copy()
    complete_env["PYTHONDONTWRITEBYTECODE"] = "1"
    if env:
        complete_env.update(env)
    result = subprocess.run(
        argv,
        cwd=cwd,
        env=complete_env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        stderr = result.stderr.decode("utf-8", "replace")
        stdout = result.stdout.decode("utf-8", "replace")
        raise ValueError(
            f"command failed ({result.returncode}): {argv!r}\n{stdout}\n{stderr}"
        )
    return result


def _git(repository: Path, *args: str) -> bytes:
    return _run(["git", "-C", str(repository), *args], cwd=repository).stdout


def _safe_archive_path(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if (
        not name
        or path.is_absolute()
        or "\\" in name
        or any(part in ("", ".", "..") for part in path.parts)
    ):
        raise ValueError(f"unsafe archive member path: {name!r}")
    return path


def _extract_git_tar(raw: bytes, destination: Path) -> None:
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
        for member in archive.getmembers():
            path = _safe_archive_path(member.name)
            target = destination.joinpath(*path.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                raise ValueError(f"non-regular Git archive member: {member.name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise ValueError(f"unreadable Git archive member: {member.name}")
            with target.open("xb") as output:
                output.write(source.read())


def resolve_source(repository: Path, destination: Path) -> dict[str, str]:
    tag_type = _git(repository, "cat-file", "-t", f"refs/tags/{SOURCE_TAG}").decode().strip()
    tag_object = _git(repository, "rev-parse", f"refs/tags/{SOURCE_TAG}").decode().strip()
    commit = _git(repository, "rev-parse", f"{SOURCE_TAG}^{{commit}}").decode().strip()
    tree = _git(repository, "rev-parse", f"{SOURCE_TAG}^{{tree}}").decode().strip()
    if tag_type != "tag" or commit != SOURCE_COMMIT:
        raise ValueError(
            f"{SOURCE_TAG} must be an annotated tag peeled to {SOURCE_COMMIT}"
        )
    source_tar = _git(repository, "archive", "--format=tar", SOURCE_TAG)
    _extract_git_tar(source_tar, destination)
    return {
        "repository": SOURCE_REPOSITORY,
        "tag": SOURCE_TAG,
        "tag_object_sha1": tag_object,
        "peeled_commit_sha1": commit,
        "tree_sha1": tree,
        "git_archive_tar_sha256": sha256(source_tar),
    }


TEST_RUNNER = r'''
import json
import sys
import unittest

class Receipt(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.outcomes = []
    def addSuccess(self, test):
        super().addSuccess(test)
        self.outcomes.append({"id": test.id(), "status": "PASS"})
    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.outcomes.append({"id": test.id(), "status": "FAIL"})
    def addError(self, test, err):
        super().addError(test, err)
        self.outcomes.append({"id": test.id(), "status": "ERROR"})
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.outcomes.append({"id": test.id(), "status": "SKIP"})

suite = unittest.defaultTestLoader.discover("tests", pattern="test_mat_spec*.py")
receipt = Receipt()
suite.run(receipt)
document = {
    "schema": "qsol.mat-spec.test-receipt/v1",
    "command": "python -m unittest discover -s tests -p test_mat_spec*.py",
    "tests_run": receipt.testsRun,
    "failures": len(receipt.failures),
    "errors": len(receipt.errors),
    "skipped": len(receipt.skipped),
    "successful": receipt.wasSuccessful(),
    "outcomes": receipt.outcomes,
}
print(json.dumps(document, sort_keys=True, separators=(",", ":")))
sys.exit(0 if receipt.wasSuccessful() else 1)
'''


def execute_tests(source_root: Path, python: str) -> bytes:
    result = _run([python, "-c", TEST_RUNNER], cwd=source_root)
    receipt = json.loads(result.stdout)
    if receipt != json.loads(canonical_json(receipt)):
        raise ValueError("test receipt is not JSON round-trip stable")
    if not receipt["successful"] or receipt["tests_run"] != 123:
        raise ValueError("frozen MAT-SPEC test suite did not pass all 123 tests")
    return canonical_json(receipt)


def execute_builders(source_root: Path, python: str) -> dict[int, dict[str, bytes]]:
    stages: dict[int, dict[str, bytes]] = {}
    for number, builder in STAGE_BUILDERS.items():
        output = f"dist/mat-spec-{number:03d}"
        _run([python, builder, "--out", output], cwd=source_root)
        directory = source_root / output
        members: dict[str, bytes] = {}
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if not path.is_file() or path.is_symlink():
                raise ValueError(f"unexpected generated member: {path}")
            if path.suffix not in {".json", ".csv", ".mid"}:
                raise ValueError(f"disallowed generated artifact: {path.name}")
            members[path.name] = path.read_bytes()
        if not members:
            raise ValueError(f"MAT-SPEC-{number:03d} generated no artifacts")
        stages[number] = members
    return stages


def verify_logical_index(stages: dict[int, dict[str, bytes]]) -> dict[str, Any]:
    archive = json.loads(stages[10]["archive-index.json"])
    verified = []
    for record in archive["ancestor_artifacts"]:
        number = int(record["stage"].removeprefix("MAT-SPEC-"))
        name = PurePosixPath(record["logical_path"]).name
        raw = stages.get(number, {}).get(name)
        if raw is None or sha256(raw) != record["sha256"]:
            raise ValueError(
                f"logical archive member is absent or mismatched: {record['logical_path']}"
            )
        verified.append(
            {
                "logical_path": record["logical_path"],
                "materialized_path": f"artifacts/MAT-SPEC-{number:03d}/{name}",
                "bytes": len(raw),
                "sha256": record["sha256"],
            }
        )
    if len(verified) != 63 or archive["ancestor_artifact_count"] != 63:
        raise ValueError("expected exactly 63 indexed MAT-SPEC-001--009 artifacts")
    return {
        "schema": "qsol.mat-spec.archive-index-cross-check/v1",
        "logical_index_status": archive["status"],
        "logical_members": len(verified),
        "all_logical_members_materialized": True,
        "members": verified,
    }


def _publication_file(publication_root: Path, relative: str) -> bytes:
    path = publication_root / relative
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"missing publication workflow file: {relative}")
    return path.read_bytes()


def assemble_payload(
    *,
    publication_root: Path,
    source_root: Path,
    source_identity: dict[str, str],
    stages: dict[int, dict[str, bytes]],
    test_receipt: bytes,
    python: str,
) -> dict[str, bytes]:
    payload: dict[str, bytes] = {}

    def add(name: str, raw: bytes) -> None:
        _safe_archive_path(name)
        if PurePosixPath(name).suffix.lower() in PROHIBITED_AUDIO_SUFFIXES:
            raise ValueError(f"rendered audio is prohibited: {name}")
        if name in payload:
            raise ValueError(f"duplicate archive path: {name}")
        payload[name] = raw

    add(
        "ARCHIVE_README.md",
        _publication_file(publication_root, "docs/MAT_SPEC_010_ARCHIVE.md"),
    )
    for name in ("LICENSE", "NOTICE", "AUTHORS.md"):
        add(name, (source_root / name).read_bytes())

    for number, members in sorted(stages.items()):
        for name, raw in sorted(members.items()):
            add(f"artifacts/MAT-SPEC-{number:03d}/{name}", raw)

    logical_cross_check = verify_logical_index(stages)
    add(
        "provenance/archive-index-cross-check.json",
        canonical_json(logical_cross_check),
    )

    archive_index = json.loads(stages[10]["archive-index.json"])
    for record in archive_index["repository_files"]:
        source_path = source_root / record["path"]
        raw = source_path.read_bytes()
        if len(raw) != record["bytes"] or sha256(raw) != record["sha256"]:
            raise ValueError(f"indexed repository source mismatch: {record['path']}")
        add(f"source/repository/{record['path']}", raw)

    for category, paths in sorted(EVIDENCE_CATEGORIES.items()):
        for relative in paths:
            add(f"evidence/{category}/{PurePosixPath(relative).name}", (source_root / relative).read_bytes())

    add(
        "evidence/synthetic-fixtures/synthetic-controls.csv",
        stages[9]["synthetic-controls.csv"],
    )
    add(
        "evidence/source-licences/SOURCE_RIGHTS.json",
        _publication_file(
            publication_root, "publication/mat-spec-010/source-rights.json"
        ),
    )
    add(
        "evidence/secondary-literature/REFERENCES.json",
        _publication_file(
            publication_root, "publication/mat-spec-010/references.json"
        ),
    )
    add(
        "tests/MAT-SPEC-001-010-test-receipt.json",
        test_receipt,
    )
    add(
        "tests/github-actions-receipts.json",
        _publication_file(
            publication_root, "publication/mat-spec-010/ci-receipts.json"
        ),
    )
    add(
        "tooling/build_mat_spec_010_archive.py",
        _publication_file(
            publication_root, "scripts/build_mat_spec_010_archive.py"
        ),
    )
    add(
        "tooling/mat_spec_010_archive.py",
        _publication_file(
            publication_root, "materials/mat_spec_010_archive.py"
        ),
    )

    python_info = json.loads(
        _run(
            [
                python,
                "-c",
                (
                    "import json,platform;"
                    "print(json.dumps({'implementation':platform.python_implementation(),"
                    "'version':platform.python_version()},sort_keys=True))"
                ),
            ],
            cwd=source_root,
        ).stdout
    )
    git_version = _run(["git", "--version"], cwd=source_root).stdout.decode().strip()
    build_receipt = {
        "schema": "qsol.mat-spec.research-archive-build/v1",
        "profile": PROFILE,
        "version": VERSION,
        "archive_filename": ARCHIVE_NAME,
        "source": source_identity,
        "toolchain": {
            "python_implementation": python_info["implementation"],
            "python_version": python_info["version"],
            "git": git_version,
            "zip_method": "ZIP_STORED",
        },
        "determinism": {
            "member_order": "lexicographic UTF-8 archive paths",
            "member_timestamp": "1980-01-01T00:00:00",
            "member_mode": "0644 regular file",
            "json": "sorted keys; compact separators; ASCII; LF",
        },
        "tests_run": json.loads(test_receipt)["tests_run"],
        "profiles_built": [f"MAT-SPEC-{number:03d}" for number in stages],
        "logical_artifacts_materialized": logical_cross_check["logical_members"],
        "repository_inputs_materialized": archive_index["repository_file_count"],
        "sampled_audio_generated": False,
        "rendered_audio_members": 0,
        "canonical_pcm_sha256": None,
        "canonical_wav_sha256": None,
        "doi": None,
        "publication_state": "PREPARED_NOT_PUBLISHED",
    }
    add("provenance/build-receipt.json", canonical_json(build_receipt))
    return payload


def _manifest(payload: dict[str, bytes]) -> bytes:
    records = [
        {"path": name, "bytes": len(raw), "sha256": sha256(raw)}
        for name, raw in sorted(payload.items())
    ]
    return canonical_json(
        {
            "schema": "qsol.mat-spec.research-archive-manifest/v1",
            "profile": PROFILE,
            "version": VERSION,
            "source_tag": SOURCE_TAG,
            "source_commit": SOURCE_COMMIT,
            "payload_file_count": len(records),
            "files": records,
            "manifest_self_hash": None,
            "sha256sums_self_hash": None,
            "sampled_audio_generated": False,
            "canonical_pcm_sha256": None,
            "canonical_wav_sha256": None,
        }
    )


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(filename=name, date_time=FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    info.flag_bits |= 0x800
    return info


def write_archive(output: Path, payload: dict[str, bytes]) -> dict[str, Any]:
    for name in payload:
        _safe_archive_path(name)
        if PurePosixPath(name).suffix.lower() in PROHIBITED_AUDIO_SUFFIXES:
            raise ValueError(f"rendered audio is prohibited: {name}")
    manifest = _manifest(payload)
    if "provenance/archive-manifest.json" in payload:
        raise ValueError("manifest path already occupied")
    payload = dict(payload)
    payload["provenance/archive-manifest.json"] = manifest
    checksums = "".join(
        f"{sha256(raw)}  {name}\n" for name, raw in sorted(payload.items())
    ).encode("ascii")
    payload["provenance/SHA256SUMS"] = checksums
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as raw_output:
        with zipfile.ZipFile(
            raw_output,
            mode="w",
            compression=zipfile.ZIP_STORED,
            allowZip64=True,
            strict_timestamps=True,
        ) as archive:
            for name, raw in sorted(payload.items()):
                archive.writestr(_zip_info(name), raw)
    raw_archive = output.read_bytes()
    return {
        "archive": str(output),
        "bytes": len(raw_archive),
        "sha256": sha256(raw_archive),
        "members": len(payload),
        "source_tag": SOURCE_TAG,
        "source_commit": SOURCE_COMMIT,
        "sampled_audio_generated": False,
    }


def verify_archive(path: Path) -> dict[str, Any]:
    raw_archive = path.read_bytes()
    with zipfile.ZipFile(io.BytesIO(raw_archive), "r") as archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        if names != sorted(names) or len(names) != len(set(names)):
            raise ValueError("archive members are not unique canonical order")
        for info in infos:
            _safe_archive_path(info.filename)
            if info.date_time != FIXED_ZIP_TIME or info.compress_type != zipfile.ZIP_STORED:
                raise ValueError("archive metadata is not deterministic")
            if PurePosixPath(info.filename).suffix.lower() in PROHIBITED_AUDIO_SUFFIXES:
                raise ValueError("rendered audio member found")
        members = {name: archive.read(name) for name in names}
    checksum_lines = members["provenance/SHA256SUMS"].decode("ascii").splitlines()
    expected = {
        name: digest
        for digest, name in (line.split("  ", 1) for line in checksum_lines)
    }
    if set(expected) != set(members) - {"provenance/SHA256SUMS"}:
        raise ValueError("SHA256SUMS membership mismatch")
    for name, digest in expected.items():
        if sha256(members[name]) != digest:
            raise ValueError(f"checksum mismatch: {name}")
    manifest = json.loads(members["provenance/archive-manifest.json"])
    for record in manifest["files"]:
        raw = members.get(record["path"])
        if raw is None or len(raw) != record["bytes"] or sha256(raw) != record["sha256"]:
            raise ValueError(f"manifest mismatch: {record['path']}")
    with tempfile.TemporaryDirectory(prefix="mat-spec-010-verify-") as temporary:
        root = Path(temporary)
        for name, raw in members.items():
            target = root.joinpath(*PurePosixPath(name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as output:
                output.write(raw)
        for name, digest in expected.items():
            if sha256(root.joinpath(*PurePosixPath(name).parts).read_bytes()) != digest:
                raise ValueError(f"extracted checksum mismatch: {name}")
    return {
        "archive": str(path),
        "bytes": len(raw_archive),
        "sha256": sha256(raw_archive),
        "members": len(members),
        "canonical_member_order": True,
        "fixed_member_metadata": True,
        "checksums_verified": len(expected),
        "extraction_verified": True,
        "rendered_audio_members": 0,
    }


def build_archive(
    *, repository: Path, publication_root: Path, output: Path, python: str
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="mat-spec-010-source-") as temporary:
        source_root = Path(temporary)
        source_identity = resolve_source(repository, source_root)
        test_receipt = execute_tests(source_root, python)
        stages = execute_builders(source_root, python)
        payload = assemble_payload(
            publication_root=publication_root,
            source_root=source_root,
            source_identity=source_identity,
            stages=stages,
            test_receipt=test_receipt,
            python=python,
        )
        summary = write_archive(output, payload)
    verification = verify_archive(output)
    for key in ("archive", "bytes", "sha256", "members"):
        if summary[key] != verification[key]:
            raise ValueError("post-build archive verification summary mismatch")
    return {"build": summary, "verification": verification}
