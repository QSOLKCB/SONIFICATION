# ETQ-101 Claim Boundaries

This document separates exact mathematics, declared design choices, numerical results, sonification conventions, and unsupported physical interpretations.

## Claim matrix

| Topic | Supported wording | Do not claim |
|---|---|---|
| E8 | “Constructed from the standard 240 E8 roots” | “A new 101-dimensional representation of E8” |
| 101 states | “A declared, deterministic, triality-closed E8 root-indexed graph truncation” | “101 independent roots in \(\mathbb R^8\)” or “a canonical E8 state space” |
| Triality | “D4 triality embedded in the E8 root system” | “Triality is an outer symmetry intrinsic to E8” |
| Qutrits | “33 mutually exclusive direct-sum qutrit/triality blocks plus two fixed singlets” | “101 factors into qutrits” or “33 independent tensor-factor qutrits” |
| `[0,1,2]` | “Computational labels with arithmetic modulo three” | “The list `[0,1,2]` is itself a Hamiltonian” |
| `[1,-2,1]` | “A second-difference stencil or traceless diagonal observable, depending on context” | “Its zero sum makes every state’s curvature vanish” |
| \(\theta=\pi/2\) | “A declared quadrature phase” | “The golden ratio equals \(\pi/2\)” |
| \(\varphi\) | “The optional golden-ratio modulation parameter” | “All E8 spectra are golden-ratio spectra” |
| 432 Hz | “A declared time and sonification reference” | “A frequency predicted or privileged by E8” |
| Density operator | “A mathematical simulation state satisfying \(\rho\succeq0\) and \(\mathrm{Tr}\rho=1\)” | “Evidence that quantum hardware was used” |
| Audio | “A deterministic observation map from model quantities” | “Physical validation of the model” |

## Exact layer

The following are exact within ordinary finite-dimensional mathematics:

- generation of 240 unique E8 roots in doubled integer coordinates;
- norm-squared and inner-product tests performed with integers;
- the displayed D4 triality matrix satisfying \(A^TA=A^3=I\);
- preservation of the 240-root set by \(A\oplus A\);
- the orbit count of 12 fixed roots and 76 three-cycles;
- the root-indexed graph-space dimension \(2+33(3)=101\);
- qutrit Weyl relations \(X^3=Z^3=I\) and \(ZX=\zeta XZ\);
- the identity \(D=3(N-\Pi_Q)^2-2\Pi_Q\);
- the phase-twisted identity \((Xe^{-i\theta D_3})^3=I\); and
- Hermiticity and positive semidefiniteness of graph Laplacians.

## Declared model layer

These choices are reproducible but are not forced by E8 mathematics:

- retaining the first two fixed roots and first 33 complete triality orbits;
- the lexicographic coordinate convention;
- naming the 101-state construction `Ouroboros`;
- choosing \(\theta=\pi/2\);
- adding golden-ratio phases or orbit potentials;
- choosing generator coefficients;
- choosing 432 Hz as \(f_0\); and
- choosing a particular sonification map.

Changing one of these choices creates another declared model profile. It must not silently reuse the canonical ETQ-101 hashes.

## Numerical layer

The graph edge count, degree range, hashes, and approximate eigenvalues are reproducible consequences of the declared selector. Hashes establish byte-level identity only under the specified compact `JSON.stringify` UTF-8 serialization; they do not prove a physical claim.

Floating-point eigendecompositions require recorded tolerances and software provenance. Degenerate eigenspaces must be handled through projectors or another basis-independent rule.

## Physical layer

ETQ-101 is presently an effective mathematical and sonification model. It does not by itself establish:

- a quantum-gravity or unified-field theory;
- a physical 101-level E8 system;
- a laboratory implementation of qutrits;
- a special biological or cosmological status for 432 Hz;
- a causal role for the golden ratio; or
- empirical confirmation through audio.

Any later physical claim needs a separately stated measurement model, falsifiable predictions, uncertainty analysis, data, and comparison against appropriate null models.

## Recommended project description

Use this sentence in summaries and releases:

> ETQ-101 is a deterministic E8-root-derived sonification model built from a D4-triality-closed 101-state root-indexed graph truncation, 33 direct-sum qutrit blocks, a ternary-curvature phase drive, and an explicitly declared 432 Hz observation scale.
