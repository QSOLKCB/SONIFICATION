# MAT-SPEC-006 v0.1.0 — Primary experimental data and phase-validation protocol

## What is new

MAT-SPEC-006 adds **experimenters' original published data tables**, rather than
another compilation of recommended helium properties. The numerical evidence
comes from the source's gravity-corrected and averaged calorimeter results,
not raw sensor records. Its phase-validation test remains **BLOCKED**, by design:
different source documents alone do not certify physical independence.

- Parent: MAT-SPEC-005 v0.1.0, merged SHA
  `5b4c89b795beb7fc8c4f7d86ce2a2fb510cb6cb2`.
- Foundational MAT-SPEC-001 record DOI: 10.5281/zenodo.24062652.
- MAT-SPEC-006 has no DOI; prior releases remain unchanged.

## Primary data provenance

William M. Fairbank and John A. Lipa, *High Accuracy Heat Capacity Measurements
through the Lambda Transition of Helium with Very High Temperature Resolution*,
NASA contractor report NASA-CR-177037 (1984), Appendix A by **J. A. Lipa and
T. C. P. Chui**, *The Heat Capacity of Liquid Helium Near the Lambda
Transition*, Data Release #1, January 15, 1984. Related experiment:
Lipa and Chui, Physical Review Letters 51, 2291 (1983),
DOI 10.1103/PhysRevLett.51.2291.

Primary NASA report:
https://ntrs.nasa.gov/citations/19860021083
PDF:
https://ntrs.nasa.gov/api/citations/19860021083/downloads/19860021083.pdf

We inspected Appendix A Table 1 (**PDF index 40**) and Table 2 (**PDF index
41**). The excerpt contains six reported heat-capacity observations selected
from each published table. The report describes the heat capacity as measured
in a helium sample approximately 3 mm high at saturated vapour pressure,
corrected for gravity and averaged before tabulation. Its individual
measurement uncertainties/covariance are not published alongside these rows.

Each source temperature is **signed T - T_lambda in microdegrees K**,
not an absolute Kelvin temperature. Positive/negative values are retained
exactly and no lambda-point numerical value is borrowed from MAT-SPEC-005.
The ABOVE/BELOW labels come from table headings and signed temperatures,
**not** an orthogonal physical phase diagnostic. Small printed decimal
facts are transcribed with leading zeros normalized; source and interpretation
are bound by SHA-256. We do not redistribute the report itself.

The excerpt is intentionally limited and **retrospectively chosen** after
inspection. It is neither a statistically random sample nor an experimental
pre-registration, and must not be presented as a blind test.

## Preliminary source search / independent-family audit

The independent-source inventory records:
- 1984 original Lipa–Chui ground calorimetry: PRIMARY experiment,
  sampled table rows available, no per-row errors or orthogonal phase labels.
- 1998 Donnelly–Barenghi recommended property tables (MAT-SPEC-005):
  EVALUATED compilation; contains citations to earlier experiments including
  Lipa. Independence between these datasets has **not been demonstrated**.
- 1996 Lipa microgravity measurements / 2003 expanded report: different
  experiment described, but raw row-level uncertainties and independent
  phase labels have not been admitted; both publications derive from the
  same orbital campaign and cannot be treated as independent of one another.
- 1988 Marek–Lipa–Philips second-sound measurements: primary experimental
  context but measurements are He-II near lambda, not above-transition
  diagnostic non-detections. No matching tabular blind-test corpus admitted.

This is a **source-selection and provenance result**, not a claim that no
further datasets exist.

## Numerical checks / symbolic receiver

For all twelve exact published decimal values:

    C_i (J/mol/K) -> (5 Hz per [J/mol/K]) * C_i

This is an authored **symbolic target**, never a physically measured heat
capacity frequency. The mapping is reversible as an exact rational
transformation of the printed numbers. Nearest 12-TET MIDI notes are only a
lossy numerical receiver; no MIDI or sampled audio is rendered.

The nearest *selected* reference records on either side are
`-0.029 microK, 105.50 J/(mol K)` (below) and
`+0.075 microK, 82.04 J/(mol K)` (above), difference
`-23.46 J/(mol K)`. **Their offsets have different magnitudes.**
This is not a temperature-matched discontinuity, calibrated significance
test, independent phase classification or critical-exponent estimate.

Missing experimental uncertainties remain `null`. They are
not inferred from significant digits, and the report's discussion of
systematic calibration effects is not a per-row uncertainty model.

## Proposed future study-level holdout (not a present pre-registration)

The evaluation contract is frozen for **future** research after the present
data inspection. It cannot retroactively pre-register the 1984 selection.

Structural conditions for a possible future experiment:
1. Separate training and held-out **experimental families**, not random
   rows of one campaign, and no shared underlying measurements.
2. Both physically identified He-I and He-II examples in each group.
3. Direct orthogonal diagnostic-based phase labels, not a threshold on
   temperature or the labels from Appendix A table headings.
4. Positive, documented experimental measurement and diagnostic errors.
5. Source identities, conditions and SHA-256 receipts for independent review.

The reusable structural preflight accepts *candidate* records and reports
either `BLOCKED` or `STRUCTURAL_ONLY_NOT_EMPIRICAL_ADMISSION`.
Even a structural pass is **not an authentication of evidence**. The tests
include synthetic positive and deliberately leaky/forged negative controls;
there are no synthetic physical test results in runtime artifacts.

The real MAT-SPEC-006 dataset contains one campaign with no independent
diagnostic labels and no per-row uncertainties, so actual held-out
phase-classifier accuracy is **null** and training is **NOT_PERFORMED**.

## Verify and reproduce

Offline Python 3.11+, standard library:

```sh
uv run --no-project python -m unittest discover -s tests -p 'test_mat_spec*.py' -v
uv run --no-project python scripts/build_mat_spec_006.py --out dist/mat-spec-006
```

A fresh output directory is required. Seven symbolic JSON/CSV artifacts:
contract, observations, receiver controls, source audit, heldout protocol,
phase gate, manifest. Source/metadata/specification/implementation/output
SHA-256 receipts bind the output chain, including all five frozen ancestor
profiles. No PCM, rendered audio, synthesized waveforms or equivalent
buffers are generated in memory or persisted. Source data attribution and
licensing must remain separate from new MPL-2.0 code.
