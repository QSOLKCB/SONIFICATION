"""Isolated source-blob mutation control for the MAT009 frozen-source binder."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from formal.sonification.mat009.source import source_bind


class Mat009SourceMutationTests(unittest.TestCase):
    def test_changed_frozen_python_module_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mat009-source-mutation-") as temp:
            checkout = Path(temp) / "frozen-checkout"
            subprocess.run(
                ["git", "worktree", "add", "--detach", str(checkout), source_bind.COMMIT],
                cwd=source_bind.ROOT, check=True, capture_output=True,
            )
            target = checkout / "materials/mat_spec_009.py"
            original = target.read_bytes()
            try:
                with patch.object(source_bind, "ROOT", checkout):
                    self.assertEqual(source_bind.verify()["status"], "SOURCE_SYNTAX_MATCH")
                    mutant = original.replace(
                        b"CAMPAIGN_CROSSES_TRAIN_HOLDOUT",
                        b"CAMPAIGN_CROSSES_TRAIN_HOLDOUT_MUTANT",
                        1,
                    )
                    self.assertNotEqual(mutant, original)
                    target.write_bytes(mutant)
                    with self.assertRaisesRegex(ValueError, "working-tree target differs"):
                        source_bind.verify()
            finally:
                target.write_bytes(original)
                subprocess.run(
                    ["git", "worktree", "remove", str(checkout)],
                    cwd=source_bind.ROOT, check=True, capture_output=True,
                )


if __name__ == "__main__":
    unittest.main()
