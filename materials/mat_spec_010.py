"""MAT-SPEC-010: final numbered evidence freeze, source ledger and archive index.

SPDX-License-Identifier: MPL-2.0
Copyright (c) 2026 Trent Slade / QSOL-IMC.

A successful deterministic replay is NOT independent physical replication,
a proof of interpretation, a listening test or a SPARK/Lean verification.
No sampled waveform, PCM, WAV or rendered audio is generated.
"""
from __future__ import annotations

import json
import os
import stat
from contextlib import suppress
from pathlib import Path, PurePosixPath

from materials import (
    mat_spec, mat_spec_002, mat_spec_003, mat_spec_004, mat_spec_005,
    mat_spec_006, mat_spec_007, mat_spec_008, mat_spec_009,
)

PROFILE = "MAT-SPEC-010"
VERSION = "0.1.0"
FINAL_NUMBER = 10
PARENT_COMMIT = "0758a96360726aafbb07abed34620eda178407ae"
FOUNDATIONAL_DOI = "10.5281/zenodo.24062652"
SPEC_PATH = "spec/mat-spec-010.v0.1.json"
CLAIMS_PATH = "data/materials/helium4/mat_spec_010_claim_registry.json"
SOURCES_PATH = "data/materials/helium4/mat_spec_010_source_inventory.json"
IMPLEMENTATION_PATHS = (
    "materials/mat_spec_010.py", "scripts/build_mat_spec_010.py",
)
OUTPUT_NAMES = frozenset({
    "contract.json", "claims.json", "source-inventory.json",
    "archive-index.json", "closure-gate.json", "handoff.json",
    "audit.json", "manifest.json",
})
STAGES = tuple(f"MAT-SPEC-{n:03d}" for n in range(1, 10))
# Pin the seven MAT-SPEC-009 receipts from merged-main CI before review.
PARENT_V9_SHA256: dict[str, str] | None = None

EXPECTED_SPEC = json.loads(
    "{\"profile\":\"MAT-SPEC-010\",\"version\":\"0.1.0\",\"name\":\"Final numbere"
    "d MAT-SPEC evidence closure and reproducible archive index\",\"fina"
    "l_numbered_profile\":\"MAT-SPEC-010\",\"numbered_profiles_total\":10,\""
    "parent_profile\":\"MAT-SPEC-009 v0.1.0\",\"parent_commit\":\"0758a96360"
    "726aafbb07abed34620eda178407ae\",\"source_replay_requirement\":\"All "
    "prior nine profiles replayed by MAT-SPEC-009 descendant chain, wi"
    "th known digests for each logical output\",\"latest_profile_status\""
    ":\"BLOCKED_NO_ADMITTED_SOURCE_SEPARATED_PHYSICAL_EVIDENCE\",\"scient"
    "ific_claims\":\"Frozen claim levels and exclusions for each of MAT-"
    "SPEC-001 through -009; no new helium phase inference in this clos"
    "ing profile\",\"archive_definition\":\"Deterministic JSON index of lo"
    "gical artifact paths and input files with SHA-256; NOT ZIP, TAR, "
    "deposited data or independent DOI\",\"release_rule\":\"External immut"
    "able tag and release may be created only after owner merge and CI"
    "; no release SHA anticipated inside its own contents\",\"allowed_ru"
    "ntime_outputs\":\"Canonical ASCII JSON/CSV only, including preexist"
    "ing symbolic MIDI SHA-256 identities but no rendered audio\",\"clos"
    "ure\":\"NUMBERED_SERIES_CLOSED_AT_010_WITH_OPEN_SCIENTIFIC_GATES\",\""
    "post_010_order\":[\"SONIFICATION_SPARK_ADA_PROOF_AND_DIFFERENTIAL_E"
    "XECUTION\",\"VANILLAJS_LEAN_TO_ECMA_REFINEMENT_REPAIR\"],\"future_mat"
    "erial_research\":\"separate post-MAT-SPEC programme; never add MAT-"
    "SPEC-011\",\"claim_policy\":\"Executed numerical proofs/tests distinc"
    "t from physics, source independence, listener perception, statist"
    "ical significance and formal verification\",\"foundational_doi\":\"10"
    ".5281/zenodo.24062652\",\"new_doi\":null}"
)
EXPECTED_CLAIMS = json.loads(
    "{\"profile\":\"MAT-SPEC-010\",\"version\":\"0.1.0\",\"foundational_mat_spe"
    "c_001_doi\":\"10.5281/zenodo.24062652\",\"stages\":[{\"profile\":\"MAT-SP"
    "EC-001\",\"version\":\"1.0.0\",\"merged_commit\":\"195b325097cd01f16e9ca9"
    "09edd95482d4863c27\",\"tag\":null,\"grade\":\"MEASURED_SPECTRAL_NUMERIC"
    "AL_REPLAY\",\"finding\":\"Seven-pressure helium-4 neutron-dispersion "
    "table preserved with symbolic mappings, observed/missing cells an"
    "d reproducible provenance\",\"evidence_file\":\"audit.json\",\"boundary"
    "\":\"No inference of new helium phase law, listening perception, or"
    " unification\"},{\"profile\":\"MAT-SPEC-002\",\"version\":\"0.1.0\",\"merge"
    "d_commit\":\"c400a27e16cc1ed63efc6657dbdd25d003b7bdbb\",\"tag\":null,\""
    "grade\":\"MEASURED_INTERVAL_AND_SAMPLING_AUDIT\",\"finding\":\"Matched-"
    "q interval ordering and sampling invariants over the frozen neutr"
    "on-dispersion source\",\"evidence_file\":\"audit.json\",\"boundary\":\"Re"
    "ported errors are not covariance or calibrated probability distri"
    "butions\"},{\"profile\":\"MAT-SPEC-003\",\"version\":\"0.1.0\",\"merged_com"
    "mit\":\"c15ef3223e78cffad1494d99ad6edbdb41195362\",\"tag\":\"mat-spec-0"
    "03-v0.1.0\",\"grade\":\"MEASURED_MODE_FEATURE_ANALYSIS\",\"finding\":\"Ph"
    "onon, maxon and roton feature comparisons retain missingness and "
    "mark post-hoc common coverage as exploratory\",\"evidence_file\":\"co"
    "ntrols.json\",\"boundary\":\"Coverage-core roton results are explorat"
    "ory, not preregistered discovery\"},{\"profile\":\"MAT-SPEC-004\",\"ver"
    "sion\":\"0.1.0\",\"merged_commit\":\"eac0659cbae1392bf63632ec8138005367"
    "e63304\",\"tag\":\"mat-spec-004-v0.1.0\",\"grade\":\"MODEL_INPUT_TEMPERAT"
    "URE_SYMBOLIC_ANALYSIS\",\"finding\":\"Eight published helium-II tempe"
    "rature model inputs mapped with exact mass-fraction closure\",\"evi"
    "dence_file\":\"audit.json\",\"boundary\":\"Published model inputs are n"
    "ot independently observed phase labels\"},{\"profile\":\"MAT-SPEC-005"
    "\",\"version\":\"0.1.0\",\"merged_commit\":\"5b4c89b795beb7fc8c4f7d86ce2a"
    "2fb510cb6cb2\",\"tag\":\"mat-spec-005-v0.1.0\",\"grade\":\"EVALUATED_REFE"
    "RENCE_CROSS_TRANSITION_REPLAY\",\"finding\":\"Fourteen evaluated SVP "
    "reference temperatures span the lambda boundary, preserving zero "
    "versus out-of-domain null distinctions\",\"evidence_file\":\"phase-ga"
    "te.json\",\"boundary\":\"Reference values are not a new measured disc"
    "ontinuity or independent phase classifier\"},{\"profile\":\"MAT-SPEC-"
    "006\",\"version\":\"0.1.0\",\"merged_commit\":\"c1abb62e8914f6790b5da5a51"
    "adf330b813b0530\",\"tag\":\"mat-spec-006-v0.1.0\",\"grade\":\"PRIMARY_PRO"
    "CESSED_EXPERIMENTAL_TABLE_REPLAY\",\"finding\":\"Twelve published gra"
    "vity-corrected and averaged Lipa-Chui experimental heat-capacity "
    "rows preserved across lambda\",\"evidence_file\":\"phase-gate.json\",\""
    "boundary\":\"One original processed campaign, no per-row errors or "
    "orthogonal phase diagnostics\"},{\"profile\":\"MAT-SPEC-007\",\"version"
    "\":\"0.1.0\",\"merged_commit\":\"b97348ff8fcf3f57764dec21a8914f153f96a7"
    "45\",\"tag\":null,\"grade\":\"SECONDARY_PUBLISHED_FIT_CONCORDANCE\",\"fin"
    "ding\":\"Four published critical-fit summaries trace four acquisiti"
    "on campaigns across three laboratory families\",\"evidence_file\":\"r"
    "eplication-gate.json\",\"boundary\":\"Secondary fit uncertainty boxes"
    " do not authenticate original measurement rows or new experimenta"
    "l replication\"},{\"profile\":\"MAT-SPEC-008\",\"version\":\"0.1.0\",\"merg"
    "ed_commit\":\"b4247877dd471e2e9d4986c86bdc1f11b14e43f8\",\"tag\":null,"
    "\"grade\":\"DOCUMENT_LINEAGE_AND_NEGATIVE_MEASUREMENT_ADMISSION\",\"fi"
    "nding\":\"Ten literature records, four campaigns and only one campa"
    "ign with source-pinned processed measurements\",\"evidence_file\":\"a"
    "dmission.json\",\"boundary\":\"Zero eligible independently sourced me"
    "asurement-campaign pairs; no classifier score\"},{\"profile\":\"MAT-S"
    "PEC-009\",\"version\":\"0.1.0\",\"merged_commit\":\"0758a96360726aafbb07a"
    "bed34620eda178407ae\",\"tag\":null,\"grade\":\"PROSPECTIVE_PROTOCOL_AND"
    "_SYNTHETIC_NEGATIVE_CONTROLS\",\"finding\":\"Fourteen synthetic prove"
    "nance/holdout controls reject evidence leakage; prospective proto"
    "col remains blocked for actual physics\",\"evidence_file\":\"split-pr"
    "otocol.json\",\"boundary\":\"Synthetic controls and prospective metad"
    "ata are not physical training, source-separated accuracy or prere"
    "gistered old experiments\"}]}"
)
EXPECTED_SOURCES = json.loads(
    "{\"profile\":\"MAT-SPEC-010\",\"version\":\"0.1.0\",\"source_stages\":[{\"pr"
    "ofile\":\"MAT-SPEC-001\",\"data_kind\":\"PUBLISHED_NEUTRON_SPECTRAL_MEA"
    "SUREMENTS\",\"paths\":[\"data/materials/helium4/DispersionAllPressure"
    "s.txt\",\"data/materials/helium4/source.json\"],\"note\":\"Original att"
    "ributed measured neutron-dispersion table; finite cells with miss"
    "ing values\"},{\"profile\":\"MAT-SPEC-002\",\"data_kind\":\"REUSES_MAT_SP"
    "EC_001_MEASUREMENTS\",\"paths\":[],\"note\":\"No independently acquired"
    " data; exact interval and sampling controls on frozen MAT-SPEC-00"
    "1\"},{\"profile\":\"MAT-SPEC-003\",\"data_kind\":\"REUSES_MAT_SPEC_001_ME"
    "ASUREMENTS\",\"paths\":[],\"note\":\"No new measured source; phonon/max"
    "on/roton features preserve missingness\"},{\"profile\":\"MAT-SPEC-004"
    "\",\"data_kind\":\"PUBLISHED_MODEL_INPUT_TABLE\",\"paths\":[\"data/materi"
    "als/helium4/temperature_table1_2022.csv\",\"data/materials/helium4/"
    "temperature_table1_2022.source.json\"],\"note\":\"Eight published mod"
    "el-input temperature rows, not original independent phase measure"
    "ments\"},{\"profile\":\"MAT-SPEC-005\",\"data_kind\":\"EVALUATED_REFERENC"
    "E_COMPILATION\",\"paths\":[\"data/materials/helium4/nist_svp_lambda_r"
    "eference_1998.csv\",\"data/materials/helium4/nist_svp_lambda_refere"
    "nce_1998.source.json\"],\"note\":\"Donnelly-Barenghi recommended expe"
    "rimental-reference property values, not one raw run\"},{\"profile\":"
    "\"MAT-SPEC-006\",\"data_kind\":\"ORIGINAL_EXPERIMENTER_PROCESSED_MEASU"
    "REMENTS\",\"paths\":[\"data/materials/helium4/lipa_chui_1984_excerpt."
    "csv\",\"data/materials/helium4/lipa_chui_1984.source.json\",\"data/ma"
    "terials/helium4/mat_spec_006_source_inventory.json\"],\"note\":\"Twel"
    "ve gravity-corrected and averaged Lipa-Chui rows from one campaig"
    "n, no row-level uncertainties\"},{\"profile\":\"MAT-SPEC-007\",\"data_k"
    "ind\":\"SECONDARY_CRITICAL_FIT_SUMMARY\",\"paths\":[\"data/materials/he"
    "lium4/mat_spec_007_svp_fit_summaries.csv\",\"data/materials/helium4"
    "/mat_spec_007_svp_fit_summaries.source.json\"],\"note\":\"Four review"
    " fit summaries with original acquisition lineage; not four source"
    "-pinned raw measurement corpora\"},{\"profile\":\"MAT-SPEC-008\",\"data"
    "_kind\":\"DOCUMENT_PROVENANCE_CATALOGUE\",\"paths\":[\"data/materials/h"
    "elium4/mat_spec_008_source_catalogue.json\"],\"note\":\"Ten publicati"
    "on records; one source-pinned original processed measurement camp"
    "aign\"},{\"profile\":\"MAT-SPEC-009\",\"data_kind\":\"PROSPECTIVE_TEST_PR"
    "OTOCOL\",\"paths\":[],\"note\":\"No new physical data; fourteen synthet"
    "ic negative controls are not experimental measurements\"}],\"notes\""
    ":\"Exact attributed source data at each stage, rather than treatin"
    "g publications, fitted models or synthetic controls as independen"
    "t experiments.\"}"
)


def _read_frozen_json(root: Path, path: str, frozen: dict) -> tuple[dict, bytes]:
    source = mat_spec.read_regular(root / path)
    try:
        parsed = json.loads(source)
    except (UnicodeDecodeError, ValueError) as exc:
        raise ValueError(f"invalid frozen MAT-SPEC-010 input {path}") from exc
    if parsed != frozen:
        raise ValueError(f"frozen MAT-SPEC-010 scientific contract drift: {path}")
    return parsed, source


def ancestor_artifact_maps(
    stage_009: dict[str, str] | None = None,
) -> list[tuple[str, str, dict[str, str]]]:
    """Recover pinned receipts from the executed, linked 001..009 code."""
    return [
        ("MAT-SPEC-001", "1.0.0", mat_spec_002.PARENT_ARTIFACT_SHA256),
        ("MAT-SPEC-002", "0.1.0", mat_spec_003.PARENT_V2_SHA256),
        ("MAT-SPEC-003", "0.1.0", mat_spec_004.PARENT_V3_SHA256),
        ("MAT-SPEC-004", "0.1.0", mat_spec_005.PARENT_V4_SHA256),
        ("MAT-SPEC-005", "0.1.0", mat_spec_006.PARENT_V5_SHA256),
        ("MAT-SPEC-006", "0.1.0", mat_spec_007.PARENT_V6_SHA256),
        ("MAT-SPEC-007", "0.1.0", mat_spec_008.PARENT_V7_SHA256),
        ("MAT-SPEC-008", "0.1.0", mat_spec_009.PARENT_V8_SHA256),
        ("MAT-SPEC-009", "0.1.0", PARENT_V9_SHA256 or stage_009),
    ]


def validate_archive_membership(
    claims: dict, snapshots: list[tuple[str, str, dict[str, str]]]
) -> list[dict]:
    """Audit unique output identities and exact stage claim/member coverage."""
    stages = claims["stages"]
    if (
        len(stages) != 9 or len(snapshots) != 9
        or tuple(s["profile"] for s in stages) != STAGES
        or tuple(item[0] for item in snapshots) != STAGES
        or len({row["merged_commit"] for row in stages}) != 9
    ):
        raise ValueError("missing, repeated or reordered frozen profile claims")
    artifacts = []
    for stage, (identifier, version, digests) in zip(
        stages, snapshots, strict=True
    ):
        if (
            not isinstance(digests, dict)
            or not digests
            or stage["version"] != version
            or stage["evidence_file"] not in digests
            or len(stage["merged_commit"]) != 40
            or any(c not in "0123456789abcdef" for c in stage["merged_commit"])
        ):
            raise ValueError("invalid frozen MAT-SPEC output membership")
        for name, digest in sorted(digests.items()):
            if (
                not isinstance(name, str)
                or "/" in name or "\\" in name or name in ("", ".", "..")
                or Path(name).suffix not in {".json", ".csv", ".mid"}
                or not isinstance(digest, str) or len(digest) != 64
                or any(ch not in "0123456789abcdef" for ch in digest)
                or (name.endswith(".mid") and identifier != "MAT-SPEC-001")
            ):
                raise ValueError("malformed ancestor artifact identity")
            artifacts.append({
                "stage": identifier, "version": version,
                "logical_path": (
                    f"dist/mat-spec-{identifier[-3:]}/{name}"
                ),
                "sha256": digest,
                "content_in_this_manifest": "HASH_ONLY_REBUILD_REQUIRED",
                "audio_rendered": False,
            })
    if (
        len({row["logical_path"] for row in artifacts}) != len(artifacts)
        or artifacts[-1]["stage"] != "MAT-SPEC-009"
    ):
        raise ValueError("repeated logical archive path")
    return artifacts


def _repo_inputs(sources: dict) -> list[tuple[str, str]]:
    """Explicit source code, tests, raw excerpts, contracts and documentation."""
    entries = [
        ("AGENTS.md", "POLICY"),
        ("README.md", "PUBLIC_PROJECT_OVERVIEW"),
        (".github/workflows/tests.yml", "CI_RECIPE"),
        ("docs/MAT_SPEC_007_TO_010.md", "ORIGINAL_STOP_AT_010_DECISION"),
        (CLAIMS_PATH, "FROZEN_CLAIM_REGISTRY"),
        (SOURCES_PATH, "FROZEN_SOURCE_INVENTORY"),
        (SPEC_PATH, "FROZEN_010_CONTRACT"),
        ("docs/MAT_SPEC_010_HANDOFF.md", "POST_RESEARCH_HANDOFF"),
    ]
    for n in range(1, FINAL_NUMBER + 1):
        label = f"{n:03d}"
        suffix = "" if n == 1 else f"_{label}"
        for base, role in (
            (f"materials/mat_spec{suffix}.py", "IMPLEMENTATION"),
            (f"scripts/build_mat_spec{suffix}.py", "BUILDER"),
            (f"tests/test_mat_spec{suffix}.py", "NEGATIVE_AND_REPLAY_TESTS"),
            (f"docs/MAT_SPEC_{label}.md", "METHODS_AND_NONCLAIMS"),
        ):
            entries.append((base, role))
        if n != 2:
            ver = "v1" if n == 1 else "v0.1"
            entries.append((f"spec/mat-spec-{label}.{ver}.json", "PROFILE_CONTRACT"))
    for row in sources["source_stages"]:
        for path in row["paths"]:
            entries.append((path, row["data_kind"]))
    if len({path for path, _ in entries}) != len(entries):
        raise ValueError("source registry has duplicate archive member paths")
    return sorted(entries)


def _source_index(root: Path, sources: dict) -> list[dict]:
    records = []
    for path, role in _repo_inputs(sources):
        if (
            path.startswith("/") or "\\" in path
            or any(piece in ("", ".", "..") for piece in path.split("/"))
            or Path(path).suffix not in {".py", ".json", ".csv", ".txt", ".md", ".yml"}
        ):
            raise ValueError("invalid source archive input path")
        content = mat_spec.read_regular(root / path)
        records.append({
            "path": path, "role": role, "sha256": mat_spec.sha256(content),
            "bytes": len(content), "materialized_in_repository": True,
        })
    return records


def verify_parent(parent: dict[str, bytes]) -> tuple[dict, dict, dict]:
    if set(parent) != mat_spec_009.OUTPUT_NAMES:
        raise ValueError("MAT-SPEC-009 ancestor file membership drift")
    checks = {name: mat_spec.sha256(data) for name, data in parent.items()}
    if PARENT_V9_SHA256 is not None and checks != PARENT_V9_SHA256:
        raise ValueError("MAT-SPEC-009 immutable output SHA-256 mismatch")
    manifest = json.loads(parent["manifest.json"])
    if (
        manifest.get("profile") != "MAT-SPEC-009"
        or manifest.get("version") != "0.1.0"
        or manifest.get("parent_commit") != mat_spec_009.PARENT_COMMIT
        or manifest.get("foundational_mat_spec_001_doi") != FOUNDATIONAL_DOI
        or set(manifest["outputs"]) != set(parent) - {"manifest.json"}
        or any(
            name not in parent or mat_spec.sha256(parent[name]) != d["sha256"]
            for name, d in manifest["outputs"].items()
        )
    ):
        raise ValueError("invalid sealed MAT-SPEC-009 parent manifest")
    split = json.loads(parent["split-protocol.json"])
    audit = json.loads(parent["audit.json"])
    gate = json.loads(parent["source-gate.json"])
    if (
        split.get("status") != (
            "BLOCKED_NO_ADMITTED_SOURCE_SEPARATED_PHYSICAL_EVIDENCE"
        )
        or split.get("training_campaigns") != 0
        or split.get("heldout_campaigns") != 0
        or split.get("physical_records_assigned") != 0
        or split.get("classifier_trained") is not False
        or split.get("holdout_accuracy") is not None
        or split.get("physical_evidence_admitted") is not False
        or audit.get("synthetic_negative_controls_passed") != 14
        or audit.get("synthetic_negative_controls_executed") != 14
        or audit.get("physical_validation_experiments_performed") != 0
        or audit.get("phase_classifier_accuracy") is not None
        or gate.get("parent_status") != (
            "BLOCKED_INSUFFICIENT_INDEPENDENT_MEASUREMENT_DATA"
        )
        or gate.get("independent_measurement_pairs") != 0
        or gate.get("calibrated_uncertainty_rows") != 0
        or gate.get("independent_diagnostic_rows") != 0
    ):
        raise ValueError("attempted promotion of unsupported physical claims")
    return split, audit, gate


def science_closure(split: dict, audit: dict, gate: dict) -> dict:
    """Closed software programme; physical validation remains explicitly open."""
    if (
        split["holdout_accuracy"] is not None
        or audit["phase_classifier_accuracy"] is not None
        or gate["physical_evidence_admitted"] is not False
    ):
        raise ValueError("physical admission invariant failed")
    return {
        "profile": PROFILE, "version": VERSION,
        "status": "NUMBERED_SERIES_CLOSED_AT_010_WITH_OPEN_SCIENTIFIC_GATES",
        "numbered_profiles": 10, "predecessor_profiles_replayed": 9,
        "mat_spec_011_allowed": False,
        "scientific_input_status": gate["parent_status"],
        "source_separated_phase_validation": split["status"],
        "independent_experimental_replication": "NOT_DEMONSTRATED",
        "real_classifier_trained": False,
        "real_heldout_accuracy": None,
        "human_auditory_test": "NOT_PERFORMED",
        "new_critical_exponent": "NOT_FITTED",
        "E8_or_unification": "NOT_CLAIMED",
        "synthetic_negative_controls_passed": audit[
            "synthetic_negative_controls_passed"
        ],
        "external_research_archive_deposited": False,
        "new_doi_assigned": None,
        "post_series_work": [
            "SPARK_ADA_KERNEL_PROOF_AND_DIFFERENTIAL_EXECUTION",
            "VANILLAJS_LEAN_TO_ECMA_REFINEMENT_REPAIR",
        ],
        "formal_proof_executed_in_this_profile": False,
    }


def handoff_plan() -> dict:
    return {
        "profile": PROFILE, "version": VERSION,
        "research_profile_series": "CLOSED_AT_MAT_SPEC_010",
        "next_projects": [
            {
                "order": 1, "name": "SPARK_ADA_KERNEL_PROOF",
                "repository": "QSOLKCB/SONIFICATION",
                "scope": (
                    "Bounded exact interval order, signed-decimal parsing, "
                    "missingness and source-lineage kernel; prove contracts "
                    "and run independent Ada-Python differential vectors"
                ),
                "proof_toolchain": "GNATprove plus GNAT, versions not yet pinned",
                "status": "NOT_STARTED",
                "proof_result": None,
            },
            {
                "order": 2, "name": "VANILLAJS_LEAN_TO_ECMASCRIPT_REFINEMENT",
                "repository": "QSOLKCB/VANILLAJS",
                "open_obligation": "docs/Q16_FORMAL_001.md: REFINEMENT_OPEN",
                "scope": (
                    "Source-constrained Lean refinement for specified "
                    "ECMAScript Number and ToInt32/ToUint32 domains with "
                    "negative zero, NaN, infinities, bounds and throws"
                ),
                "historic_proof_seals_must_be_preserved": True,
                "status": "NOT_STARTED",
                "proof_result": None,
            },
        ],
        "new_mat_spec_profiles_permitted": False,
        "external_release_archive": "REQUIRES_LATER_OWNER_RELEASE_AND_PUBLICATION",
    }


def build_evidence(root: Path) -> dict[str, bytes]:
    """Replay and pin nine ancestors; freeze the *claims*, not invented physics."""
    parent = mat_spec_009.build_evidence(root)
    split, audit, source_gate = verify_parent(parent)
    contract, raw_contract = _read_frozen_json(root, SPEC_PATH, EXPECTED_SPEC)
    claims, raw_claims = _read_frozen_json(root, CLAIMS_PATH, EXPECTED_CLAIMS)
    sources, raw_sources = _read_frozen_json(root, SOURCES_PATH, EXPECTED_SOURCES)
    if (
        contract["final_numbered_profile"] != PROFILE
        or contract["numbered_profiles_total"] != FINAL_NUMBER
        or contract["new_doi"] is not None
        or claims["foundational_mat_spec_001_doi"] != FOUNDATIONAL_DOI
        or tuple(s["profile"] for s in sources["source_stages"]) != STAGES
    ):
        raise ValueError("MAT-SPEC-010 final programme closure drift")

    frozen = ancestor_artifact_maps(
        {name: mat_spec.sha256(raw) for name, raw in parent.items()}
    )
    archive_members = validate_archive_membership(claims, frozen)
    inputs = _source_index(root, sources)
    closure = science_closure(split, audit, source_gate)
    handoff = handoff_plan()
    archive = {
        "profile": PROFILE, "version": VERSION,
        "status": "REPLAYABLE_INDEX_NOT_AN_EXTERNAL_ARCHIVE",
        "archive_release_tag": None,
        "external_doi": None,
        "source_repository_commit": PARENT_COMMIT,
        "profiles_indexed": [item[0] for item in frozen],
        "ancestor_artifact_count": len(archive_members),
        "ancestor_artifacts": archive_members,
        "repository_file_count": len(inputs),
        "repository_files": inputs,
        "source_custody": "SOURCE_ATTRIBUTION_IS_NOT_INDEPENDENT_AUTHENTICATION",
        "merging_or_tagging_completed_by_this_build": False,
        "external_archive_in_this_build": False,
        "existing_symbolic_mid_fingerprints_only": True,
        "rendered_audio_generated": False,
    }
    outcome_audit = {
        "profile": PROFILE, "version": VERSION,
        "frozen_predecessor_profiles": len(frozen),
        "prior_artifact_sha256_members": len(archive_members),
        "source_and_implementation_inputs_hashed": len(inputs),
        "scientific_claim_records": len(claims["stages"]),
        "source_class_records": len(sources["source_stages"]),
        "original_physical_holdouts_executed": 0,
        "synthetic_controls_replayed": audit["synthetic_negative_controls_passed"],
        "real_phase_classifier_accuracy": None,
        "root_audio_generation": "PERMANENTLY_DISABLED",
        "stage_010_final": True,
    }
    outputs = {
        "contract.json": mat_spec.canonical_json(contract),
        "claims.json": mat_spec.canonical_json(claims),
        "source-inventory.json": mat_spec.canonical_json(sources),
        "archive-index.json": mat_spec.canonical_json(archive),
        "closure-gate.json": mat_spec.canonical_json(closure),
        "handoff.json": mat_spec.canonical_json(handoff),
        "audit.json": mat_spec.canonical_json(outcome_audit),
    }
    impl = {
        path: mat_spec.sha256(mat_spec.read_regular(root / path))
        for path in IMPLEMENTATION_PATHS
    }
    receipt = {
        "profile": PROFILE, "version": VERSION, "final_numbered_profile": True,
        "parent_commit": PARENT_COMMIT,
        "parent_artifacts": {
            name: {"sha256": mat_spec.sha256(raw), "bytes": len(raw)}
            for name, raw in sorted(parent.items())
        },
        "contract": {"path": SPEC_PATH, "sha256": mat_spec.sha256(raw_contract)},
        "claim_registry": {"path": CLAIMS_PATH, "sha256": mat_spec.sha256(raw_claims)},
        "source_inventory": {
            "path": SOURCES_PATH, "sha256": mat_spec.sha256(raw_sources)
        },
        "implementation": impl,
        "outputs": {
            name: {"sha256": mat_spec.sha256(raw), "bytes": len(raw)}
            for name, raw in sorted(outputs.items())
        },
        "foundational_mat_spec_001_doi": FOUNDATIONAL_DOI,
        "new_doi": None,
        "manifest_self_hash": None,
        "canonical_pcm_sha256": None,
        "canonical_wav_sha256": None,
        "audio_generated": False,
        "canonical_serialization": "ASCII sorted compact JSON LF and CSV LF",
    }
    outputs["manifest.json"] = mat_spec.canonical_json(receipt)
    return outputs


def write_evidence(root: Path, destination: str, outputs: dict[str, bytes]) -> Path:
    """POSIX exclusive, no-follow descriptor-relative JSON-only export."""
    relative = PurePosixPath(destination)
    if (
        not destination or relative.is_absolute() or "\\" in destination
        or any(part in ("", ".", "..") for part in destination.split("/"))
    ):
        raise ValueError("destination must be fresh and relative")
    if set(outputs) != OUTPUT_NAMES or any(
        PurePosixPath(name).name != name or not name.endswith(".json")
        for name in outputs
    ):
        raise ValueError("final archive receipt allows JSON only")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fds = [os.open(root, flags)]
    try:
        for part in relative.parts[:-1]:
            with suppress(FileExistsError):
                os.mkdir(part, mode=0o755, dir_fd=fds[-1])
            fds.append(os.open(part, flags, dir_fd=fds[-1]))
        parent_fd = fds[-1]
        os.mkdir(relative.parts[-1], mode=0o755, dir_fd=parent_fd)
        fds.append(os.open(relative.parts[-1], flags, dir_fd=parent_fd))
        out = fds[-1]
        for name in sorted(outputs):
            fd = os.open(
                name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                mode=0o644, dir_fd=out,
            )
            with os.fdopen(fd, "wb") as target:
                target.write(outputs[name])
        opened = os.fstat(out)
        visible = os.stat(relative.parts[-1], dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISDIR(visible.st_mode) or (
            opened.st_dev, opened.st_ino
        ) != (visible.st_dev, visible.st_ino):
            raise ValueError("output directory changed during export")
    finally:
        for fd in reversed(fds):
            os.close(fd)
    return root / relative
