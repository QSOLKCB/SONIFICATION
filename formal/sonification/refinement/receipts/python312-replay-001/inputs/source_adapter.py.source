"""Source-sensitive, closed-AST conformance adapter; NOT a refinement prover.

The hard-coded baseline is intentionally independent of SOURCE_MANIFEST.json.
Only the frozen production `classify` body is compiled. No production module
initializers or dependency pipelines execute.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Any

TAG = "mat-spec-007-v0.1.0"
TAG_OBJECT = "8b933a5ab09b8e76afe4c8e169e089f251e23314"
COMMIT = "b97348ff8fcf3f57764dec21a8914f153f96a745"
TREE = "c1b842c6bace3ccb01714007b8d7ebb05bcecd31"
PATH = "materials/mat_spec_007.py"
MODULE_SHA256 = "2e363adea6c781ab68aec69d2ee5c7d712fc5e46346ae5be21d8cf3e929781c6"
# Independently authored syntax contract. Matching it checks syntactic identity,
# not correctness of ast.parse, compile, CPython or Fraction.
EXPECTED = """def classify(a: tuple[Fraction, Fraction], b: tuple[Fraction, Fraction]) -> str:
    if a[0] > a[1] or b[0] > b[1]:
        raise ValueError("invalid reported-fit interval")
    if a[1] < b[0]:
        return "a_below_b"
    if b[1] < a[0]:
        return "b_below_a"
    return "overlap"
"""


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, timeout=30
    ).stdout


def load_frozen(root: Path) -> bytes:
    identities = {TAG: TAG_OBJECT, f"{TAG}^{{}}": COMMIT, f"{COMMIT}^{{tree}}": TREE}
    for ref, expected in identities.items():
        if git(root, "rev-parse", ref).decode("ascii").strip() != expected:
            raise ValueError(f"frozen Git identity mismatch: {ref}")
    raw = git(root, "show", f"{COMMIT}:{PATH}")
    if digest(raw) != MODULE_SHA256:
        raise ValueError("frozen source-module SHA-256 mismatch")
    return raw


def extract(raw: bytes, *, enforce_pin: bool = True) -> ast.FunctionDef:
    if enforce_pin and digest(raw) != MODULE_SHA256:
        raise ValueError("frozen source-module SHA-256 mismatch")
    module = ast.parse(raw.decode("utf-8"), filename=f"{COMMIT}:{PATH}")
    matches = [n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == "classify"]
    if len(matches) != 1:
        raise ValueError("expected exactly one top-level classify definition")
    actual = matches[0]
    expected = ast.parse(EXPECTED).body[0]
    if ast.dump(actual, include_attributes=False) != ast.dump(expected, include_attributes=False):
        raise ValueError("unsupported or changed classify AST")
    return actual


def compile_production(node: ast.FunctionDef) -> Any:
    namespace: dict[str, Any] = {"Fraction": Fraction, "__builtins__": {"ValueError": ValueError}}
    code = compile(ast.Module(body=[node], type_ignores=[]), f"{COMMIT}:{PATH}", "exec")
    exec(code, namespace)
    return namespace["classify"]


def _expression(node: ast.expr, state: dict[str, tuple[Fraction, Fraction]]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Subscript):
        if not isinstance(node.value, ast.Name) or not isinstance(node.slice, ast.Constant):
            raise ValueError("unsupported subscript")
        return state[node.value.id][node.slice.value]
    if isinstance(node, ast.Compare) and len(node.ops) == len(node.comparators) == 1:
        left, right = _expression(node.left, state), _expression(node.comparators[0], state)
        if isinstance(node.ops[0], ast.Lt):
            return left < right
        if isinstance(node.ops[0], ast.Gt):
            return left > right
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
        for value in node.values:
            result = _expression(value, state)
            if result:
                return result
        return result
    raise ValueError(f"unsupported expression: {type(node).__name__}")


def evaluate(
    node: ast.FunctionDef, a: tuple[Fraction, Fraction], b: tuple[Fraction, Fraction]
) -> str:
    """Execute the accepted AST in a second, explicit, finite-test interpreter.

    This interpreter has no machine-checked semantic correspondence proof.
    """
    for pair in (a, b):
        if type(pair) is not tuple or len(pair) != 2 or any(type(x) is not Fraction for x in pair):
            raise TypeError(
                "adapter domain requires exact two-element tuples of exact Fraction objects"
            )
    state = {"a": a, "b": b}
    for statement in node.body:
        selected = (
            statement.body
            if isinstance(statement, ast.If) and _expression(statement.test, state)
            else []
        )
        if not isinstance(statement, ast.If):
            selected = [statement]
        for operation in selected:
            if isinstance(operation, ast.Raise):
                # The exact AST contract above already restricts this call to
                # ValueError and the exact message; it does not execute calls.
                raise ValueError("invalid reported-fit interval")
            if isinstance(operation, ast.Return):
                return _expression(operation.value, state)
            raise ValueError("unsupported statement")
    raise ValueError("unsupported fallthrough")


def oracle(a: tuple[Fraction, Fraction], b: tuple[Fraction, Fraction]) -> str:
    """Independent rational oracle: integer cross-products, no Fraction order.

    `Fraction` normalizes denominators positive. That library contract is a
    trusted premise here, independently exercised but not proved.
    """

    def lt(x: Fraction, y: Fraction) -> bool:
        return x.numerator * y.denominator < y.numerator * x.denominator

    if lt(a[1], a[0]) or lt(b[1], b[0]):
        raise ValueError("invalid reported-fit interval")
    # Compute semantic regions in parallel, independently of production order.
    below, above = lt(a[1], b[0]), lt(b[1], a[0])
    if below and above:
        raise AssertionError("valid closed intervals cannot have both strict orders")
    return "a_below_b" if below else "b_below_a" if above else "overlap"


def outcome(function: Any, a: Any, b: Any) -> tuple[str, str]:
    try:
        return "return", function(a, b)
    except (ValueError, TypeError, IndexError, KeyError) as exc:
        return type(exc).__name__, str(exc)


def describe(node: ast.FunctionDef, raw: bytes) -> dict[str, Any]:
    lines = raw.splitlines(keepends=True)
    function_raw = b"".join(lines[node.lineno - 1 : node.end_lineno])
    return {
        "claim_class": "FINITE_CONFORMANCE",
        "implementation_refinement": "OPEN",
        "tag": TAG,
        "tag_object": TAG_OBJECT,
        "commit": COMMIT,
        "tree": TREE,
        "path": PATH,
        "module_sha256": MODULE_SHA256,
        "symbol": node.name,
        "start_line": node.lineno,
        "end_line": node.end_lineno,
        "function_sha256": digest(function_raw),
        "ast_sha256": digest(ast.dump(node, include_attributes=False).encode("utf-8")),
        "closed_ast": json.loads(json.dumps(ast.dump(node, include_attributes=False))),
        "unsupported_semantics": [
            "CPython parser, bytecode/compiler and evaluator correctness",
            "Universal correspondence of this AST adapter to CPython",
            "fractions.Fraction implementation and its transitive Python dependencies",
            "Subclass overrides and dynamic user-defined comparison operators",
            "Arbitrary sequences, malformed arguments and non-Fraction numeric types",
            "Allocation/resource failure, tracing, concurrent mutation and runtime monkey-patching",
            "decimal, interval, pairwise_fits and whole-module import behavior",
        ],
    }
