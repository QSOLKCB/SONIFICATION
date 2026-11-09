# SONIFICATION-FORMAL-001 proof inventory

This inventory records targets and unresolved obligations. It makes no proof-completion claim.

Frozen reference main: `8c62517138e3b86a4672d8969e190b747f81c398`. Protocol identity: `a1f74e8d1847d218d6b68c125fac9522e2ffc2fb`.

`SOURCE_MANIFEST.json` records every tracked path at each listed snapshot, Git blob identities, SHA-256 digests, tag object identities, peeled commits and source trees. `SOURCE_INVENTORY.json` enumerates source-module versions and Python function definitions. Module-level OPEN obligations cover initialization, unnamed expressions and unsupported extraction. No unexamined function is covered by a theorem.

## Historical identities

| Snapshot | Ref kind | Ref object | Peeled commit | Tree |
|---|---|---|---|---|
| mat-spec-003-v0.1.0 | commit | `c15ef3223e78cffad1494d99ad6edbdb41195362` | `c15ef3223e78cffad1494d99ad6edbdb41195362` | `6fd6a3d6a72a3b06b0c8481d2490ae24c4f483f0` |
| mat-spec-004-v0.1.0 | commit | `eac0659cbae1392bf63632ec8138005367e63304` | `eac0659cbae1392bf63632ec8138005367e63304` | `089e8c4bf5743e1108b2d828ab33475b9bbe4c1b` |
| mat-spec-005-v0.1.0 | commit | `5b4c89b795beb7fc8c4f7d86ce2a2fb510cb6cb2` | `5b4c89b795beb7fc8c4f7d86ce2a2fb510cb6cb2` | `4bbafd212484c7123785c84292a9645b6763559e` |
| mat-spec-006-v0.1.0 | commit | `c1abb62e8914f6790b5da5a51adf330b813b0530` | `c1abb62e8914f6790b5da5a51adf330b813b0530` | `15eddc0cd03646dda34522b67ac585bf95c9b56c` |
| mat-spec-007-v0.1.0 | tag | `8b933a5ab09b8e76afe4c8e169e089f251e23314` | `b97348ff8fcf3f57764dec21a8914f153f96a745` | `c1b842c6bace3ccb01714007b8d7ebb05bcecd31` |
| mat-spec-008-v0.1.0 | tag | `a02088e3c68addb41c9c7145694c0f566e84f87f` | `b4247877dd471e2e9d4986c86bdc1f11b14e43f8` | `eb19f2e06a502442f621a73be1e5696c2fa25a65` |
| mat-spec-009-v0.1.0 | tag | `ad99d9e52f9ede423a4fb9d6a622624e32955263` | `0758a96360726aafbb07abed34620eda178407ae` | `a6a03e1227e666680d656b886201ee9dde9de32d` |
| mat-spec-010-v0.1.0 | tag | `b8e88a0a32db30558e00704669eeaafee3a8d5f5` | `9d12c6a5098f4edba972bb6b1067555d8f48f693` | `646f1de532738feeb59336a427881d643cf32dc1` |
| d4-tia-v2.0.0 | commit | `7aa6df165d0ad70297365dbf0d69072634ed4314` | `7aa6df165d0ad70297365dbf0d69072634ed4314` | `8f6926b14c3616b7445b18cca42463382164dee7` |
| v2.0.0 | commit | `8c24d58ca76abbac77c427a4f63ca434570c82b3` | `8c24d58ca76abbac77c427a4f63ca434570c82b3` | `9d727cd6919f4940d2d117e24f24d12c3842ee09` |
| v3.0.0 | commit | `6b55e51647226d1c248dc8d79f9ed9336241c2ac` | `6b55e51647226d1c248dc8d79f9ed9336241c2ac` | `e2d8b532b849fccb369073fe539367e527b347dc` |
| v3.0.1 | commit | `da3207663ecf4ff9936dc18bca3429f5a65a17ec` | `da3207663ecf4ff9936dc18bca3429f5a65a17ec` | `1b0cd929b2f98a8024cde2a7c261627fe84adcda` |
| spark-001-v1.0.0 | tag | `d4a0aeb1a5d07e4c41935d4a5c7c672685c98b20` | `95cc7c455535c1c4562d4241f5b387c811d90e5d` | `a4fd30e5b30e3719e84ed83d11c28c0f5bb250d0` |
| mat-spec-001-first-source | commit | `8493d59959d0d4416c516ad5615cdedcb32fcf93` | `8493d59959d0d4416c516ad5615cdedcb32fcf93` | `6772facc938fb9dc86c4c5355ed8e1789b081966` |
| mat-spec-002-first-source | commit | `26f9aca04a73e5ed5b14340a0bf97ecb6b1d662f` | `26f9aca04a73e5ed5b14340a0bf97ecb6b1d662f` | `512c2a2d760216f399e0b3c6b14279b7fc7a2b9b` |
| sonification-main-reference | commit | `8c62517138e3b86a4672d8969e190b747f81c398` | `8c62517138e3b86a4672d8969e190b747f81c398` | `641ef7d40d8ed887d639e61b92acf4b85bd72440` |
| spark-002-phase-1a-historical | commit | `06b1294bf1617e9eb3b825051e8bfbf7470e395c` | `06b1294bf1617e9eb3b825051e8bfbf7470e395c` | `03ef9a5ab1e674b9d31eb3705eb309ee2f0408fc` |
| spark-002-phase-1b-historical | commit | `6f0f1be1ba8885fa708d7328bcb92fbf4ecc324f` | `6f0f1be1ba8885fa708d7328bcb92fbf4ecc324f` | `7a841ee0dcf285d8fc625f52972e266d5949679f` |

MAT-SPEC-001 and MAT-SPEC-002 have no corresponding repository tags. Their first introduction commits are dependency-root locators; they are not asserted to be published release identities. Downstream pinned artifact maps and the exact root module versions at each release must be followed independently.

## Required verification domains

| Domain | Required investigation | Current coverage |
|---|---|---|
| Exact arithmetic | Integers, decimal lexical grammar, Fraction normalization/comparison, rational interval endpoints, float conversions | OPEN |
| MAT-SPEC transformations | Parent-chain source and artifact pins, numerical and symbolic invariants for stages 001-010 | OPEN |
| Missingness | Missing/invalid/measured zero/physical boundary zero; parse and exception paths | OPEN |
| Source identity | Campaign, laboratory, run, document and digest ownership; uniqueness and normalization | OPEN |
| Partitioning | TRAIN/HOLDOUT source family separation, duplicate records and campaign reuse | OPEN |
| Evidence admission | Fail-closed eligibility; synthetic/secondary versus primary; blocked classifier scores | OPEN |
| Determinism | Iteration/sorting, dictionary/set behavior, canonical JSON/CSV/MIDI, stable archive bytes | OPEN |
| Provenance | Exact member sets, duplicate/missing/extra files, SHA-256, path safety, declared source linkage | OPEN |
| D4-TIA | D4 transforms, group and permutation laws, covariance/invariance and bridge semantics | OPEN |
| ETQ | Graph traversal, state transitions, symbolic tuning/event mappings, deterministic MIDI and audit output | OPEN |
| Separate music laboratories | Python sonification and browser APP module semantics inventoried; numerical/audio assurance OPEN; no rendering executed | OPEN |

## Prioritized operation obligations

| Production locator | Intended property | Layer A | Layer B | Layer C |
|---|---|---|---|---|
| `materials/mat_spec_007.py::interval` | Exact Fraction conversion; central value plus/minus strictly positive uncertainty; conversion and exception semantics | OPEN | OPEN | NOT_RUN |
| `materials/mat_spec_007.py::classify` | Closed interval order/overlap exhaustiveness and exclusivity under ordered endpoints; Exact rational comparisons and Python short-circuit branch semantics | OPEN | OPEN | NOT_RUN |
| `materials/mat_spec_007.py::pairwise_fits` | All intended fit pairs visited once; missingness preserved; counts match classifications | OPEN | OPEN | NOT_RUN |
| `materials/mat_spec_008.py::validate_future_measurement_packet` | Eligible packets satisfy row and source identity invariants; Missing, invalid, measured zero and physical boundary zero stay distinct; Campaign/lab/run/document/digest ownership and reuse fail closed | OPEN | OPEN | NOT_RUN |
| `materials/mat_spec_008.py::evidence_admission` | Synthetic and secondary evidence never admitted as primary physical evidence; mandatory gates fail closed | OPEN | OPEN | NOT_RUN |
| `materials/mat_spec_009.py::check_future_challenge` | No source family or campaign crosses TRAIN/HOLDOUT in an eligible packet; Diagnostic provenance and structural eligibility fail closed; classifier score remains prohibited | OPEN | OPEN | NOT_RUN |
| `materials/mat_spec_009.py::source_gate` | Parent source identities and admission prerequisites verified before challenge eligibility | OPEN | OPEN | NOT_RUN |
| `materials/mat_spec_010.py::verify_parent` | Exact parent artifact membership and hashes, manifest identity and admission boundaries checked | OPEN | OPEN | NOT_RUN |
| `materials/mat_spec_010.py::science_closure` | NUMBERED_SERIES_CLOSED_AT_010_WITH_OPEN_SCIENTIFIC_GATES; no classifier score from blocked evidence | OPEN | OPEN | NOT_RUN |
| `materials/mat_spec_010.py::validate_archive_membership` | Exact deterministic archive membership; duplicate, extra, missing or unsafe paths rejected | OPEN | OPEN | NOT_RUN |

For every locator above, the release → commit → module/blob → source span mapping is in the two JSON inventories. Formal definitions, named theorems, theorem dependencies, representation relations, source-refinement evidence, regression test selection and evidence receipts must be added as work is executed; null fields are unresolved obligations. Existing tests in each frozen tree are identity-inventoried, but test selection and execution are not inferred.

## Dependency investigation

All historical tracked files, including `materials/`, `sonification/`, `src/`, `scripts/`, `APP/`, `verification/`, schemas, examples, datasets, papers and package metadata, have exact byte identities. Python imports and ECMAScript import candidates are resolved against each frozen tree. Module constants and literal locators are retained as investigation clues. These are static navigation edges; transitive semantic closure, external library semantics and dynamically constructed file names remain OPEN.

MAT-SPEC parent relationships are implemented through imports and pinned artifact maps (`PARENT_*_SHA256`, `PARENT_COMMIT`), not merely numeric release labels. For example, MAT-SPEC-010 `ancestor_artifact_maps` refers to all nine predecessor maps through their actual imported modules. The MAT-SPEC-001 version spelling in that code is `1.0.0`; the dependency-root commit does not invent a matching tag.

SPARK-002 Phase 1A and Phase 1B are inventoried at the supplied historical proof commits. Their preserved receipts report 23/23 and 9/9 checks respectively. This inventory does not rerun, reinterpret, replace or extend those receipts to Python.

## Inventory totals and reproducibility

- snapshots: 18
- unique blobs: 360
- source module versions: 177
- python function versions: 600
- lexical function candidates: 490

Run from the repository root:

```sh
python3 formal/sonification/tools/inventory.py --check
```

The generator reads Git objects and compares deterministic generated bytes. It does not execute old production workflows, instantiate any PCM buffers, modify tags or datasets, or treat source hashes as proofs. Re-pinning both an inventory and its generator requires review against designated canonical historical Git objects; this command alone cannot prevent an authorized-code change from changing its own expected baseline.

## Claim and scientific boundaries

All implementation refinement remains OPEN until separate source-sensitive evidence is accepted. Passing tests or a similar Lean model cannot promote these rows. MAT-SPEC remains `NUMBERED_SERIES_CLOSED_AT_010_WITH_OPEN_SCIENTIFIC_GATES`. No MAT-SPEC-011. No software proof establishes independent helium experiments, calibrated physical uncertainty, classifier accuracy, human auditory discrimination or E8 physical theory.
