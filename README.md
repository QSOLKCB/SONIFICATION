# ETQ-303 v3.0.1: Exact 303-State Root-Indexed Event Protocol

**A deterministic, receiver-neutral event protocol built as the exact product
`H_101 tensor C^3` over the preserved ETQ-101 v2 selected-root model.**

ETQ-303 v3.0.1 is a documentation-only clarification of the exact protocol
first archived as v3.0.0. It does not change the mathematical construction,
state indexing, event generation, deterministic outputs, or scientific claim
boundary. The canonical output remains a 303-entry event document, not a MIDI
file and not rendered audio.

```text
ETQ-101 v2 selected roots
        x independent C^3 fibre
                -> 303 exact tensor states
                -> one exact 303-step event traversal
                -> committed event document
                -> JSON / CSV / symbolic MIDI receivers
```

## The central result

For basis states `|j,a>` with `j in Z_101` and `a in Z_3`, define

```text
(j,a) -> (j+1 mod 101, a+1 mod 3).
```

The exact local phase multiplier is supplied by
`X_3 exp(-i*pi*diag(1,-2,1)/2)`. Its phase exponents are `[3,2,3]`, with aligned
Gaussian-unit symbols `[-i,-1,-i]`.

Because `gcd(101,3)=1`, the support step visits all 303 pairs exactly once and
returns after 303 steps. The three-step phase product is one, so the complete
monomial operator has exact order 303.

**These are 303 root-indexed tensor states, not 303 distinct E8 roots.**

## Notation and Conventions

Unless explicitly stated otherwise, scalars are in \(\mathbb C\), all vector
spaces in the ETQ-303 construction are finite-dimensional, \(\dim(V)\) is
algebraic vector-space dimension, and \(\otimes\) is the tensor product over
\(\mathbb C\). Operators act on the finite-dimensional spaces declared by the
construction.

Throughout the ETQ-303 documentation, “dimension” means finite-dimensional
vector-space dimension unless another mathematical meaning is explicitly
declared. It never means physical spacetime dimension. The \(E_8\) root system
is represented in an 8-dimensional Euclidean root space, while each \(D_4\)
factor has rank 4. Those numbers describe algebraic root spaces, not spacetime.
No physical interpretation follows from rank, dimension, state count, or
tensor-product notation alone.

The state-space construction is explicitly

\[
\mathcal H_{303}=\mathcal H_{101}\otimes\mathbb C^3,
\]

with

\[
\dim(\mathcal H_{303})
=\dim(\mathcal H_{101})\dim(\mathbb C^3)
=101\times3
=303.
\]

Thus 303 is both the algebraic dimension of the finite event/state vector space
and the number of basis-indexed states. The \(\mathbb C^3\) factor is the
declared independent three-state, or qutrit-like, protocol factor; it introduces
no additional physical ontology.

## Exact graph context

V3 defines the Cartesian graph lift

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

`npm run build:v3` writes only root-policy-allowed `.json`, `.csv`, and `.mid`
artifacts into a new or empty dedicated subdirectory of `dist/`:

```text
contract.json
contract.schema.json
events.json
events.csv
graph.json
event-atlas.json
events.mid
observation-receipt.json
manifest.json
```

`events.json` is the canonical event commitment. `graph.json` preserves the
exact Cartesian graph data, while `event-atlas.json` supplies integer-grid
layout metadata without privileging a rendered image format. External tools may
convert these JSON records to GraphML, SVG, OSC, DMX, or other receiver formats;
such conversions are outside the root ETQ export workflow.

The MIDI receiver uses the external fibre as channel and the preserved v2
symbolic note as note number. No tempo or hertz value is canonical.

## Provenance and implementation identity

The contract, observation receipt, and manifest all record a deterministic v3
implementation identity. It hashes the normalized UTF-8 bytes of the exact v3
core, canonical serializer, receivers, artifact builder, and build entrypoint.
This binds generated artifacts to the implementation that produced them even
when the semantic version remains `3.0.0`.

The repository/documentation release is v3.0.1, while the unchanged canonical
runtime contract remains v3.0.0. Consequently this patch does not regenerate or
rename protocol fixtures, event hashes, or the v3 implementation identity.

The generated bundle uses `./contract.schema.json`, so its contract validates
without depending on the repository directory layout. The committed repository
fixture continues to reference `../spec/etq-303.v3.schema.json`. `$schema` is
excluded from the semantic contract-payload hash, so the two location-correct
references do not create different mathematical contract identities.

## No numerical or acoustic noise in identity

The v3 canonical contract contains no floating-point identity field,
eigensolver output, ring-Laplacian replacement, sorted degree multiset
substituted for labelled vertices, sample rate, hertz, waveform, PCM, WAV,
random input, wall clock, or empirical validation claim.

Identity-bearing JSON accepts safe integers only for numeric values.

## Verify

Node.js 20 or newer:

```bash
npm test
npm run verify
npm run build:v3
```

`npm run verify` validates v3 and continues to validate the immutable v2 and v1
contracts. The build command fails closed for unsafe, existing nonempty, or
non-`dist/` output paths and never recursively deletes a caller-selected path.

## Documentation

- [Exact event protocol](docs/ETQ_V3_EVENT_PROTOCOL.md)
- [Claim boundaries](docs/ETQ_V3_CLAIM_BOUNDARIES.md)
- [v2 to v3 migration](docs/ETQ_V2_TO_V3_MIGRATION.md)
- [Formal v3.0.1 paper and build instructions](docs/etq-303/README.md)
- [v3.0.1 release notes](docs/ETQ_V3_0_1_RELEASE_NOTES.md)
- [ETQ-101 v2 mathematical model](docs/MATHEMATICAL_MODEL.md)
- [Auxiliary Tanner tuning fork](docs/TANNER_TUNING_FORK.md)

## Lineage

The preserved base release is ETQ-101 v2.0.0:

- source: Git tag `v2.0.0`, commit
  `8c24d58ca76abbac77c427a4f63ca434570c82b3`
- archive DOI: `10.5281/zenodo.21432511`

The original ETQ-303 release remains immutable:

- source: Git tag `v3.0.0`, commit
  `6b55e51647226d1c248dc8d79f9ed9336241c2ac`
- archive DOI: `10.5281/zenodo.21455181`

Version 3.0.1 adds only terminology and exposition clarifications. It is
intended to receive its own tag and Zenodo version DOI after review and merge.

The acyclic receipt architecture is methodologically informed by the archived
receipt-bound observation protocol versions `10.5281/zenodo.21292906` and
`10.5281/zenodo.21293821`. They are provenance-method references, not
mathematical dependencies of ETQ-303.

## Scientific boundary

A precise description is:

> ETQ-303 v3.0.1 documents the exact finite 303-state tensor extension of the preserved
> ETQ-101 v2 selected-root basis, with a single 303-step monomial support
> traversal, exact Gaussian-unit phase labels, an exact Cartesian graph lift,
> and deterministic receiver artifacts bound to one canonical event document.

Here “303-dimensional” is strictly algebraic. The construction does not claim
303 physical dimensions, a 303-dimensional E8 representation, 303 distinct
roots, physical qutrit hardware, an E8-selected acoustic scale, or empirical
validation.

## Creator and licence

Created by **Trent Slade / QSOL-IMC**. Licensed under the Mozilla Public License
2.0. Preserve the copyright and licence notices and use `CITATION.cff` for
citation metadata.
