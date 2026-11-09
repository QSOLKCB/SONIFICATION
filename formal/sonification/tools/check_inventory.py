#!/usr/bin/env python3
"""Check independently authored public inventory records; no proof inference."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / "formal/sonification"
DIMENSIONS = ("MODEL_PROVED", "REFINEMENT_PROVED", "DIFFERENTIAL_TESTED", "AUDIT_ACCEPTED")
STATES = {"OPEN", "FAILED", "BLOCKED", "NOT_EXECUTED", "NOT_RUN", "PASS"}


def validate_map(data: dict) -> None:
    if data["target_commit"] != "8c62517138e3b86a4672d8969e190b747f81c398":
        raise ValueError("wrong production baseline")
    if not data["targets"]:
        raise ValueError("empty target inventory")
    ids = [entry["id"] for entry in data["targets"]]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate target")
    for entry in data["targets"]:
        if set(entry["assurance"]) != set(DIMENSIONS):
            raise ValueError("missing independent assurance dimension")
        if any(state not in STATES for state in entry["assurance"].values()):
            raise ValueError("invalid assurance state")
        for dimension in DIMENSIONS:
            if entry["assurance"][dimension] == "PASS" and not entry["evidence"].get(dimension):
                raise ValueError(f"unsupported {dimension} promotion")
        if (entry["assurance"]["REFINEMENT_PROVED"] == "PASS"
                and not entry.get("refinement_theorem")):
            raise ValueError("missing source refinement theorem")


def main() -> int:
    subprocess.run([sys.executable, str(HERE / "tools/inventory.py"), "--check"],
                   cwd=ROOT, check=True)
    data = json.loads((HERE / "theorem-map.json").read_text())
    validate_map(data)
    print(json.dumps({"status": "INVENTORY_CONSISTENT", "proof_acceptance": "NOT_INFERRED",
                      "targets": len(data["targets"]), "dimensions": list(DIMENSIONS)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
