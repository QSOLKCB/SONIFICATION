#!/usr/bin/env python3
"""Verify retained MAT009 Lean receipts against pinned proof inputs and toolchain.

This verifies archived execution integrity. Independent proof acceptance still
requires review of the intended statements and trust model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DEFAULT_ATTEMPT = HERE / "attempts/003"
BASELINE = "c562377308ebbb4694685076af12e79eefe0a479"
MANIFEST_SHA256 = "575f9996a160db4ff01b69a155f2210046ce7a40b4d2ffdd78ca7c13afeb73be"
MODULES = (
    "SplitModel", "DiagnosticFirstOwner", "TypedConsumer", "ExactTypes",
    "LeanAudit",
)
INPUTS = {*(f"{m}.lean" for m in MODULES), "PROOF_NOTES.md", "lean-toolchain", "check.py"}
ALLOWED_AXIOMS = {"propext", "Quot.sound", "Classical.choice"}
TRUSTED_COMPILER_AXIOM_TYPES = {
    "MAT009.initial._elambda_1": "String → Option MAT009.Role",
    "MAT009.step._elambda_1":
        "MAT009.State → MAT009.Row → String → Option MAT009.Role",
}
TRUSTED_COMPILER_AXIOMS = set(TRUSTED_COMPILER_AXIOM_TYPES) | {
    "lcProof", "lcUnreachable",
}
VERSION = "Lean (version 4.19.0, x86_64-unknown-linux-gnu, commit 6caaee842e94, Release)"
AXIOM_LINE = re.compile(
    r"^'([^']+)' (?:depends on axioms: \[([^]]*)\]|does not depend on any axioms)$"
)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify(attempt: Path = DEFAULT_ATTEMPT, lean: Path | None = None) -> dict:
    require(attempt.is_dir() and not attempt.is_symlink(), "missing ordinary attempt directory")
    manifest_path = attempt / "EVIDENCE_MANIFEST.json"
    require(manifest_path.is_file() and not manifest_path.is_symlink(), "missing evidence manifest")
    raw = manifest_path.read_bytes()
    require(sha(raw) == MANIFEST_SHA256, "evidence manifest changed")
    manifest = json.loads(raw)
    require(manifest["schema"] == "sonification-mat009-lean-evidence-v1", "manifest schema changed")
    require(manifest["proof_input_commit"] == BASELINE, "proof input commit changed")
    files = manifest["files_sha256"]
    require(len(files) == 23, "retained evidence file count changed")
    require({p.name for p in attempt.iterdir()} == set(files) | {manifest_path.name},
            "retained evidence file inventory changed")
    for name, digest in files.items():
        path = attempt / name
        require(path.is_file() and not path.is_symlink(), f"missing ordinary evidence file: {name}")
        require(sha(path.read_bytes()) == digest, f"altered evidence file: {name}")

    result = json.loads((attempt / "result.json").read_text())
    require(result["status"] == "PASS" and result["MODEL_PROVED"] ==
            "PASS_FOR_SCOPED_MATHEMATICAL_MODEL", "proof execution did not pass")
    require(result["REFINEMENT_PROVED"] == "OPEN" and
            result["AUDIT_ACCEPTED"] == "OPEN", "receipt overstates assurance")
    require(result["baseline_commit"] == BASELINE, "result proof baseline changed")
    require(set(result["input_sha256"]) == INPUTS, "proof input inventory changed")
    require(result["declaration_count"] == 351 and
            result["theorem_declaration_count_including_generated"] == 95 and
            len(result["named_intended_theorems"]) == 22,
            "proof declaration count changed")
    # Recovery contains archived reproductions, not active proof modules.
    actual_modules = {
        p.name for p in HERE.rglob("*.lean")
        if "recovery" not in p.relative_to(HERE).parts
    }
    require(actual_modules == {f"{module}.lean" for module in MODULES},
            "current proof module coverage changed")
    for name, digest in result["input_sha256"].items():
        current = HERE / name
        require(current.is_file() and not current.is_symlink() and
                sha(current.read_bytes()) == digest, f"stale proof source: {name}")
        original = subprocess.check_output(
            ["git", "show", f"{BASELINE}:formal/sonification/mat009/lean/{name}"],
            cwd=ROOT,
        )
        require(sha(original) == digest, f"proof commit input mismatch: {name}")
    if lean is None:
        lean = Path.home() / ".elan/toolchains/leanprover--lean4---v4.19.0/bin/lean"
    lean = lean.resolve(strict=True)
    require(sha(lean.read_bytes()) == result["lean_executable_sha256"],
            "installed Lean executable changed")
    local_version = subprocess.run([str(lean), "--version"], capture_output=True, check=True)
    require(local_version.stdout.decode().strip() == VERSION and
            result["lean_version"] == VERSION, "installed Lean version changed")

    for label in ("lean-version", *(f"build-{i:02d}-{m}" for i, m in enumerate(MODULES))):
        receipt = json.loads((attempt / f"{label}.json").read_text())
        require(receipt["exit_code"] == 0 and receipt["timed_out"] is False,
                f"failed or timed-out Lean job: {label}")
        argv = receipt["argv"]
        require(Path(argv[0]).name == "lean", f"unexpected prover executable: {label}")
        if label == "lean-version":
            require(argv[1:] == ["--version"], "version command changed")
        else:
            module = label.split("-", 2)[2]
            require(argv[1:3] == ["--error=warning", "-o"] and
                    argv[-1] == f"{module}.lean" and
                    Path(argv[-2]).name == f"{module}.olean" and
                    receipt["cwd"].endswith("formal/sonification/mat009/lean"),
                    f"Lean build command changed: {label}")
        for stream in ("stdout", "stderr"):
            require(sha((attempt / f"{label}.{stream}").read_bytes()) ==
                    receipt[f"{stream}_sha256"], f"altered {label} {stream}")

    audit_lines = (attempt / "build-04-LeanAudit.stdout").read_text().splitlines()
    modules = {line.removeprefix("MAT009_MODULE ") for line in audit_lines
               if line.startswith("MAT009_MODULE ")}
    require(modules == set(MODULES), "retained audit module coverage changed")
    summaries = [line for line in audit_lines if line.startswith("MAT009_AUDIT ")]
    require(summaries == ["MAT009_AUDIT declarations=351 theorems=95"],
            "retained audit summary changed")
    declarations = [json.loads(line.removeprefix("MAT009_DECL ")) for line in audit_lines
                    if line.startswith("MAT009_DECL ")]
    require(declarations == json.loads((attempt / "declarations.json").read_text()) and
            len(declarations) == 351, "retained declaration inventory changed")
    names = [row["declaration"] for row in declarations]
    require(len(set(names)) == len(names), "duplicate declaration in retained audit")
    named = {row["declaration"]: row["type"] for row in declarations
             if row["declaration"] in result["named_intended_theorems"]}
    require(named == json.loads((attempt / "theorem-types.json").read_text()) and
            set(named) == set(result["named_intended_theorems"]),
            "retained theorem statements changed")
    require({row["declaration"] for row in declarations if row["is_axiom"]} ==
            set(TRUSTED_COMPILER_AXIOM_TYPES),
            "project compiler axiom inventory changed")
    for row in declarations:
        require(row["origin"] in MODULES, "declaration from unexpected module")
        require(row["kind"] in {"theorem", "non_theorem", "compiler_auxiliary"},
                f"unknown declaration kind: {row['declaration']}")
        compiler_aux = row["kind"] == "compiler_auxiliary"
        if row["is_axiom"]:
            require(compiler_aux and row["unsafe_axiom"] and
                    not row["has_source_range"] and
                    TRUSTED_COMPILER_AXIOM_TYPES.get(row["declaration"]) == row["type"],
                    f"unapproved project axiom: {row['declaration']}")
        else:
            require(not row["unsafe_axiom"],
                    f"inconsistent axiom metadata: {row['declaration']}")
        if row["unsafe_definition"]:
            require(compiler_aux and not row["has_source_range"],
                    f"unsafe project definition: {row['declaration']}")
        elif compiler_aux:
            require(row["is_axiom"],
                    f"unclassified compiler auxiliary: {row['declaration']}")
        allowed = ALLOWED_AXIOMS | (TRUSTED_COMPILER_AXIOMS if compiler_aux else set())
        require(set(row["axioms"]) <= allowed,
                f"unapproved transitive axiom: {row['declaration']}")
    require(sum(row["kind"] == "compiler_auxiliary" for row in declarations) == 146 and
            sum(row["unsafe_definition"] for row in declarations) == 144,
            "compiler auxiliary inventory changed")

    printed = {}
    for line in (attempt / "build-02-TypedConsumer.stdout").read_text().splitlines():
        match = AXIOM_LINE.match(line)
        if match:
            printed[match[1]] = (
                sorted(a.strip() for a in match[2].split(",")) if match[2] else []
            )
    require(printed == json.loads((attempt / "named-axioms.json").read_text()) and
            len(printed) == 18 and all(set(v) <= ALLOWED_AXIOMS for v in printed.values()),
            "named theorem transitive axioms changed")

    imports = {line.removeprefix("MAT009_IMPORT ") for line in audit_lines
               if line.startswith("MAT009_IMPORT ")}
    external = json.loads((attempt / "toolchain-imports.json").read_text())
    require(set(external) == imports - set(MODULES) and len(external) == 1303,
            "toolchain import closure changed")
    root = lean.parent.parent
    for module, identity in external.items():
        relative = Path("lib/lean") / (module.replace(".", "/") + ".olean")
        require(identity["relative_path"] == str(relative),
                f"toolchain relative import changed: {module}")
        path = root / relative
        require(path.is_file() and not path.is_symlink() and
                sha(path.read_bytes()) == identity["sha256"],
                f"installed toolchain import changed: {module}")
    return {
        "status": "MAT009_LEAN_EVIDENCE_BOUND",
        "named_model_theorems": len(named),
        "toolchain_imports": len(external),
        "REFINEMENT_PROVED": "OPEN",
        "AUDIT_ACCEPTED": "OPEN",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, default=DEFAULT_ATTEMPT)
    parser.add_argument("--lean", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.attempt, args.lean), sort_keys=True))
