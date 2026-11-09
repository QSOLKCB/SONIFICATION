"""Post-release MAT-SPEC-010 handoff packaging controls."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath

from materials import mat_spec_010_archive as release_archive
from materials import mat_spec_010_handoff as handoff

ROOT = Path(__file__).resolve().parents[1]


class MatSpec010HandoffTests(unittest.TestCase):
    def test_initializer_is_exactly_pinned_and_materialized(self) -> None:
        payload = {
            "source/repository/materials/mat_spec.py":
                (ROOT / "materials/mat_spec.py").read_bytes()
        }
        record = handoff.add_supplemental_source(payload, ROOT)
        member = "source/repository/materials/__init__.py"
        self.assertIn(member, payload)
        self.assertEqual(len(payload[member]), handoff.INITIALIZER_BYTES)
        self.assertEqual(release_archive.sha256(payload[member]), handoff.INITIALIZER_SHA256)
        self.assertEqual(record["materialized_path"], member)

    def test_materialized_package_imports_without_external_source(self) -> None:
        payload = {
            "source/repository/materials/mat_spec.py":
                (ROOT / "materials/mat_spec.py").read_bytes()
        }
        handoff.add_supplemental_source(payload, ROOT)
        with tempfile.TemporaryDirectory() as temporary:
            source_root = Path(temporary)
            prefix = PurePosixPath("source/repository")
            for name, raw in payload.items():
                relative = PurePosixPath(name).relative_to(prefix)
                output = source_root.joinpath(*relative.parts)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(raw)
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "from materials import __version__; "
                        "from materials import mat_spec; "
                        "assert __version__ == '1.0.0'; "
                        "assert mat_spec.__version__ == __version__"
                    ),
                ],
                cwd=source_root,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_release_identity_is_preserved_as_parent(self) -> None:
        self.assertEqual(handoff.IMMUTABLE_RELEASE_NAME, release_archive.ARCHIVE_NAME)
        self.assertEqual(
            handoff.IMMUTABLE_RELEASE_SHA256,
            "c135f24c4a51a91444e2645c4850f326620dc54cb95b3b98d9bbae6d59235993",
        )
        self.assertNotEqual(handoff.ARCHIVE_NAME, handoff.IMMUTABLE_RELEASE_NAME)


if __name__ == "__main__":
    unittest.main()
