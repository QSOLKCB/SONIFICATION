"""Regression coverage for historical Python relative-import inventory navigation."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from formal.sonification.tools.inventory import generate, resolve_python_relative_import

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "formal/sonification/SOURCE_INVENTORY.json"


class PythonRelativeImports(unittest.TestCase):
    def test_package_initializer_stays_in_its_package(self) -> None:
        self.assertEqual(
            resolve_python_relative_import(
                "sonification/core/synthesis/__init__.py", "additive", 1
            ),
            "sonification.core.synthesis.additive",
        )
        self.assertEqual(
            resolve_python_relative_import(
                "sonification/core/math/__init__.py", "", 1
            ),
            "sonification.core.math",
        )

    def test_double_dot_ascends_one_package_from_initializer(self) -> None:
        self.assertEqual(
            resolve_python_relative_import(
                "sonification/core/synthesis/__init__.py", "base", 2
            ),
            "sonification.core.base",
        )

    def test_regular_module_is_resolved_from_containing_package(self) -> None:
        self.assertEqual(
            resolve_python_relative_import(
                "sonification/core/synthesis/helper.py", "additive", 1
            ),
            "sonification.core.synthesis.additive",
        )
        self.assertEqual(
            resolve_python_relative_import(
                "sonification/core/synthesis/helper.py", "math", 2
            ),
            "sonification.core.math",
        )

    def test_absolute_and_invalid_relative_imports(self) -> None:
        self.assertEqual(
            resolve_python_relative_import("sonification/core/helper.py", "json", 0),
            "json",
        )
        self.assertIsNone(
            resolve_python_relative_import(
                "sonification/core/synthesis/__init__.py", "outside", 4
            )
        )
        self.assertIsNone(resolve_python_relative_import("__init__.py", "outside", 1))
        self.assertIsNone(resolve_python_relative_import("top.py", "outside", 1))

    def test_full_generator_replays_committed_inventory(self) -> None:
        # CI's full-history checkout reproduces the pinned source inventory.
        _manifest, generated, _markdown = generate(ROOT)
        expected = INVENTORY.read_bytes()
        observed = (json.dumps(generated, sort_keys=True, indent=2) + "\n").encode("utf-8")
        self.assertEqual(
            hashlib.sha256(observed).hexdigest(),
            hashlib.sha256(expected).hexdigest(),
        )

    def test_all_snapshots_have_expected_package_import_edges(self) -> None:
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        targets = {
            "sonification/core/synthesis/__init__.py": (
                "sonification/core/synthesis/additive.py"
            ),
            "sonification/core/math/__init__.py": (
                "sonification/core/math/prng.py"
            ),
            "sonification/core/sequencing/__init__.py": (
                "sonification/core/sequencing/events.py"
            ),
        }
        verified = {path: set() for path in targets}
        for module in inventory["modules"]:
            expected = targets.get(module["path"])
            if expected is None:
                continue
            for snapshot in module["snapshots"]:
                with self.subTest(path=module["path"], snapshot=snapshot):
                    edges = module["dependency_edges_by_snapshot"][snapshot]
                    self.assertIn(expected, {edge["target"] for edge in edges})
                    verified[module["path"]].add(snapshot)
        for path in targets:
            self.assertEqual(
                len(verified[path]), inventory["counts"]["snapshots"], path
            )


if __name__ == "__main__":
    unittest.main()
