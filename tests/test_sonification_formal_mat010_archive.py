"""Source binding and finite archive-membership boundary controls."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from formal.sonification.mat010 import conformance, source_bind


class Mat010ArchiveEvidenceTests(unittest.TestCase):
    def test_frozen_source_binding(self) -> None:
        result = source_bind.verify()
        self.assertEqual(result["status"], "SOURCE_SYNTAX_MATCH")
        self.assertEqual(result["REFINEMENT_PROVED"], "OPEN")

    def test_changed_source_manifest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mat010-source-control-") as temp:
            copied = Path(temp) / "SOURCE_BINDING.json"
            shutil.copyfile(source_bind.HERE / "SOURCE_BINDING.json", copied)
            copied.write_text(copied.read_text().replace(
                '"REFINEMENT_PROVED": "OPEN"',
                '"REFINEMENT_PROVED": "PASS"',
            ))
            with (
                patch.object(source_bind, "HERE", Path(temp)),
                self.assertRaisesRegex(ValueError, "source manifest changed"),
            ):
                source_bind.verify()

    def test_exact_builtin_cases_and_subclass_counterexamples(self) -> None:
        result = conformance.execute()
        self.assertEqual(result["status"], "PASS_WITH_BOUNDARY_COUNTEREXAMPLES")
        self.assertEqual(result["case_count"], 28)
        self.assertEqual(result["exact_builtin_passed"], 23)
        self.assertEqual(set(result["boundary_counterexamples"]),
                         conformance.COUNTEREXAMPLES)
        rows = {row["case"]: row for row in result["cases"]}
        for name in ("extra_well_formed_member", "missing_non_evidence_member"):
            self.assertEqual(rows[name]["observed"], "ACCEPT")
        self.assertEqual(rows["disallowed_mid_stage002"]["observed"], "ValueError")
        self.assertEqual(rows["subclass_mid_suffix_override"]["observed"], "ACCEPT")


if __name__ == "__main__":
    unittest.main()
