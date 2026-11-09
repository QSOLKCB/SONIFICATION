# MAT-SPEC-004 v0.1.0 — Temperature preservation and phase-evidence gate

**Research status:** observational/model-parameter preservation and admission
safeguards implemented. **No phase classifier was trained or evaluated.**

## Why this source?

Bhadra, A., and Mishra, P. K. (2022), *Energy spectrum and energy budget of
superfluid turbulence using two-fluid shell model*, AIP Advances 12, 025021,
DOI **10.1063/5.0083847**, Table I, contains eight helium-4 temperature
parameter values at 0.9, 1.1, 1.2, 1.4, 1.6, 1.8, 1.9 and 2.1 K.
The authors' **model parameter** table reports dimensionless normal density
fractions rho_n/rho and mutual-friction coefficients alpha.

The source is open access under CC BY 4.0. The eight numbers are independently
transcribed into 'data/materials/helium4/temperature_table1_2022.csv', not
copied from the original Godfrin neutron-scattering dispersion dataset.
The pin is **SHA-256
e741aac11809d18d05451efd30ca96dba0ae98765bde4952b0af96daeef8cf82**.

The source article's Table I gives no independently certified measurement
uncertainties on those entries and does not, in the cited extract, specify a
matched experimental pressure for every number. The Table I entries served as
turbulence simulation *inputs*: they are **not raw experiment measurements**,
not a temperature-controlled independent phase-diagnostic campaign and not
the output of the authors' shell-model simulation.

In particular, the Donnelly–Barenghi saturated-vapour-pressure lambda
temperature **2.1768 K** is bibliographic context, **not** a threshold trained
or applied to relabel Table I. The MAT-SPEC-003 helium dispersion series was
collected below 100 mK at multiple pressures; it must not be joined to the
MAT-SPEC-004 temperature rows as though these were one matched physical study.

Source:
- https://doi.org/10.1063/5.0083847
- https://www.mas.ncl.ac.uk/helium/
- https://doi.org/10.1063/1.556028

Existing parent record: DOI **10.5281/zenodo.24062652**, MAT-SPEC-001 only.
MAT-SPEC-004 has **no assigned DOI**.

## Exact numerical contract

For the eight attributed decimal strings, using Python Fraction:

    s_i = 1 - (rho_n/rho)_i
    f_i = 400 * s_i Hz

These are exact representations of reported *rounded decimal inputs*.
They are not the true unrounded physical fraction, a measured acoustic
frequency or an independently calibrated fractional uncertainty.

The "400 Hz" scale is an authored sonification target; it coincides
numerically with the material profile's earlier chosen factor but now acts on
a dimensionless fraction rather than energy in meV. It is **not** a physical
energy-to-sound conversion and the two datasets are not commensurate.
The symbolic MIDI note rounds f_i to the nearest equal-tempered pitch using
the existing MAT-SPEC-001 exact threshold routine; cent deviation is
reported. Dense rank offsets preserve ordering but not magnitudes.

The numerical checks cover eight exact fraction sums, eight target
roundtrips, 28 unique source-value pairs and a reverse-reassociation
negative control. Rank scores and quantized notes cannot make a temperature
series into evidence of a phase transition. Alpha is retained separately;
it is **not** an independent phase label.

## Nonclaims and fail-closed phase gate

All eight observations come from one *He-II* model-parameter table.
MAT-SPEC-004 therefore emits a phase admission result:

    BLOCKED_INSUFFICIENT_PHYSICAL_EVIDENCE

It records five missing requirements:
1. independently attributed observations from normal He-I as well as He-II;
2. an independent physical phase diagnostic (e.g. second-sound response);
3. reported uncertainties or an explicitly calibrated uncertainty model;
4. source-separated held-out phase evaluations, not same-table leakage;
5. measurement-level provenance, not only a secondary model input table.

No phase predictor, threshold classifier, confidence interval, power-law fit,
critical exponent, blinded listening trial or E8 interpretation is calculated.
No sound/PCM/WAV is generated; only CSV/JSON symbolic controls are produced.

To progress to phase discrimination, obtain independently attributed,
appropriately licensed He-I/He-II observations under documented pressure and
temperature conditions, with the diagnostic and uncertainties bound in a
versioned source contract. Predeclare the evaluation plan *before* testing
those observations; the current numerical controls are exploratory.

## Reproduce locally

Python >= 3.11, standard library, offline, no dependency installation:

    uv run --no-project python -m unittest discover -s tests -p 'test_mat_spec*.py' -v
    uv run --no-project python scripts/build_mat_spec_004.py --out dist/mat-spec-004

Output directory must be new. Runtime outputs:
- contract.json — versioned receiver and phase-gate contract
- observations.json — source attribution, exact fractions and absent uncertainties
- temperature-controls.csv — eight exact/quantized/rank controls
- audit.json — conservation, collisions and negative control
- phase-gate.json — mandatory scientific evidence hold with reason codes
- manifest.json — parent, input, implementation and output identity receipts

The profile inherits and replays the pinned MAT-SPEC-001, 002 and 003
ancestors before emitting its own content-bound artifacts. Source data are
CC BY 4.0 with attribution; new code MPL-2.0 and new interpretive prose
CC BY 4.0. Hashes establish identity, not physical truth.
