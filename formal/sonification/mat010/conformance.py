#!/usr/bin/env python3
"""Finite direct-call conformance for frozen MAT010 archive membership.

The declared exact built-in cases test source behavior. Subclass probes retain
counterexamples to stronger identity expectations; they do not change expected
results after execution. No production output or audio is generated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from formal.sonification.mat010.source_bind import verify as verify_source
from materials import mat_spec_010

STAGES = tuple(f"MAT-SPEC-{number:03d}" for number in range(1, 10))
VERSION = "0.1.0"
COUNTEREXAMPLES = {
    "subclass_duplicate_commit_text",
    "subclass_hidden_evidence_iteration",
    "subclass_mid_suffix_override",
}


class IdentityText(str):
    """Equal text with object-identity equality and hashing."""

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> bool:
        return self is other


class HiddenEvidenceItems(dict):
    """Membership sees evidence, but iteration hides it."""

    def items(self):
        return ((key, value) for key, value in super().items()
                if key != "audit.json")


class DuplicateItems(dict):
    """Iteration emits one logical member twice."""

    def items(self):
        pairs = list(super().items())
        return pairs + pairs[:1]


class HiddenMidSuffix(str):
    def endswith(self, suffix, *args):
        if suffix == ".mid":
            return False
        return super().endswith(suffix, *args)


@dataclass
class Case:
    name: str
    claims: dict
    snapshots: list[tuple[str, str, dict[str, str]]]
    expected: str
    exact_builtin: bool = True
    expected_count: int | None = None
    same_as_valid: bool = False


def base() -> tuple[dict, list[tuple[str, str, dict[str, str]]]]:
    claims = {"stages": [
        {"profile": stage,
         "version": "1.0.0" if index == 1 else VERSION,
         "merged_commit": f"{index:040x}", "evidence_file": "audit.json"}
        for index, stage in enumerate(STAGES, 1)
    ]}
    snapshots = [
        (stage, "1.0.0" if index == 1 else VERSION,
         {"audit.json": f"{index:064x}",
          "contract.json": f"{index + 100:064x}"})
        for index, stage in enumerate(STAGES, 1)
    ]
    return claims, snapshots


def case(
    name: str,
    change: Callable[[dict, list], None] | None = None,
    *,
    expected: str = "ACCEPT",
    exact_builtin: bool = True,
    count: int | None = None,
    same_as_valid: bool = False,
) -> Case:
    claims, snapshots = base()
    if change is not None:
        change(claims, snapshots)
    return Case(name, claims, snapshots, expected, exact_builtin, count,
                same_as_valid)


def replace_map(snapshots: list, index: int, new: dict) -> None:
    stage, version, _ = snapshots[index]
    snapshots[index] = (stage, version, new)


def cases() -> list[Case]:
    def reordered_claims(claims: dict, _: list) -> None:
        claims["stages"][0], claims["stages"][1] = (
            claims["stages"][1], claims["stages"][0]
        )

    def reordered_snapshots(_: dict, snapshots: list) -> None:
        snapshots[0], snapshots[1] = snapshots[1], snapshots[0]

    def duplicate_commit(claims: dict, _: list) -> None:
        claims["stages"][1]["merged_commit"] = claims["stages"][0]["merged_commit"]

    def insertion_order(_: dict, snapshots: list) -> None:
        for index, (stage, version, digests) in enumerate(snapshots):
            snapshots[index] = (stage, version,
                                dict(reversed(list(digests.items()))))

    def duplicate_path(_: dict, snapshots: list) -> None:
        replace_map(snapshots, 3, DuplicateItems(snapshots[3][2]))

    def hidden_evidence(_: dict, snapshots: list) -> None:
        replace_map(snapshots, 3, HiddenEvidenceItems(snapshots[3][2]))

    def duplicate_commit_text(claims: dict, _: list) -> None:
        text = claims["stages"][0]["merged_commit"]
        claims["stages"][0]["merged_commit"] = IdentityText(text)
        claims["stages"][1]["merged_commit"] = IdentityText(text)

    return [
        case("valid_nine_stage", count=18),
        case("valid_stage001_mid", lambda c, s:
             s[0][2].update({"symbolic.mid": "a" * 64}), count=19),
        case("extra_well_formed_member", lambda c, s:
             s[3][2].update({"extra.json": "b" * 64}), count=19),
        case("missing_non_evidence_member", lambda c, s:
             s[3][2].pop("contract.json"), count=17),
        case("reversed_dict_insertion_order", insertion_order,
             count=18, same_as_valid=True),
        case("missing_claim_predecessor", lambda c, s:
             c["stages"].pop(), expected="ValueError"),
        case("missing_snapshot_predecessor", lambda c, s:
             s.pop(), expected="ValueError"),
        case("reordered_claim_predecessor", reordered_claims,
             expected="ValueError"),
        case("reordered_snapshot_predecessor", reordered_snapshots,
             expected="ValueError"),
        case("duplicate_merged_commit", duplicate_commit,
             expected="ValueError"),
        case("wrong_predecessor_version", lambda c, s:
             c["stages"][4].update({"version": "9.9.9"}),
             expected="ValueError"),
        case("missing_declared_evidence_file", lambda c, s:
             s[3][2].pop("audit.json"), expected="ValueError"),
        case("empty_artifact_map", lambda c, s:
             s[3][2].clear(), expected="ValueError"),
        case("invalid_sha256_character", lambda c, s:
             s[3][2].update({"audit.json": "g" * 64}), expected="ValueError"),
        case("invalid_sha256_length", lambda c, s:
             s[3][2].update({"audit.json": "a" * 63}), expected="ValueError"),
        case("invalid_artifact_extension", lambda c, s:
             s[3][2].update({"notes.txt": "a" * 64}), expected="ValueError"),
        case("forward_directory_separator", lambda c, s:
             s[3][2].update({"sub/extra.json": "a" * 64}),
             expected="ValueError"),
        case("backward_directory_separator", lambda c, s:
             s[3][2].update({"sub\\extra.json": "a" * 64}),
             expected="ValueError"),
        case("path_traversal", lambda c, s:
             s[3][2].update({"../extra.json": "a" * 64}),
             expected="ValueError"),
        case("dot_filename", lambda c, s:
             s[3][2].update({"..": "a" * 64}), expected="ValueError"),
        case("duplicate_logical_path", duplicate_path,
             expected="ValueError", exact_builtin=False),
        case("disallowed_mid_stage002", lambda c, s:
             s[1][2].update({"symbolic.mid": "a" * 64}),
             expected="ValueError"),
        case("uppercase_merged_commit", lambda c, s:
             c["stages"][0].update({"merged_commit": "A" * 40}),
             expected="ValueError"),
        case("short_merged_commit", lambda c, s:
             c["stages"][0].update({"merged_commit": "a" * 39}),
             expected="ValueError"),
        case("unhashable_merged_commit", lambda c, s:
             c["stages"][0].update({"merged_commit": ["a"] * 40}),
             expected="TypeError", exact_builtin=False),
        case("subclass_duplicate_commit_text", duplicate_commit_text,
             expected="ValueError", exact_builtin=False),
        case("subclass_hidden_evidence_iteration", hidden_evidence,
             expected="ValueError", exact_builtin=False),
        case("subclass_mid_suffix_override", lambda c, s:
             s[1][2].update({HiddenMidSuffix("symbolic.mid"): "a" * 64}),
             expected="ValueError", exact_builtin=False),
    ]


def canonical_sha(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def expected_exact(case_: Case) -> list[dict]:
    """Independent declared index construction for stable exact built-in maps."""
    result = []
    for stage, version, digests in case_.snapshots:
        for name in sorted(digests):
            result.append({
                "stage": stage, "version": version,
                "logical_path": f"dist/mat-spec-{stage[-3:]}/{name}",
                "sha256": digests[name],
                "content_in_this_manifest": "HASH_ONLY_REBUILD_REQUIRED",
                "audio_rendered": False,
            })
    return result


def execute() -> dict:
    source = verify_source()
    rows = []
    valid_hash = None
    for item in cases():
        try:
            actual = mat_spec_010.validate_archive_membership(
                item.claims, item.snapshots
            )
            observed = "ACCEPT"
            detail = {
                "artifact_count": len(actual),
                "artifact_sha256": canonical_sha(actual),
                "ordered_paths": [row["logical_path"] for row in actual],
            }
        except Exception as exc:
            observed = type(exc).__name__
            detail = {"exception_message": str(exc)}
        matches = observed == item.expected
        if matches and observed == "ACCEPT" and item.exact_builtin:
            expected = expected_exact(item)
            matches = actual == expected
            if item.expected_count is not None:
                matches = matches and len(actual) == item.expected_count
            if item.same_as_valid:
                matches = matches and canonical_sha(actual) == valid_hash
        if item.name == "valid_nine_stage" and observed == "ACCEPT":
            valid_hash = canonical_sha(actual)
        rows.append({
            "case": item.name, "domain": "EXACT_BUILTIN" if item.exact_builtin
            else "PYTHON_SUBCLASS_OR_MALFORMED_OBJECT",
            "expected": item.expected, "observed": observed,
            "matches_expected": matches, **detail,
        })
    mismatches = [row["case"] for row in rows if not row["matches_expected"]]
    exact_failures = [row["case"] for row in rows
                      if row["domain"] == "EXACT_BUILTIN" and
                      not row["matches_expected"]]
    status = ("PASS_WITH_BOUNDARY_COUNTEREXAMPLES"
              if not exact_failures and set(mismatches) == COUNTEREXAMPLES
              else "FAIL")
    return {
        "schema": "sonification-mat010-archive-finite/v1",
        "status": status, "source_binding": source,
        "python_version": sys.version, "python_executable": sys.executable,
        "cases": rows, "case_count": len(rows),
        "exact_builtin_passed": sum(row["domain"] == "EXACT_BUILTIN" and
                                    row["matches_expected"] for row in rows),
        "boundary_counterexamples": mismatches,
        "REFINEMENT_PROVED": "OPEN",
        "DIFFERENTIAL_TESTED": "PASS_FOR_DECLARED_EXACT_BUILTIN_CASES_ONLY"
        if status != "FAIL" else "FAILED",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    result = execute()
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": result["status"], "case_count": result["case_count"],
        "exact_builtin_passed": result["exact_builtin_passed"],
        "boundary_counterexamples": result["boundary_counterexamples"],
    }, sort_keys=True))
    raise SystemExit(0 if result["status"] != "FAIL" else 1)
