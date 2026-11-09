"""SPARK-001 Zenodo archive controls. SPDX-License-Identifier: MPL-2.0"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from materials import spark_001_archive as archive

ROOT = Path(__file__).resolve().parents[1]


class SparkArchiveTests(unittest.TestCase):
    def test_annotated_source_tag_resolves_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            identity = archive.resolve_source(ROOT, Path(temporary))
        self.assertEqual(identity["tag"], archive.SOURCE_TAG)
        self.assertEqual(identity["peeled_commit_sha1"], archive.SOURCE_COMMIT)
        self.assertEqual(len(identity["tag_object_sha1"]), 40)
        self.assertEqual(len(identity["git_archive_tar_sha256"]), 64)

    def test_deterministic_primary_zip_and_extraction(self) -> None:
        payload = {
            "ARCHIVE_README.md": b"SPARK-001\n",
            "source/example.adb": b"procedure Example is begin null; end Example;\n",
        }
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first.zip"
            second = Path(temporary) / "second.zip"
            one = archive.write_archive(first, payload)
            two = archive.write_archive(second, payload)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(one["sha256"], two["sha256"])
            verified = archive.verify_archive(first)
        self.assertTrue(verified["extraction_verified"])
        self.assertEqual(verified["rendered_audio_members"], 0)

    def test_rendered_audio_and_unsafe_paths_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(ValueError, "rendered audio"):
                archive.write_archive(root / "bad.zip", {"audio.wav": b""})
            with self.assertRaisesRegex(ValueError, "unsafe archive"):
                archive.write_archive(root / "unsafe.zip", {"../bad.json": b"{}"})

    def test_zenodo_metadata_is_separate_and_unpublished(self) -> None:
        metadata = json.loads(
            (ROOT / "publication/spark-001/zenodo-metadata.json").read_bytes()
        )
        self.assertEqual(metadata["metadata"]["resource_type"]["id"], "software")
        self.assertEqual(metadata["metadata"]["version"], "1.0.0")
        self.assertIsNone(metadata["record"]["id"])
        self.assertIsNone(metadata["record"]["reserved_doi"])
        self.assertTrue(metadata["record"]["publication_requires_owner_approval"])


if __name__ == "__main__":
    unittest.main()
