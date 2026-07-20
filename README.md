# ETQ-303 v3: Exact 303-State Root-Indexed Event Protocol

**A deterministic, receiver-neutral event protocol built as the exact product
`H_101 tensor C^3` over the preserved ETQ-101 v2 selected-root model.**

ETQ-303 v3.0.0 turns the optional full-qutrit extension from ETQ-101 v2 into a
complete implementation. Its canonical output is a 303-entry event document,
not a MIDI file and not rendered audio.

```text
ETQ-101 v2 selected roots
        x independent C^3 fibre
                -> 303 exact tensor states
                -> one exact 303-step event traversal
                -> committed event document
                -> JSON / CSV / NDJSON / GraphML / SVG / MIDI receivers
```

## The central result

For basis states `|j,a>` with `j in Z_101` and `a in Z_3`, define the support
step

```text
(j,a) -> (j+1 mod 101, a+1 mod 3)
```

and the exact local phase multiplier from
`X_3 exp(-i*pi*diag(1,-2,1)/2)`. The phase multipliers are `[-i,-1,-i]`, or
Gaussian exponents `[3,2,3]`.

Because `gcd(101,3)=1`, the support step visits all 303 pairs exactly once and
returns after 303 steps. The three-step phase product is one, so the full
monomial operator has exact order 303.

**These are 303 root-indexed tensor states, not 303 distinct E8 roots.**

## Exact graph context

V3 defines

```text
G_303 = G_101 square C_3
```

with exact fixtures:

| Fixture | Value |
|---|---:|
| vertices | 303 |
| horizontal edges | 5,061 |
| vertical fibre edges | 303 |
| total edges | 5,364 |
| degree range | 24-57 |
| connected | yes |

The event ordering is not claimed to be a graph walk.

## Canonical artifacts

`npm run build:v3` creates:

```text
contract.json
contract.schema.json
events.json
events.csv
events.ndjson
graph.graphml
events.svg
events.mid
observation-receipt.json
manifest.json
```

`events.json` is the canonical event commitment. Every receiver is a
deterministic projection of it. The MIDI receiver uses the external fibre as
channel and the preserved v2 symbolic note as note number; no tempo or hertz is
canonical.

## No numerical or acoustic noise in identity

The v3 canonical contract contains no floating-point identity field,
eigensolver output, ring-Laplacian replacement, sorted degree multiset
substituted for labelled vertices, sample rate, hertz, waveform, PCM, WAV,
random input, wall clock, or empirical validation claim.

Identity-bearing JSON accepts safe integers only for numbers.

## Verify

Node.js 20 or newer:

```bash
npm test
npm run verify
npm run build:v3
```

`npm run verify` validates v3 and continues to validate the immutable v2 and v1
contracts.

## Documentation

- [Exact event protocol](docs/ETQ_V3_EVENT_PROTOCOL.md)
- [Claim boundaries](docs/ETQ_V3_CLAIM_BOUNDARIES.md)
- [v2 to v3 migration](docs/ETQ_V2_TO_V3_MIGRATION.md)
- [ETQ-101 v2 mathematical model](docs/MATHEMATICAL_MODEL.md)
- [Auxiliary Tanner tuning fork](docs/TANNER_TUNING_FORK.md)

## Lineage

The preserved base release is ETQ-101 v2.0.0:

- source: Git tag `v2.0.0`, commit
  `8c24d58ca76abbac77c427a4f63ca434570c82b3`
- archive DOI: `10.5281/zenodo.21432511`

The acyclic receipt architecture is methodologically informed by the archived
receipt-bound observation protocol versions `10.5281/zenodo.21292906` and
`10.5281/zenodo.21293821`. They are provenance-method references, not
mathematical dependencies of ETQ-303.

## Scientific boundary

A precise description is:

> ETQ-303 v3.0.0 is an exact finite 303-state tensor extension of the preserved
> ETQ-101 v2 selected-root basis, with a single 303-step monomial support
> traversal, exact Gaussian-unit phase labels, an exact Cartesian graph lift,
> and deterministic receiver artifacts bound to one canonical event document.

It does not claim a 303-dimensional E8 representation, 303 distinct roots,
physical qutrit hardware, an E8-selected acoustic scale, or empirical
validation.

## Creator and licence

Created by **Trent Slade / QSOL-IMC**. Licensed under the Mozilla Public License
2.0. Preserve the copyright and licence notices and use `CITATION.cff` for
citation metadata.
