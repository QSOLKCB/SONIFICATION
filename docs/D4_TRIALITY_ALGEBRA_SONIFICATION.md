# D4-TIA-15 v1.0.0 — Triality-Invariant Algebra Sonification Profile

**Status:** implemented root research profile  
**Profile ID:** `D4-TIA-15`  
**Version:** `1.0.0`  
**Relationship to ETQ:** separate; ETQ-101 v2 and ETQ-303 v3 identities are unchanged

## Purpose

D4-TIA-15 turns the published 15-generator minimal basis used in Kazuhiro
Sakai's 2026 treatment of the ring of D4 triality invariants into a deterministic
symbolic event profile. The source object is not an invented 15-state physical
system: it is the finite generator ledger of the invariant/covariant algebra.

The profile preserves the published grading

$$
(d_a,d_b,m,k,\omega)
$$

and the relations

$$
k=4d_a+6d_b+m,
\qquad
\omega=2d_a+3d_b-m
=\frac{k-3m}{2}.
$$

The total covariant degree is

$$
d=d_a+d_b.
$$

No grade is normalized, ranked, fitted, interpolated, or replaced by an
additional latent quantity.

## Direct receiver projection

Version 1 deliberately uses identity transfers wherever a published integer
grade already fits a MIDI/event field:

| Published quantity | Profile field | Transfer |
|---|---|---|
| generator basis order | event sequence | identity |
| polynomial degree \(m\) | onset tick | identity |
| covariant degree \(d=d_a+d_b\) | duration ticks | identity |
| modular weight \(k\) | MIDI note number | identity |
| covariant order \(\omega\) | MIDI channel | identity |
| refined degree \(d_a\) | event metadata | unchanged |
| refined degree \(d_b\) | event metadata | unchanged |

The velocity is the fixed receiver constant 64. It carries no mathematical
meaning. MIDI division is 1 tick per quarter-note unit, but **no tempo meta
event is emitted**. Acoustic tuning, instrument, timbre, loudness, and wall-clock
tempo remain receiver choices.

This is still an authored sonification mapping: mathematics does not say that
modular weight "is pitch" or that covariant order "is channel." The point of v1
is narrower: once those assignments are declared, the values are copied
losslessly rather than rescaled or aesthetically massaged.

## Why the MIDI file uses separate tracks

The 15 generators occupy 15 generator tracks plus one metadata track. This
retains generator identity even when two generators share the same
\((k,\omega,m)\)-projection. Track text records all exact grades, so the MIDI
view does not replace the JSON/CSV ledger.

The canonical information-bearing objects remain:

- `contract.json` — versioned mapping contract;
- `events.json` — lossless generator/event document;
- `events.csv` — auditable grading table;
- `events.mid` — symbolic MIDI projection; and
- `manifest.json` — artifact hashes and implementation identity.

Root artifacts remain restricted to JSON, CSV, and MIDI. No PCM or rendered
audio is constructed anywhere in the profile.

## Published generator ledger

| # | Generator | \(d_a\) | \(d_b\) | \(d\) | \(m\) | \(k\) | \(\omega\) |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | \(f\) | 1 | 0 | 1 | 0 | 4 | 2 |
| 2 | \(g\) | 0 | 1 | 1 | 0 | 6 | 3 |
| 3 | \((f,g)_1\) | 1 | 1 | 2 | 2 | 12 | 3 |
| 4 | quadratic discriminant | 2 | 0 | 2 | 4 | 12 | 0 |
| 5 | \((f,g)_2\) | 1 | 1 | 2 | 4 | 14 | 1 |
| 6 | \(P=(g,g)_2\) | 0 | 2 | 2 | 4 | 16 | 2 |
| 7 | \((f^2,g)_3\) | 2 | 1 | 3 | 6 | 20 | 1 |
| 8 | \((f,P)_1\) | 1 | 2 | 3 | 6 | 22 | 2 |
| 9 | \(Q=(g,P)_1\) | 0 | 3 | 3 | 6 | 24 | 3 |
| 10 | \((f,P)_2\) | 1 | 2 | 3 | 8 | 24 | 0 |
| 11 | \((f,Q)_2\) | 1 | 3 | 4 | 10 | 32 | 1 |
| 12 | \((f^3,g^2)_6\) | 3 | 2 | 5 | 12 | 36 | 0 |
| 13 | cubic discriminant \((P,P)_2\) | 0 | 4 | 4 | 12 | 36 | 0 |
| 14 | \((f^2,Q)_3\) | 2 | 3 | 5 | 12 | 38 | 1 |
| 15 | \((f^3,gQ)_6\) | 3 | 4 | 7 | 18 | 54 | 0 |

## Determinism and provenance

`manifest.json` records SHA-256 for each emitted artifact and an implementation
identity over the reference ledger, profile implementation, artifact builder,
canonical serializer, and build entrypoint. The build command refuses a
nonempty target and writes exclusively into a dedicated `dist/` subdirectory.

Run:

```bash
npm test
npm run verify:d4-tia
npm run build:d4-tia
```

## Claim boundary

Supported:

- the 15 generator rows are copied from the repository's Sakai-aligned
  reference ledger;
- every grading relation is checked before event generation;
- the v1 mapping uses the declared identity transfers with no grade
  normalization;
- JSON/CSV are lossless for the grading ledger; and
- MIDI is a deterministic symbolic projection.

Not supported:

- the MIDI mapping is uniquely selected by invariant theory;
- MIDI note number is a physical frequency predicted by the algebra;
- a listener can necessarily distinguish all 15 generators;
- the 15 generators are physical states; or
- the profile validates ETQ, E-string theory, or any physical interpretation.

## References

- K. Sakai, *The ring of D4 triality invariants*, arXiv:2504.00546v2 (2026).
- K. Sakai, *E-strings, F4, and D4 triality*, JHEP 07 (2023) 192,
  arXiv:2304.04878.

## Successor profile

This document remains the immutable specification for **D4-TIA-15 v1.0.0**.
The separately versioned **D4-TIA-15 v2.0.0** profile is downstream of the
exact covariant engine and \(S_3\) equivariance harness. It evaluates the
covariants across six quotient representatives and sonifies their exact
within-generator orbit value classes while enforcing receiver invariance for
order-zero covariants.

See [D4-TIA-15 v2.0.0](D4_TRIALITY_ALGEBRA_SONIFICATION_V2.md).
