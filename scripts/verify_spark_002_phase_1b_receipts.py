#!/usr/bin/env python3
"""Offline integrity audit of retained SPARK-002 Phase 1B GNATprove receipts.

No prover is invoked. Original receipt bytes are pinned to known SHA-256s.
SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

SOURCE_COMMIT = "6f0f1be1ba8885fa708d7328bcb92fbf4ecc324f"
RECEIPTS = {
    "GNATPROVE_SUMMARY.txt": (
        "ba472f544021d95b9b98a0e9bd99c0f3b57405120694653b59253aff11b6a00e"
    ),
    "PROOF.log": "5ec7eb817083d4d4466efe08a8d221576ee418bc58d3cdc33adc0fe0a63bf335",
    "RESULT.txt": "b577143f56c972bebd14855c00a4ba58cfd5ac93e8e8cccf56367c8025bf20da",
    "SHA256SUMS": "3299ff07ff6e3a2c104956dc9b2a168ea028291a90708dee3071077c4368efa1",
    "SOURCE_COMMIT.txt": (
        "8a663cd33dd12b70edd85343dd2df962660bd1bb72cea3b644f64a208e21d0b1"
    ),
    "SOURCES.sha256": (
        "f8993becc76f30d8669b3211afb50d0f24f3cc026936f6fbdb774a9b81fc5872"
    ),
    "TOOLCHAIN.txt": "d0ec78c178655565104dd97553954ba573633797216446fad8b3254aad79de55",
}
SOURCES = {
    "verification/spark002/phase1b/spark_002_partition.ads": (
        "7242919b7385a0726064ffc22ac20133"
        "099564cdcf5bcd811944ab176cb87ac0"
    ),
    "verification/spark002/phase1b/spark_002_partition.adb": (
        "6b9887c12694001be9f627a91d159cd"
        "57d57af65770023c2bfd7c791f12760a2"
    ),
    "verification/spark002/phase1b/spark_002_partition.gpr": (
        "41a00e231762e0907fccc2e2f06d99f"
        "6bbf470d7d2a19845b0efaac0654c6a9d"
    ),
}
PROOF_STATUS = "ALL_9_REPORTED_CHECKS_PROVED"
CLOSURE = "NUMBERED_SERIES_CLOSED_AT_010_WITH_OPEN_SCIENTIFIC_GATES"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _entries(raw: bytes) -> dict[str, str]:
    if not raw.endswith(b"\n"):
        raise ValueError("checksum file must end with a newline")
    entries: dict[str, str] = {}
    for line in raw.decode("ascii").splitlines():
        match = re.fullmatch(r"([a-f0-9]{64})  ([A-Za-z0-9_./-]+)", line)
        if not match:
            raise ValueError("malformed SHA-256 manifest entry")
        digest, name = match.groups()
        if (name in entries or name.startswith("/") or
                any(part in (".", "..") for part in name.split("/"))):
            raise ValueError("duplicate or unsafe SHA-256 manifest path")
        entries[name] = digest
    return entries


def _historical_sources(root: Path) -> None:
    """Verify the pinned source from historical Git objects, not the PR head."""
    for path, digest in SOURCES.items():
        result = subprocess.run(
            ["git", "-C", str(root), "show", f"{SOURCE_COMMIT}:{path}"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=20,
        )
        if result.returncode != 0 or _sha(result.stdout) != digest:
            raise ValueError(f"pinned historical Git source mismatch: {path}")


def _proof_markers(raw: dict[str, bytes]) -> None:
    if raw["RESULT.txt"] != b"SPARK-002 Phase 1B GNATprove exit status: 0\n":
        raise ValueError("recorded GNATprove exit status is not zero")
    proof = raw["PROOF.log"].decode("utf-8")
    summary = raw["GNATPROVE_SUMMARY.txt"].decode("utf-8")
    toolchain = raw["TOOLCHAIN.txt"].decode("utf-8")
    expected_proof = (
        "Success: all checks proved (9 checks).",
        "postcondition proved (CVC5: 5 VC",
        "postcondition proved (CVC5: 9 VC",
        "Trivial: 2 VC",
    )
    expected_summary = (
        "Functional Contracts              2",
        "Termination                       7",
        "Total                             9",
        "Analyzed 2 units",
        "8 subprograms and packages out of 8 analyzed",
        "skipped; SPARK_Mode => Off",
        "0 pragma Assume statements",
    )
    if (not all(marker in proof for marker in expected_proof) or
            not all(marker in summary for marker in expected_summary)):
        raise ValueError("historical GNATprove proof marker mismatch")
    if not re.search(r"(?m)^Run-time Checks\s+\.\s+\.\s+\.\s+\.\s+\.$", summary):
        raise ValueError("runtime check summary mismatch")
    if not re.search(r"(?m)^Total\s+9\s+7\s+\(78%\)\s+2\s+\(22%\)\s+\.\s+\.$",
                     summary):
        raise ValueError("reported proof count or unproved column mismatch")
    if "alr 2.1.1" not in toolchain or "FSF 16.1.0" not in toolchain:
        raise ValueError("recorded GNATprove toolchain mismatch")


def _audit_matches(evidence: Path) -> None:
    audit_path = evidence / "AUDIT.json"
    if not audit_path.is_file() or audit_path.is_symlink():
        raise ValueError("missing or linked derived audit")
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    proof = audit.get("gnatprove", {})
    science = audit.get("admission_boundary", {})
    if (audit.get("schema") != "qsol.spark-002.phase-1b.proof-receipt-audit/v1" or
            audit.get("source_commit") != SOURCE_COMMIT or
            audit.get("receipt_sha256") != RECEIPTS or
            audit.get("source_sha256") != SOURCES or
            audit.get("publication_state") != "GIT_PROOF_RECEIPT_PRESERVATION_ONLY" or
            proof.get("status") != PROOF_STATUS or
            proof.get("exit_status") != 0 or
            proof.get("reported_checks") != 9 or
            proof.get("functional_contract_checks") != 2 or
            proof.get("termination_checks") != 7 or
            proof.get("runtime_checks_separately_reported") != 0 or
            proof.get("unproved") != 0 or
            proof.get("justified") != 0 or
            proof.get("pragma_assume_statements_reported") != 0 or
            proof.get("non_spark_probe_excluded") is not True or
            science.get("mat_spec_closure") != CLOSURE or
            science.get("physical_evidence_authenticated") is not False or
            science.get("classifier_score_established") is not False):
        raise ValueError("derived audit metadata mismatch")


def verify(root: Path, evidence: Path) -> dict[str, object]:
    receipt_dir = evidence / "receipts"
    if (not receipt_dir.is_dir() or receipt_dir.is_symlink() or
            {p.name for p in receipt_dir.iterdir()} != set(RECEIPTS)):
        raise ValueError("original receipt membership mismatch")
    raw: dict[str, bytes] = {}
    for name, digest in RECEIPTS.items():
        path = receipt_dir / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"missing or linked original receipt: {name}")
        raw[name] = path.read_bytes()
        if _sha(raw[name]) != digest:
            raise ValueError(f"original receipt SHA-256 mismatch: {name}")
    manifest = _entries(raw["SHA256SUMS"])
    if manifest != {name: digest for name, digest in RECEIPTS.items()
                    if name != "SHA256SUMS"}:
        raise ValueError("original checksum declaration mismatch")
    if raw["SOURCE_COMMIT.txt"] != (SOURCE_COMMIT + "\n").encode("ascii"):
        raise ValueError("recorded source commit mismatch")
    if _entries(raw["SOURCES.sha256"]) != SOURCES:
        raise ValueError("original source inventory mismatch")
    _historical_sources(root)
    _proof_markers(raw)
    _audit_matches(evidence)
    return {
        "historical_source_commit": SOURCE_COMMIT,
        "original_receipts_verified": len(RECEIPTS),
        "historical_sources_verified": len(SOURCES),
        "reported_proof_checks": 9,
        "unproved": 0,
        "new_prover_run": False,
        "physical_evidence_admitted": False,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    evidence = root / "publication/spark-002/phase-1b"
    try:
        result = verify(root, evidence)
    except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired) as exc:
        print(f"SPARK-002 PHASE 1B RECEIPT VERIFICATION FAILED: {exc}", file=sys.stderr)
        return 1
    print("SPARK-002 PHASE 1B HISTORICAL PROOF VERIFIED; GNATPROVE NOT RERUN")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
