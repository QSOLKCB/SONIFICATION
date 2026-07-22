# ETQ-303 v3 Exact Event Protocol

> **Documentation version 3.0.1.** This is a terminology and exposition
> clarification of the protocol first archived as v3.0.0. No mathematical
> construction, event behavior, ordering, fixture, hash, or scientific claim
> changed.

## 1. Scope and normative status

ETQ-303 v3.0.1 documents the exact finite extension of the released ETQ-101
v2.0.0 selected-root model first published as ETQ-303 v3.0.0. The original
release promotes the optional product space from the v2 formal specification
into a separately named event protocol:

\[
\mathcal H_{303}=\mathcal H_{101}\otimes\mathbb C^3.
\]

Because both factors are finite-dimensional,

\[
\dim(\mathcal H_{303})
=\dim(\mathcal H_{101})\dim(\mathbb C^3)
=101\times3
=303.
\]

Thus 303 is the algebraic dimension of the finite event/state vector space and
also the number of basis-indexed states in the exact construction. It is not a
claim about 303 physical dimensions. The `C^3` factor is the declared
independent three-state, or qutrit-like, factor used by the protocol; the tensor
product introduces no additional physical ontology.

The v3 core is not an audio renderer. It defines a finite state registry, an
exact monomial step, one complete 303-event traversal, an exact graph lift, and
canonical reproducibility receipts. Persisted root receiver artifacts are JSON,
CSV, or MIDI serializations of the same committed event document.

The repository fixture is `examples/etq-303.v3.canonical.json`, with schema
`spec/etq-303.v3.schema.json`. A generated bundle instead writes
`contract.json` beside `contract.schema.json`, and the generated contract uses
`./contract.schema.json` so it remains valid outside the repository layout.

## Notation and Conventions

Unless explicitly stated otherwise, scalars are elements of \(\mathbb C\), all
vector spaces in the ETQ-303 construction are finite-dimensional, and
\(\dim(V)\) denotes the algebraic dimension of the vector space \(V\). The
symbol \(\otimes\) denotes the tensor product over \(\mathbb C\). Operators act
on the finite-dimensional spaces declared by the construction; real Euclidean
root-coordinate spaces are identified explicitly where used.

Throughout this document, “dimension” means finite-dimensional vector-space
dimension unless another mathematical meaning is explicitly declared. It does
not mean physical spacetime dimension. References to the rank or dimensionality
of \(D_4\), \(E_8\), root spaces, selected-state spaces, and tensor-product
spaces are purely mathematical. No physical interpretation should be inferred
unless one is explicitly introduced.

## 2. Preserved v2 base

The base is the immutable ETQ-101 v2.0.0 release:

- Git tag: `v2.0.0`
- Git commit: `8c24d58ca76abbac77c427a4f63ca434570c82b3`
- version DOI: `10.5281/zenodo.21432511`
- selected-basis SHA-256:
  `97cfd1f087745422fd66d3640c7b86c3209593c4b53741018c08a5e9cdb15f6f`
- selected-adjacency SHA-256:
  `29ae0af5b1090c9de30f1efc25789060fb1791eb175d2afcd6888847f7fe6324`

V3 imports the v2 root generator and selector rather than modifying them. The
101 selected E8 roots remain 101 distinct root labels. Tensoring each selected
site with an independent three-state fibre creates 303 states; it does not
create 303 distinct E8 roots.

The ambient \(E_8\) root system is realized in the 8-dimensional Euclidean root
space \(\mathbb R^8\). The embedded \(D_4\) subsystem has rank 4; the numeral 4
describes algebraic rank/root-space dimension, not four-dimensional spacetime.
The selected ETQ-101 graph-state basis contains 101 states, whereas its ETQ-303
tensor extension contains 303 states. These counts are not coordinate-space or
spacetime dimensions.

## 3. Two ternary labels that must not be conflated

For a non-fixed v2 site, the selected basis already carries an **internal D4
triality label** in `{0,1,2}`. V3 adds a separate **external fibre label**
`a in {0,1,2}` through `H_101 tensor C^3`.

The canonical tensor basis is

\[
|j,a\rangle,\qquad j\in\mathbb Z_{101},\quad a\in\mathbb Z_3,
\]

with tensor index

\[
\operatorname{tensorIndex}(j,a)=3j+a.
\]

The two fixed singlets have no internal triality label, but all 101 sites have
all three external fibre labels.

## 4. Exact monomial step

Let

\[
D_3=\operatorname{diag}(1,-2,1),\qquad
F_3=X_3\exp(-i\pi D_3/2),
\]

and let `R_101` be the declared selector-order cyclic shift. V3 uses

\[
F_{303}=R_{101}\otimes F_3.
\]

At the basis-support level,

\[
(j,a)\longmapsto(j+1\bmod101,\ a+1\bmod3).
\]

The exact phase multiplier applied before the fibre shift is a Gaussian unit:

| fibre `a` | curvature `d_a` | multiplier | exponent `g_a` in `i^g_a` |
|---:|---:|---:|---:|
| 0 | 1 | `-i` | 3 |
| 1 | -2 | `-1` | 2 |
| 2 | 1 | `-i` | 3 |

The canonical contract records both the three aligned phase symbols
`[-i,-1,-i]` and the four-value lookup table `[1,i,-1,-i]`; it does not confuse
the two arrays.

The three-step phase exponent is

\[
3+2+3=8\equiv0\pmod4,
\]

so the accumulated local phase over one fibre cycle is exactly one.

### Exact order proof

If the support returns to its initial address after `n` steps, then

\[
n\equiv0\pmod{101},\qquad n\equiv0\pmod3.
\]

Since `gcd(101,3)=1`, the least positive solution is

\[
\operatorname{lcm}(101,3)=303.
\]

The accumulated Gaussian-unit phase over 303 steps is one because the
three-step phase product occurs 101 times. Therefore

\[
F_{303}^{303}=I_{303},
\]

and no smaller positive power is the identity. The tests exhaustively check all
positive powers below 303 and closure on all 303 basis states.

## 5. Canonical event ordering

Starting from `(0,0)`, event `n` has address

\[
j=n\bmod101,\qquad a=n\bmod3,
\]

for `n=0,...,302`. Coprimality makes this a bijection onto all 303 pairs.

The exact inverse is

\[
n=j+101k,
\qquad
k=2(a-(j\bmod3))\bmod3.
\]

Each event records sequence index, tensor index, base site, external fibre,
exact transition phase, next sequence index, and next tensor index. The event
document also contains the 101-entry site registry: exact doubled E8 root
coordinates, v2 state class, internal triality label where present, selected-
graph degree, degree-potential numerator, and preserved v2 MIDI note code.

## 6. Exact graph lift

V3 defines

\[
G_{303}=G_{101}\square C_3.
\]

Horizontal edges copy each of the 1,687 selected-root edges into each of three
fibre layers. Vertical edges attach a copy of `C_3` to every base site. Hence

\[
|V|=101\cdot3=303,
\]

\[
|E|=3(1687)+101(3)=5364.
\]

For a base vertex of degree `d_j`, the lifted degree is `d_j+2`; the v2 range
`22..55` therefore becomes `24..57`. Connectivity follows from the Cartesian
product of connected graphs and is checked directly on the generated edge
list.

The 303-event ordering is **not claimed to be a graph walk** in `G_303`.
`R_101` advances selector order and is not asserted to be an automorphism of
the selected E8 root graph.

## 7. Canonical identity and implementation provenance

Identity-bearing JSON permits only null, booleans, strings, arrays, plain
objects, and safe integers. Object keys are serialized recursively in
lexicographic order. Arrays preserve declared order. Files use UTF-8 with no
BOM and no trailing newline where canonical JSON bytes define identity.

Hashes are domain-separated as

```text
UTF-8(domain) + NUL + payload bytes
```

The contract records an implementation identity built from a declared set of
v3 runtime/export source files. Each file is read as UTF-8 text, CRLF and CR are
normalized to LF, and its byte length and SHA-256 are recorded. A
domain-separated source-bundle hash binds the ordered list. The same identity
is repeated in the contract, observation receipt, and manifest lineage.

The acyclic build order is:

```text
preserved v2 fixtures + v3 implementation identity
  -> site registry + lifted edges + 303 events
  -> canonical event document commitment
  -> deterministic receiver artifacts
  -> observation receipt
  -> manifest core + manifest-core receipt
```

No document claims an ordinary hash of final bytes that include that same hash.
The receipt architecture is methodologically informed by
`10.5281/zenodo.21292906` and `10.5281/zenodo.21293821`; those works are method
references, not mathematical dependencies of the 303-state construction.

## 8. Reference receivers and root output policy

All receivers consume the same committed event document.

| Artifact | Exact role |
|---|---|
| `events.json` | canonical core event document |
| `events.csv` | lossless fixed-column table |
| `graph.json` | exact `G_101 square C_3` nodes and edges |
| `event-atlas.json` | authored integer-grid atlas metadata |
| `events.mid` | symbolic channel-plus-note projection |

The root output policy allows only `.json`, `.csv`, and `.mid`. GraphML, SVG,
NDJSON, WAV, PCM, and other formats are not emitted by the root v3 build. A
separate application or external tool may transform the committed JSON data,
but that transform is not a canonical root artifact.

The MIDI profile uses the external fibre as zero-based channel and the
preserved v2 symbolic note for the base site. It emits one integer tick per
event, velocity 64, and no tempo meta-event. This is a deterministic receiver
convention, not an acoustic scale or mathematical necessity.

## 9. Build safety

`npm run build:v3` writes to a dedicated subdirectory under `dist/`. A custom
`--output` path outside `dist/`, the `dist/` root itself, or an existing
nonempty directory is rejected. The script does not recursively delete caller-
selected paths and writes each artifact with exclusive creation semantics.

## 10. Deliberately excluded from v3 identity

V3 does not use:

- a ring Laplacian as a replacement for the selected-root graph;
- a sorted degree multiset in place of the labelled vertex-degree sequence;
- floating eigensolver output;
- sample rate, hertz, duration, waveform, PCM, or WAV;
- an additive 303-partial renderer;
- claims of exact long-time physical dynamics;
- empirical, statistical, or perceptual validation; or
- 303 distinct E8 roots.

The earlier experimental Python renderer remains a useful design probe. Its
ring surrogate, sorted degrees, continuous evolution, frequency map,
interpolation, and additive synthesis do not enter the v3 contract.

## 11. Verification

Use Node.js 20 or later:

```bash
npm test
npm run verify
npm run build:v3
```

The tests check preserved v2 fixtures, tensor and CRT bijections, exact order,
phase closure and symbol alignment, labelled degree identity, graph product,
receiver allowlisting, implementation identity, schema portability, output-path
safety, and the acyclic receipt chain. `npm run verify` additionally checks the
committed v3 fixtures and continues to run the preserved v2 and v1 verifiers.
