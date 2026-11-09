# MAT-SPEC-009 v0.1.0 — Source-separated phase challenge preflight

## Outcome: PHYSICAL EVALUATION BLOCKED; 14 synthetic controls exercised

The MAT-SPEC-009 objective is to establish an *auditable future experimental
challenge*, not to train a classifier on arbitrary splits of the same
helium data. MAT-SPEC-008 concludes that only **one** experiment campaign
has 12 source-pinned processed calorimetry rows, with **zero** row-level
calibrated uncertainties, **zero** independent physical phase-diagnostic
observations, and **zero** independent measurement pairs. These facts
block a genuine cross-experiment, blind physical phase validation.

MAT-SPEC-009 preserves that admission gate without adding made-up
experimental observations, label provenance or sound measurements.
**No real classifier is trained, and no phase or receiver prediction
accuracy is calculated.** The result is not a null hypothesis rejection,
evidence against physical superfluidity or absence of independently
replicable helium experiments in the world.

## Prospective protocol and source-level separation

The v0.1.0 contract was frozen **after examining** MAT-SPEC-001–008
observations. It is prospective for *future* externally acquired
measurements and **cannot be called a preregistered evaluation of the
older campaigns**. A caller-supplied SHA-256 "registration receipt"
is only a structural field; registration, date order, custody and
publication would still require independent verification.

The permitted future physical evidence would require:

1. Physically independent source-origin acquisitions in distinct
   experiment and laboratory families, with independent original
   source/run/document identifiers and SHA-256s.
2. Entire original **campaigns** partitioned to TRAIN or HOLDOUT;
   not a random row split from an experiment. Both physical helium
   phases must be independently represented in each partition.
3. Independent, orthogonal phase diagnostics, not labels recreated
   from a temperature threshold or published table-side heading.
   Diagnostic provenance must be distinct from measurement provenance.
4. Calibrated per-row physical measurement/diagnostic uncertainties and
   documented matching conditions: helium-4 at saturated vapour pressure,
   heat capacity in J/(mol K). Other conditions and units are not silently
   pooled with this challenge.
5. The **fixed** authored numerical receiver mapping of
   5 Hz per J/(mol K), exact rational input and nearest symbolic
   12-TET pitch. This scale may not be selected using held-out labels.
   The symbolic Hz is **not** a helium acoustic frequency.
6. An externally independently verified preregistration, acquisition
   source-byte receipts, a source separation audit and independent
   uncertainty-calibration review **before** any physical score could
   be admitted or published.

The preflight is intentionally structural. If a candidate record passes
all these checks, the best possible result remains
\`STRUCTURAL_ONLY_UNAUTHENTICATED\`, with `physical_evidence_admitted: false`.
An independent research witness would still have to authenticate the
original measurements, metadata and phase labels. No experiment has been
admitted or scored in this version.

## Negative-control matrix

Fourteen deterministic tests construct metadata-only, **synthetic
in-memory fixtures** and demonstrate fail-closed rejection. The tests
include:

- Baseline synthetic evidence cannot count as physical observations.
- Reusing a run ID, source bytes or original document across experiment
  families cannot represent independent acquisitions.
- Moving one record across a campaign's TRAIN/HOLDOUT boundary is rejected.
- Temperature-derived labels, missing orthogonal diagnostic source and
  diagnostic hashes reused as measurement hashes are rejected.
- Zero experimental uncertainty, missing preregistration and changing the
  receiver scale after the fact are rejected.
- Mixed pressure conditions and missing a phase class from the held-out
  partition are rejected.
- A secondary review or refitted summary cannot masquerade as
  an original experimentally acquired record.

The symbolic output records each named control, its expected rejection,
the matching observed rejection, and the **PASS_REJECTED** result.
Synthetic input records, predictions, numerical accuracy scores,
synthetic confusion matrices and fabricated experimental measurements
are **not** published as physical evidence.

## Source inheritance, deterministic output and limitations

The builder replays MAT-SPEC-001–008 in the repository's existing
strictly source-pinned order. It will fail if the frozen MAT-SPEC-008
artifact membership, original metadata or source hashes have drifted.
The MAT-SPEC-009 contract, implementation and six data products receive
explicit SHA-256 receipts in the manifest. Existing tags, source
data, licenses and DOI assignments are unchanged.

Seven canonical JSON/CSV artifacts:

- `contract.json`: prospective contract and scientific boundaries
- `source-gate.json`: inherited MAT-SPEC-008 scientific admission
- `split-protocol.json`: present zero-assignment blocked challenge
- `synthetic-controls.csv`: fourteen named synthetic rejection controls
- `receiver-gate.json`: fixed symbolic receiver, not exercised as physics
- `audit.json`: control execution counts and nonclaims
- `manifest.json`: ancestor/contract/implementation/artifact receipts

Offline Python 3.11+, standard library, no network dependencies:

```sh
uv run --no-project python -m unittest discover -s tests -p 'test_mat_spec*.py' -v
uv run --no-project python scripts/build_mat_spec_009.py --out dist/mat-spec-009
```

A new relative directory is required. Output uses POSIX descriptor-anchored
no-follow and exclusive file creation. Only symbolic JSON/CSV output is
allowed. No sampled PCM, WAV, waveform arrays, synthesizers or MIDI
playback are constructed or invoked.

## Remaining research and verification

**MAT-SPEC-010 is the FINAL numbered MAT-SPEC stage.** It must freeze and
audit every prior profile, including all blocked physical admission results,
explicit data inventories, provenance and implementation identities,
and the exact verified software test results.

Once 010 is completed and tagged, the separate work programme proceeds
to bounded SPARK/Ada kernel proof and independent differential execution,
then the existing **VANILLAJS Lean/ECMAScript** refinement obligation.
Neither is implicitly completed by MAT-SPEC-009.
