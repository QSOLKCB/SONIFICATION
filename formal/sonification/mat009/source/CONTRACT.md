# Frozen MAT009 challenge source contract

This document describes `materials/mat_spec_009.py::check_future_challenge`
at annotated tag `mat-spec-009-v0.1.0`. The tag object is
`ad99d9e52f9ede423a4fb9d6a622624e32955263`, its peeled commit is
`0758a96360726aafbb07abed34620eda178407ae`, its tree is
`a6a03e1227e666680d656b886201ee9dde9de32d`, and the module blob and
SHA-256 are `c447f0ce76b91acf458221390ac4261166145a0b` and
`a68089df7d1901fb7c17ffc2889b844b3573024aec4b66348f9c2ef71930c690`.
`SOURCE_BINDING.json` and `source_bind.py` check these identities and selected
syntax. They do not establish CPython refinement or physical authenticity.

The operation is a structural check on asserted metadata. It never trains a
classifier, measures accuracy, authenticates independence, or admits physical
evidence. An empty reason list means only `STRUCTURAL_ONLY_UNAUTHENTICATED`.

## Exact evaluation order

1. The outer guard at MAT009 lines 122–129 returns immediately if `records` is
   not an `isinstance(..., list)`, is falsey, or has length greater than 10,000.
   Its result has exactly `status`, `reasons`, `physical_evidence_admitted`,
   `independence_authenticated`, and `heldout_accuracy`. The sole reason is
   `EMPTY_OR_MALFORMED_CHALLENGE`. It does not call MAT008 and has no counts,
   `trained_classifier`, or `meaning` key.
2. For any list passing that guard, MAT009 calls
   `mat_spec_008.validate_future_measurement_packet(records)` once, with the
   same object, before any child scan. It initializes `reasons` as a set of
   `parent["reasons"]`; it does not inspect the parent's status or counts.
   Exceptions from the parent propagate.
3. The child initializes the campaign role map, three split-indexed sets,
   valid receipt set, and two diagnostic owner maps empty. It scans rows in
   input order. The three early `continue` paths are: non-`dict` row;
   `study_role` not equal to either `TRAIN` or `HOLDOUT`; and campaign or lab
   failing `_identifier`. A skipped row contributes no child campaign, lab,
   phase, diagnostic, receipt, unit, pressure, scale, or label check. The
   parent may still have processed that row, because its eligibility differs.
4. An eligible row first checks and then overwrites `split_by_campaign` with
   its role. It adds campaign and lab to the selected split sets and adds
   `HE_I` or `HE_II` to that split's phase set when recognized. These state
   updates happen before unit, pressure, scale, label, diagnostic, and receipt
   checks. A later invalid field does not undo them.
5. After the row scan, MAT009 checks the count of distinct valid receipt
   digests, presence of both campaign splits, intersection of campaign or lab
   sets, and both phases in each split. It sorts the union of parent and child
   reason IDs. A nonempty union yields `BLOCKED`; an empty union yields
   `STRUCTURAL_ONLY_UNAUTHENTICATED`.

On the normal path, the result additionally contains `train_campaigns` and
`heldout_campaigns` as set cardinalities, `trained_classifier: false`, and a
fixed `meaning` string. `physical_evidence_admitted` and
`independence_authenticated` are always false, and `heldout_accuracy` is
always null on both result paths.

## Child checks after the third skip guard

`_identifier` accepts a `str` or subclass with length at most 100 whose full
text matches `[A-Z0-9_]+`; the `+` rejects empty text. `_digest` accepts a
`str` or subclass matching exactly 64 lowercase hexadecimal characters.
Neither helper requires `type(value) is str`. Subclass behavior is discussed
in `CALLER_DOMAIN.md`.

| Child reason | Trigger and state detail |
| --- | --- |
| `MALFORMED_CANDIDATE_RECORD` | Row fails `isinstance(record, dict)`; skip. |
| `UNDECLARED_TRAIN_HOLDOUT_ROLE` | Role fails membership in the two literal strings; skip. |
| `MISSING_EXPERIMENT_FAMILY_IDENTITY` | Campaign or lab fails `_identifier`; skip. |
| `CAMPAIGN_CROSSES_TRAIN_HOLDOUT` | The campaign key was already mapped to a different role. The map is then overwritten; both split sets still retain their entries. |
| `INCOMMENSURATE_MEASUREMENT_UNITS` | Quantity is not equal to `HEAT_CAPACITY` or unit is not equal to `J_PER_MOL_K`. |
| `UNDECLARED_PRESSURE_CONDITION` | Pressure is not equal to `HE4_SVP`, even though MAT008 also accepts `DOCUMENTED_FIXED_PRESSURE`. |
| `UNDECLARED_RECEIVER_SCALE` | Scale is not equal to the string `5`. |
| `CIRCULAR_OR_MISSING_ORTHOGONAL_LABEL` | Label basis is not equal to `ORTHOGONAL_DIAGNOSTIC`. |
| `INDEPENDENT_DIAGNOSTIC_SOURCE_REQUIRED` | Diagnostic SHA is invalid, equals the row's source SHA, or event ID fails `_identifier`. This reason does not skip the ownership loop. |
| `DIAGNOSTIC_PROVENANCE_REUSED_ACROSS_CAMPAIGNS` | A valid diagnostic hash or valid event ID was previously registered with a different campaign key. |
| `DIAGNOSTIC_PROVENANCE_LEAKAGE_ACROSS_SPLITS` | A valid diagnostic hash or valid event ID was previously registered with a different role. This also applies when the campaign key is unchanged but its role changes. |
| `MISSING_PROSPECTIVE_REGISTRATION_RECEIPT` | Receipt fails `_digest`; it is not added to the receipt set. |
| `INCONSISTENT_PREREGISTRATION_RECEIPT` | Final set of valid, eligible receipt digests has cardinality other than one. One invalid receipt among otherwise identical valid receipts adds the missing reason but not this one. |
| `BOTH_EXPERIMENT_SPLITS_REQUIRED` | At least one split has no eligible campaign. |
| `SOURCE_FAMILY_LEAKAGE_ACROSS_SPLITS` | Train and holdout campaign sets intersect, or train and holdout lab sets intersect. The two predicates share one reason ID. |
| `TRAIN_REQUIRES_BOTH_PHASES`, `HOLDOUT_REQUIRES_BOTH_PHASES` | The selected split's recognized phase set is not exactly `{HE_I, HE_II}`. |

The diagnostic loop checks hash and event provenance independently. Its tuple
has the hash first, then event ID. Only a valid identity enters its respective
owner map. `registry.setdefault(identity, (campaign, role))` retains the first
owner seen for that identity. Repeating a diagnostic document or event within
the same campaign and role is allowed by this child gate. A valid diagnostic
hash is registered even when it equals the measurement source hash, and a
valid event ID is registered even when the diagnostic hash is invalid. Other
row errors do not skip this loop. Reason IDs are deduplicated by a set.

`pre_registration_sha256` is only a syntactic digest assertion. The source
does not inspect receipt contents, timing, signer, or external audit.

## Direct MAT008 call contract

The direct parent is `materials/mat_spec_008.py` at blob
`3117adbc3739c834f8203d5d2dd2b80d6caf862b`, SHA-256
`e56563235d87da43293bc46661b077660538b476d2bb340a1d208cc59aaa5f08`.
Its selected operation is lines 228–332. The MAT009 outer guard makes the
parent's empty-packet return unreachable for ordinary exact lists passed
through this call.

MAT008 scans the same rows before MAT009. It skips a non-`dict` row with
`MALFORMED_CANDIDATE_RECORD`. For a `dict`, it parses campaign, lab, original
run, source document, and row ID in that order with `_identity`. A `ValueError`
from any parse adds `MISSING_OR_INVALID_SOURCE_IDENTITIES` and skips all later
parent checks for that row. `_identity` requires a nonempty `str` or subclass,
length at most 100, no leading or trailing whitespace as judged by `strip`
and equality, and the same full ASCII identifier pattern. For exact built-in
strings, `_identity` and MAT009 `_identifier` accept the same text. However,
MAT009 checks only campaign and lab, so a row with a bad run, document, or row
ID can be parent-skipped and still child-processed.

After identity acceptance, MAT008 applies these checks and state updates in
the listed order:

| Parent reason | Condition |
| --- | --- |
| `DUPLICATE_MEASUREMENT_ROW_ID` | Row ID already in `seen_rows`; the set is then updated. |
| `CAMPAIGN_LAB_IDENTITY_CONTRADICTION` | Existing campaign-to-lab mapping differs; map is overwritten. |
| `CAMPAIGN_RUN_OR_DOCUMENT_INCONSISTENT` | Existing campaign-to-`doc:run` mapping differs; map is overwritten. |
| `REUSED_ORIGINAL_RUN_ACROSS_CAMPAIGNS` | Run owner's campaign differs; run owner map is overwritten. |
| `REUSED_ORIGINAL_DOCUMENT_ACROSS_CAMPAIGNS` | Document owner's campaign differs; document owner map is overwritten. |
| `UNVERIFIED_PHASE_LABEL` | Phase is not a `str` or is not `HE_I`/`HE_II`. A non-string becomes `INVALID` in the campaign phase set. |
| `DERIVED_FIT_OR_COMPILATION_IS_NOT_PRIMARY_DATA` | Source type differs from `ORIGINAL_EXPERIMENTAL_RECORD`. |
| `SYNTHETIC_FIXTURE_NOT_PHYSICAL_MEASUREMENT` | `synthetic_fixture is True` by identity. Truthy integer `1` does not trigger it. |
| `CIRCULAR_OR_MISSING_PHASE_DIAGNOSTIC` | Diagnostic basis differs from `INDEPENDENT_NON_TEMPERATURE_DIAGNOSTIC`. |
| `MISSING_CALIBRATED_MEASUREMENT_UNCERTAINTY` | `_decimal` raises `ValueError` on measurement value, measurement sigma, or diagnostic sigma. The first failure short-circuits later numeric parsing. |
| `SOURCE_HASH_OR_PHYSICAL_CONDITION_NOT_DOCUMENTED` | Source SHA is not 64 lowercase hex, or pressure is neither `HE4_SVP` nor `DOCUMENTED_FIXED_PRESSURE`. This branch skips hash ownership checks for that row. |
| `REUSED_SOURCE_BYTES_ACROSS_CAMPAIGNS` | A valid source digest's previous campaign differs; hash owner map is overwritten. |
| `CAMPAIGN_SOURCE_BYTES_INCONSISTENT` | A campaign's previous valid source digest differs; campaign hash map is overwritten. |
| `BOTH_PHASES_REQUIRED_FOR_EACH_CAMPAIGN` | At least one parent-accepted campaign phase set differs from `{HE_I, HE_II}`. |
| `TWO_INDEPENDENT_CAMPAIGNS_AND_LABS_REQUIRED` | Fewer than two distinct campaign keys or fewer than two distinct lab keys were seen. This is a metadata cardinality check, not authentication. |
| `DISTINCT_ORIGINAL_RUNS_REQUIRED` | Fewer than two distinct `doc:run` strings were stored in `experiment_to_source`. Despite its name, this uses document plus run. |

`_decimal` accepts an exact positive decimal string matching
`(?:0|[1-9][0-9]*)(?:\.[0-9]+)?` and then requires `Fraction(value) > 0`.
MAT008's normal return sorts its reason set and always reports physical
admission and independence authentication as false. MAT009 imports only its
`reasons` list. Neither layer verifies the real-world identity or independence
of a source.

## Frozen synthetic controls

`_synthetic_controls()` constructs four in-memory metadata rows: both phases
for `SYNTH_TRAIN`/`SYNTH_LAB_A` and both for
`SYNTH_HELD`/`SYNTH_LAB_B`. Every row has `synthetic_fixture: True`.
`negative_controls()` executes the following 14 mutations, checking that
`BLOCKED`, its designated reason, and the synthetic rejection are present.
It writes no empirical score. Its `observed_rejection` field repeats the
designated reason after a membership check; it is not the complete reason
list, and a mutation can add other reasons.

| Control ID | Mutation | Designated reason | Layer |
| --- | --- | --- | --- |
| `SYNTHETIC_CANDIDATE_DENIED` | None beyond the synthetic marker | `SYNTHETIC_FIXTURE_NOT_PHYSICAL_MEASUREMENT` | MAT008 |
| `CROSS_CAMPAIGN_RUN_REUSE` | Both heldout run IDs become `SYNTH_RUN_A` | `REUSED_ORIGINAL_RUN_ACROSS_CAMPAIGNS` | MAT008 |
| `CAMPAIGN_SPLIT_LEAKAGE` | Second train phase row changes role to `HOLDOUT` | `CAMPAIGN_CROSSES_TRAIN_HOLDOUT` | MAT009 |
| `SOURCE_BYTES_REUSED` | Both heldout source SHAs become `a` repeated 64 times | `REUSED_SOURCE_BYTES_ACROSS_CAMPAIGNS` | MAT008 |
| `TEMPERATURE_DERIVED_LABEL` | First train row diagnostic basis becomes `TEMPERATURE_THRESHOLD` | `CIRCULAR_OR_MISSING_PHASE_DIAGNOSTIC` | MAT008 |
| `ZERO_MEASUREMENT_SIGMA` | First train row measurement sigma becomes `0` | `MISSING_CALIBRATED_MEASUREMENT_UNCERTAINTY` | MAT008 |
| `ORTHOGONAL_DIAGNOSTIC_ABSENT` | First train row diagnostic SHA becomes null | `INDEPENDENT_DIAGNOSTIC_SOURCE_REQUIRED` | MAT009 |
| `DIAGNOSTIC_SOURCE_EQUALS_MEASUREMENT` | First train row diagnostic SHA becomes its source SHA | `INDEPENDENT_DIAGNOSTIC_SOURCE_REQUIRED` | MAT009 |
| `UNDECLARED_RECEIVER_SCALE` | First train row scale becomes `10` | `UNDECLARED_RECEIVER_SCALE` | MAT009 |
| `MISSING_PROSPECTIVE_REGISTRATION` | First train row receipt becomes empty | `MISSING_PROSPECTIVE_REGISTRATION_RECEIPT` | MAT009 |
| `MIXED_PHYSICAL_PRESSURE` | First train row pressure becomes `DOCUMENTED_FIXED_PRESSURE` | `UNDECLARED_PRESSURE_CONDITION` | MAT009 |
| `HOLDOUT_MISSING_PHASE` | Second heldout phase becomes `HE_I`, with a new row ID | `HOLDOUT_REQUIRES_BOTH_PHASES` | MAT009 |
| `DERIVED_FIT_AS_MEASUREMENT` | First train row source type becomes `REANALYSIS` | `DERIVED_FIT_OR_COMPILATION_IS_NOT_PRIMARY_DATA` | MAT008 |
| `DOCUMENT_REUSED` | Both heldout document IDs become `DOC_SYNTH_TRAIN` | `REUSED_ORIGINAL_DOCUMENT_ACROSS_CAMPAIGNS` | MAT008 |

The 14 controls do not include the separate cross-campaign diagnostic replay
case tested in the frozen MAT009 unit tests and the focused finite checks.
All controls and new finite rows remain synthetic or self-declared metadata;
none supplies an independent physical holdout.
