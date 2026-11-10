"""Verify frozen MAT009 split-gate syntax and its direct MAT008 dependency.

This binder checks Git bytes and selected AST structure. It is not a proof of
CPython semantics, source-to-model refinement, or scientific provenance.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MANIFEST_SHA256 = "baf3401c300c062a31596e68a6f595978a8810c0f0b9d361445c75764e042b91"
TAG = "refs/tags/mat-spec-009-v0.1.0"
TAG_OBJECT = "ad99d9e52f9ede423a4fb9d6a622624e32955263"
COMMIT = "0758a96360726aafbb07abed34620eda178407ae"
TREE = "a6a03e1227e666680d656b886201ee9dde9de32d"
TARGET = (
    "materials/mat_spec_009.py",
    "c447f0ce76b91acf458221390ac4261166145a0b",
    "a68089df7d1901fb7c17ffc2889b844b3573024aec4b66348f9c2ef71930c690",
)
PARENT = (
    "materials/mat_spec_008.py",
    "3117adbc3739c834f8203d5d2dd2b80d6caf862b",
    "e56563235d87da43293bc46661b077660538b476d2bb340a1d208cc59aaa5f08",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def unique_pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def git(*arguments: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(ROOT), *arguments],
        check=True,
        capture_output=True,
        timeout=30,
    ).stdout


def one_function(module: ast.Module, name: str) -> ast.FunctionDef:
    matches = [
        node for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    require(len(matches) == 1, f"expected one top-level function: {name}")
    return matches[0]


def same_statement(node: ast.AST, expected: str) -> bool:
    parsed = ast.parse(expected)
    require(len(parsed.body) == 1, "binder expected one statement")
    return ast.dump(node, include_attributes=False) == ast.dump(
        parsed.body[0], include_attributes=False
    )


def spans(raw: bytes, names: set[str]) -> tuple[dict, ast.Module]:
    source = raw.decode("utf-8")
    module = ast.parse(source)
    result = {}
    for name in sorted(names):
        node = one_function(module, name)
        segment = ast.get_source_segment(source, node)
        require(segment is not None, f"missing AST source segment: {name}")
        result[name] = {
            "start_line": node.lineno,
            "end_line": node.end_lineno,
            "ast_source_segment_sha256": sha256(segment.encode("utf-8")),
        }
    return result, module


def require_selected_ast_shape(target: ast.Module, parent: ast.Module) -> None:
    """Check the small interpretation inventory used by the source contract."""
    child = one_function(target, "check_future_challenge")
    require(len(child.body) == 18, "child top-level statement inventory changed")
    require(isinstance(child.body[1], ast.If)
            and ast.dump(child.body[1].test, include_attributes=False)
            == ast.dump(ast.parse(
                "not isinstance(records, list) or not records or len(records) > 10000",
                mode="eval",
            ).body, include_attributes=False),
            "child outer guard changed")
    require(same_statement(
        child.body[2],
        "parent = mat_spec_008.validate_future_measurement_packet(records)",
    ), "MAT008 parent call changed")
    require(same_statement(
        child.body[3], 'reasons = set(parent["reasons"])',
    ), "MAT008 reason union initialization changed")
    row_loop = child.body[11]
    require(isinstance(row_loop, ast.For) and isinstance(row_loop.iter, ast.Name)
            and row_loop.iter.id == "records" and len(row_loop.body) == 22,
            "child row-loop inventory changed")
    for index, expected in (
        (0, '''if not isinstance(record, dict):
    reasons.add("MALFORMED_CANDIDATE_RECORD")
    continue'''),
        (2, '''if role not in ("TRAIN", "HOLDOUT"):
    reasons.add("UNDECLARED_TRAIN_HOLDOUT_ROLE")
    continue'''),
        (4, '''if not _identifier(campaign) or not _identifier(lab):
    reasons.add("MISSING_EXPERIMENT_FAMILY_IDENTITY")
    continue'''),
    ):
        require(same_statement(row_loop.body[index], expected),
                f"child skip guard {index} changed")
    require(same_statement(row_loop.body[19], '''for identity, registry, valid in (
    (diagnostic_hash, diagnostic_hash_owners, _digest(diagnostic_hash)),
    (diagnostic_event_id, diagnostic_event_owners, _identifier(diagnostic_event_id)),
):
    if not valid:
        continue
    prior = registry.setdefault(identity, (campaign, role))
    if prior[0] != campaign:
        reasons.add("DIAGNOSTIC_PROVENANCE_REUSED_ACROSS_CAMPAIGNS")
    if prior[1] != role:
        reasons.add("DIAGNOSTIC_PROVENANCE_LEAKAGE_ACROSS_SPLITS")'''),
            "diagnostic first-owner gate changed")
    require(same_statement(child.body[16], "outcome = sorted(reasons)"),
            "normal reason sorting changed")
    require(isinstance(child.body[17], ast.Return)
            and isinstance(child.body[17].value, ast.Dict),
            "normal result shape changed")
    normal_keys = [
        key.value for key in child.body[17].value.keys
        if isinstance(key, ast.Constant)
    ]
    require(normal_keys == [
        "status", "reasons", "train_campaigns", "heldout_campaigns",
        "physical_evidence_admitted", "independence_authenticated",
        "heldout_accuracy", "trained_classifier", "meaning",
    ], "normal result keys changed")
    father = one_function(parent, "validate_future_measurement_packet")
    require(isinstance(father.body[13], ast.For)
            and isinstance(father.body[13].iter, ast.Name)
            and father.body[13].iter.id == "records", "parent row loop changed")
    require(same_statement(father.body[13].body[0], '''if not isinstance(row, dict):
    reasons.add("MALFORMED_CANDIDATE_RECORD")
    continue'''), "parent row type guard changed")
    require(same_statement(father.body[13].body[1], '''try:
    camp = _identity(row.get("campaign_id"))
    lab = _identity(row.get("lab_family_id"))
    run = _identity(row.get("original_run_id"))
    doc = _identity(row.get("source_document_id"))
    identifier = _identity(row.get("row_id"))
except ValueError:
    reasons.add("MISSING_OR_INVALID_SOURCE_IDENTITIES")
    continue'''), "parent identity skip guard changed")


def verify() -> dict:
    manifest_bytes = (HERE / "SOURCE_BINDING.json").read_bytes()
    require(sha256(manifest_bytes) == MANIFEST_SHA256,
            "MAT009 source binding manifest changed")
    manifest = json.loads(manifest_bytes, object_pairs_hook=unique_pairs)
    require(manifest["assurance"] == "SOURCE_SYNTAX_PINNED_ONLY"
            and manifest["refinement_to_cpython"] == "OPEN",
            "source binding assurance changed")
    require(manifest["frozen_release"] == {
        "tag": TAG,
        "tag_type": "tag",
        "tag_object": TAG_OBJECT,
        "peeled_commit": COMMIT,
        "tree": TREE,
    }, "frozen tag identity changed")
    require(git("cat-file", "-t", TAG).strip() == b"tag",
            "MAT009 release tag is not annotated")
    for ref, expected in (
        (TAG, TAG_OBJECT),
        (TAG + "^{commit}", COMMIT),
        (TAG + "^{tree}", TREE),
    ):
        require(git("rev-parse", ref).decode("ascii").strip() == expected,
                f"frozen Git identity mismatch: {ref}")
    parsed = {}
    for label, pinned in (("target", TARGET), ("direct_parent", PARENT)):
        path, blob, digest = pinned
        record = manifest[label]
        require((record["path"], record["git_blob"], record["sha256"])
                == pinned, f"{label} manifest identity changed")
        frozen_blob = git("rev-parse", f"{COMMIT}:{path}").decode("ascii").strip()
        frozen_raw = git("show", f"{COMMIT}:{path}")
        require(frozen_blob == blob and sha256(frozen_raw) == digest
                and len(frozen_raw) == record["bytes"],
                f"frozen {label} bytes changed")
        require((ROOT / path).read_bytes() == frozen_raw,
                f"working-tree {label} differs from frozen release")
        computed, parsed[label] = spans(frozen_raw, set(record["functions"]))
        require(computed == record["functions"], f"{label} AST spans changed")
    require_selected_ast_shape(parsed["target"], parsed["direct_parent"])
    require(manifest["selected_call_edge"] == {
        "caller": "materials.mat_spec_009.check_future_challenge",
        "callee": "materials.mat_spec_008.validate_future_measurement_packet",
        "order": (
            "outer list guard; parent call; parent reason set; child row scan; "
            "final checks; sorted normal result"
        ),
        "parent_invocations_per_accepted_outer_list": 1,
    }, "selected call edge description changed")
    return {
        "status": "SOURCE_SYNTAX_MATCH",
        "assurance": "SOURCE_SYNTAX_PINNED_ONLY",
        "refinement_to_cpython": "OPEN",
        "tag_object": TAG_OBJECT,
        "commit": COMMIT,
        "tree": TREE,
        "target_sha256": TARGET[2],
        "direct_parent_sha256": PARENT[2],
        "selected_functions": 8,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
