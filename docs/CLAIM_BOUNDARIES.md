# ETQ-101 v2 Claim Boundaries

This document separates exact mathematics, selected-graph consequences,
declared model choices, symbolic MIDI conventions, numerical tests, perceptual
evidence, and unsupported physical interpretations.

## Claim matrix

| Topic | Supported wording | Do not claim |
|---|---|---|
| E8 | “Constructed from the standard 240 E8 roots” | “A new 101-dimensional representation of E8” |
| 101 states | “A declared deterministic, triality-closed E8 root-indexed graph truncation” | “101 independent roots in R8” or “the canonical 101-state E8 space” |
| Triality | “D4 triality embedded in the E8 root system” | “An outer symmetry intrinsic to E8” |
| Qutrits | “33 mutually exclusive direct-sum qutrit/triality blocks plus two fixed singlets” | “101 factors into qutrits” or “33 tensor-factor qutrits” |
| `[0,1,2]` | “Cyclic computational labels with arithmetic modulo three” | “Intrinsic low, middle, and high energy levels” |
| `[1,-2,1]` | “A second-difference stencil or traceless diagonal observable” | “An ordered low/mid/high register operator” |
| `theta=pi/2` | “A declared quadrature phase used by the SCL phase kick” | “A value derived from E8” |
| Degree potential | “Derived from degrees of the selected 101-node root graph” | “An independent invariant of the complete E8 root system” |
| MIDI lanes | “An authored reversible code for qutrit labels and canonical orbit order” | “A physical or spectral qutrit hierarchy” |
| MIDI notes | “Symbolic note numbers” | “Canonical hertz values” |
| Fixed bookends | “Codebook boundaries for two non-qutrit singlets” | “Spectral extrema” |
| Graph surrogate | “A topology-aware conditional null comparison” | “Physical confirmation of ETQ” |
| Listener study | “Task performance for a fixed realization” | “Validation of E8 or qutrit ontology” |

## Exact layer

The following are exact within ordinary finite-dimensional mathematics:

- generation of 240 unique E8 roots in doubled integer coordinates;
- integer norm and inner-product tests;
- the displayed D4 triality matrix satisfying \(A^TA=A^3=I\);
- preservation of the root set by the embedded action;
- orbit count \(12+76(3)=240\);
- selected dimension \(2+33(3)=101\);
- qutrit Weyl relations \(X^3=Z^3=I\) and \(ZX=\zeta XZ\);
- \(D=3(N-\Pi_Q)^2-2\Pi_Q\);
- \((Xe^{-i\theta D_3})^3=I\);
- symmetry and positive semidefiniteness of graph Laplacians;
- selected-graph edge count 1,687 and degree sum 3,374;
- zero trace and unit operator norm of the exact rational degree potential;
- the 101-entry MIDI codebook and its inverse; and
- triality as addition of 33 modulo 99 on the qutrit codebook interior.

## Selected-graph layer

The basis and graph become deterministic only after the declared selector is
fixed. Consequently, graph degrees, edge count, adjacency, Laplacian spectrum,
degree potential, and their hashes are consequences of

1. the exact E8 root set;
2. the embedded D4 triality;
3. the coordinate convention; and
4. the lexicographic `2 + 33*3` selector.

They are not invariants of E8 without those additional choices.

The degree potential

$$
(V_{\deg})_{jj}=\frac{101d_j-3374}{2181}
$$

is an exact function of the selected graph. Choosing it as a generator term
and assigning coefficient \(1/5\) are model-design choices. Because
\(L_E=D_G-W\), with \(D_G\) the graph degree matrix, already contains degree
information. The potential is a declared
on-site connectivity contrast, not independent evidence.

## Declared model layer

These choices are reproducible but not forced by E8 mathematics:

- retaining the first two fixed roots and first 33 complete triality orbits;
- numeric lexicographic coordinate and orbit order;
- naming the state recipe `Ouroboros`;
- choosing \(\theta=\pi/2\);
- choosing the three generator coefficients;
- using the selected-graph degree potential;
- choosing \(\delta=2\pi/303\);
- mapping cyclic qutrit labels to ascending low/mid/high registers;
- centering the 101-note codebook at notes 13–113 with a lower-start tie break;
- assigning the fixed singlets to codebook bookends; and
- any future MIDI timing, velocity, channel, program, or tempo rule.

Changing one of these choices creates another named model or observation
profile and a new contract hash.

## Removed forward anchors

ETQ-101 v2 does not use golden-ratio modulation or an absolute hertz
reference. Those quantities are absent from the forward state, generator,
dynamics, and MIDI mapping.

The DOI-linked v1.0.0 profile used both. Its canonical JSON, schema, and hash
remain immutable for historical identity and citation. It does not supply an
executable renderer that v1 never implemented, and it is not an ongoing v2
claim.

Adjustable A4 defaults in `APP/` and `sonification/` belong to separate
music-first laboratories. They are neither ETQ constants nor E8 consequences.

## Symbolic MIDI layer

The v2 note codebook is lossless as symbolic data. It does not determine:

- acoustic frequency;
- tuning temperament;
- soundfont or synthesizer;
- instrument program;
- loudness;
- timbre;
- perceptual stream formation; or
- listening-room calibration.

Low/mid/high provides an authored ordered display for a cyclic label set. That
polarity is plausible and testable, not self-validating. The codebook's
deterministic bijection proves identity preservation only.

## Numerical and statistical layer

Hashes establish byte identity under the declared serialization domain. They
do not prove scientific validity or authorship.

Floating-point eigendecomposition requires recorded tolerances, numeric ABI,
and runtime provenance. Degenerate eigenspaces must be represented by complete
projectors or another basis-invariant object.

A graph-Fourier surrogate test supplies a conditional null. Rejection means
only that the preregistered statistic is unusual under that null. It does not
show that:

- the selected graph is physically realized;
- the graph is the unique explanatory topology;
- qutrit labels are measured quantum states;
- MIDI register order is natural; or
- a physical theory is confirmed.

For constructed data, use “conditional null comparison” or “stress test,” not
“empirical validation.”

## Perceptual layer

The effectiveness of the ternary display is an empirical human-factors
question. It requires a frozen receiver setup, naive-listener tasks,
counterbalanced polarity and spacing, confusion matrices, reaction times, and
reported training.

Pleasantness, designer familiarity, or successful decoding by one listener is
not sufficient evidence. Even a successful controlled study validates only
the tested display task and realization.

## Physical layer

ETQ-101 remains a mathematical and sonification model. It does not establish:

- a quantum-gravity or unified-field theory;
- a physical 101-level E8 system;
- laboratory qutrit hardware;
- a preferred biological or cosmological frequency;
- a causal role for any musical tuning;
- empirical confirmation through MIDI or audio; or
- physical validation through a graph-surrogate p-value.

Any later physical claim needs a measurement model, falsifiable predictions,
uncertainty analysis, empirical data, and comparison against appropriate nulls.

## Recommended description

> ETQ-101 v2 is a deterministic E8-root-derived graph model built from a
> D4-triality-closed 101-state truncation, 33 direct-sum qutrit blocks, two
> fixed singlets, a ternary-curvature phase drive, a selected-graph degree
> potential, and an explicit symbolic ternary MIDI codebook.
