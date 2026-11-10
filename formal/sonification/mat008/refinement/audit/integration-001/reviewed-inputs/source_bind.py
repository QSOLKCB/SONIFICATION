"""Bind the selected MAT008 gate syntax to the frozen production source.

This checks source identity and AST shape. It does not prove CPython semantics.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MANIFEST_SHA256 = "5c43bdf9247e92d50e67eadc4a1521235e9297d69beadeb580b0f83fd6044691"
FROZEN_TAG = "refs/tags/mat-spec-008-v0.1.0"
FROZEN_TAG_OBJECT = "a02088e3c68addb41c9c7145694c0f566e84f87f"
FROZEN_COMMIT = "b4247877dd471e2e9d4986c86bdc1f11b14e43f8"
FROZEN_TREE = "eb19f2e06a502442f621a73be1e5696c2fa25a65"
FROZEN_BLOB = "3117adbc3739c834f8203d5d2dd2b80d6caf862b"
FROZEN_SHA256 = "e56563235d87da43293bc46661b077660538b476d2bb340a1d208cc59aaa5f08"
PRIOR_BINDING_SHA256 = "0745c4178e6c06e8e16f0028eddf2152c480088daa3c35b36d96b5053d7bd0d4"
ACCEPTED_MODEL_SHA256 = "653f4638568e4e461176cca7659360737f3ac2632152163602c789fd65ead201"

NON_DICT_GUARD = '''if not isinstance(row, dict):
    reasons.add("MALFORMED_CANDIDATE_RECORD")
    continue
'''
IDENTITY_TRY = '''try:
    camp = _identity(row.get("campaign_id"))
    lab = _identity(row.get("lab_family_id"))
    run = _identity(row.get("original_run_id"))
    doc = _identity(row.get("source_document_id"))
    identifier = _identity(row.get("row_id"))
except ValueError:
    reasons.add("MISSING_OR_INVALID_SOURCE_IDENTITIES")
    continue
'''
GATE = '''for key, owner, prior in (
    ("REUSED_ORIGINAL_RUN_ACROSS_CAMPAIGNS", run_to_campaign, run),
    ("REUSED_ORIGINAL_DOCUMENT_ACROSS_CAMPAIGNS", document_to_campaign, doc),
):
    if prior in owner and owner[prior] != camp:
        reasons.add(key)
    owner[prior] = camp
'''


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def unique_pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def git(*args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=True,
        capture_output=True,
        timeout=30,
    ).stdout


def same_ast(observed: ast.AST, expected_source: str) -> bool:
    expected = ast.parse(expected_source).body[0]
    return ast.dump(observed, include_attributes=False) == ast.dump(
        expected, include_attributes=False
    )


def only_function(module: ast.Module, name: str) -> ast.FunctionDef:
    matches = [
        node for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    require(len(matches) == 1, f"expected one top-level function {name}")
    return matches[0]


def source_slice(text: str, node: ast.AST) -> dict:
    segment = ast.get_source_segment(text, node)
    require(segment is not None, "AST source segment unavailable")
    return {
        "start_line": node.lineno,
        "end_line": node.end_lineno,
        "bytes": len(segment.encode("utf-8")),
        "sha256": sha(segment.encode("utf-8")),
    }


def parsed_identity_order(try_node: ast.Try) -> list[list[str]]:
    pairs = []
    for statement in try_node.body:
        require(isinstance(statement, ast.Assign) and len(statement.targets) == 1,
                "identity parsing statement changed")
        target = statement.targets[0]
        value = statement.value
        require(isinstance(target, ast.Name) and isinstance(value, ast.Call)
                and isinstance(value.func, ast.Name) and value.func.id == "_identity"
                and len(value.args) == 1 and not value.keywords,
                "identity parsing call changed")
        getter = value.args[0]
        require(isinstance(getter, ast.Call) and isinstance(getter.func, ast.Attribute)
                and isinstance(getter.func.value, ast.Name)
                and getter.func.value.id == "row" and getter.func.attr == "get"
                and len(getter.args) == 1 and not getter.keywords
                and isinstance(getter.args[0], ast.Constant)
                and isinstance(getter.args[0].value, str),
                "identity source key changed")
        pairs.append([target.id, getter.args[0].value])
    return pairs


def gate_ir(gate: ast.For, row_loop: ast.For, return_node: ast.Return) -> dict:
    require(isinstance(row_loop.iter, ast.Name) and row_loop.iter.id == "records",
            "row iteration source changed")
    require(same_ast(gate, GATE), "run/document gate AST changed")
    require(isinstance(gate.iter, ast.Tuple), "gate tuple changed")
    iterations = []
    for item in gate.iter.elts:
        require(isinstance(item, ast.Tuple) and len(item.elts) == 3,
                "gate iteration record changed")
        reason, owner, key = item.elts
        require(isinstance(reason, ast.Constant) and isinstance(reason.value, str)
                and isinstance(owner, ast.Name) and isinstance(key, ast.Name),
                "gate iteration fields changed")
        iterations.append([reason.value, owner.id, key.id])
    require(isinstance(return_node.value, ast.Dict), "validator return shape changed")
    reason_values = [
        value for key, value in zip(return_node.value.keys, return_node.value.values, strict=True)
        if isinstance(key, ast.Constant) and key.value == "reasons"
    ]
    require(len(reason_values) == 1 and ast.dump(reason_values[0], include_attributes=False)
            == ast.dump(ast.parse("sorted(reasons)", mode="eval").body,
                        include_attributes=False),
            "observable reasons return changed")
    return {
        "row_source": row_loop.iter.id,
        "iterations": iterations,
        "condition": "prior in owner and owner[prior] != camp",
        "conditional_effect": "reasons.add(key)",
        "unconditional_effect": "owner[prior] = camp",
        "normal_return_observation": "sorted(reasons)",
    }


def analyze(raw: bytes, manifest: dict) -> dict:
    """Check the frozen bytes and selected AST; callable on mutant bytes in tests."""
    require(sha(raw) == FROZEN_SHA256, "frozen MAT008 source SHA-256 mismatch")
    text = raw.decode("utf-8")
    module = ast.parse(text)
    identity = only_function(module, "_identity")
    decimal = only_function(module, "_decimal")
    validator = only_function(module, "validate_future_measurement_packet")
    loops = [node for node in validator.body if isinstance(node, ast.For)]
    require(len(loops) == 1, "raw-record loop inventory changed")
    row_loop = loops[0]
    gates = [node for node in row_loop.body if isinstance(node, ast.For)]
    require(len(gates) == 1, "run/document gate inventory changed")
    gate = gates[0]
    gate_index = row_loop.body.index(gate)
    require(gate_index >= 2 and same_ast(row_loop.body[0], NON_DICT_GUARD)
            and isinstance(row_loop.body[1], ast.Try)
            and same_ast(row_loop.body[1], IDENTITY_TRY),
            "accepted-row projection changed")
    parse_try = row_loop.body[1]
    require(not any(isinstance(node, ast.Continue)
                    for statement in row_loop.body[gate_index:]
                    for node in ast.walk(statement)),
            "unexpected post-identity skip path")
    returns = [node for node in validator.body if isinstance(node, ast.Return)]
    require(len(returns) == 1, "normal return inventory changed")
    return_node = returns[0]
    initial = {
        statement.target.id: statement.value for statement in validator.body
        if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name)
    }
    for name, expression in (
        ("reasons", "set()"),
        ("run_to_campaign", "{}"),
        ("document_to_campaign", "{}"),
    ):
        require(name in initial and ast.dump(initial[name], include_attributes=False)
                == ast.dump(ast.parse(expression, mode="eval").body,
                            include_attributes=False),
                f"initial {name} state changed")
    require(len([node for node in ast.walk(validator)
                 if isinstance(node, ast.Name) and node.id == "reasons"
                 and isinstance(node.ctx, ast.Store)]) == 1,
            "reasons variable is reassigned")
    reason_methods = [
        node.attr for node in ast.walk(validator)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
        and node.value.id == "reasons"
    ]
    require(reason_methods and set(reason_methods) == {"add"},
            "reason set has a non-add method access")
    nodes = {
        "_identity": identity,
        "_decimal": decimal,
        "validator": validator,
        "row_loop": row_loop,
        "non_dict_guard": row_loop.body[0],
        "identity_try": parse_try,
        "run_document_gate": gate,
        "return": return_node,
    }
    slices = {name: source_slice(text, node) for name, node in nodes.items()}
    require(slices == manifest["source_slices"], "selected AST source spans changed")
    order = parsed_identity_order(parse_try)
    require(order == manifest["parsed_identity_order"], "identity parse order changed")
    ir = gate_ir(gate, row_loop, return_node)
    require(ir == manifest["gate_ir"], "gate interpretation inventory changed")
    return {
        "source_slices": len(slices),
        "accepted_identity_fields": len(order),
        "gate_iterations": len(ir["iterations"]),
        "scope": "source bytes and selected AST shape only; no CPython refinement",
    }


def verify(check_worktree: bool = False) -> dict:
    raw_manifest = (HERE / "SOURCE_BINDING.json").read_bytes()
    require(sha(raw_manifest) == MANIFEST_SHA256, "refinement source manifest changed")
    manifest = json.loads(raw_manifest, object_pairs_hook=unique_pairs)
    require(manifest["assurance"] == "SOURCE_SYNTAX_PINNED_ONLY",
            "source assurance was promoted")
    require(manifest["frozen_source"] == {
        "tag": FROZEN_TAG,
        "tag_object": FROZEN_TAG_OBJECT,
        "commit": FROZEN_COMMIT,
        "tree": FROZEN_TREE,
        "path": "materials/mat_spec_008.py",
        "blob": FROZEN_BLOB,
        "sha256": FROZEN_SHA256,
    }, "frozen source manifest identity changed")
    prior = manifest["prior_binding"]
    require(prior["sha256"] == PRIOR_BINDING_SHA256
            and sha((ROOT / prior["path"]).read_bytes()) == PRIOR_BINDING_SHA256,
            "prior source binding changed")
    model = manifest["accepted_model"]
    require(model["sha256"] == ACCEPTED_MODEL_SHA256
            and sha((ROOT / model["path"]).read_bytes()) == ACCEPTED_MODEL_SHA256,
            "accepted model source changed")
    for ref, expected in (
        (FROZEN_TAG, FROZEN_TAG_OBJECT),
        (FROZEN_TAG + "^{commit}", FROZEN_COMMIT),
        (FROZEN_TAG + "^{tree}", FROZEN_TREE),
        (FROZEN_COMMIT + ":materials/mat_spec_008.py", FROZEN_BLOB),
    ):
        require(git("rev-parse", ref).decode("ascii").strip() == expected,
                f"Git source identity mismatch: {ref}")
    require(git("cat-file", "-t", FROZEN_TAG).strip() == b"tag",
            "frozen tag is not annotated")
    raw = git("show", FROZEN_COMMIT + ":materials/mat_spec_008.py")
    analysis = analyze(raw, manifest)
    if check_worktree:
        require((ROOT / "materials/mat_spec_008.py").read_bytes() == raw,
                "checked-out MAT008 source differs from frozen source")
    return {
        "status": "SOURCE_SYNTAX_BINDING_MATCH",
        "frozen_commit": FROZEN_COMMIT,
        "frozen_source_sha256": FROZEN_SHA256,
        "worktree_source_checked": check_worktree,
        **analysis,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-worktree", action="store_true",
                        help="also require the current checkout module to match frozen bytes")
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.check_worktree), sort_keys=True))
    except (KeyError, OSError, UnicodeError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
