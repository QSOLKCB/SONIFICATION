#!/usr/bin/env python3
"""Reconstruct the SONIFICATION-FORMAL-001 historical source inventory from Git.

Reads frozen Git objects; never imports or runs historical production modules.
This is an identity/static-navigation inventory, not a semantic coverage proof.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

BASE = "8c62517138e3b86a4672d8969e190b747f81c398"
CONTEXT = "a1f74e8d1847d218d6b68c125fac9522e2ffc2fb"
TAGS = [f"mat-spec-{i:03d}-v0.1.0" for i in range(3, 11)] + [
    "d4-tia-v2.0.0",
    "v2.0.0",
    "v3.0.0",
    "v3.0.1",
    "spark-001-v1.0.0",
]
ROOTS = {
    "mat-spec-001-first-source": "8493d59959d0d4416c516ad5615cdedcb32fcf93",
    "mat-spec-002-first-source": "26f9aca04a73e5ed5b14340a0bf97ecb6b1d662f",
    "sonification-main-reference": BASE,
    "spark-002-phase-1a-historical": "06b1294bf1617e9eb3b825051e8bfbf7470e395c",
    "spark-002-phase-1b-historical": "6f0f1be1ba8885fa708d7328bcb92fbf4ecc324f",
}
SOURCE_EXTENSIONS = {".py", ".js", ".mjs", ".cjs", ".ads", ".adb", ".gpr", ".sh", ".html", ".yml"}
PRIORITY = {
    ("materials/mat_spec_007.py", "interval"): [
        (
            "Exact Fraction conversion; central value plus/minus strictly positive "
            "uncertainty; conversion and exception semantics"
        )
    ],
    ("materials/mat_spec_007.py", "classify"): [
        ("Closed interval order/overlap exhaustiveness and exclusivity under ordered endpoints"),
        "Exact rational comparisons and Python short-circuit branch semantics",
    ],
    ("materials/mat_spec_007.py", "pairwise_fits"): [
        ("All intended fit pairs visited once; missingness preserved; counts match classifications")
    ],
    ("materials/mat_spec_008.py", "validate_future_measurement_packet"): [
        "Eligible packets satisfy row and source identity invariants",
        ("Missing, invalid, measured zero and physical boundary zero stay distinct"),
        "Campaign/lab/run/document/digest ownership and reuse fail closed",
    ],
    ("materials/mat_spec_008.py", "evidence_admission"): [
        (
            "Synthetic and secondary evidence never admitted as primary physical "
            "evidence; mandatory gates fail closed"
        )
    ],
    ("materials/mat_spec_009.py", "check_future_challenge"): [
        ("No source family or campaign crosses TRAIN/HOLDOUT in an eligible packet"),
        (
            "Diagnostic provenance and structural eligibility fail closed; "
            "classifier score remains prohibited"
        ),
    ],
    ("materials/mat_spec_009.py", "source_gate"): [
        (
            "Parent source identities and admission prerequisites verified before "
            "challenge eligibility"
        )
    ],
    ("materials/mat_spec_010.py", "verify_parent"): [
        (
            "Exact parent artifact membership and hashes, manifest identity and "
            "admission boundaries checked"
        )
    ],
    ("materials/mat_spec_010.py", "science_closure"): [
        (
            "NUMBERED_SERIES_CLOSED_AT_010_WITH_OPEN_SCIENTIFIC_GATES; no "
            "classifier score from blocked evidence"
        )
    ],
    ("materials/mat_spec_010.py", "validate_archive_membership"): [
        (
            "Exact deterministic archive membership; duplicate, extra, missing or "
            "unsafe paths rejected"
        )
    ],
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args])


def resolve(root: Path, label: str, ref: str, kind: str) -> dict:
    obj = git(root, "rev-parse", "--verify", ref).decode().strip()
    obj_type = git(root, "cat-file", "-t", obj).decode().strip()
    commit = git(root, "rev-parse", "--verify", f"{obj}^{{commit}}").decode().strip()
    tree = git(root, "rev-parse", f"{commit}^{{tree}}").decode().strip()
    result = {
        "id": label,
        "kind": kind,
        "ref": ref,
        "ref_object": obj,
        "ref_object_type": obj_type,
        "peeled_commit": commit,
        "tree": tree,
    }
    if obj_type == "tag":
        result["tag_object_sha256"] = sha(git(root, "cat-file", "tag", obj))
    files = []
    for row in git(root, "ls-tree", "-rz", "--full-tree", commit).split(b"\0"):
        if not row:
            continue
        metadata, path = row.split(b"\t", 1)
        mode, item_type, blob = metadata.decode().split()
        files.append({"path": path.decode(), "mode": mode, "type": item_type, "object": blob})
    result["files"] = sorted(files, key=lambda r: r["path"])
    return result


def load_blobs(root: Path, ids: list[str]) -> dict[str, bytes]:
    # communicate() avoids pipe deadlock for large historical trees.
    proc = subprocess.run(
        ["git", "-C", str(root), "cat-file", "--batch"],
        input=("\n".join(ids) + "\n").encode(),
        capture_output=True,
        check=True,
    )
    result = {}
    offset = 0
    for expected in ids:
        line_end = proc.stdout.index(b"\n", offset)
        actual, kind, length = proc.stdout[offset:line_end].decode().split()
        if actual != expected or kind != "blob":
            raise ValueError(f"Unexpected Git batch object: {expected}")
        start = line_end + 1
        size = int(length)
        result[actual] = proc.stdout[start : start + size]
        offset = start + size + 1
    if offset != len(proc.stdout):
        raise ValueError("Trailing batch data")
    return result


def module_name(path: str) -> str:
    stem = str(PurePosixPath(path).with_suffix("")).replace("/", ".")
    return stem.removesuffix(".__init__")


def python_inventory(path: str, raw: bytes) -> tuple[list[dict], list[dict], list[str]]:
    source = raw.decode("utf-8")
    tree = ast.parse(source, filename=path)
    functions = []
    imports = []

    def visit(node: ast.AST, scope: str = "") -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = f"{scope}.{child.name}" if scope else child.name
                if not isinstance(child, ast.ClassDef):
                    segment = ast.get_source_segment(source, child)
                    functions.append(
                        {
                            "symbol": name,
                            "line": child.lineno,
                            "end_line": child.end_lineno,
                            "source_span_sha256": sha(segment.encode()),
                            "span_scope": (
                                "AST function node, excluding leading decorators; "
                                "entire source blob separately pinned"
                            ),
                            "call_syntax": sorted(
                                {
                                    ast.unparse(call.func)
                                    for call in ast.walk(child)
                                    if isinstance(call, ast.Call)
                                }
                            ),
                            "intended_properties": PRIORITY.get(
                                (path, name),
                                [
                                    (
                                        "OPEN: intended contract and semantic "
                                        "dependency closure require examination"
                                    )
                                ],
                            ),
                            "MODEL_PROVED": "OPEN",
                            "REFINEMENT_PROVED": "OPEN",
                            "DIFFERENTIAL_TESTED": "NOT_RUN",
                            "AUDIT_ACCEPTED": "OPEN",
                            "layer_a": "OPEN",
                            "layer_b": "OPEN",
                            "layer_c": "NOT_RUN",
                            "theorem": None,
                            "refinement_theorem": None,
                            "evidence_receipt": None,
                        }
                    )
                visit(child, name)
            else:
                visit(child, scope)

    visit(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(
                {"kind": "python_import", "module": a.name, "line": node.lineno} for a in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            imports.append(
                {
                    "kind": "python_from_import",
                    "module": node.module or "",
                    "level": node.level,
                    "names": [a.name for a in node.names],
                    "line": node.lineno,
                }
            )
    strings = sorted(
        {
            n.value
            for n in ast.walk(tree)
            if isinstance(n, ast.Constant)
            and isinstance(n.value, str)
            and re.search(
                r"(?:data/|examples/|spec/|publication/|verification/|materials/|src/)|[0-9a-f]{40}",
                n.value,
            )
            and len(n.value) < 600
        }
    )
    return functions, imports, strings


def other_inventory(path: str, raw: bytes) -> tuple[list[dict], list[dict], list[str]]:
    source = raw.decode("utf-8")
    patterns = [
        r"\b(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(",
        r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^\n]*?\)|[\w$]+)\s*=>",
    ]
    if PurePosixPath(path).suffix in {".ads", ".adb"}:
        patterns = [r"(?i)\b(?:procedure|function)\s+([A-Za-z_][\w.]*)"]
    functions = []
    for pattern in patterns:
        for match in re.finditer(pattern, source):
            functions.append(
                {
                    "symbol": match.group(1),
                    "line": source[: match.start()].count("\n") + 1,
                    "candidate_only": True,
                    "MODEL_PROVED": "OPEN",
                    "REFINEMENT_PROVED": "OPEN",
                    "DIFFERENTIAL_TESTED": "NOT_RUN",
                    "AUDIT_ACCEPTED": "OPEN",
                    "layer_a": "OPEN",
                    "layer_b": "OPEN",
                    "layer_c": "NOT_RUN",
                    "theorem": None,
                    "refinement_theorem": None,
                    "evidence_receipt": None,
                    "intended_properties": [
                        "OPEN: lexical candidate; parser and intended contract required"
                    ],
                }
            )
    imports = [
        {"kind": "ecmascript_import_candidate", "module": m.group(1)}
        for m in re.finditer(
            r"\b(?:from\s*|import\s*\(?\s*|require\s*\(\s*)['\"]([^'\"]+)['\"]", source
        )
    ]
    return functions, imports, []


def generate(root: Path) -> tuple[dict, dict, str]:
    snapshots = [resolve(root, tag, "refs/tags/" + tag, "historical_release_tag") for tag in TAGS]
    snapshots.extend(
        resolve(root, label, commit, "historical_commit") for label, commit in ROOTS.items()
    )
    ids = sorted({f["object"] for s in snapshots for f in s["files"] if f["type"] == "blob"})
    blobs = load_blobs(root, ids)
    blob_records = {key: {"sha256": sha(raw), "bytes": len(raw)} for key, raw in blobs.items()}
    versions = {}
    for snap in snapshots:
        module_paths = {
            module_name(f["path"]): f["path"] for f in snap["files"] if f["path"].endswith(".py")
        }
        tracked_paths = {f["path"] for f in snap["files"]}
        for file in snap["files"]:
            path, obj = file["path"], file["object"]
            if PurePosixPath(path).suffix not in SOURCE_EXTENSIONS or file["type"] != "blob":
                continue
            key = f"{path}@{obj}"
            if key not in versions:
                raw = blobs[obj]
                parser = python_inventory if path.endswith(".py") else other_inventory
                error = None
                try:
                    functions, imports, locators = parser(path, raw)
                except (SyntaxError, UnicodeError, ValueError) as exc:
                    functions, imports, locators = [], [], []
                    error = f"{type(exc).__name__}: {exc}"
                versions[key] = {
                    "id": key,
                    "path": path,
                    "git_blob": obj,
                    "sha256": sha(raw),
                    "snapshots": [],
                    "functions": functions,
                    "imports": imports,
                    "literal_source_locators": locators,
                    "parsing": "python_ast_complete_function_definitions"
                    if path.endswith(".py")
                    else "lexical_candidates_only",
                    "parse_error": error,
                    "MODEL_PROVED": "OPEN",
                    "REFINEMENT_PROVED": "OPEN",
                    "DIFFERENTIAL_TESTED": "NOT_RUN",
                    "AUDIT_ACCEPTED": "OPEN",
                    "module_obligations": {
                        "semantic_coverage": "OPEN",
                        "dependency_semantics": "OPEN",
                        "exceptions_and_initialization": "OPEN",
                        "top_level_code": "OPEN",
                    },
                    "dependency_edges_by_snapshot": {},
                }
            entry = versions[key]
            entry["snapshots"].append(snap["id"])
            resolved = []
            for imp in entry["imports"]:
                module = imp["module"]
                candidates = [module]
                if imp["kind"] == "python_from_import":
                    if imp.get("level"):
                        parts = module_name(path).split(".")[: -imp["level"]]
                        module = ".".join(parts + ([module] if module else []))
                    candidates = [module, *(module + "." + name for name in imp["names"])]
                for candidate in candidates:
                    if candidate in module_paths:
                        resolved.append(
                            {
                                "import": imp,
                                "target": module_paths[candidate],
                                "relation": "static_import",
                            }
                        )
                if imp["kind"] == "ecmascript_import_candidate" and module.startswith("."):
                    # Resolve dot components using POSIX path syntax; no filesystem dependency.
                    parts = []
                    for part in (PurePosixPath(path).parent / module).parts:
                        if part == "..":
                            if parts:
                                parts.pop()
                        elif part != ".":
                            parts.append(part)
                    candidate = "/".join(parts)
                    if candidate in tracked_paths:
                        resolved.append(
                            {
                                "import": imp,
                                "target": candidate,
                                "relation": "static_import_candidate",
                            }
                        )
            entry["dependency_edges_by_snapshot"][snap["id"]] = resolved
    modules = [versions[k] for k in sorted(versions)]
    counts = {
        "snapshots": len(snapshots),
        "unique_blobs": len(blobs),
        "source_module_versions": len(modules),
        "python_function_versions": sum(
            len(m["functions"]) for m in modules if m["path"].endswith(".py")
        ),
        "lexical_function_candidates": sum(
            len(m["functions"]) for m in modules if not m["path"].endswith(".py")
        ),
    }
    manifest = {
        "schema": "qsol.sonification-formal-001.source-manifest/v1",
        "project": "SONIFICATION-FORMAL-001",
        "target_repository": "https://github.com/QSOLKCB/SONIFICATION",
        "reference_main": BASE,
        "reference_main_tree": git(root, "rev-parse", f"{BASE}^{{tree}}").decode().strip(),
        "protocol_repository": "QSOLKCB/Private-Context-For-Formalization",
        "protocol_commit": CONTEXT,
        "protocol_tree": "d7c4e6ffe277015d517e8edd79b2420a29c5673d",
        "initial_reference_identity_changes": [],
        "identity_observation": (
            "Both remote main commits independently queried through authenticated "
            "GitHub API and matched supplied reference identities before work"
        ),
        "hash_algorithm": "SHA-256",
        "git_object_format": "sha1",
        "no_tags_for_dependency_roots": ["MAT-SPEC-001", "MAT-SPEC-002"],
        "root_identity_rule": (
            "First source-introduction commits are dependency-root locators, not "
            "invented releases; root module versions at each actual historical tag "
            "remain distinct"
        ),
        "snapshots": snapshots,
        "blobs": blob_records,
        "counts": counts,
        "limitations": [
            (
                "Git and SHA-256 identify bytes; they do not authenticate authors, "
                "scientific sources or execution"
            ),
            (
                "All tracked files at the listed snapshots are inventoried, including "
                "datasets, specifications, tests, archives and provenance"
            ),
            "No historical module was executed during inventory",
            (
                "Untracked external artifacts, remote archive payloads and unlisted "
                "historical commits require additional independent identity "
                "investigation"
            ),
            "This inventory is not a proof-acceptance authority",
        ],
    }
    inventory = {
        "schema": "qsol.sonification-formal-001.implementation-inventory/v1",
        "project": "SONIFICATION-FORMAL-001",
        "target_commit": BASE,
        "counts": counts,
        "modules": modules,
        "coverage": {
            "all_tracked_files_at_listed_snapshots": "IDENTITY_INVENTORIED",
            "python_named_functions_and_methods": "AST_ENUMERATED; all semantic obligations OPEN",
            "python_lambdas_comprehensions_top_level": (
                "Covered by module OPEN obligation; not individual function claims"
            ),
            "ecmascript_and_ada_functions": (
                "LEXICAL_CANDIDATES_ONLY; complete grammar-aware extraction OPEN"
            ),
            "dynamic_imports_path_construction_external_dependencies": "OPEN",
            "proof_dependency_closure": "OPEN",
            "implementation_refinement": "OPEN",
        },
        "scan_limitations": [
            ("Static imports are navigation edges, not a complete semantic dependency proof"),
            (
                "Call syntax may include nested functions and cannot resolve aliases, "
                "dynamic dispatch or runtime monkeypatching"
            ),
            (
                "Python default arguments, decorators, globals, module initialization, "
                "parsing, serialization and external dependency behavior require "
                "separate obligations"
            ),
            ("No numeric or physical source semantics inferred from a filename or hash"),
            (
                "JS arrow callbacks, object/class methods and dynamically constructed "
                "functions may be absent from lexical candidate lists; every source "
                "module remains OPEN"
            ),
            (
                "Existing SPARK evidence remains source-specific and does not "
                "discharge these Python obligations"
            ),
        ],
    }
    lines = [
        "# SONIFICATION-FORMAL-001 proof inventory",
        "",
        (
            "This inventory records targets and unresolved obligations. It makes "
            "no proof-completion claim."
        ),
        "",
        f"Frozen reference main: `{BASE}`. Protocol identity: `{CONTEXT}`.",
        "",
        (
            "`SOURCE_MANIFEST.json` records every tracked path at each listed "
            "snapshot, Git blob identities, SHA-256 digests, tag object "
            "identities, peeled commits and source trees. "
            "`SOURCE_INVENTORY.json` enumerates source-module versions and "
            "Python function definitions. Module-level OPEN obligations cover "
            "initialization, unnamed expressions and unsupported extraction. No "
            "unexamined function is covered by a theorem."
        ),
        "",
        "## Historical identities",
        "",
        "| Snapshot | Ref kind | Ref object | Peeled commit | Tree |",
        "|---|---|---|---|---|",
    ]
    for snap in snapshots:
        lines.append(
            f"| {snap['id']} | {snap['ref_object_type']} | `{snap['ref_object']}` "
            f"| `{snap['peeled_commit']}` | `{snap['tree']}` |"
        )
    lines += [
        "",
        (
            "MAT-SPEC-001 and MAT-SPEC-002 have no corresponding repository tags. "
            "Their first introduction commits are dependency-root locators; they "
            "are not asserted to be published release identities. Downstream "
            "pinned artifact maps and the exact root module versions at each "
            "release must be followed independently."
        ),
        "",
        "## Required verification domains",
        "",
        "| Domain | Required investigation | Current coverage |",
        "|---|---|---|",
    ]
    domains = {
        "Exact arithmetic": (
            "Integers, decimal lexical grammar, Fraction normalization/comparison, "
            "rational interval endpoints, float conversions"
        ),
        "MAT-SPEC transformations": (
            "Parent-chain source and artifact pins, numerical and symbolic "
            "invariants for stages 001-010"
        ),
        "Missingness": (
            "Missing/invalid/measured zero/physical boundary zero; parse and exception paths"
        ),
        "Source identity": (
            "Campaign, laboratory, run, document and digest ownership; uniqueness and normalization"
        ),
        "Partitioning": (
            "TRAIN/HOLDOUT source family separation, duplicate records and campaign reuse"
        ),
        "Evidence admission": (
            "Fail-closed eligibility; synthetic/secondary versus primary; blocked classifier scores"
        ),
        "Determinism": (
            "Iteration/sorting, dictionary/set behavior, canonical JSON/CSV/MIDI, "
            "stable archive bytes"
        ),
        "Provenance": (
            "Exact member sets, duplicate/missing/extra files, SHA-256, path "
            "safety, declared source linkage"
        ),
        "D4-TIA": (
            "D4 transforms, group and permutation laws, covariance/invariance and bridge semantics"
        ),
        "ETQ": (
            "Graph traversal, state transitions, symbolic tuning/event mappings, "
            "deterministic MIDI and audit output"
        ),
        "Separate music laboratories": (
            "Python sonification and browser APP module semantics inventoried; "
            "numerical/audio assurance OPEN; no rendering executed"
        ),
    }
    lines.extend(
        f"| {domain} | {requirements} | OPEN |" for domain, requirements in domains.items()
    )
    lines += [
        "",
        "## Prioritized operation obligations",
        "",
        ("| Production locator | Intended property | Layer A | Layer B | Layer C |"),
        "|---|---|---|---|---|",
    ]
    for (path, name), properties in PRIORITY.items():
        lines.append(f"| `{path}::{name}` | {'; '.join(properties)} | OPEN | OPEN | NOT_RUN |")
    lines += [
        "",
        (
            "For every locator above, the release → commit → module/blob → source "
            "span mapping is in the two JSON inventories. Formal definitions, "
            "named theorems, theorem dependencies, representation relations, "
            "source-refinement evidence, regression test selection and evidence "
            "receipts must be added as work is executed; null fields are "
            "unresolved obligations. Existing tests in each frozen tree are "
            "identity-inventoried, but test selection and execution are not "
            "inferred."
        ),
        "",
        "## Dependency investigation",
        "",
        (
            "All historical tracked files, including `materials/`, "
            "`sonification/`, `src/`, `scripts/`, `APP/`, `verification/`, "
            "schemas, examples, datasets, papers and package metadata, have exact "
            "byte identities. Python imports and ECMAScript import candidates are "
            "resolved against each frozen tree. Module constants and literal "
            "locators are retained as investigation clues. These are static "
            "navigation edges; transitive semantic closure, external library "
            "semantics and dynamically constructed file names remain OPEN."
        ),
        "",
        (
            "MAT-SPEC parent relationships are implemented through imports and "
            "pinned artifact maps (`PARENT_*_SHA256`, `PARENT_COMMIT`), not merely "
            "numeric release labels. For example, MAT-SPEC-010 "
            "`ancestor_artifact_maps` refers to all nine predecessor maps through "
            "their actual imported modules. The MAT-SPEC-001 version spelling in "
            "that code is `1.0.0`; the dependency-root commit does not invent a "
            "matching tag."
        ),
        "",
        (
            "SPARK-002 Phase 1A and Phase 1B are inventoried at the supplied "
            "historical proof commits. Their preserved receipts report 23/23 and "
            "9/9 checks respectively. This inventory does not rerun, reinterpret, "
            "replace or extend those receipts to Python."
        ),
        "",
        "## Inventory totals and reproducibility",
        "",
    ]
    lines += [f"- {name.replace('_', ' ')}: {count}" for name, count in counts.items()]
    lines += [
        "",
        "Run from the repository root:",
        "",
        "```sh",
        "python3 formal/sonification/tools/inventory.py --check",
        "```",
        "",
        (
            "The generator reads Git objects and compares deterministic generated "
            "bytes. It does not execute old production workflows, instantiate any "
            "PCM buffers, modify tags or datasets, or treat source hashes as "
            "proofs. Re-pinning both an inventory and its generator requires "
            "review against designated canonical historical Git objects; this "
            "command alone cannot prevent an authorized-code change from changing "
            "its own expected baseline."
        ),
        "",
        "## Claim and scientific boundaries",
        "",
        (
            "All implementation refinement remains OPEN until separate "
            "source-sensitive evidence is accepted. Passing tests or a similar "
            "Lean model cannot promote these rows. MAT-SPEC remains "
            "`NUMBERED_SERIES_CLOSED_AT_010_WITH_OPEN_SCIENTIFIC_GATES`. No "
            "MAT-SPEC-011. No software proof establishes independent helium "
            "experiments, calibrated physical uncertainty, classifier accuracy, "
            "human auditory discrimination or E8 physical theory."
        ),
        "",
    ]
    return manifest, inventory, "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="compare generated identities without writing"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    manifest, inventory, markdown = generate(root)
    outputs = {
        "SOURCE_MANIFEST.json": json.dumps(manifest, sort_keys=True, indent=2) + "\n",
        "SOURCE_INVENTORY.json": json.dumps(inventory, sort_keys=True, indent=2) + "\n",
        "PROOF_INVENTORY.md": markdown,
    }
    failed = []
    for name, content in outputs.items():
        path = root / "formal/sonification" / name
        if args.check:
            if not path.is_file() or path.read_text() != content:
                failed.append(name)
        else:
            path.write_text(content)
    if failed:
        print("INVENTORY MISMATCH: " + ", ".join(failed), file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "status": "IDENTITY_INVENTORY_MATCH" if args.check else "GENERATED",
                "counts": manifest["counts"],
                "implementation_refinement": "OPEN",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
