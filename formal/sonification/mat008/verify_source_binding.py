"""Verify the frozen MAT-SPEC-008 source and context-file identities."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MANIFEST_SHA256 = "0745c4178e6c06e8e16f0028eddf2152c480088daa3c35b36d96b5053d7bd0d4"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git(*args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=True,
        capture_output=True,
        timeout=30,
    ).stdout


def verify() -> dict:
    manifest_path = HERE / "SOURCE_BINDING.json"
    if sha(manifest_path.read_bytes()) != MANIFEST_SHA256:
        raise ValueError("MAT-SPEC-008 source-binding manifest changed")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    release = manifest["frozen_release"]
    target = manifest["target"]
    commit = release["peeled_commit"]
    if manifest["assurance"] != "SOURCE_PINNED_ONLY":
        raise ValueError("source binding overstates assurance")
    for ref, expected in (
        (release["tag"], release["tag_object"]),
        (release["tag"] + "^{commit}", commit),
        (release["tag"] + "^{tree}", release["tree"]),
    ):
        if git("rev-parse", ref).decode("ascii").strip() != expected:
            raise ValueError(f"frozen MAT-SPEC-008 Git identity mismatch: {ref}")
    files = manifest["context_file_identities"]
    if len(files) != 14 or len({item["path"] for item in files}) != 14:
        raise ValueError("MAT-SPEC-008 context file inventory changed")
    for item in files:
        raw = git("show", f"{commit}:{item['path']}")
        blob = git("rev-parse", f"{commit}:{item['path']}").decode("ascii").strip()
        if (
            len(raw) != item["bytes"]
            or sha(raw) != item["sha256"]
            or blob != item["git_blob"]
            or item["commit"] != commit
        ):
            raise ValueError(f"frozen context file mismatch: {item['path']}")
    raw = git("show", f"{commit}:{target['path']}")
    if sha(raw) != target["sha256"]:
        raise ValueError("frozen target source SHA-256 mismatch")
    text = raw.decode("utf-8")
    lines = raw.splitlines(keepends=True)
    spans = {}
    for node in ast.parse(text).body:
        if isinstance(node, ast.FunctionDef) and node.name in target["spans"]:
            spans[node.name] = {
                "start_line": node.lineno,
                "end_line": node.end_lineno,
                "ast_source_segment_sha256": sha(ast.get_source_segment(text, node).encode()),
                "inclusive_line_span_sha256": sha(
                    b"".join(lines[node.lineno - 1 : node.end_lineno])
                ),
            }
    if spans != target["spans"] or target["symbol"] not in spans:
        raise ValueError("frozen MAT-SPEC-008 function spans changed")
    return {"status": "SOURCE_BINDING_MATCH", "commit": commit, "context_files": 14}


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
