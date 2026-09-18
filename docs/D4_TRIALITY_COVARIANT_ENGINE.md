# D4-TIA-COV v0.1.0 — Exact Covariant Algebra Engine

**Status:** implemented research engine  
**Engine ID:** `D4-TIA-COV`  
**Version:** `0.1.0`  
**Sonification impact:** none — this phase adds mathematics only

## Purpose

D4-TIA-15 v1.0.0 sonifies the published grading ledger for 15 generators. This
engine takes the next step: it constructs those covariants themselves as exact
symbolic polynomials.

The implementation follows Kazuhiro Sakai, *The ring of D4 triality invariants*
(arXiv:2504.00546v2). In the paper, binary forms are written without binomial
coefficient weights,

```math
f(u,v)=\sum_{i=0}^{2}\alpha_i u^{2-i}v^i,
\qquad
g(u,v)=\sum_{i=0}^{3}\beta_i u^{3-i}v^i,
```

and the normalized transvectant of binary forms \(F,G\) of orders \(m,n\) is

$$
(F,G)_r =
\frac{(m-r)!(n-r)!}{m!n!}
\sum_{j=0}^{r}
(-1)^j {r \choose j}
\frac{\partial^r F}{\partial u^{r-j}\partial v^j}
\frac{\partial^r G}{\partial u^j\partial v^{r-j}}.
$$

These are the conventions used by the engine.

## Exact arithmetic

All polynomial coefficients are reduced rational numbers represented internally
with `BigInt` numerators and denominators. There is no floating-point path in
the algebra engine.

A sparse monomial uses the fixed variable order

```text
a0,a1,a2,b0,b1,b2,b3,u,v
```

and canonical polynomial serialization sorts exponent vectors
lexicographically. Each of the 15 generated covariants has a committed SHA-256
fixture over this exact serialization.

## Constructed basis

The engine constructs Sakai's Theorem 5.2 basis:

- quadratic covariants: \(f\), \(D_f=(f,f)_2\);
- cubic covariants: \(g\), \(P=(g,g)_2\), \(Q=(g,P)_1\),
  \(D_g=(P,P)_2\);
- joint covariants:
  \((f,g)_1\), \((f,g)_2\), \((f^2,g)_3\),
  \((f,P)_1\), \((f,P)_2\), \((f,Q)_2\),
  \((f^2,Q)_3\), \((f^3,g^2)_6\), and
  \((f^3,gQ)_6\).

It also verifies exactly the cubic syzygy

$$
2Q^2+P^3+g^2D_g=0.
$$

## Grades are derived, not trusted

For every symbolic polynomial, the engine counts the degrees in
\(\alpha_i\), \(\beta_j\), and \(u,v\) to derive

$$
d_a,\qquad d_b,\qquad \omega.
$$

It then derives

$$
d=d_a+d_b,
\qquad
m=2d_a+3d_b-\omega,
\qquad
k=4d_a+6d_b+m.
$$

Only after those quantities have been obtained from the actual covariant does
the engine compare them with the existing 15-row literature ledger. A mismatch
is a verification failure.

## Deterministic fixture

`examples/d4-tia-cov.v0.1.canonical.json` freezes, for every generator:

- basis index and label;
- derived grading;
- exact sparse term count; and
- SHA-256 of the canonical exact polynomial.

The fixture is deliberately kept separate from D4-TIA-15's MIDI/event contract.
This engine does not alter MIDI mapping, tempo, tuning, timbre, or any ETQ identity.

Run:

```bash
npm test
npm run verify:d4-tia-cov
```

## Completed research sequence and archive

This engine became the first executable layer of the now-completed D4-TIA v2
research sequence:

1. **D4-TIA-COV v0.1.0** — exact covariant algebra engine — complete.
2. **D4-TIA-S3-EQUIV v0.1.0** — exact D4/F4 \(S_3\) orbit and equivariance
   harness — complete.
3. **D4-TIA-15 v2.0.0** — evaluated-covariant orbit sonification downstream of
   those exact checks — complete.
4. **Freeze/tag/archive** — complete at immutable Git tag
   `d4-tia-v2.0.0`, release commit
   `7aa6df165d0ad70297365dbf0d69072634ed4314`.
5. **Zenodo formalization** — complete at DOI
   `10.5281/zenodo.22831753`.

The completed sequence preserves the original design rule: test the mathematical
action and covariant equivariance before introducing the receiver mapping. Any
future receiver remapping or semantic change belongs to a new D4-TIA version,
not a modification of the frozen v2.0.0 release.

## Source boundary

The paper supports the binary-form convention, normalized transvectant,
quadratic/cubic covariants, cubic syzygy, the 15-generator basis, and the grade
relations used here. It does not prescribe a sonification or assert that these
covariants are physical states.

## References

- K. Sakai, *The ring of D4 triality invariants*, arXiv:2504.00546v2 (2026),
  especially Eq. (5.1), Eqs. (5.7)–(5.10), Theorem 5.2, and Remark 4.17.
