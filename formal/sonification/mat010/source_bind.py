#!/usr/bin/env python3
"""Bind the frozen MAT-SPEC-010 source and named function spans.

This is byte and syntax identity, not CPython refinement or source authenticity.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MANIFEST_SHA256 = "63ba2c981666a8854f01f43cceb0301a5e7d211d66738aa67b78457351eb38c7"
SOURCE_COMMIT = "9d12c6a5098f4edba972bb6b1067555d8f48f693"
PARENT_COMMIT = "0758a96360726aafbb07abed34620eda178407ae"
FUNCTIONS = {
    "ancestor_artifact_maps", "validate_archive_membership", "verify_parent",
    "science_closure", "build_evidence",
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def git(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, timeout=30
    ).stdout


def verify() -> dict:
    manifest_file = HERE / "SOURCE_BINDING.json"
    require(manifest_file.is_file() and not manifest_file.is_symlink(),
            "missing ordinary MAT010 source manifest")
    raw_manifest = manifest_file.read_bytes()
    require(sha(raw_manifest) == MANIFEST_SHA256, "MAT010 source manifest changed")
    manifest = json.loads(raw_manifest)
    require(manifest["schema"] == "sonification-mat010-source-binding/v1" and
            manifest["assurance"] == {
                "source": "SOURCE_SYNTAX_PINNED_ONLY", "REFINEMENT_PROVED": "OPEN"
            }, "MAT010 source assurance changed")
    release = manifest["frozen_release"]
    require(release == {
        "tag": "refs/tags/mat-spec-010-v0.1.0", "tag_type": "tag",
        "tag_object": "b8e88a0a32db30558e00704669eeaafee3a8d5f5",
        "peeled_commit": SOURCE_COMMIT,
        "tree": "646f1de532738feeb59336a427881d643cf32dc1",
    }, "MAT010 release identity changed")
    require(git("cat-file", "-t", release["tag"]).strip() == b"tag" and
            git("rev-parse", release["tag"]).strip() == release["tag_object"].encode() and
            git("rev-parse", release["tag"] + "^{commit}").strip() ==
            SOURCE_COMMIT.encode() and
            git("rev-parse", SOURCE_COMMIT + "^{tree}").strip() ==
            release["tree"].encode(),
            "frozen MAT010 tag or tree changed")
    require(manifest["immediate_predecessor"] == {
        "release": "mat-spec-009-v0.1.0", "commit": PARENT_COMMIT,
    } and git("cat-file", "-t", PARENT_COMMIT).strip() == b"commit" and
            git("rev-parse", "refs/tags/mat-spec-009-v0.1.0^{commit}").strip() ==
            PARENT_COMMIT.encode(), "MAT009 immediate predecessor changed")
    identity = manifest["module"]
    require(identity == {
        "path": "materials/mat_spec_010.py",
        "blob": "180e44dc81a0ff59cb08bd87d6a87538c275b054",
        "sha256": "e062474d4435e769f8c6c8407bc44ad89cfb2dfa04677b820c3a035d604a9056",
    }, "MAT010 module identity changed")
    require(git("rev-parse", f"{SOURCE_COMMIT}:{identity['path']}").strip() ==
            identity["blob"].encode(), "frozen MAT010 blob changed")
    frozen = git("show", f"{SOURCE_COMMIT}:{identity['path']}")
    require(sha(frozen) == identity["sha256"], "frozen MAT010 bytes changed")
    working = ROOT / identity["path"]
    require(working.is_file() and not working.is_symlink() and
            working.read_bytes() == frozen, "working MAT010 module differs from release")
    source = frozen.decode("utf-8")
    tree = ast.parse(source)
    spans = {}
    for name in FUNCTIONS:
        nodes = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name == name]
        require(len(nodes) == 1, f"missing or repeated function: {name}")
        node = nodes[0]
        segment = ast.get_source_segment(source, node)
        require(segment is not None, f"missing source span: {name}")
        spans[name] = {
            "start_line": node.lineno, "end_line": node.end_lineno,
            "ast_source_segment_sha256": sha(segment.encode("utf-8")),
        }
    require(spans == manifest["function_spans"], "MAT010 function spans changed")
    return {
        "status": "SOURCE_SYNTAX_MATCH", "release": release["tag"],
        "commit": SOURCE_COMMIT, "module_sha256": identity["sha256"],
        "functions": len(spans), "REFINEMENT_PROVED": "OPEN",
    }


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
