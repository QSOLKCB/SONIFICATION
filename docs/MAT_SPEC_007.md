# MAT-SPEC-007 v0.1.0: independent campaign fit concordance

MAT-SPEC-007 adds one small, attributed set of *fitted-parameter summaries*
from different helium-4 experimental acquisition campaigns. It is not a
blind phase test and does not establish independent replication of raw data.
Previous MAT-SPEC-001 through MAT-SPEC-006 releases are unchanged.

## Source

Barmatz, Hahn, Lipa and Duncan (2007), Critical phenomena in microgravity:
Past, present, and future, Reviews of Modern Physics 79, 1, DOI
10.1103/RevModPhys.79.1, Table VII. Only the four asterisked
pure-He4 saturated-vapour-pressure (SVP) rows are transcribed.

Each source row includes both the *original measurement campaign* and the
paper supplying or reanalyzing its fit. The two 1970s refits must not be
counted as new acquisition campaigns:

- Ahlers 1971, Bell Labs, DOI 10.1103/PhysRevA.3.696. Mueller et al.
  1976 reanalyzed those data, DOI 10.1103/PhysRevB.14.2096.
- Gasparini and Moldover 1975, DOI 10.1103/PhysRevB.12.93.
  Gasparini and Gaeta 1978 reanalyzed those results, DOI
  10.1103/PhysRevB.17.1466.
- Lipa and Chui 1983 ground calorimetry, DOI
  10.1103/PhysRevLett.51.2291. This is MAT-SPEC-006's source campaign.
- Lipa STS-52 1992 microgravity experiment, DOI
  10.1103/PhysRevLett.76.944, revised 2003 in DOI
  10.1103/PhysRevB.68.174518. These two publications concern one
  orbital experiment, not two independent trials.

Thus there are four *described acquisition campaigns* but only three
laboratory families and one secondary review table. Original primary
article abstracts identify distinct acquisition contexts; source-run
independence and calibration remain unaudited. A later reanalysis is not
a new experiment. The Lipa ground and orbital campaigns share authors.

## Numerical results

For published critical exponent alpha and leading amplitude ratio A+/A-
form the **closed interval** fitted value plus/minus reported fit error.
Exact rational arithmetic avoids threshold rounding, includes touching
as overlap, and checks reversal and positive-scaling covariance.

| Comparison | Overlapping published fit-error boxes | Disjoint boxes |
|---|---:|---:|
| Alpha across six acquisition pairs | 3 | 3 |
| A+/A- across six acquisition pairs | 4 | 2 |

Of six campaign pairs, five cross laboratory families and one compares
distinct Stanford campaigns. This is not a significance test: fit error
distributions, confidence level, model functional forms and covariance
are not harmonized. It is not proof of or against universality.

The authored positive receiver maps dimensionless A+/A- to 400 Hz per
ratio unit and ordinary nearest 12-TET pitch. Four distinct ratios
become two MIDI notes, with three colliding pairs. Signed alpha is not
treated as a positive acoustic frequency. No listening tests are made.

## Scientific admission gate

The gate is PUBLISHED_FIT_CONCORDANCE_ONLY. Primary raw data are not replayed;
the secondary review is not a source-separated held-out experiment;
independent row-level phase diagnoses are missing; errors cannot be
treated as comparable calibrated confidence intervals. There is **no**
trained phase classifier, held-out accuracy, p-value, critical exponent
*newly fitted by this code*, E8 claim, or claim of absolute-zero physics.

## Reproduce

Python >=3.11, stdlib, offline, no new dependencies:

    uv run --no-project python -m unittest discover -s tests -p 'test_mat_spec*.py' -v
    uv run --no-project python scripts/build_mat_spec_007.py --out dist/mat-spec-007

Eight symbolic files: contract, fit summaries, pair relations, lineage,
receiver, replication gate, audit and manifest in JSON/CSV. Source bytes,
metadata, contract, implementation, outputs and all prior profiles are
SHA-256 tied. No PCM, waveform buffer, rendered audio, or MIDI playback.
A fresh output directory is required.

## Finite completion programme

See docs/MAT_SPEC_007_TO_010.md. **MAT-SPEC-010 is the final profile.**
Only after -010 do we begin SPARK/Ada formal verification and a separate
VANILLAJS Lean-to-ECMAScript refinement repair. These obligations are
not completed or silently claimed by MAT-SPEC-007.
