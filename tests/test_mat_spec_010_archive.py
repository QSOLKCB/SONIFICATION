"""Publication-archive controls for the frozen MAT-SPEC-010 source tag.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from materials import mat_spec_010_archive as archive

ROOT = Path(__file__).resolve().parents[1]


def source_tag_available() -> bool:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "cat-file",
            "-e",
            f"refs/tags/{archive.SOURCE_TAG}^{{commit}}",
        ],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


class ArchivePublicationTests(unittest.TestCase):
    def test_annotated_source_tag_resolves_exactly(self) -> None:
        if not source_tag_available():
            self.skipTest("integration check requires the fetched MAT-SPEC-010 tag")
        with tempfile.TemporaryDirectory() as temporary:
            identity = archive.resolve_source(ROOT, Path(temporary))
        self.assertEqual(identity["tag"], archive.SOURCE_TAG)
        self.assertEqual(identity["peeled_commit_sha1"], archive.SOURCE_COMMIT)
        self.assertEqual(len(identity["tag_object_sha1"]), 40)
        self.assertEqual(len(identity["tree_sha1"]), 40)
        self.assertEqual(len(identity["git_archive_tar_sha256"]), 64)

    def test_deterministic_zip_checksums_and_extraction(self) -> None:
        payload = {
            "ARCHIVE_README.md": b"bounded archive\n",
            "data/example.json": b'{"value":1}\n',
        }
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first.zip"
            second = Path(temporary) / "second.zip"
            one = archive.write_archive(first, payload)
            two = archive.write_archive(second, payload)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(one["sha256"], two["sha256"])
            verified = archive.verify_archive(first)
        self.assertTrue(verified["canonical_member_order"])
        self.assertTrue(verified["fixed_member_metadata"])
        self.assertTrue(verified["extraction_verified"])
        self.assertEqual(verified["rendered_audio_members"], 0)

    def test_rendered_audio_and_unsafe_paths_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(ValueError, "rendered audio"):
                archive.write_archive(root / "audio.zip", {"bad.wav": b""})
            with self.assertRaisesRegex(ValueError, "unsafe archive"):
                archive.write_archive(root / "unsafe.zip", {"../bad.json": b"{}"})

    def test_publication_metadata_has_no_invented_record(self) -> None:
        metadata = json.loads(
            (ROOT / "publication/mat-spec-010/zenodo-metadata.json").read_bytes()
        )
        self.assertEqual(metadata["metadata"]["resource_type"]["id"], "dataset")
        self.assertEqual(metadata["metadata"]["version"], "0.1.0")
        self.assertIsNone(metadata["record"]["id"])
        self.assertIsNone(metadata["record"]["reserved_doi"])
        self.assertTrue(metadata["record"]["publication_requires_owner_approval"])

    def test_evidence_categories_reference_real_frozen_files(self) -> None:
        for paths in archive.EVIDENCE_CATEGORIES.values():
            for relative in paths:
                path = ROOT / relative
                self.assertTrue(path.is_file())
                self.assertFalse(path.is_symlink())


if __name__ == "__main__":
    unittest.main()
