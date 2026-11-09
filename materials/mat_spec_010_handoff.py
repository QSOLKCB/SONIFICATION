"""Corrected post-release MAT-SPEC-010 handoff and Zenodo package.

SPDX-License-Identifier: MPL-2.0

The immutable GitHub release remains reproducible with the original builder
embedded in that release.  This separate builder retains that verified payload
and adds the pinned package initializer omitted from its repository-source
subtree, so the deposited source can import the MAT-SPEC implementation without
recovering that byte from Git.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from materials import mat_spec_010_archive as release_archive

ARCHIVE_NAME = "MAT-SPEC-010-v0.1.0-zenodo-deposit.zip"
IMMUTABLE_RELEASE_NAME = release_archive.ARCHIVE_NAME
IMMUTABLE_RELEASE_BYTES = 3_161_581
IMMUTABLE_RELEASE_SHA256 = (
    "c135f24c4a51a91444e2645c4850f326620dc54cb95b3b98d9bbae6d59235993"
)
INITIALIZER_PATH = "materials/__init__.py"
INITIALIZER_BYTES = 133
INITIALIZER_SHA256 = (
    "1a7d56f6231fc6ae77ef7701785939aca31327719ae85a31b0ebe32c7ce90055"
)


def add_supplemental_source(
    payload: dict[str, bytes], source_root: Path
) -> dict[str, Any]:
    """Add the exact pinned package initializer omitted by the logical index."""
    raw = (source_root / INITIALIZER_PATH).read_bytes()
    if len(raw) != INITIALIZER_BYTES or release_archive.sha256(raw) != INITIALIZER_SHA256:
        raise ValueError("pinned materials package initializer mismatch")
    member = f"source/repository/{INITIALIZER_PATH}"
    if member in payload:
        raise ValueError("supplemental source collides with an indexed archive member")
    payload[member] = raw
    return {
        "path": INITIALIZER_PATH,
        "materialized_path": member,
        "bytes": len(raw),
        "sha256": INITIALIZER_SHA256,
        "reason": "required package initializer omitted by the frozen logical source index",
    }


def assemble_payload(
    *,
    publication_root: Path,
    source_root: Path,
    source_identity: dict[str, str],
    stages: dict[int, dict[str, bytes]],
    test_receipt: bytes,
    python: str,
) -> dict[str, bytes]:
    """Extend the byte-verified release payload without altering that release."""
    payload = release_archive.assemble_payload(
        publication_root=publication_root,
        source_root=source_root,
        source_identity=source_identity,
        stages=stages,
        test_receipt=test_receipt,
        python=python,
    )
    supplemental = add_supplemental_source(payload, source_root)
    for archive_path, repository_path in (
        (
            "HANDOFF_README.md",
            "docs/MAT_SPEC_010_ARCHIVE_HANDOFF.md",
        ),
        (
            "tooling/build_mat_spec_010_handoff.py",
            "scripts/build_mat_spec_010_handoff.py",
        ),
        (
            "tooling/mat_spec_010_handoff.py",
            "materials/mat_spec_010_handoff.py",
        ),
    ):
        if archive_path in payload:
            raise ValueError(f"handoff tooling path already occupied: {archive_path}")
        payload[archive_path] = (publication_root / repository_path).read_bytes()

    receipt_path = "provenance/build-receipt.json"
    receipt = json.loads(payload[receipt_path])
    receipt.update(
        {
            "archive_filename": ARCHIVE_NAME,
            "publication_state": "POST_RELEASE_HANDOFF_PREPARED_NOT_PUBLISHED",
            "supplemental_repository_inputs_materialized": 1,
            "total_repository_inputs_materialized": (
                receipt["repository_inputs_materialized"] + 1
            ),
            "immutable_release_parent": {
                "filename": IMMUTABLE_RELEASE_NAME,
                "bytes": IMMUTABLE_RELEASE_BYTES,
                "sha256": IMMUTABLE_RELEASE_SHA256,
                "state": "VERIFIED_REPRODUCIBLE_UNCHANGED",
            },
            "post_release_correction": supplemental,
        }
    )
    payload[receipt_path] = release_archive.canonical_json(receipt)
    payload["provenance/post-release-handoff.json"] = release_archive.canonical_json(
        {
            "schema": "qsol.mat-spec-010.post-release-handoff/v1",
            "source_tag": release_archive.SOURCE_TAG,
            "source_commit": release_archive.SOURCE_COMMIT,
            "immutable_release": receipt["immutable_release_parent"],
            "correction": supplemental,
            "claim_boundary": (
                "Packaging completeness correction only; no scientific result, "
                "admission gate, release tag or immutable release asset is changed."
            ),
        }
    )
    return payload


def build_archive(
    *, repository: Path, publication_root: Path, output: Path, python: str
) -> dict[str, Any]:
    """Build and verify the corrected post-release deposit in a clean tag tree."""
    with tempfile.TemporaryDirectory(prefix="mat-spec-010-handoff-source-") as temporary:
        source_root = Path(temporary)
        identity = release_archive.resolve_source(repository, source_root)
        test_receipt = release_archive.execute_tests(source_root, python)
        stages = release_archive.execute_builders(source_root, python)
        payload = assemble_payload(
            publication_root=publication_root,
            source_root=source_root,
            source_identity=identity,
            stages=stages,
            test_receipt=test_receipt,
            python=python,
        )
        build = release_archive.write_archive(output, payload)
    verification = release_archive.verify_archive(output)
    for key in ("archive", "bytes", "sha256", "members"):
        if build[key] != verification[key]:
            raise ValueError("post-build handoff verification summary mismatch")
    build["archive_filename"] = ARCHIVE_NAME
    build["immutable_release_parent_sha256"] = IMMUTABLE_RELEASE_SHA256
    return {"build": build, "verification": verification}
