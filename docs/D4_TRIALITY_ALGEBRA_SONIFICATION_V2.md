# D4-TIA-15 v2.0.0 — Evaluated-Covariant Orbit Sonification

**Status:** implemented root symbolic receiver profile  
**Profile ID:** `D4-TIA-15`  
**Version:** `2.0.0`  
**Predecessor:** `D4-TIA-15@1.0.0`  
**Rendered audio:** permanently disabled in the root profile

## Purpose

Version 1 sonified the published 15-generator grading ledger. Version 2 moves
one layer closer to the actual algebra: it evaluates the exact symbolic
covariants from `D4-TIA-COV` under the six canonical quotient representatives
validated by `D4-TIA-S3-EQUIV`, and then creates a symbolic MIDI contour from
their exact orbit values.

The order of construction is therefore:

```text
published 15-generator basis
        -> exact covariant polynomials
        -> exact six-representative coefficient actions
        -> exact evaluated covariant orbit
        -> within-generator exact value classes
        -> symbolic MIDI contour
```

No step uses floating-point evaluation.

## Exact probe

The coefficient probe is deliberately simple and explicit:

```text
a0=1, a1=2, a2=3
b0=4, b1=5, b2=6, b3=7
```

This probe is an authored deterministic research fixture. It is **not** claimed
to be selected by the invariant theory, a physical parameter set, or a
canonical point of the moduli space.

The receiver variables are fixed at

\[
(u,v)=(1,0).
\]

This anchor is mathematically useful because a covariant

\[
\Psi(\alpha;u,v)
\]

evaluated at \((1,0)\) returns its leading coefficient, the semi-invariant
appearing in the Roberts isomorphism.

## Six quotient positions

The orbit order is frozen as

```text
e, S, T, ST, TS, STS
```

using the six canonical `SL2(Z)` representatives from
`D4-TIA-S3-EQUIV`. For every representative the transformed coefficients are
derived from

\[
f'(u,v)=f(u',v'),
\qquad
g'(u,v)=g(u',v'),
\]

not copied from an independent transformation table.

Before sonification, each evaluated covariant must satisfy the already tested
equivariance law

\[
\Psi(\alpha';u,v)=\Psi(\alpha;u',v')
\]

exactly.

## Exact value classes

For one generator, let its six exact rational evaluated values be

\[
x_e,x_S,x_T,x_{ST},x_{TS},x_{STS}.
\]

Version 2 sorts the **distinct exact rational values** in ascending numerical
order. Equal rationals remain in the same value class. No decimal conversion,
z-score, logarithm, fitted normalization, or cross-generator magnitude scale is
used.

If a generator has \(N\) distinct exact values and one value has zero-based
class index \(r\), its pitch offset is

\[
\Delta n=r-\left\lfloor\frac{N}{2}\right\rfloor.
\]

The MIDI note is then

\[
n=k+\Delta n,
\]

where \(k\) is the published modular weight already used as the v1 base note.

This is still an authored receiver convention. The invariant theory does not
identify rational-value rank with musical pitch.

## Time and channel mapping

Each quotient position occupies one symbolic tick block. The block stride is
derived rather than chosen as a free musical constant:

\[
B=1+\max_i(m_i+d_i).
\]

For the published 15-generator basis this gives

\[
B=26.
\]

Within every block, v1 grading placement is preserved:

```text
orbit-relative onset = m
duration             = d = d_a + d_b
base MIDI note       = k
MIDI channel         = omega
velocity             = 64
```

Thus absolute onset for orbit index \(q\in\{0,\ldots,5\}\) is

\[
t=qB+m.
\]

No tempo meta event is emitted. Wall-clock tempo, tuning, timbre, and
synthesizer response remain external and non-normative.

## Invariant projections stay invariant

A covariant of order

\[
\omega=0
\]

is an `SL2` invariant rather than a nontrivial covariant in the receiver
variables. The published 15-generator basis contains five such generators:

```text
4   quadratic-discriminant
10  (f,P)_2
12  (f^3,g^2)_6
13  cubic-discriminant=(P,P)_2
15  (f^3,gQ)_6
```

For these five rows, v2 requires all six evaluated rational values to be
exactly equal. Consequently the exact value-class count is one and

\[
\Delta n=0.
\]

The receiver also requires the same MIDI note, channel, velocity, and duration
at all six quotient positions.

The event appears at six different times because the orbit positions are
presented sequentially. The **audible-control tuple** is invariant; the time at
which the repeated tuple is presented is not.

This is the precise sense in which the invariant projections remain
"audibly invariant" in the root profile. The repository guarantees identical
symbolic MIDI controls, not identical acoustic output from every external
synthesizer or listening environment.

## Non-invariant covariants

For \(\omega>0\), the six exact evaluated values are allowed to move under the
group action. Their exact within-generator value classes generate the pitch
contour. Equal orbit values still receive the same pitch offset.

No requirement says every non-invariant covariant must have six distinct
values at this authored probe. The receiver preserves exact equality when it
occurs.

## Artifacts

`npm run build:d4-tia-v2` writes one new or empty dedicated directory under
`dist/` containing only root-policy-allowed artifact types:

```text
contract.json
evaluations.json
events.json
events.csv
events.mid
manifest.json
```

`evaluations.json` contains the complete exact 15-by-6 evaluation matrix before
receiver projection. `events.json` contains the 90-event symbolic receiver
document.

The MIDI file remains format 1 with one conductor/metadata track and one track
per generator. Each generator track contains its six orbit events.

## Determinism and provenance

The manifest binds:

- the versioned mapping contract;
- the exact evaluation document;
- the 90-event document;
- CSV and MIDI receiver bytes;
- the invariant-projection summary; and
- a normalized source-bundle implementation identity.

Source files are normalized from CRLF/CR to LF before hashing, matching the
existing repository provenance convention.

## Verify

Run:

```bash
npm test
npm run verify:d4-tia-v2
npm run build:d4-tia-v2
```

The root `npm run verify` chain also executes the algebra engine, the
equivariance harness, this v2 profile, the preserved D4-TIA-15 v1 profile, and
the existing ETQ verification chain.

## Claim boundary

Mathematically grounded:

- the 15 exact covariants;
- the six quotient representatives and their tested correspondence;
- exact covariant equivariance;
- the leading-coefficient evaluation at \((1,0)\); and
- invariance of order-zero covariants.

Authored sonification choices:

- coefficient probe \((1,2,3,4,5,6,7)\);
- presentation order of the six quotient classes;
- sequential block layout;
- exact value-class rank as a pitch offset; and
- fixed MIDI velocity 64.

Therefore D4-TIA-15 v2 is an auditable symbolic sonification experiment, not a
claim that invariant theory predicts a unique melody, pitch system, tempo,
physical spectrum, or listener response.

## References

- K. Sakai, *The ring of D4 triality invariants*, arXiv:2504.00546v2 (2026),
  especially Definition 4.2, the Roberts isomorphism in Theorem 4.4,
  Remark 4.17, and Theorem 5.2.
- `docs/D4_TRIALITY_COVARIANT_ENGINE.md`
- `docs/D4_TRIALITY_S3_EQUIVARIANCE.md`
- `docs/D4_TRIALITY_ALGEBRA_SONIFICATION.md`
