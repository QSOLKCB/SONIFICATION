# SONIFICATION — ETQ-303 and D4 Triality Research

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21494678.svg)](https://doi.org/10.5281/zenodo.21494678)

This repository contains two related but separately versioned research lines:

- **ETQ-303 v3.0.1** — an exact 303-state event protocol built from the preserved ETQ-101 v2 model.
- **D4-TIA** — exact D4 triality covariants, an exact S3 symmetry harness, and a symbolic sonification profile built on top of them.

They share D4 triality context, but the D4-TIA work does **not** change ETQ-101 or ETQ-303 protocol identity.

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

ETQ-303 extends the preserved 101-state ETQ-101 model with an independent three-state factor:

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
→ ETQ-303 v3
→ preserved ETQ-101 v2 and v1
```

Build the main root bundles with:

```bash
npm run build:v3
npm run build:d4-tia-v2
```

## Root artifact policy

Root builds produce only:

```text
.json
.csv
.mid
```

Rendered PCM/WAV audio is intentionally excluded from root protocol identity.

The separate `APP/` and `sonification/` directories are audio laboratories. They can render audio without changing the root ETQ or D4-TIA contracts.

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

## Archived ETQ releases

- **ETQ-101 v2.0.0** — DOI `10.5281/zenodo.21432511`
- **ETQ-303 v3.0.0** — DOI `10.5281/zenodo.21455181`
- **ETQ-303 v3.0.1** — DOI `10.5281/zenodo.21494678`

The D4-TIA-COV, D4-TIA-S3-EQUIV, and D4-TIA-15 v2 line is implemented and is the next research line to freeze and archive.

## Creator and licence

Created by **Trent Slade / QSOL-IMC**.

Licensed under the Mozilla Public License 2.0. Preserve the copyright and licence notices and use `CITATION.cff` for citation metadata.
