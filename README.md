# SONIFICATION — ETQ-303, D4 Triality and Material Spectra

[![ETQ-303 v3.0.1 DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21494678.svg)](https://doi.org/10.5281/zenodo.21494678) [![D4-TIA v2.0.0 DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22831753.svg)](https://doi.org/10.5281/zenodo.22831753)

This repository contains three separately versioned research lines:

- **ETQ-303 v3.0.1** — the current documentation/publication release for the exact ETQ-303 protocol. The canonical runtime contract and deterministic outputs remain **v3.0.0**.
- **D4-TIA** — exact D4 triality covariants, an exact S3 symmetry harness, and a symbolic sonification profile built on top of them.
- **MAT-SPEC-001 v1.0.0** — attributed superfluid-helium measurements, an exact common-scale frequency mapping, and explicit comparisons with rank contours and quantized MIDI. Record DOI: [10.5281/zenodo.24062652](https://doi.org/10.5281/zenodo.24062652).

ETQ and D4-TIA share D4 triality context. MAT-SPEC-001 adds an independent physical-data profile. Neither extension changes ETQ-101 or ETQ-303 protocol identity.

## MAT-SPEC-001: measured materials, declared mappings

The first material profile retains all 7,350 positions in Godfrin et al.'s
helium-4 table: 7,118 energy/error pairs and 232 explicitly missing pairs.
A fixed 400 Hz/meV symbolic mapping preserves the tabulated energy ratios and
scales the reported errors. Six selected wavevectors at each of seven pressures
provide 42 matched comparison events. Rank mapping yields three contours;
quantized MIDI records its own rounding error. These are numerical preservation
results, not listener results or an identification of E8 symmetry in helium.

Python 3.11+ standard library; no project install or network access is needed:

```bash
uv run --no-project python -m unittest discover -s tests -p test_mat_spec.py -v
uv run --no-project python scripts/build_mat_spec.py --out dist/mat-spec-001
```

The output directory must be new. Runtime artifacts are JSON, CSV and symbolic
MIDI only. [The profile specification](docs/MAT_SPEC_001.md) describes the
mapping, controls and provenance. The [original feasibility study](docs/materials/FEASIBILITY.md)
is preserved as its research background.

## MAT-SPEC-002: uncertainty and sampling sensitivity

A separately versioned, symbolic-only successor adds **22,050 matched-q pressure comparisons**, exact reported-interval checks, stream/tile parity, and GLUBALL uniform-floor sampling controls at 6/12/24/48 positions. It borrows invariant/evidence engineering from QEC, OPT, SPECTRAL, GALAXY, GLUBALL and UFF while keeping physical-model and listener claims explicitly untested.

Reproduce: `uv run --no-project python scripts/build_mat_spec_002.py --out dist/mat-spec-002`.

See [MAT-SPEC-002 experimental controls](docs/MAT_SPEC_002.md). The frozen MAT-SPEC-001 package and archived DOI remain unchanged.

## MAT-SPEC-003: Physical Mode Discrimination

An independently versioned, offline research adapter extracts explicitly windowed
**phonon-region slope**, **maxon-like maximum**, and **roton-like minimum** descriptors
from the measured low-temperature helium dispersion table. It propagates reported
error bounds, rejects incomplete-window claims, compares 63 pressure/feature
pairs, audits alternative wavevector windows, and tests exact-energy versus rank
and 12-TET MIDI information loss. It does **not** classify material phases,
measure a q→0 sound speed, fit a Hamiltonian, recognize E8, or test listeners.

Run `uv run --no-project python scripts/build_mat_spec_003.py --out dist/mat-spec-003`.
The broad roton window remains ineligible because of explicitly missing
measurements. A **separately labelled post-hoc, coverage-selected core** at
q=1.860–2.150 inverse angstrom (146 shared observed positions) supplies
21 conditional roton comparisons: 20 separated, one overlapping.
The exact two-energy receiver distinguishes seven pressures; quantized
MIDI gives four contours and two-value ranks collapse to one. These are
numerical preservation results, not phase or listening evidence.

[Full methods and nonclaims](docs/MAT_SPEC_003.md). MAT-SPEC-001 DOI:
[10.5281/zenodo.24062652](https://doi.org/10.5281/zenodo.24062652).

## MAT-SPEC-004 v0.1.0 — temperature-series preservation and phase gate

The next independent research profile transcribes eight 0.9–2.1 K
superfluid-helium **model-parameter** entries from Bhadra and Mishra
(AIP Advances, DOI 10.1063/5.0083847, CC BY 4.0). It derives exact
two-fluid fractions and symbolic receiver controls while preserving
missing uncertainty metadata.

The eight exact fractions remain distinct; authored 12-TET controls retain
six distinct notes (three pair collisions). This is numerical quantization,
not evidence of audibility.

**Scientific gate:** All published inputs are He-II model parameters, not
independently phase-labelled measurements spanning the transition.
MAT-SPEC-004 therefore explicitly reports
\`BLOCKED_INSUFFICIENT_PHYSICAL_EVIDENCE\`: no classifier, critical exponent,
temperature threshold or listener outcome is claimed. MAT-SPEC-003's
pressure-dependent below-100-mK spectra are not matched to this new series.

Reproduce: \`uv run --no-project python scripts/build_mat_spec_004.py --out dist/mat-spec-004\`.
Read the [methods and evidence boundaries](docs/MAT_SPEC_004.md).
The DOI 10.5281/zenodo.24062652 remains the MAT-SPEC-001 record.

## MAT-SPEC-005 — cross-transition helium reference and phase-witness boundary

An independently versioned, offline physical-reference adapter transcribes
14 selected Donnelly–Barenghi recommended helium-4 observations (DOI
10.1063/1.556028) at saturated vapour pressure, covering both sides of the
2.1768 K lambda reference. First-sound and heat-capacity recommendations
cross the transition; second sound is tabulated only in helium-II, with a
separate recommended zero limit exactly at lambda. **Absent values above
lambda remain null, not zero.**

The profile compares exact physical-property targets against lossy
symbolic 12-TET mappings while requiring frozen source/provenance receipts.
**Contextual He-I/He-II labels are not independent phase diagnostics**;
the classifier/held-out scientific gate remains BLOCKED. Source is an
experiment-derived reference compilation, not original raw measurements.

Reproduce: \`uv run --no-project python scripts/build_mat_spec_005.py --out dist/mat-spec-005\`.
[Methods and nonclaims](docs/MAT_SPEC_005.md). The MAT-SPEC-001 DOI
10.5281/zenodo.24062652 remains assigned to the original record.

## MAT-SPEC-006 — primary calorimetry evidence and phase validation preflight

A separately versioned scientific evidence layer transcribes twelve
gravity-corrected and averaged **original experimental heat-capacity values**
from the Stanford Lipa–Chui 1984 data release (NASA-CR-177037, Appendix A).
Six values are below and six above the SVP lambda point, recorded as signed
**microkelvin offsets**, not inferred absolute temperatures. The excerpt
is pinned by SHA-256 with source metadata and a five-source provenance
inventory. Exact controls retain 12 distinct heat capacities but yield 7
quantized MIDI notes and 7 colliding sample pairs. These measurements are experimentally reported, not raw
per-instrument event files.

A future **source-family-separated** validation protocol rejects row
leakage, temperature-derived labels, fabricated error bars and missing
orthogonal phase witnesses. There is **no independently validated phase
classifier or held-out accuracy** in this release: only one primary
experimental campaign is admitted, per-row uncertainty is missing, and
experimental overlap with the MAT-SPEC-005 compilation remains unverified.

Reproduce: \`uv run --no-project python scripts/build_mat_spec_006.py --out dist/mat-spec-006\`.
[Physical provenance and limits](docs/MAT_SPEC_006.md).
The DOI 10.5281/zenodo.24062652 remains MAT-SPEC-001's record only.

## MAT-SPEC-007 — Independent experiment fit concordance

Four published fit-summary records for pure helium-4 at SVP are compared
with separate original experiment, later reanalysis and laboratory-family
provenance. Signed critical-exponent and positive amplitude-ratio uncertainty
boxes are audited using exact arithmetic. They are **review-derived fitted
parameters**, not raw independent measurements or verified phase labels.

Reproduce: uv run --no-project python scripts/build_mat_spec_007.py
--out dist/mat-spec-007. See docs/MAT_SPEC_007.md.

**Stop at MAT-SPEC-010** for numbered profiles. Separate SPARK/Ada proof
work and the VANILLAJS Q16-ECMA corrective investigation have already been
executed. See [verification status](docs/ROADMAP.md) and
[acceptance gates](docs/MAT_SPEC_007_TO_010.md).

## MAT-SPEC-008 — Measurement-level independence admission

Audits ten attributed publications covering four experimental helium
acquisitions and three lab families, while differentiating *original
processed heat-capacity observations* from reanalyses and reviews.

Only the existing 12 source-pinned Lipa–Chui measurements (MAT-SPEC-006)
currently meet the pinned numeric-row requirement. **No other acquisition
has a verified original measurement packet**, so there are zero
independently replicable source-pair comparisons and no classifier score.
This is an explicit evidence-gate result, not a scientific falsification.

Run \`uv run --no-project python scripts/build_mat_spec_008.py --out
dist/mat-spec-008\`. See [full source admission audit](docs/MAT_SPEC_008.md).

The programme still **stops at MAT-SPEC-010**. The scoped SPARK/Ada
and VANILLAJS Q16-ECMA follow-ups have been executed separately; see
[current verification status](docs/ROADMAP.md).

## MAT-SPEC-009 — Prospective physical challenge, synthetic controls

MAT-SPEC-008 admits no independent two-experiment source-bound measurements.
MAT-SPEC-009 therefore refuses to generate a physical phase-classifier
score, defines a prospective source-family-separated TRAIN/HOLDOUT
protocol, and executes 14 synthetic negative-control tests for
same-experiment leakage, forged source independence, circular labels,
missing errors, post hoc receiver changes and malformed preregistration
receipts. Even a structural candidate pass never authenticates physics.

Reproduce with
\`uv run --no-project python scripts/build_mat_spec_009.py --out dist/mat-spec-009\`.
See [scientific protocol and negative evidence](docs/MAT_SPEC_009.md).

**MAT-SPEC-010 closes the numbered series.** Separate SPARK/Ada and
VANILLAJS Q16-ECMA corrective work has already been performed. Its
precise proof limits are in the [roadmap](docs/ROADMAP.md).

## MAT-SPEC-010 — Final evidence freeze (no MAT-SPEC-011)

The MAT-SPEC numbered research programme ends at 010. This stage
replays the earlier profiles, inventories original measured data,
model input tables, reference compilations, secondary fits and
synthetic controls, and publishes a source-checked SHA-256 JSON
archive *index* rather than a deposited scientific archive.

The independent physical phase-classifier gate remains BLOCKED:
only one campaign has pinned processed measurement rows, and no
source-separated heldout phase evaluation has occurred. Hash replay
is software reproducibility, not independent physical replication.

Run: uv run --no-project python scripts/build_mat_spec_010.py
--out dist/mat-spec-010.

See docs/MAT_SPEC_010.md and docs/MAT_SPEC_010_HANDOFF.md.
The post-010 scoped SPARK/Ada and VANILLAJS Q16-ECMA milestones are
already documented; universal production-JS refinement remains open
in VANILLAJS, not as a future SONIFICATION repair phase.
No MAT-SPEC-011.

## SPARK-001 — Numerical verification after MAT-SPEC-010

The bounded Ada/SPARK kernel lives under verification/spark/, outside
the completed MAT-SPEC-001 through 010 research profiles. It checks
exact signed hundredths, closed intervals, missingness versus boundary
zero and declared source/diagnostic isolation. A deterministic Python
reference compares hundreds of inputs with an independently compiled
GNAT executable. This **tests code**, not experimental helium physics.

GNATprove is a separate **owner-authorized local main-only workflow**:
.github/workflows/spark-001-proof.yml. No automatic untrusted-branch
execution on the QSOL self-hosted runner. A completed compiler/differential
job does not mean proof obligations are discharged.

See [SPARK-001 method and limits](docs/SPARK_001.md) and the
[updated roadmap](docs/ROADMAP.md). VANILLAJS Q16-ECMA-001 is merged
(PR #60); a broader universal ECMAScript refinement is still OPEN
within VANILLAJS.

## The short version

ETQ-303:

```text
ETQ-101 v2 selected states
        × independent 3-state fibre
                → 303 exact tensor states
                → one exact 303-step traversal
                → deterministic event document
                → JSON / CSV / symbolic MIDI
```

D4-TIA:

```text
published 15-generator D4 covariant basis
        → exact symbolic covariants
        → exact S3 action and equivariance checks
        → exact six-position evaluations
        → symbolic MIDI contour
```

The repository is designed so that the mathematics, the event data, and the receiver choices remain distinguishable.

## ETQ-303 in plain language

The ETQ-303 runtime contract is **v3.0.0**. The **v3.0.1** repository release only clarifies its documentation and publication material; it does not change the runtime contract, state indexing, event generation, or deterministic outputs.

The protocol extends the preserved 101-state ETQ-101 model with an independent three-state factor:

```math
\mathcal H_{303}=\mathcal H_{101}\otimes\mathbb C^3.
```

That gives exactly $101\times3=303$ basis-indexed states.

The support step advances both indices:

```text
(j,a) → (j+1 mod 101, a+1 mod 3)
```

Because 101 and 3 are coprime, one traversal visits all 303 tensor addresses exactly once before returning to the start.

**303 means algebraic states here. It does not mean 303 physical dimensions or 303 distinct E8 roots.**

The canonical ETQ output is an event document. JSON, CSV, and MIDI are deterministic receiver formats built from that document.

See [the ETQ-303 event protocol](docs/ETQ_V3_EVENT_PROTOCOL.md) for the full construction.

## D4 triality bridge

The repository also checks that the four-coordinate ETQ triality matrix matches the D4/F4 convention used by Kazuhiro Sakai:

```math
A=w_Sw_T,
\qquad
W(F_4)/W(D_4)\cong S_3.
```

That is a literature alignment. It does not mean Sakai's papers derive ETQ's state selector, qutrit factor, SCL stencil, or sonification choices.

See [the D4/F4 triality reference bridge](docs/D4_TRIALITY_REFERENCE_BRIDGE.md).

## D4-TIA: from published algebra to sound

The D4-TIA work is split into three layers.

### 1. Exact covariant algebra

**D4-TIA-COV v0.1.0** constructs the published 15-generator basis directly with exact rational arithmetic.

It verifies the covariants, their grading, and the cubic syzygy. No floating-point algebra is used.

Verify it with:

```bash
npm run verify:d4-tia-cov
```

See [D4-TIA-COV](docs/D4_TRIALITY_COVARIANT_ENGINE.md).

### 2. Exact symmetry and equivariance

**D4-TIA-S3-EQUIV v0.1.0** builds the six-element D4/F4 triality quotient and matches it to six canonical representatives of

```math
SL_2(\mathbb Z)/\Gamma(2)\cong S_3.
```

For all 15 covariants and all six representatives, the repository verifies the exact transformation law

```math
\Psi(\alpha';u,v)=\Psi(\alpha;u',v').
```

That is **90 exact symbolic equivariance checks**.

Verify it with:

```bash
npm run verify:d4-tia-s3
```

See [D4-TIA-S3-EQUIV](docs/D4_TRIALITY_S3_EQUIVARIANCE.md).

### 3. Evaluated-covariant sonification

**D4-TIA-15 v2.0.0** evaluates the 15 exact covariants across the six quotient positions and maps their exact within-generator value ordering into a small MIDI pitch contour.

The fixed evaluation probe is:

```text
(a0,a1,a2,b0,b1,b2,b3) = (1,2,3,4,5,6,7)
(u,v) = (1,0)
```

This produces:

```text
15 generators × 6 orbit positions = 90 symbolic events
```

The coefficient probe and pitch mapping are authored sonification choices. The exact algebra and symmetry checks are separate from those choices.

For the five order-zero invariants, the receiver requires the same:

- exact value;
- MIDI note;
- MIDI channel;
- velocity; and
- duration

at every orbit position.

So the invariant rows remain invariant at the symbolic MIDI-control level. Their playback time changes because the six orbit positions are presented in sequence.

Verify and build v2 with:

```bash
npm run verify:d4-tia-v2
npm run build:d4-tia-v2
```

See [D4-TIA-15 v2](docs/D4_TRIALITY_ALGEBRA_SONIFICATION_V2.md).

The preserved v1 grading-only profile is documented at [D4-TIA-15 v1](docs/D4_TRIALITY_ALGEBRA_SONIFICATION.md).

## Quick verification

Node.js 20 or newer:

```bash
npm test
npm run verify
```

The full verifier checks:

```text
D4-TIA-COV
→ D4-TIA-S3-EQUIV
→ D4-TIA-15 v2
→ preserved D4-TIA-15 v1
→ ETQ-303 runtime v3.0.0
→ preserved ETQ-101 v2 and v1
```

Build the main root bundles with:

```bash
npm run build:v3
npm run build:d4-tia-v2
```

## Runtime/export artifact policy

The root runtime/export bundle commands — `npm run build:v3`, `npm run build:d4-tia`, and `npm run build:d4-tia-v2` — persist only:

```text
.json
.csv
.mid
```

That allowlist applies to generated runtime/export artifacts, not normal repository or publication files. For example, `npm run build:paper` may produce archival PDF and checksum files.

Rendered audio generation is **permanently prohibited** in root ETQ runtime/export workflows. Root code must not create PCM or sampled-audio buffers even transiently — in memory, temporary files, caches, logs, snapshots, fixtures, playback paths, or analysis steps — and must not encode or emit WAV or any other rendered-audio format.

The separate `APP/` and `sonification/` directories are independent audio laboratories. They may render audio, but those features must not be imported into, called from, or used to bypass the root ETQ runtime/export policy.

## ETQ-303 artifacts

`npm run build:v3` writes a deterministic bundle containing the canonical contract, event document, graph data, observation receipt, symbolic MIDI, and manifest.

The exact file list and provenance rules are documented in [the ETQ-303 event protocol](docs/ETQ_V3_EVENT_PROTOCOL.md).

No tempo or hertz value is canonical.

## D4-TIA v2 artifacts

`npm run build:d4-tia-v2` writes:

```text
contract.json
evaluations.json
events.json
events.csv
events.mid
manifest.json
```

`evaluations.json` keeps the exact 15-by-6 covariant evaluation matrix separate from the 90-event receiver document.

## Scientific boundary

This repository makes exact mathematical and deterministic software claims about the constructions it implements.

It does **not** claim:

- physical spacetime dimensions from algebraic dimension;
- 303 distinct E8 roots;
- a unique pitch system implied by E8 or D4 invariant theory;
- physical qutrit hardware;
- canonical tempo, tuning, timbre, or loudness;
- empirical validation from symbolic MIDI alone.

Where a mapping is authored rather than mathematically forced, the documentation says so.

## Documentation

- [ETQ-303 exact event protocol](docs/ETQ_V3_EVENT_PROTOCOL.md)
- [D4/F4 triality reference bridge](docs/D4_TRIALITY_REFERENCE_BRIDGE.md)
- [D4-TIA-COV exact covariant engine](docs/D4_TRIALITY_COVARIANT_ENGINE.md)
- [D4-TIA-S3-EQUIV symmetry harness](docs/D4_TRIALITY_S3_EQUIVARIANCE.md)
- [D4-TIA-15 v2 evaluated-covariant sonification](docs/D4_TRIALITY_ALGEBRA_SONIFICATION_V2.md)
- [D4-TIA-15 v1 grading-only sonification](docs/D4_TRIALITY_ALGEBRA_SONIFICATION.md)
- [ETQ claim boundaries](docs/ETQ_V3_CLAIM_BOUNDARIES.md)
- [ETQ v2 to v3 migration](docs/ETQ_V2_TO_V3_MIGRATION.md)
- [ETQ-101 v2 mathematical model](docs/MATHEMATICAL_MODEL.md)
- [Implementation roadmap](docs/ROADMAP.md)
- [Formal ETQ-303 v3.0.1 paper](docs/etq-303/README.md)

## Archived releases

- **ETQ-101 v2.0.0** — DOI `10.5281/zenodo.21432511`
- **ETQ-303 v3.0.0** — DOI `10.5281/zenodo.21455181`
- **ETQ-303 v3.0.1 documentation/publication release** — DOI `10.5281/zenodo.21494678`
- **D4-TIA v2.0.0** — DOI `10.5281/zenodo.22831753`

D4-TIA v2.0.0 archives the frozen D4-TIA-COV v0.1.0, D4-TIA-S3-EQUIV v0.1.0, and D4-TIA-15 v2.0.0 research line. The immutable implementation tag `d4-tia-v2.0.0` points to commit `7aa6df165d0ad70297365dbf0d69072634ed4314`. Publication/citation metadata was finalized afterward on the documentation line without changing the frozen D4-TIA runtime identity or deterministic commitments. D4-TIA remains separately versioned from the preserved ETQ runtime contracts.

## Creator and licence

Created by **Trent Slade / QSOL-IMC**.

Licensed under the Mozilla Public License 2.0. Preserve the copyright and licence notices. Use `CITATION.cff` for ETQ-303 citation metadata and `CITATION-D4-TIA.cff` for the archived D4-TIA v2.0.0 release.
