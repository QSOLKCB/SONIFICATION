# ETQ-101: E8-Root-Derived, D4-Triality Qutrit Sonification Model

**A deterministic mathematical model for E8-root-indexed, triality-structured
qutrit sonification.**

[![Tests](https://github.com/QSOLKCB/SONIFICATION/actions/workflows/tests.yml/badge.svg)](https://github.com/QSOLKCB/SONIFICATION/actions/workflows/tests.yml)
[![Node.js 20+](https://img.shields.io/badge/Node.js-20%2B-339933.svg)](https://nodejs.org/)
[![License: MPL-2.0](https://img.shields.io/badge/License-MPL--2.0-blue.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21404224.svg)](https://doi.org/10.5281/zenodo.21404224)

ETQ-101 v1.0.0 formalizes an E8-root-derived graph model with an embedded
order-three D4 triality, 33 orbit-labelled direct-sum qutrit blocks plus two
fixed singlets, the ternary-curvature observable `[1, -2, 1]`, qutrit labels
`[0, 1, 2]`, phase `theta = pi/2`, optional golden-ratio modulation, and a
declared 432 Hz reference scale.

The construction is exact, deterministic, machine-verifiable, and explicit
about which parts are mathematical consequences and which are authored
sonification choices.

## Model at a glance

| Element | ETQ-101 definition |
|---|---|
| E8 | Exact standard set of 240 roots in doubled integer coordinates |
| Triality | Explicit order-three D4 action preserving the E8 root set |
| 101-state sector | Canonical triality-closed root-indexed graph space |
| Ternary curvature | `D3 = diag(1, -2, 1)` |
| Qutrit logic | Computational labels `[0, 1, 2]` with generalized Pauli operators `X3` and `Z3` |
| Phase | `theta = pi/2` |
| Golden ratio | `varphi = (1 + sqrt(5)) / 2`, kept distinct from the phase |
| Reference scale | `f0 = 432 Hz`, declared rather than derived from E8 |

The compact state space is

$$
\boxed{
\mathcal H_{101}
=\mathbb C^2
\oplus
\left(\mathbb C^{33}\otimes\mathbb C^3\right).
}
$$

This resolves the central arithmetic constraint: 101 is not divisible by
three, so the space cannot globally factor as `something x qutrit`. Instead it
contains **33 complete qutrit/triality orbits and two fixed singlets**.

The selected E8 roots label formal orthonormal graph states in
`ell^2(S_101)`. They are not claimed to be 101 linearly independent vectors in
R8 or a 101-dimensional representation of E8. The 33 qutrit blocks form a
direct sum, not 33 independent tensor-factor qutrits.

If every mode must carry a full qutrit, the model provides the tensor extension

$$
\mathcal H_{303}=\mathcal H_{101}\otimes\mathbb C^3.
$$

## Core qutrit and SCL algebra

For `zeta = exp(2 pi i / 3)`, the generalized Pauli operators satisfy

$$
X_3|q\rangle=|q+1\!\!\pmod 3\rangle,
\qquad
Z_3|q\rangle=\zeta^q|q\rangle,
$$

and

$$
X_3^3=Z_3^3=I,
\qquad
Z_3X_3=\zeta X_3Z_3.
$$

The SCL operator is

$$
D_3=\operatorname{diag}(1,-2,1),
$$

and the phase-twisted cycle

$$
F_3=X_3e^{-i\theta D_3}
$$

obeys `F3^3 = I` for every `theta`, including `theta = pi/2`, because the
accumulated three-step curvature is `1 - 2 + 1 = 0`.

## Dimensionally correct dynamics

Structural terms are assembled into a dimensionless Hermitian generator `K`.
The physical time scale is introduced only through

$$
\boxed{
H=\hbar\Omega_0K,
\qquad
\Omega_0=2\pi(432)\ \mathrm{s}^{-1}.
}
$$

Closed evolution is therefore

$$
\dot\rho=-i\Omega_0[K,\rho].
$$

This replaces the original scalar expression, which mixed a dimensionless
quantity with a term measured in inverse seconds. Only `1 - 2 + 1` vanishes in
that expression; the normalized trace term does not.

## ETQ-101 resources

| Resource | Purpose |
|---|---|
| [Mathematical model](docs/MATHEMATICAL_MODEL.md) | Normative construction, operators, dynamics, observables, and 303-state extension |
| [Sonification mapping](docs/SONIFICATION_MAPPING.md) | Static generator-spectrum mapping and deterministic render contract |
| [Claim boundaries](docs/CLAIM_BOUNDARIES.md) | Exact results, authored choices, and excluded physical claims |
| [Canonical contract](examples/etq-101.canonical.json) | Fixed v1.0.0 parameters and regression hashes |
| [JSON Schema](spec/etq-101.schema.json) | Machine-readable canonical schema |
| [Reference construction](src/etq-model.mjs) | Dependency-free E8, triality, graph, and qutrit implementation |
| [Model tests](tests/etq-model.test.mjs) | Algebraic, graph, phase, hash, and normalization tests |
| [Verifier](scripts/verify.mjs) | Canonical-contract and fixture verification |

## Canonical deterministic fixtures

| Fixture | Value |
|---|---:|
| Standard E8 roots | 240 |
| Triality-fixed roots | 12 |
| Triality three-cycles | 76 |
| Selected states | 101 |
| Selected qutrit orbits | 33 |
| Selected graph edges | 1,687 |
| Selected graph degree range | 22-55 |
| Basis SHA-256 | `97cfd1f087745422fd66d3640c7b86c3209593c4b53741018c08a5e9cdb15f6f` |
| Adjacency SHA-256 | `29ae0af5b1090c9de30f1efc25789060fb1791eb175d2afcd6888847f7fe6324` |
| Contract SHA-256 | `6577443641be02609c045ee0afc423c2be37bbe5ae83f671cbae304c0e9cb930` |

## Verify the model

The reference implementation has no runtime dependencies. Node.js 20 or newer
is used for its test runner and SHA-256 verification.

```bash
npm test
npm run verify
```

The verifier reconstructs the E8 roots, triality orbits, 101 selected labels,
and adjacency matrix from first principles, then checks the fixed fields and
cross-field relations in the canonical contract.

## Sonification status

The ETQ-101 static generator-spectrum PCM renderer is formally specified in
[the mapping document](docs/SONIFICATION_MAPPING.md), but is intentionally
marked **not yet implemented**. This repository does not claim an ETQ-101 WAV
artifact that it does not ship.

The repository also contains two separate, runnable music-first synthesis
interfaces. Neither is presented as the not-yet-implemented ETQ-101 renderer:

- **[Offline browser app ->](APP/README.md)** — zero-dependency local rendering,
  playback, WAV export, and provenance receipts;
- **[Python synthesis laboratory ->](sonification/README.md)** — additive, FM,
  and Karplus-Strong synthesis with exact replay verification.

## Scientific boundary

A precise description of ETQ-101 is:

> A deterministic 101-dimensional E8-root-indexed graph truncation closed
> under an embedded D4 triality, with direct-sum qutrit blocks and an explicit
> sonification map.

ETQ-101 does **not** claim:

- a 101-dimensional representation of E8;
- that triality is an intrinsic outer symmetry of E8 rather than D4/Spin(8);
- that 432 Hz is physically selected by E8;
- that a mathematical qutrit simulation implies qutrit hardware; or
- that sonification validates a physical theory.

See [Claim Boundaries](docs/CLAIM_BOUNDARIES.md) for the complete distinction
between exact results, model definitions, sonification choices, and excluded
claims.

## Authorship, citation, and license

Created by **Trent Slade / QSOL-IMC**. Preferred citation metadata is provided
in [CITATION.cff](CITATION.cff), with archival metadata in
[.zenodo.json](.zenodo.json).

Licensed under the [Mozilla Public License 2.0](LICENSE). Covered source files
and modifications must remain available under MPL-2.0 when distributed, and
copyright and licence notices may not be removed or altered. See
[NOTICE](NOTICE), [AUTHORS.md](AUTHORS.md),
[CONTRIBUTING.md](CONTRIBUTING.md), and
[Rights and Archiving](docs/RIGHTS_AND_ARCHIVING.md).
