#!/usr/bin/env python3
"""Build and audit the committed MAT010 Phase A Lean proof inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MODULES = ("ArchiveModel", "ArchiveConsumer", "LeanAudit")
INPUTS = (
    *(f"{module}.lean" for module in MODULES),
    "PROOF_NOTES.md", "TRUSTED_COMPILER.md", "lean-toolchain", "check.py",
    "negative.py",
)
NAMED_THEOREMS = {
    f"MAT010.Archive.{name}" for name in (
        "M010_A1_ordered_nine",
        "M010_A2_commit_identities",
        "M010_A3_valid_artifact_identity",
        "M010_A4_unique_logical_paths",
        "M010_A5_deterministic_enumeration",
        "M010_A6_fail_closed_malformed",
        "M010_A7_accepted_and_rejected_nonvacuity",
    )
}
THEOREM_TYPE_SHA256 = {
    "MAT010.Archive.M010_A1_ordered_nine":
        "6d547b423fd0ffa74efae9fc36ae25bcbc3a0bc05baa40d9d53808296df93b4c",
    "MAT010.Archive.M010_A2_commit_identities":
        "2c7926c3aa42ccdf99181b422c64316d42a04d09dc443b9b0684f85bf1f04aad",
    "MAT010.Archive.M010_A3_valid_artifact_identity":
        "9b5dff3e880c9a13838e079337b9e78257f40bc65e9e2877e783aafa0a07e510",
    "MAT010.Archive.M010_A4_unique_logical_paths":
        "8a0cf1d1f235b5613d1adc58a2758676b4bfbfe07951c1951c41bef4b94f36b4",
    "MAT010.Archive.M010_A5_deterministic_enumeration":
        "5fa560581f48d5b48e408cc512c9d111609b3728ae9e3136f193c0389b61fd99",
    "MAT010.Archive.M010_A6_fail_closed_malformed":
        "b7b2fb6602a898f3331359601b78ab173f240adaff6ac4865c71137168d9783b",
    "MAT010.Archive.M010_A7_accepted_and_rejected_nonvacuity":
        "56524db6caa3f1be5207c969888b9d6647a0aee28366a2948ec3eff0222c7de2",
}
TRUSTED_PROJECT_COMPILER_AXIOMS = {
    "List.flatMapTR.go._at.MAT010.Archive.emit._spec_1",
    "List.foldl._at.MAT010.Archive.stageSuffix._spec_1",
    "List.hasDecEq._at.MAT010.Archive.instDecidableValidInput._spec_2",
    "List.hasDecEq._at.MAT010.Archive.instDecidableValidPair._spec_1",
    "List.isPrefixOf._at._private.ArchiveModel.0.MAT010.Archive.suffixCase._spec_1",
    "List.isSuffixOf._at.MAT010.Archive.hasMidiSuffix._spec_1",
    "List.mapTR.loop._at.MAT010.Archive.demoClaims._spec_1",
    "List.mapTR.loop._at.MAT010.Archive.demoSnapshots._spec_1",
    "List.mapTR.loop._at.MAT010.Archive.demoSnapshotsExtra._spec_1",
    "List.mapTR.loop._at.MAT010.Archive.emitFor._spec_1",
    "List.mapTR.loop._at.MAT010.Archive.instDecidableValidInput._spec_1",
    "List.mapTR.loop._at.MAT010.Archive.instDecidableValidInput._spec_3",
    "List.mapTR.loop._at.MAT010.Archive.instDecidableValidInput._spec_4",
    "List.mapTR.loop._at.MAT010.Archive.instDecidableValidInput._spec_5",
    "List.mapTR.loop._at.MAT010.Archive.instDecidableValidPair._spec_2",
}
TRUSTED_IMPORTED_COMPILER_AXIOMS = {
    "List.elem._at.System.FilePath.normalize._spec_1",
    "_private.Init.Data.Option.Basic.0.Option.decEqOption.«_@».Init.Data.Option.Basic._hyg.4._at.Std.Time.Database.TZdb.idFromPath._spec_1",
    "lcProof",
}
ALLOWED_LOGICAL_AXIOMS = {"propext", "Quot.sound", "Classical.choice"}
DECLARATIONS_SHA256 = "2bd2e259f54ca1186ee3171a3fbeee05d049d77a59c2ce93738a6cdce32ece07"
LEAN_VERSION = "Lean (version 4.19.0, x86_64-unknown-linux-gnu, commit 6caaee842e94, Release)"
LEAN_SHA256 = "92c3d35b5bfaa5e0fea413a775d504cf46cd95e1345df61c2274f76779e7e023"
PROHIBITED = re.compile(
    r"\b(?:sorry|admit|axiom|opaque|unsafe|partial|run_cmd|macro|elab)\b"
)
AXIOM_LINE = re.compile(
    r"^'([^']+)' (?:depends on axioms: \[([^]]*)\]|does not depend on any axioms)$"
)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def source_inventory(source_dir: Path = HERE) -> set[str]:
    """Exclude retained execution snapshots, but no unimported source module."""
    actual = {
        str(path.relative_to(source_dir)) for path in source_dir.rglob("*.lean")
        if path.relative_to(source_dir).parts[0] not in
        {"development", "audit-development", "receipts"}
    }
    require(actual == {f"{module}.lean" for module in MODULES},
            f"unexpected Lean module inventory: {sorted(actual)}")
    return actual


def verify_baseline(commit: str) -> dict[str, str]:
    require(bool(re.fullmatch(r"[0-9a-f]{40}", commit)),
            "proof baseline must be a full Git commit SHA")
    subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"],
                   cwd=ROOT, check=True, capture_output=True, timeout=30)
    source_inventory()
    observed = {}
    for name in INPUTS:
        current = HERE / name
        require(current.is_file() and not current.is_symlink(),
                f"missing ordinary proof input: {name}")
        raw = current.read_bytes()
        historical = subprocess.check_output(
            ["git", "show", f"{commit}:formal/sonification/mat010/lean/{name}"],
            cwd=ROOT, timeout=30,
        )
        require(raw == historical, f"stale proof input: {name}")
        observed[name] = sha(raw)
    for module in MODULES[:2]:
        require(not PROHIBITED.search((HERE / f"{module}.lean").read_text()),
                f"prohibited proof shortcut in {module}")
    require((HERE / "lean-toolchain").read_text() ==
            "leanprover/lean4:v4.19.0\n", "Lean toolchain declaration changed")
    return observed


def record_command(out: Path, label: str, argv: list[str], *,
                   cwd: Path, env: dict[str, str], timeout: int = 180) -> tuple:
    timed_out = False
    try:
        run = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                             timeout=timeout)
        code, stdout, stderr = run.returncode, run.stdout, run.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        code, stdout, stderr = None, exc.stdout or b"", exc.stderr or b""
    (out / f"{label}.stdout").write_bytes(stdout)
    (out / f"{label}.stderr").write_bytes(stderr)
    (out / f"{label}.json").write_text(json.dumps({
        "argv": argv, "cwd": str(cwd), "exit_code": code,
        "timed_out": timed_out, "timeout_seconds": timeout,
        "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr),
    }, indent=2, sort_keys=True) + "\n")
    return code, stdout, stderr, timed_out


def check_named_axioms(raw: bytes, out: Path) -> None:
    found = {}
    for line in raw.decode().splitlines():
        match = AXIOM_LINE.match(line)
        if match:
            found[match[1]] = (
                {a.strip() for a in match[2].split(",")} if match[2] else set()
            )
    require(set(found) == NAMED_THEOREMS,
            "typed theorem axiom report coverage changed")
    require(all(ax <= ALLOWED_LOGICAL_AXIOMS for ax in found.values()),
            "typed theorem depends on unapproved axiom")
    (out / "named-axioms.json").write_text(json.dumps(
        {name: sorted(ax) for name, ax in found.items()}, indent=2,
        sort_keys=True,
    ) + "\n")


def audit_output(raw: bytes, lean: Path, out: Path) -> dict:
    lines = raw.decode().splitlines()
    modules = {x.removeprefix("MAT010_MODULE ") for x in lines
               if x.startswith("MAT010_MODULE ")}
    require(modules == set(MODULES), "project module coverage changed")
    require([x for x in lines if x.startswith("MAT010_AUDIT ")] ==
            ["MAT010_AUDIT declarations=333 theorems=63"],
            "project declaration summary changed")
    declarations = [json.loads(x.removeprefix("MAT010_DECL ")) for x in lines
                    if x.startswith("MAT010_DECL ")]
    canonical = json.dumps(declarations, indent=2, sort_keys=True) + "\n"
    require(len(declarations) == 333 and
            len({r["declaration"] for r in declarations}) == 333 and
            sha(canonical.encode()) == DECLARATIONS_SHA256,
            "complete declaration inventory changed")
    (out / "declarations.json").write_text(canonical)
    require(sum(r["kind"] == "theorem" for r in declarations) == 63 and
            sum(r["kind"] == "compiler_auxiliary" for r in declarations) == 151 and
            sum(r["unsafe_definition"] for r in declarations) == 136,
            "declaration category counts changed")
    axiom_names = {r["declaration"] for r in declarations if r["is_axiom"]}
    require(axiom_names == TRUSTED_PROJECT_COMPILER_AXIOMS,
            "project compiler axiom inventory changed")
    by_name = {r["declaration"]: r for r in declarations}
    require(by_name.keys() >= NAMED_THEOREMS, "named theorem declaration missing")
    for name in NAMED_THEOREMS:
        row = by_name[name]
        require(row["kind"] == "theorem" and
                sha(row["type"].encode()) == THEOREM_TYPE_SHA256[name] and
                set(row["axioms"]) <= ALLOWED_LOGICAL_AXIOMS,
                f"named theorem type or trust changed: {name}")
    for row in declarations:
        compiler = row["kind"] == "compiler_auxiliary"
        require(row["origin"] in MODULES and
                row["kind"] in {"theorem", "non_theorem", "compiler_auxiliary"},
                f"unclassified project declaration: {row['declaration']}")
        require(not row["is_axiom"] or
                (compiler and row["unsafe_axiom"] and
                 not row["has_source_range"]),
                f"unapproved project axiom: {row['declaration']}")
        require(not row["unsafe_definition"] or
                (compiler and not row["has_source_range"]),
                f"unapproved unsafe definition: {row['declaration']}")
        require(not compiler or row["unsafe_definition"] or row["is_axiom"],
                f"unclassified compiler auxiliary: {row['declaration']}")
        allowed = ALLOWED_LOGICAL_AXIOMS | (
            TRUSTED_PROJECT_COMPILER_AXIOMS | TRUSTED_IMPORTED_COMPILER_AXIOMS
            if compiler else set()
        )
        require(set(row["axioms"]) <= allowed,
                f"unapproved transitive axiom: {row['declaration']}")
    (out / "theorem-types.json").write_text(json.dumps(
        {name: by_name[name]["type"] for name in sorted(NAMED_THEOREMS)},
        indent=2, sort_keys=True,
    ) + "\n")
    (out / "compiler-trust.json").write_text(json.dumps({
        "project_compiler_axioms": [
            {"name": name, "type": by_name[name]["type"]}
            for name in sorted(TRUSTED_PROJECT_COMPILER_AXIOMS)
        ],
        "imported_compiler_axioms": sorted(TRUSTED_IMPORTED_COMPILER_AXIOMS),
        "unsafe_generated_definition_count": 136,
        "ordinary_logical_axioms": sorted(ALLOWED_LOGICAL_AXIOMS),
    }, indent=2, sort_keys=True) + "\n")
    imports = {x.removeprefix("MAT010_IMPORT ") for x in lines
               if x.startswith("MAT010_IMPORT ")}
    require({"ArchiveModel", "ArchiveConsumer"} <= imports and
            len(imports) == 1305,
            "import closure changed")
    external = {}
    for module in sorted(imports - set(MODULES)):
        relative = Path("lib/lean") / (module.replace(".", "/") + ".olean")
        path = lean.parent.parent / relative
        require(path.is_file() and not path.is_symlink(),
                f"missing toolchain import: {relative}")
        external[module] = {"relative_path": str(relative),
                            "sha256": sha(path.read_bytes())}
    (out / "toolchain-imports.json").write_text(json.dumps(
        external, indent=2, sort_keys=True,
    ) + "\n")
    return {
        "declaration_count": len(declarations),
        "theorem_declaration_count_including_generated": 63,
        "compiler_auxiliary_count": 151,
        "project_compiler_axiom_count": len(axiom_names),
        "named_intended_theorems": sorted(NAMED_THEOREMS),
        "external_import_count": len(external),
        "declarations_sha256": sha(canonical.encode()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean", required=True, type=Path)
    parser.add_argument("--baseline-commit", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {
        "status": "INCOMPLETE", "proof_input_commit": args.baseline_commit,
        "started_utc": datetime.now(UTC).isoformat(),
        "frozen_source_sha256":
            "e062474d4435e769f8c6c8407bc44ad89cfb2dfa04677b820c3a035d604a9056",
        "MODEL_PROVED": "NOT_EXECUTED", "REFINEMENT_PROVED": "OPEN",
        "DIFFERENTIAL_TESTED": "NOT_EXECUTED", "AUDIT_ACCEPTED": "OPEN",
    }
    try:
        report["proof_input_sha256"] = verify_baseline(args.baseline_commit)
        lean = args.lean.resolve(strict=True)
        report["lean_executable_sha256"] = sha(lean.read_bytes())
        require(report["lean_executable_sha256"] == LEAN_SHA256,
                "pinned Lean binary changed")
        code, stdout, _, timed_out = record_command(
            out, "lean-version", [str(lean), "--version"], cwd=ROOT,
            env=os.environ.copy(), timeout=30,
        )
        require(not timed_out and code == 0 and
                stdout.decode().strip() == LEAN_VERSION,
                "pinned Lean version changed")
        report["lean_version"] = LEAN_VERSION
        with tempfile.TemporaryDirectory(prefix="mat010-phase-a-lean-") as temp:
            build = Path(temp)
            env = {**os.environ, "LEAN_PATH": str(build)}
            proof_imports = {}
            for number, module in enumerate(MODULES):
                target = build / f"{module}.olean"
                argv = [str(lean), "--error=warning", "-o",
                        str(target), f"{module}.lean"]
                code, stdout, _, timed_out = record_command(
                    out, f"build-{number:02d}-{module}", argv,
                    cwd=HERE, env=env,
                )
                require(not timed_out and code == 0,
                        f"Lean rejected or timed out on {module}")
                proof_imports[module] = {
                    "source_sha256": report["proof_input_sha256"][f"{module}.lean"],
                    "olean_sha256": sha(target.read_bytes()),
                }
                if module == "ArchiveConsumer":
                    check_named_axioms(stdout, out)
                if module == "LeanAudit":
                    report.update(audit_output(stdout, lean, out))
            (out / "proof-imports.json").write_text(json.dumps(
                proof_imports, indent=2, sort_keys=True,
            ) + "\n")
        report["status"] = "PASS"
        report["MODEL_PROVED"] = "PASS_FOR_SCOPED_PHASE_A_MODEL"
        report["AUDIT_ACCEPTED"] = "PENDING_INDEPENDENT_REVIEW"
    except (OSError, ValueError, subprocess.SubprocessError,
            UnicodeError, KeyError, TypeError) as exc:
        report["status"] = "FAIL"
        report["AUDIT_ACCEPTED"] = "FAILED"
        report["error"] = str(exc)
    report["completed_utc"] = datetime.now(UTC).isoformat()
    (out / "result.json").write_text(json.dumps(report, indent=2,
                                                 sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"], "out": str(out),
        "error": report.get("error"),
        "named_theorems": len(report.get("named_intended_theorems", [])),
    }, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
