"""Deterministic SPARK-001 Zenodo software archive builder.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import io
import json
import stat
import subprocess
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from materials.mat_spec_010_archive import (
    FIXED_ZIP_TIME,
    PROHIBITED_AUDIO_SUFFIXES,
    _extract_git_tar,
    _safe_archive_path,
    canonical_json,
    sha256,
)

PROFILE = "SPARK-001"
VERSION = "1.0.0"
SOURCE_TAG = "spark-001-v1.0.0"
SOURCE_COMMIT = "95cc7c455535c1c4562d4241f5b387c811d90e5d"
SOURCE_REPOSITORY = "https://github.com/QSOLKCB/SONIFICATION"
ARCHIVE_NAME = "SPARK-001-v1.0.0-zenodo-software.zip"
EVIDENCE_NAME = "SPARK-001-v1.0.0-proof-evidence.zip"
EVIDENCE_SHA256 = "69ae22cf1e88407c26e98e657ec80b92aba89b28f7bbd683887266e4dd0f23d8"

SOURCE_PATHS = (
    ".github/workflows/spark-001-proof.yml",
    ".github/workflows/spark-001.yml",
    "AGENTS.md",
    "AUTHORS.md",
    "LICENSE",
    "NOTICE",
    "docs/SPARK_001.md",
    "scripts/verify_spark_001.py",
    "tests/test_spark_001.py",
    "verification/spark/spark_core.adb",
    "verification/spark/spark_core.ads",
    "verification/spark/spark_core.gpr",
    "verification/spark/spark_probe.adb",
)


def _run(argv: list[str], cwd: Path) -> bytes:
    result = subprocess.run(
        argv,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise ValueError(
            f"command failed ({result.returncode}): {argv!r}\n"
            + result.stderr.decode("utf-8", "replace")
        )
    return result.stdout


def _git(repository: Path, *args: str) -> bytes:
    return _run(["git", "-C", str(repository), *args], repository)


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


def _checksum_map(raw: bytes) -> dict[str, str]:
    result = {}
    for line in raw.decode("ascii").splitlines():
        digest, name = line.split("  ", 1)
        if len(digest) != 64 or name in result:
            raise ValueError("malformed evidence checksum list")
        result[name] = digest
    return result


def verify_evidence(evidence: bytes, source_root: Path) -> dict[str, Any]:
    if sha256(evidence) != EVIDENCE_SHA256:
        raise ValueError("SPARK-001 proof evidence ZIP SHA-256 mismatch")
    with zipfile.ZipFile(io.BytesIO(evidence), "r") as archive:
        if archive.testzip() is not None:
            raise ValueError("corrupt SPARK-001 proof evidence ZIP")
        members = {}
        for info in archive.infolist():
            path = _safe_archive_path(info.filename)
            if path.suffix.lower() in PROHIBITED_AUDIO_SUFFIXES:
                raise ValueError("rendered audio is prohibited in proof evidence")
            relative = PurePosixPath(*path.parts[1:])
            if not relative.parts:
                raise ValueError("invalid proof evidence member")
            members[str(relative)] = archive.read(info)
    bundle = _checksum_map(members["BUNDLE_SHA256SUMS"])
    if set(bundle) != set(members) - {"BUNDLE_SHA256SUMS"}:
        raise ValueError("proof evidence bundle membership mismatch")
    for name, digest in bundle.items():
        if sha256(members[name]) != digest:
            raise ValueError(f"proof evidence bundle checksum mismatch: {name}")
    original = _checksum_map(members["SHA256SUMS"])
    for name, digest in original.items():
        if sha256(members[name]) != digest:
            raise ValueError(f"original proof receipt checksum mismatch: {name}")
    source_hashes = _checksum_map(members["SOURCES.sha256"])
    for name, digest in source_hashes.items():
        if sha256((source_root / name).read_bytes()) != digest:
            raise ValueError(f"proof source mismatch: {name}")
    receipt = json.loads(members["RECEIPT_METADATA.json"])
    counts = receipt["count"]
    if (
        members["SOURCE_COMMIT.txt"].decode("ascii").strip() != SOURCE_COMMIT
        or receipt["source_commit_sha"] != SOURCE_COMMIT
        or receipt["recorded_gnatprove_exit_status"] != 0
        or receipt["proof_status"] != "ALL_26_REPORTED_GNATPROVE_CHECKS_PROVED"
        or counts != {
            "functional_contracts": 2,
            "justified": 0,
            "runtime_checks": 18,
            "termination": 6,
            "total": 26,
            "unproved": 0,
        }
        or receipt["coverage"]["Spark_Probe"] != "SPARK_Mode Off, excluded"
    ):
        raise ValueError("SPARK-001 proof receipt claims do not match the release")
    summary = members["GNATPROVE_SUMMARY.txt"].decode("utf-8")
    if "Total                            26" not in summary:
        raise ValueError("GNATprove summary total is absent")
    if "0 pragma Assume statements" not in summary:
        raise ValueError("GNATprove assumption report is absent")
    return {
        "outer_sha256": EVIDENCE_SHA256,
        "outer_bytes": len(evidence),
        "members": len(members),
        "bundle_checksums_verified": len(bundle),
        "original_receipt_checksums_verified": len(original),
        "source_checksums_verified": len(source_hashes),
        "gnatprove": {
            "version": "FSF 16.1.0",
            "runtime_checks": 18,
            "functional_contracts": 2,
            "termination_checks": 6,
            "total": 26,
            "unproved": 0,
            "pragma_assume_reported": 0,
            "recorded_exit_status": 0,
        },
        "spark_probe_formal_scope": False,
    }


def _publication_file(root: Path, relative: str) -> bytes:
    path = root / relative
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"missing publication workflow file: {relative}")
    return path.read_bytes()


def assemble_payload(
    *,
    publication_root: Path,
    source_root: Path,
    source_identity: dict[str, str],
    evidence: bytes,
) -> dict[str, bytes]:
    evidence_receipt = verify_evidence(evidence, source_root)
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
        _publication_file(publication_root, "publication/spark-001/ARCHIVE_README.md"),
    )
    for relative in SOURCE_PATHS:
        add(f"source/{relative}", (source_root / relative).read_bytes())
    add(f"evidence/{EVIDENCE_NAME}", evidence)
    with zipfile.ZipFile(io.BytesIO(evidence), "r") as proof:
        for info in proof.infolist():
            path = _safe_archive_path(info.filename)
            relative = PurePosixPath(*path.parts[1:])
            add(f"evidence/expanded/{relative}", proof.read(info))
    add(
        "publication/github-release-receipt.json",
        _publication_file(publication_root, "publication/spark-001/github-release.json"),
    )
    add(
        "publication/github-actions-receipts.json",
        _publication_file(publication_root, "publication/spark-001/ci-receipts.json"),
    )
    add(
        "tooling/build_spark_001_archive.py",
        _publication_file(publication_root, "scripts/build_spark_001_archive.py"),
    )
    add(
        "tooling/spark_001_archive.py",
        _publication_file(publication_root, "materials/spark_001_archive.py"),
    )
    source_manifest = {
        "schema": "qsol.spark-001.source-manifest/v1",
        "source": source_identity,
        "files": [
            {
                "path": relative,
                "bytes": len((source_root / relative).read_bytes()),
                "sha256": sha256((source_root / relative).read_bytes()),
            }
            for relative in SOURCE_PATHS
        ],
    }
    add("provenance/source-manifest.json", canonical_json(source_manifest))
    build_receipt = {
        "schema": "qsol.spark-001.zenodo-archive-build/v1",
        "profile": PROFILE,
        "version": VERSION,
        "archive_filename": ARCHIVE_NAME,
        "source": source_identity,
        "proof_evidence": evidence_receipt,
        "differential_ci_vectors": 372,
        "formal_scope": "Spark_Core declared properties only",
        "excluded_from_formal_scope": ["Spark_Probe"],
        "limitations": [
            "Parser postcondition is not a complete grammar-equivalence theorem",
            "Source identity comparison is not cryptographic authenticity",
            "No independent helium physical phase validation",
            "No E8 physical theory, audio perception result or material classifier",
        ],
        "publication_state": "PREPARED_NOT_PUBLISHED",
        "record_id": None,
        "doi": None,
        "sampled_audio_generated": False,
    }
    add("provenance/build-receipt.json", canonical_json(build_receipt))
    return payload


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(filename=name, date_time=FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    info.flag_bits |= 0x800
    return info


def _manifest(payload: dict[str, bytes]) -> bytes:
    return canonical_json(
        {
            "schema": "qsol.spark-001.zenodo-archive-manifest/v1",
            "profile": PROFILE,
            "version": VERSION,
            "source_tag": SOURCE_TAG,
            "source_commit": SOURCE_COMMIT,
            "payload_file_count": len(payload),
            "files": [
                {"path": name, "bytes": len(raw), "sha256": sha256(raw)}
                for name, raw in sorted(payload.items())
            ],
            "manifest_self_hash": None,
            "sha256sums_self_hash": None,
            "sampled_audio_generated": False,
        }
    )


def write_archive(output: Path, payload: dict[str, bytes]) -> dict[str, Any]:
    for name in payload:
        _safe_archive_path(name)
        if PurePosixPath(name).suffix.lower() in PROHIBITED_AUDIO_SUFFIXES:
            raise ValueError(f"rendered audio is prohibited: {name}")
    payload = dict(payload)
    payload["provenance/archive-manifest.json"] = _manifest(payload)
    payload["provenance/SHA256SUMS"] = "".join(
        f"{sha256(raw)}  {name}\n" for name, raw in sorted(payload.items())
    ).encode("ascii")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as raw_output:
        with zipfile.ZipFile(raw_output, "w", compression=zipfile.ZIP_STORED) as archive:
            for name, raw in sorted(payload.items()):
                archive.writestr(_zip_info(name), raw)
    raw = output.read_bytes()
    return {
        "archive": str(output),
        "bytes": len(raw),
        "sha256": sha256(raw),
        "members": len(payload),
        "source_tag": SOURCE_TAG,
        "source_commit": SOURCE_COMMIT,
    }


def verify_archive(path: Path) -> dict[str, Any]:
    raw_archive = path.read_bytes()
    with zipfile.ZipFile(io.BytesIO(raw_archive), "r") as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if names != sorted(names) or len(names) != len(set(names)):
            raise ValueError("archive members are not canonical and unique")
        for info in infos:
            _safe_archive_path(info.filename)
            if info.date_time != FIXED_ZIP_TIME or info.compress_type != zipfile.ZIP_STORED:
                raise ValueError("archive metadata is not deterministic")
            if PurePosixPath(info.filename).suffix.lower() in PROHIBITED_AUDIO_SUFFIXES:
                raise ValueError("rendered audio member found")
        members = {name: archive.read(name) for name in names}
    checksums = _checksum_map(members["provenance/SHA256SUMS"])
    if set(checksums) != set(members) - {"provenance/SHA256SUMS"}:
        raise ValueError("archive checksum membership mismatch")
    for name, digest in checksums.items():
        if sha256(members[name]) != digest:
            raise ValueError(f"archive checksum mismatch: {name}")
    manifest = json.loads(members["provenance/archive-manifest.json"])
    for record in manifest["files"]:
        raw = members.get(record["path"])
        if raw is None or len(raw) != record["bytes"] or sha256(raw) != record["sha256"]:
            raise ValueError(f"archive manifest mismatch: {record['path']}")
    with tempfile.TemporaryDirectory(prefix="spark-001-verify-") as temporary:
        root = Path(temporary)
        for name, raw in members.items():
            target = root.joinpath(*PurePosixPath(name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as output:
                output.write(raw)
        for name, digest in checksums.items():
            if sha256(root.joinpath(*PurePosixPath(name).parts).read_bytes()) != digest:
                raise ValueError(f"extracted checksum mismatch: {name}")
    return {
        "archive": str(path),
        "bytes": len(raw_archive),
        "sha256": sha256(raw_archive),
        "members": len(members),
        "checksums_verified": len(checksums),
        "extraction_verified": True,
        "rendered_audio_members": 0,
    }


def build_archive(
    *, repository: Path, publication_root: Path, evidence_path: Path, output: Path
) -> dict[str, Any]:
    evidence = evidence_path.read_bytes()
    with tempfile.TemporaryDirectory(prefix="spark-001-source-") as temporary:
        source_root = Path(temporary)
        identity = resolve_source(repository, source_root)
        payload = assemble_payload(
            publication_root=publication_root,
            source_root=source_root,
            source_identity=identity,
            evidence=evidence,
        )
        build = write_archive(output, payload)
    verification = verify_archive(output)
    for key in ("archive", "bytes", "sha256", "members"):
        if build[key] != verification[key]:
            raise ValueError("post-build archive verification summary mismatch")
    return {"build": build, "verification": verification}
