#!/usr/bin/env python3
"""Offline integrity check for historical SPARK-002 Phase 1A proof receipts.

This verifies pre-existing evidence. It does NOT execute GNATprove.
SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

SOURCE_COMMIT = "06b1294bf1617e9eb3b825051e8bfbf7470e395c"
RECEIPTS = {
    "GNATPROVE_SUMMARY.txt": "71b04db9a09d292c826d2e366bd7c37e03fee33b2a3f81588f7e8d91b2715f38",
    "PROOF.log": "a4af0cb30c7f2686f5b9f7bdf526f1d99bc782a9286f5934ca1c59fb66808e92",
    "RESULT.txt": "9d4615f375c9745a87a3d8668646709762ba401db609d8695cf57f2d5cb0ee05",
    "SHA256SUMS": "5423389a13b361e3f3c338aed8c4575cd597959025b9cdc619b2ae7fc2ecc77d",
    "SOURCE_COMMIT.txt": "ddfffcbe8f175147f5516d3a066ad67b86ce35891f09aa0255680075e02734f5",
    "SOURCES.sha256": "64bd121fe4d02ca66bd39e3161dcd8893e6c8de84449263f37aa2cca15db2ee3",
    "TOOLCHAIN.txt": "d0ec78c178655565104dd97553954ba573633797216446fad8b3254aad79de55"
}
SOURCES = {
    "verification/spark002/spark_002_core.ads": "808648a2190ce8a28bd84313b7f88c4ec5fa0ca704c357bd2a44eb08fdb8e832",
    "verification/spark002/spark_002_core.adb": "0df1ee836efc96d7c506a2b8523fe4e18ca388246dfeb7697172936e05b18f17",
    "verification/spark002/spark_002_core.gpr": "91fcadee68bad68e0fd727196b4d299228a63825ae1d31412b24dc15e81b4afc"
}

def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def _entries(raw: bytes) -> dict[str, str]:
    items = {}
    for line in raw.decode("ascii").splitlines():
        if len(line) < 67 or line[64:66] != "  ":
            raise ValueError("malformed SHA256SUMS entry")
        hexdigest, name = line[:64], line[66:]
        if (not name or name.startswith("/") or ".." in Path(name).parts
                or name in items or len(hexdigest) != 64
                or any(c not in "0123456789abcdef" for c in hexdigest)):
            raise ValueError("invalid or duplicate SHA256SUMS entry")
        items[name] = hexdigest
    return items

def verify(root: Path, evidence: Path) -> dict[str, object]:
    receipt_dir = evidence / "receipts"
    if not receipt_dir.is_dir() or {x.name for x in receipt_dir.iterdir()} != set(RECEIPTS):
        raise ValueError("original receipt membership mismatch")
    raw = {}
    for name, expected in RECEIPTS.items():
        path = receipt_dir / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"missing or linked original receipt: {name}")
        raw[name] = path.read_bytes()
        if _sha(raw[name]) != expected:
            raise ValueError(f"original receipt SHA-256 mismatch: {name}")
    if _entries(raw["SHA256SUMS"]) != {
        name: expected for name, expected in RECEIPTS.items() if name != "SHA256SUMS"
    }:
        raise ValueError("original checksum declaration mismatch")
    if raw["SOURCE_COMMIT.txt"] != (SOURCE_COMMIT + "\n").encode("ascii"):
        raise ValueError("recorded merge commit mismatch")
    if _entries(raw["SOURCES.sha256"]) != SOURCES:
        raise ValueError("recorded source inventory mismatch")
    for path, expected in SOURCES.items():
        result = subprocess.run(
            ["git", "-C", str(root), "show", f"{SOURCE_COMMIT}:{path}"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False,
        )
        if result.returncode or _sha(result.stdout) != expected:
            raise ValueError(f"historical Git source identity mismatch: {path}")
    proof = raw["PROOF.log"].decode("utf-8")
    summary = raw["GNATPROVE_SUMMARY.txt"].decode("utf-8")
    if (b"SPARK-002 GNATprove exit status: 0\n" != raw["RESULT.txt"]
            or "Success: all checks proved (23 checks)." not in proof
            or "Functional Contracts             11" not in summary
            or "Termination                      12" not in summary
            or "Total                            23" not in summary
            or "11 (CVC5)" not in summary
            or "0 pragma Assume statements" not in summary
            or "SPARK_Mode => Off" not in summary):
        raise ValueError("historical proof-status markers mismatch")
    audit = json.loads((evidence / "AUDIT.json").read_text("utf-8"))
    if (audit.get("source_commit") != SOURCE_COMMIT
            or audit.get("receipt_sha256") != RECEIPTS
            or audit.get("source_sha256") != SOURCES
            or audit.get("gnatprove", {}).get("reported_checks") != 23):
        raise ValueError("derived audit metadata mismatch")
    return {"historical_source_commit": SOURCE_COMMIT,
            "original_receipts_verified": len(RECEIPTS),
            "historical_git_sources_verified": len(SOURCES),
            "reported_proof_checks": 23,
            "new_prover_run": False}

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    try:
        receipt = verify(root, root / "publication/spark-002/phase-1a")
    except (OSError, ValueError) as exc:
        print(f"SPARK-002 RECEIPT VERIFICATION FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print("SPARK-002 HISTORICAL RECEIPTS VERIFIED — NO NEW PROOF EXECUTED")
    print(json.dumps(receipt, sort_keys=True))
