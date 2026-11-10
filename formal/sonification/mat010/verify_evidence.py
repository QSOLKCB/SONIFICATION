#!/usr/bin/env python3
"""Bind retained MAT010 source and finite execution files to committed inputs.

This verifies archive integrity. It does not replay CPython or prove refinement.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RECEIPTS = HERE / "receipts"
INPUT_COMMIT = "1d07f94d03cd871c6d2a17c870f367b3e4d5a4a1"
MANIFESTS = {
    "source-001": "5c492e731aa53565ee59b6501831d34654689959f70963b916402ef935623ea6",
    "finite-001": "8dc1d00f4a1bfb9a88d60415cf42fb33dcc0242addc279c7b0f5a9075dbb066d",
}
PROOF_MANIFESTS = {
    "proof-001": "d74293f7e9611af2445d6c34fa0ae7267816de125e4ac0a7453266913cb83c9e",
    "negative-001": "4ea744e807d6cebb359cf72c4ba90baaceef74e4f89396336522dec1866b4a1c",
    "proof-002": "cb117a9335eb0eb3c68f238750749f6523938c9d95b67829cacab4aea1c71567",
    "negative-002": "4194411b7a448f4dbf647ef2fd8659cad59ac5841b71dceced87765d5b63cf84",
}
PROOF_COMMITS = {
    "proof-001": "dfb4afad4f326c45a9502b4825d08b06d48566c3",
    "negative-001": "dfb4afad4f326c45a9502b4825d08b06d48566c3",
    "proof-002": "2f2ea6d3deffebc7a552ec79f42ea829b9812d3e",
    "negative-002": "2f2ea6d3deffebc7a552ec79f42ea829b9812d3e",
}
DEVELOPMENT_INVENTORY_SHA256 = (
    "2c990881ea2d45f55240aeb9bfd4f51a174d66f3b132db5fd8b1c78bb6140e83"
)
DECLARATIONS_SHA256 = "2bd2e259f54ca1186ee3171a3fbeee05d049d77a59c2ce93738a6cdce32ece07"
LEAN_SHA256 = "92c3d35b5bfaa5e0fea413a775d504cf46cd95e1345df61c2274f76779e7e023"
FINITE_DEV_MANIFEST_SHA256 = (
    "6ede1d3480bd3cd592960f66a854497dc4cf6f6febcf1e354be5cadf0c3e3ee6"
)
COUNTEREXAMPLES = {
    "subclass_duplicate_commit_text",
    "subclass_hidden_evidence_iteration",
    "subclass_mid_suffix_override",
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def check_manifest(folder: Path, expected_sha: str, label: str,
                   input_commit: str) -> None:
    require(folder.is_dir() and not folder.is_symlink(),
            f"missing ordinary receipt directory: {label}")
    path = folder / "EVIDENCE_MANIFEST.json"
    require(path.is_file() and not path.is_symlink() and
            sha(path.read_bytes()) == expected_sha,
            f"changed evidence manifest: {label}")
    manifest = json.loads(path.read_text())
    require(manifest["schema"] == "sonification-mat010-execution-files/v1" and
            manifest["label"] == label and
            manifest["input_commit"] == input_commit,
            f"changed receipt identity: {label}")
    files = manifest["files_sha256"]
    observed = {str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file()}
    require(observed == set(files) | {path.name},
            f"receipt file inventory changed: {label}")
    for relative, digest in files.items():
        member_path = Path(relative)
        require(not member_path.is_absolute() and ".." not in member_path.parts,
                f"invalid receipt member: {relative}")
        member = folder / member_path
        require(member.is_file() and not member.is_symlink() and
                sha(member.read_bytes()) == digest,
                f"altered receipt file: {label}/{relative}")


def check_command(folder: Path, label: str) -> dict:
    command = json.loads((folder / f"{label}.json").read_text())
    for stream in ("stdout", "stderr"):
        require(sha((folder / f"{label}.{stream}").read_bytes()) ==
                command[f"{stream}_sha256"],
                f"altered execution stream: {folder.name}/{label}/{stream}")
    require(command["exit_code"] == 0 and command["timed_out"] is False,
            f"unsuccessful accepted proof command: {folder.name}/{label}")
    return command


def verify_proof_receipts(base: Path) -> dict:
    require({p.name for p in base.iterdir() if p.is_dir()} ==
            set(MANIFESTS) | set(PROOF_MANIFESTS) | {"finite-dev-001"},
            "MAT010 receipt directory coverage changed")
    dev = base / "finite-dev-001"
    dev_manifest = dev / "EVIDENCE_MANIFEST.json"
    require(sha(dev_manifest.read_bytes()) == FINITE_DEV_MANIFEST_SHA256,
            "finite development manifest changed")
    dev_files = json.loads(dev_manifest.read_text())["files_sha256"]
    require({p.name for p in dev.iterdir() if p.is_file()} ==
            set(dev_files) | {dev_manifest.name},
            "finite development receipt coverage changed")
    for name, digest in dev_files.items():
        require(sha((dev / name).read_bytes()) == digest,
                f"finite development file changed: {name}")
    results = {}
    for label, digest in PROOF_MANIFESTS.items():
        folder = base / label
        commit = PROOF_COMMITS[label]
        check_manifest(folder, digest, label, commit)
        result = json.loads((folder / "result.json").read_text())
        require(result["proof_input_commit"] == commit and
                result["REFINEMENT_PROVED"] == "OPEN" and
                result["lean_executable_sha256"] == LEAN_SHA256,
                f"proof receipt identity changed: {label}")
        for name, file_sha in result["proof_input_sha256"].items():
            relative = f"formal/sonification/mat010/lean/{name}"
            historical = subprocess.check_output(
                ["git", "show", f"{commit}:{relative}"], cwd=ROOT,
                timeout=30,
            )
            require(sha(historical) == file_sha,
                    f"proof input commit mismatch: {label}/{name}")
            if label in {"proof-002", "negative-002"}:
                require(sha((ROOT / relative).read_bytes()) == file_sha,
                        f"current accepted proof input drift: {name}")
        if label.startswith("proof-"):
            require(result["status"] == "PASS" and
                    result["MODEL_PROVED"] == "PASS_FOR_SCOPED_PHASE_A_MODEL" and
                    result["AUDIT_ACCEPTED"] == "PENDING_INDEPENDENT_REVIEW" and
                    result["declaration_count"] == 333 and
                    result["declarations_sha256"] == DECLARATIONS_SHA256 and
                    result["external_import_count"] == 1303 and
                    len(result["named_intended_theorems"]) == 7,
                    f"accepted proof report changed: {label}")
            for command in ("lean-version", "build-00-ArchiveModel",
                            "build-01-ArchiveConsumer", "build-02-LeanAudit"):
                check_command(folder, command)
            declarations = json.loads((folder / "declarations.json").read_text())
            require(len(declarations) == 333 and
                    sha((folder / "declarations.json").read_bytes()) ==
                    DECLARATIONS_SHA256,
                    f"complete declaration receipt changed: {label}")
            require(len(json.loads((folder / "toolchain-imports.json").read_text())) ==
                    1303 and
                    len(json.loads((folder / "theorem-types.json").read_text())) == 7 and
                    len(json.loads((folder / "named-axioms.json").read_text())) == 7,
                    f"proof import or type receipt incomplete: {label}")
            trust = json.loads((folder / "compiler-trust.json").read_text())
            require(len(trust["project_compiler_axioms"]) == 15 and
                    trust["unsafe_generated_definition_count"] == 136,
                    f"compiler trust receipt incomplete: {label}")
        else:
            expected = 5 if label == "negative-001" else 6
            require(result["status"] == ("FAIL" if expected == 5 else "PASS") and
                    len(result["cases"]) == 6 and
                    sum(row["detected"] for row in result["cases"]) == expected,
                    f"negative-control report changed: {label}")
            for summary in result["cases"]:
                case = folder / summary["mutation"]
                row = json.loads((case / "result.json").read_text())
                require(row["detected"] == summary["detected"] and
                        row["mutant_sha256"] == summary["mutant_sha256"],
                        f"negative-control case changed: {label}/{case.name}")
                mutant = (case / ("Hidden.lean" if case.name ==
                          "unimported_failing_module" else "mutant-source.lean.txt"))
                require(sha(mutant.read_bytes()) == row["mutant_sha256"],
                        f"mutant source changed: {label}/{case.name}")
                for index, command in enumerate(row["commands"]):
                    module = Path(command["argv"][-1]).stem
                    prefix = case / f"build-{index:02d}-{module}"
                    for stream in ("stdout", "stderr"):
                        require(sha(Path(f"{prefix}.{stream}").read_bytes()) ==
                                command[f"{stream}_sha256"],
                                f"negative command stream changed: {label}/{case.name}")
        results[label] = result["status"]
    return results


def verify_development(base_dir: Path = HERE) -> dict:
    base = base_dir / "lean"
    path = base_dir / "DEVELOPMENT_INVENTORY.json"
    require(path.is_file() and not path.is_symlink() and
            sha(path.read_bytes()) == DEVELOPMENT_INVENTORY_SHA256,
            "development inventory changed")
    inventory = json.loads(path.read_text())
    require(inventory["schema"] == "sonification-mat010-development-inventory/v1"
            and inventory["excluded_cache_suffix"] == ".olean",
            "development inventory schema changed")
    counts = {}
    for category, expected in inventory["manifest_sha256"].items():
        root = base / category
        require({p.name for p in root.iterdir() if p.is_dir()} == set(expected),
                f"development attempt coverage changed: {category}")
        for label, digest in expected.items():
            folder = root / label
            manifest_path = folder / "EVIDENCE_MANIFEST.json"
            require(sha(manifest_path.read_bytes()) == digest,
                    f"development manifest changed: {category}/{label}")
            manifest = json.loads(manifest_path.read_text())
            require(manifest["schema"] ==
                    "sonification-mat010-development-files/v1" and
                    manifest["label"] == label and
                    manifest["excluded_cache_suffix"] == ".olean",
                    f"development identity changed: {category}/{label}")
            files = manifest["files_sha256"]
            observed = {p.name for p in folder.iterdir()
                        if p.is_file() and p.suffix != ".olean"}
            require(observed == set(files) | {manifest_path.name},
                    f"development file coverage changed: {category}/{label}")
            for name, file_sha in files.items():
                file = folder / name
                require(file.is_file() and not file.is_symlink() and
                        sha(file.read_bytes()) == file_sha,
                        f"altered development file: {category}/{label}/{name}")
        counts[category] = len(expected)
    require(counts == {"development": 17, "audit-development": 5},
            "development attempt counts changed")
    return counts


def verify(base: Path = RECEIPTS) -> dict:
    subprocess.run(["git", "merge-base", "--is-ancestor", INPUT_COMMIT, "HEAD"],
                   cwd=ROOT, check=True, capture_output=True, timeout=30)
    reports = {}
    for name, expected_manifest_sha in MANIFESTS.items():
        folder = base / name
        require(folder.is_dir() and not folder.is_symlink(),
                f"missing ordinary receipt directory: {name}")
        manifest_file = folder / "EVIDENCE_MANIFEST.json"
        require(manifest_file.is_file() and not manifest_file.is_symlink() and
                sha(manifest_file.read_bytes()) == expected_manifest_sha,
                f"changed evidence manifest: {name}")
        manifest = json.loads(manifest_file.read_text())
        require(manifest["schema"] == "sonification-mat010-execution-files/v1" and
                manifest["label"] == name and
                manifest["input_commit"] == INPUT_COMMIT,
                f"changed receipt identity: {name}")
        files = manifest["files_sha256"]
        observed = {str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file()}
        require(observed == set(files) | {manifest_file.name},
                f"receipt file inventory changed: {name}")
        for relative, digest in files.items():
            path = Path(relative)
            require(not path.is_absolute() and ".." not in path.parts,
                    f"invalid receipt member: {relative}")
            member = folder / path
            require(member.is_file() and not member.is_symlink() and
                    sha(member.read_bytes()) == digest,
                    f"altered receipt file: {name}/{relative}")
        receipt = json.loads((folder / "receipt.json").read_text())
        require(receipt["schema"] == "sonification-mat010-execution-receipt/v1" and
                receipt["label"] == name and
                receipt["input_commit"] == INPUT_COMMIT and
                receipt["exit_code"] == 0 and
                receipt["REFINEMENT_PROVED"] == "OPEN" and
                receipt["cwd"].endswith("sonification-formal-001-mat010-closure"),
                f"execution receipt changed: {name}")
        for stream in ("stdout", "stderr"):
            require(sha((folder / f"{stream}.log").read_bytes()) ==
                    receipt[f"{stream}_sha256"],
                    f"altered execution stream: {name}/{stream}")
        require(receipt["frozen_source_sha256"] ==
                "e062474d4435e769f8c6c8407bc44ad89cfb2dfa04677b820c3a035d604a9056",
                f"frozen source identity changed: {name}")
        for relative, digest in receipt["inputs_sha256"].items():
            path = ROOT / relative
            require(path.is_file() and not path.is_symlink() and
                    sha(path.read_bytes()) == digest,
                    f"stale verification input: {relative}")
            historical = subprocess.check_output(
                ["git", "show", f"{INPUT_COMMIT}:{relative}"], cwd=ROOT,
                timeout=30,
            )
            require(sha(historical) == digest,
                    f"input commit mismatch: {relative}")
        reports[name] = receipt
    source = json.loads((base / "source-001/stdout.log").read_text())
    require(source["status"] == "SOURCE_SYNTAX_MATCH" and
            source["REFINEMENT_PROVED"] == "OPEN" and
            source["functions"] == 5,
            "source binder result changed")
    finite = json.loads((base / "finite-001/result/result.json").read_text())
    summary = json.loads((base / "finite-001/stdout.log").read_text())
    require(finite["status"] == summary["status"] ==
            "PASS_WITH_BOUNDARY_COUNTEREXAMPLES" and
            finite["case_count"] == summary["case_count"] == 28 and
            finite["exact_builtin_passed"] == summary["exact_builtin_passed"] == 23 and
            set(finite["boundary_counterexamples"]) ==
            set(summary["boundary_counterexamples"]) == COUNTEREXAMPLES and
            finite["REFINEMENT_PROVED"] == "OPEN",
            "finite conformance result changed")
    require(len(reports) == 2, "source/finite receipt coverage changed")
    proof = verify_proof_receipts(base)
    development = verify_development()
    return {
        "status": "MAT010_ALL_RETAINED_RECEIPTS_BOUND",
        "receipt_count": len(reports) + len(proof),
        "finite_cases": finite["case_count"],
        "boundary_counterexamples": sorted(COUNTEREXAMPLES),
        "proof_receipts": proof, "development_attempts": development,
        "REFINEMENT_PROVED": "OPEN",
    }


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
