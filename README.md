# ETQ-101 v2: E8-Root, D4-Triality Ternary MIDI Model

**A deterministic mathematical model and symbolic MIDI codebook for an
E8-root-indexed, triality-structured 101-state space.**

[![Tests](https://github.com/QSOLKCB/SONIFICATION/actions/workflows/tests.yml/badge.svg)](https://github.com/QSOLKCB/SONIFICATION/actions/workflows/tests.yml)
[![Node.js 20+](https://img.shields.io/badge/Node.js-20%2B-339933.svg)](https://nodejs.org/)
[![License: MPL-2.0](https://img.shields.io/badge/License-MPL--2.0-blue.svg)](LICENSE)
[![Archived v1 DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21404224.svg)](https://doi.org/10.5281/zenodo.21404224)

ETQ-101 v2.0.0 keeps the exact E8-root construction, embedded order-three D4
triality, 33 direct-sum qutrit blocks, two fixed singlets, and ternary-curvature
phase drive. It removes the two least defensible forward-profile choices:

- the golden ratio is no longer used in the state, generator, or pitch map;
- 432 Hz is no longer used as a dynamics clock or sonification reference.

The replacement uses a selected-root-graph degree potential and a symbolic
Standard MIDI note codebook. No canonical acoustic frequency is defined.

## Model at a glance

| Element | ETQ-101 v2 definition |
|---|---|
| E8 | Exact standard set of 240 roots in doubled integer coordinates |
| Triality | Explicit order-three D4 action preserving the E8 root set |
| 101-state sector | Canonical triality-closed root-indexed graph space |
| State-space split | `C^2 direct-sum (C^33 tensor C^3)` |
| Ternary curvature | `D3 = diag(1, -2, 1)` |
| Qutrit labels | Cyclic computational labels `[0, 1, 2]` |
| Phase | Declared quadrature `theta = pi/2` |
| Third generator term | Exact centered degree potential of the selected E8 root graph |
| Observation map | Qutrit labels → authored low/mid/high MIDI registers |
| Absolute frequency | Undefined; receiver tuning is external and non-normative |
| Root audio | Permanently disabled; no PCM or rendered-audio pipeline |

The compact state space is

$$
\boxed{
\mathcal H_{101}
=\mathbb C^2
\oplus
\left(\mathbb C^{33}\otimes\mathbb C^3\right).
}
$$

This resolves the arithmetic constraint that 101 is not divisible by three.
The construction contains 33 complete qutrit/triality orbits and two fixed
singlets; it is not a tensor product of 33 independent qutrits.

## Model-native replacement for golden modulation

Let \(W\) be the selected 101-node E8 root-graph adjacency, let
\(d_j=\sum_kW_{jk}\), and note that

$$
\sum_jd_j=3374=2(1687),
\qquad
\overline d=\frac{3374}{101}.
$$

The forward profile uses the exact centered, operator-norm-normalized degree
potential

$$
\boxed{
(V_{\deg})_{jj}
=\frac{101d_j-3374}{2181}.
}
$$

It has zero trace, operator norm one, and is constant on each triality orbit;
therefore it commutes with the triality permutation. Its use and coefficient
remain declared model choices. It is derived from the **selected** root graph,
not claimed as an invariant of the complete E8 root system or as independent
information beyond the graph Laplacian.

The v2 generator is

$$
K=\frac{11}{20}\overline L_E
+\frac14\overline L_Q
+\frac15V_{\deg}.
$$

The initial state uses qutrit character and SCL phase directly:

$$
|\Omega_{3,\theta}\rangle
=\frac1{\sqrt{101}}
\left[
|s_0\rangle+|s_1\rangle+
\sum_{m=0}^{32}\sum_{q=0}^{2}
e^{2\pi iq/3-i\theta d_q}|m,q\rangle
\right],
$$

where \((d_0,d_1,d_2)=(1,-2,1)\). The fixed singlets have explicitly zero
phase; they are not silently assigned a qutrit label.

## Dimensionless dynamics

The forward model has no built-in clock measured in hertz or seconds. Its
continuous parameter \(s\) and Floquet step are dimensionless:

$$
\frac{d\rho}{ds}=-i[K,\rho],
\qquad
U_F=e^{-i\delta K}F_Q,
\qquad
\delta=\frac{2\pi}{303}.
$$

Any later MIDI tempo or wall-clock schedule belongs to a separately versioned
observation profile. It is not an E8 prediction.

## Low, mid, and high ternary MIDI codebook

For basis indices

$$
j=2+3m+q,
\qquad
m\in\{0,\ldots,32\},
\quad q\in\{0,1,2\},
$$

the exact codebook is

$$
\boxed{M(m,q)=14+33q+m.}
$$

The two fixed singlets occupy the bookend notes 13 and 113.

| State class | MIDI notes | Interpretation |
|---|---:|---|
| Fixed singlet 0 | 13 | Lower codebook boundary |
| \(q=0\) | 14–46 | Low register |
| \(q=1\) | 47–79 | Mid register |
| \(q=2\) | 80–112 | High register |
| Fixed singlet 1 | 113 | Upper codebook boundary |

This is a bijection between 101 basis states and 101 MIDI note numbers. The
inverse for notes 14–112 is

```text
offset = note - 14
q = floor(offset / 33)
m = offset mod 33
j = 2 + 3*m + q
```

The codebook is model-aligned but not a physical spectrum:

- qutrit labels form a cyclic set, not an intrinsic energy ordering;
- low/mid/high is an authored perceptual code for those labels;
- orbit order is the canonical lexicographic selector order;
- the singlet bookends are code boundaries, not spectral extrema; and
- MIDI notes do not determine acoustic hertz, timbre, or loudness.

The current v2 release implements and hashes the codebook. A dynamics-to-event
rule and Standard MIDI file exporter remain future, separately versioned work.

## Validation layers

ETQ separates three questions that must not be conflated:

1. **Deterministic correctness** — exact roots, triality, graph fixtures,
   potential receipts, codebook bijection, schema, and hashes.
2. **Graph-conditional null testing** — optional graph-Fourier surrogate tests
   ask whether a node signal differs from a topology-aware stationary null.
3. **Perceptual evaluation** — listener studies ask whether people can decode
   the low/mid/high display reliably.

The graph-surrogate design follows Pirondini et al.'s graph-Fourier
sign-randomization method while strengthening degenerate-mode handling through
grouped eigenspace projectors. See
[Graph Surrogate Testbench](docs/GRAPH_SURROGATE_TESTBENCH.md).

The parameter map follows the design discipline in Grond and Berger's
“Parameter Mapping Sonification”: make data classes, target parameters,
polarity, scaling, timing, receiver assumptions, and evaluation explicit. See
[Ternary MIDI Mapping](docs/SONIFICATION_MAPPING.md).

Neither validation layer establishes a physical E8 system or makes one
auditory code uniquely correct.

## Contracts and implementation

| Resource | Purpose |
|---|---|
| [Mathematical model](docs/MATHEMATICAL_MODEL.md) | Normative v2 construction, operators, dynamics, and observables |
| [Ternary MIDI mapping](docs/SONIFICATION_MAPPING.md) | Symbolic codebook, mapping boundaries, and evaluation requirements |
| [Claim boundaries](docs/CLAIM_BOUNDARIES.md) | Exact results, authored choices, and excluded claims |
| [Graph surrogate testbench](docs/GRAPH_SURROGATE_TESTBENCH.md) | Optional topology-aware null-test design |
| [v2 canonical contract](examples/etq-101.v2.canonical.json) | Fixed forward parameters and regression hashes |
| [v2 JSON Schema](spec/etq-101.v2.schema.json) | Machine-readable forward schema |
| [Reference construction](src/etq-model.mjs) | Dependency-free E8, triality, potential, generator, state, and MIDI codebook implementation |
| [Model tests](tests/etq-model.test.mjs) | Algebraic, graph, phase, potential, and codebook tests |
| [Verifier](scripts/verify.mjs) | v2 contract and fixture verification |

## Legacy v1.0.0 preservation

The DOI-linked ETQ-101 v1.0.0 contract is preserved byte-for-byte at
[`examples/etq-101.canonical.json`](examples/etq-101.canonical.json), with its
original schema at [`spec/etq-101.schema.json`](spec/etq-101.schema.json) and
payload hash
`6577443641be02609c045ee0afc423c2be37bbe5ae83f671cbae304c0e9cb930`.

That legacy profile specified golden modulation and a declared 432 Hz scale.
It is retained as a historical identity and citation fixture; this repository
does not claim that the originally unimplemented renderer is now replayable.
It is not the forward default.
The v2 verifier also checks that the legacy bytes and structural hashes remain
unchanged.

The Tanner frame-bin modules remain useful auxiliary graph-spectral research.
Their nominal clock calibration is not the v2 root mapping and does not define
an ETQ acoustic reference.

## Verify

The reference implementation has no runtime dependencies. Use Node.js 20 or
newer:

```bash
npm test
npm run verify
```

`npm run verify` checks both the v2 forward contract and the immutable v1
legacy contract. CI runs this command unconditionally.

## Root artifact policy

Root ETQ runtime/export work may produce only:

- Standard MIDI (`.mid`);
- event or audit tables (`.csv`); and
- contracts, manifests, and provenance (`.json`).

PCM and rendered-audio generation are permanently disabled in the root ETQ
system. The separate `APP/` and `sonification/` music-first laboratories retain
their existing adjustable synthesis settings, including adjustable A4 tuning;
those defaults are not ETQ constants or E8-derived quantities.

## Scientific boundary

A precise description is:

> ETQ-101 v2 is a deterministic 101-dimensional E8-root-indexed graph model
> closed under an embedded D4 triality, with 33 direct-sum qutrit blocks, two
> fixed singlets, a graph-degree potential, and an explicit symbolic ternary
> MIDI codebook.

ETQ-101 does **not** claim:

- a 101-dimensional representation of E8;
- that triality is an intrinsic outer symmetry of E8 rather than D4/Spin(8);
- that MIDI register order is a qutrit energy spectrum;
- that any acoustic frequency is selected by E8;
- that a mathematical qutrit simulation implies qutrit hardware;
- that a statistical null rejection validates a physical theory; or
- that sonification alone validates the model.

## Authorship, citation, and license

Created by **Trent Slade / QSOL-IMC**. Preferred citation metadata is in
[`CITATION.cff`](CITATION.cff). The displayed DOI identifies the archived
v1.0.0 release until a v2 archive is deposited.

Licensed under the [Mozilla Public License 2.0](LICENSE). See
[`NOTICE`](NOTICE), [`AUTHORS.md`](AUTHORS.md),
[`CONTRIBUTING.md`](CONTRIBUTING.md), and
[`Rights and Archiving`](docs/RIGHTS_AND_ARCHIVING.md).
