# ETQ-101 Mathematical Model

**Version:** 2.0.0
**Status:** Normative specification
**Model name:** E8-Root Triality-Qutrit 101-State Sonification Model (ETQ-101)

## Abstract

ETQ-101 is a deterministic finite-dimensional model that combines:

- an exact coordinate construction of the 240-root E8 root system;
- an order-three D4 triality embedded in that root system;
- a declared 101-state, triality-closed truncation;
- 33 mutually exclusive qutrit/triality blocks with computational values `[0, 1, 2]` plus two triality-fixed singlets;
- the SCL ternary-curvature observable `diag(1, -2, 1)`;
- a phase kick at \(\theta=\pi/2\);
- a selected-root-graph degree potential; and
- a symbolic low/mid/high ternary MIDI codebook with no acoustic reference.

The precise claim is:

> **ETQ-101 is a deterministic 101-dimensional root-indexed graph truncation derived from E8, closed under a D4 triality embedded in E8, with 33 direct-sum qutrit/triality blocks and two fixed singlets.**

It is not a 101-dimensional representation of the E8 Lie group or Lie algebra. It is an authored effective model whose basis selector, operators, dimensionless dynamics, observables, and symbolic mapping are explicit and testable.

## 1. Correction of the proposed scalar equation

The forward profile uses separate symbols for the phase and qutrit character:

$$
\theta=\frac{\pi}{2},\qquad
\zeta=e^{2\pi i/3}.
$$

Here \(\theta\) is a declared phase and \(\zeta\) is the primitive qutrit root
of unity. ETQ-101 v2 defines no absolute frequency.

The original proposal contained a scalar expression of the form

$$
\theta^2\left[
\mathrm{Tr}(\rho)-\frac12(1-2+1)
\right]
+\text{a term with inverse-time units}=0.
$$

Because

$$
1-2+1=0
$$

and a density operator is normalized by \(\mathrm{Tr}(\rho)=1\), only the
ternary sum vanishes. The trace contribution does **not** vanish. Adding it to
an inverse-time term is dimensionally invalid, so v2 removes the dimensional
term instead of assigning it an arbitrary calibration.

If a scalar zero condition is aesthetically useful, a dimensionless calibration residual may be defined instead:

$$
\begin{aligned}
\mathcal R(\rho)
={}&\theta^2\bigl(\mathrm{Tr}\rho-1\bigr)^2
+\frac16\bigl(\mathrm{Tr}(\rho D)\bigr)^2\\
&+\frac12\bigl(\mathrm{Tr}(\rho Q)\bigr)^2
\ge 0.
\end{aligned}
$$

Then \(\mathcal R=0\) expresses normalization, aggregate ternary balance, and
aggregate centered-qutrit balance. It is a declared diagnostic constraint—not
an equation of motion or physical law. Positivity and Hermiticity of \(\rho\)
remain separate axioms.

## 2. Notation

| Symbol | Meaning | Units |
|---|---|---|
| \(\theta\) | SCL phase, canonically \(\pi/2\) | rad (dimensionless) |
| \(\zeta\) | Qutrit root of unity \(e^{2\pi i/3}\) | dimensionless |
| \(\mathcal H_{101}\) | Compact ETQ-101 state space | — |
| \(\rho\) | Density operator on the selected state space | — |
| \(U_\tau\) | Embedded order-three triality action | — |
| \(D\) | SCL ternary-curvature observable | — |
| \(N\) | Qutrit number-label observable | — |
| \(V_{\deg}\) | Centered selected-graph degree potential | — |
| \(K\) | Dimensionless Hermitian generator | — |
| \(s\) | Dimensionless continuous evolution parameter | — |
| \(\delta\) | Dimensionless Floquet step, \(2\pi/303\) | — |
| \(M(m,q)\) | Symbolic MIDI note-number code | integer |

`SCL` is project terminology. This specification does not claim it is a standard mathematical acronym.

## 3. Exact E8 root construction

Use the standard 240-root realization in \(\mathbb R^8\):

$$
R_{E_8}=
\{\,\pm e_i\pm e_j:i<j\,\}
\cup
\left\{
\frac12(s_1,\ldots,s_8):
s_i\in\{-1,1\},\
\#\{i:s_i=-1\}\ \text{even}
\right\}.
$$

There are 112 integer roots and 128 half-integer roots. Every root satisfies

$$
r\cdot r=2.
$$

The reference implementation stores doubled integer coordinates \(\widetilde r=2r\). Consequently,

$$
\widetilde r\cdot\widetilde r=8,
$$

and the root-graph adjacency test \(r_a\cdot r_b=1\) becomes the exact integer test

$$
\widetilde r_a\cdot\widetilde r_b=4.
$$

No floating-point comparison is needed to generate or connect the roots.

## 4. D4 triality embedded in E8

On one four-coordinate D4 block, define

$$
A=\frac12
\begin{pmatrix}
1&1&1&1\\
1&1&-1&-1\\
1&-1&1&-1\\
-1&1&1&-1
\end{pmatrix}.
$$

It satisfies

$$
A^TA=I_4,\qquad A^3=I_4.
$$

Define the simultaneous eight-dimensional action

$$
\tau=A\oplus A.
$$

Direct enumeration verifies

$$
\tau R_{E_8}=R_{E_8},\qquad \tau^3=I_8.
$$

The action of \(\tau\) on the 240 roots decomposes exactly into

$$
12\ \text{fixed roots}
\quad\oplus\quad
76\ \text{orbits of length three},
$$

because

$$
12+76(3)=240.
$$

Triality is fundamentally the exceptional outer symmetry of D4/Spin(8). The safe wording is **“D4 triality embedded in an E8-derived model.”** “Intrinsic E8 triality” is not claimed.

## 5. Canonical 101-state selector and Hilbert space

Represent each E8 root by its doubled integer coordinate vector and order the vectors lexicographically.

1. Sort the 12 \(\tau\)-fixed roots and retain the first two.
2. For each non-fixed orbit, choose its lexicographically least root as representative.
3. Sort the 76 representatives and retain the first 33 complete orbits.
4. Order each retained orbit as \((r,\tau r,\tau^2r)\).
5. Put the two fixed roots first, followed by the 33 ordered triples. Call the
   resulting selected root set $S_{101}$.

The roots in $S_{101}\subset\mathbb R^8$ are **labels**, not a linearly
independent vector basis of \(\mathbb R^8\). Define the model Hilbert space as

$$
\mathcal H_{101}=\ell^2(S_{101})
=\mathrm{span}_{\mathbb C}\{|r\rangle:r\in S_{101}\},
\qquad
\langle r|s\rangle=\delta_{r,s}.
$$

This formal graph-state basis is 101-dimensional even though its vertex labels
are eight-dimensional root coordinates.

The resulting space has dimension

$$
2+33(3)=101
$$

and the exact decomposition

$$
\boxed{
\mathcal H_{101}
=
\mathbb C^2
\oplus
\left(\mathbb C^{33}\otimes\mathbb C^3\right).
}
$$

Thus qutrit logic acts exactly on a 99-dimensional subspace, while the two remaining states are triality-fixed singlets. The 33 three-dimensional blocks are mutually exclusive direct-sum sectors; they are **not** 33 independent qutrit tensor factors, which would have dimension \(3^{33}\). Define

$$
U_\tau
=I_2\oplus(I_{33}\otimes X_3),
\qquad U_\tau^3=I_{101}.
$$

The eigenvalue multiplicities of \(U_\tau\) are

$$
1:35,\qquad \zeta:33,\qquad \zeta^2:33.
$$

The canonical selector deliberately chooses a coordinate frame and breaks full E8 Weyl symmetry. Its exact basis and adjacency hashes are therefore part of the model contract.

There is no nontrivial 101-dimensional E8 representation behind this construction. Finite-dimensional representations of the semisimple Lie algebra \(\mathfrak e_8\) are completely reducible, and its smallest nontrivial complex irreducible representation has dimension 248. Consequently, a 101-dimensional representation can contain only trivial summands. ETQ-101 is instead a symmetry-closed **root-indexed graph truncation**.

## 6. Qutrit logic and generalized Pauli operators

On one qutrit with computational basis \(|0\rangle,|1\rangle,|2\rangle\), define

$$
N_3=\mathrm{diag}(0,1,2),
$$

$$
X_3|q\rangle=|q+1\!\!\pmod3\rangle,
$$

and

$$
Z_3|q\rangle=\zeta^q|q\rangle.
$$

These satisfy

$$
X_3^3=Z_3^3=I_3,
\qquad
Z_3X_3=\zeta X_3Z_3.
$$

The labels `[0, 1, 2]` become ternary logic under

$$
a\oplus_3 b=(a+b)\bmod3,
\qquad
a\odot_3 b=ab\bmod3.
$$

They are basis or measurement labels—not a Hamiltonian by themselves.

Let \(\Pi_Q\) project onto the 99-dimensional qutrit sector. The global number operator is

$$
N=0_2\oplus(I_{33}\otimes N_3),
$$

and its centered form is

$$
Q=N-\Pi_Q
=0_2\oplus
\left(I_{33}\otimes\mathrm{diag}(-1,0,1)\right).
$$

## 7. The SCL ternary-curvature operator

The three coefficients `[1, -2, 1]` have two related but distinct uses.

As a row stencil acting on three scalar samples,

$$
\Delta^2a=a_0-2a_1+a_2.
$$

As a qutrit observable,

$$
D_3=\mathrm{diag}(1,-2,1).
$$

The compact global operator is

$$
D=0_2\oplus(I_{33}\otimes D_3).
$$

It is related exactly to the qutrit number operator by

$$
\boxed{
D=3(N-\Pi_Q)^2-2\Pi_Q.
}
$$

Its spectrum is

$$
+1\ \text{with multiplicity }66,
\quad
-2\ \text{with multiplicity }33,
\quad
0\ \text{with multiplicity }2.
$$

The bare identity \(1-2+1=0\) says that each local \(D_3\) is traceless. The state-dependent curvature is instead

$$
\kappa(\rho)=\mathrm{Tr}(\rho D).
$$

For orbit \(m\) with populations \(p_{m,0},p_{m,1},p_{m,2}\),

$$
\kappa_m=p_{m,0}-2p_{m,1}+p_{m,2}.
$$

## 8. Phase kick and triality covariance

Define the SCL phase kick

$$
U_D(\theta)=e^{-i\theta D}.
$$

At \(\theta=\pi/2\), each qutrit block is

$$
U_{D_3}\!\left(\frac\pi2\right)
=\mathrm{diag}(-i,-1,-i).
$$

A fixed nonzero \(D\) does not commute with \(U_\tau\). It is therefore a controlled triality-symmetry-breaking probe, not a triality-invariant static field.

For a covariant three-step drive, define

$$
D_a=U_\tau^aDU_\tau^{-a},\qquad a\in\{0,1,2\}.
$$

Then

$$
D_0+D_1+D_2=0,
\qquad
D_{a+1}=U_\tau D_aU_\tau^{-1}.
$$

The compact local combination

$$
F_3=X_3e^{-i\theta D_3}
$$

satisfies the exact identity

$$
F_3^3=I_3
$$

for every \(\theta\), because one three-cycle accumulates the total phase

$$
\theta(1-2+1)=0.
$$

This gives a precise algebraic meaning to combining qutrit cycling, \(\theta=\pi/2\), and `[1, -2, 1]`.

## 9. E8-derived graph operator

For the 101 graph labels \(r_a\in S_{101}\), define

$$
W_{ab}=
\begin{cases}
1,&a\ne b\ \text{and}\ r_a\cdot r_b=1,\\
0,&\text{otherwise}.
\end{cases}
$$

Let

$$
L_E=\mathrm{diag}(W\mathbf1)-W.
$$

This is a real symmetric positive-semidefinite graph Laplacian. Since \(\tau\) preserves inner products and the selector retains complete triality orbits,

$$
[L_E,U_\tau]=0.
$$

The canonical graph fixtures are:

| Property | Value |
|---|---:|
| Vertices | 101 |
| Edges | 1,687 |
| Minimum degree | 22 |
| Maximum degree | 55 |
| Connected components | 1 |
| Spectral gap | approximately 13.7625149924 |
| Largest Laplacian eigenvalue | approximately 56.6814734538 |

The canonical degree-bound normalization is

$$
\overline L_E=\frac{L_E}{2d_{\max}}=\frac{L_E}{110}.
$$

This guarantees \(0\preceq\overline L_E\preceq I\) without making a numerical eigensolver part of the model contract. Spectral-radius normalization is permitted only when explicitly recorded.

Let \(d_j=\sum_kW_{jk}\), so the selected graph has

$$
\sum_jd_j=3374,
\qquad
\overline d=\frac{3374}{101}.
$$

Define the exact centered degree potential

$$
\boxed{
(V_{\deg})_{jj}
=\frac{101d_j-3374}{2181}.
}
$$

Its numerator sum is zero and its maximum absolute numerator is 2181, hence

$$
\mathrm{Tr}(V_{\deg})=0,
\qquad
\|V_{\deg}\|=1.
$$

Triality preserves graph degree, so

$$
[V_{\deg},U_\tau]=0.
$$

The potential is an exact consequence of the **selected** graph. Choosing it
as a generator term is authored, and it is not an independent full-E8
invariant. In general \([V_{\deg},L_E]\ne0\) because the graph is irregular.

## 10. Ouroboros state and optional ring

`Ouroboros` is a declared ETQ model name, not a standard mathematical state class.

Write the fixed singlets as \(|s_0\rangle,|s_1\rangle\), and write the 33
qutrit orbits as \(|m,q\rangle\). For

$$
(d_0,d_1,d_2)=(1,-2,1),
$$

define the ternary/SCL state

$$
|\Omega_{3,\theta}\rangle
=\frac1{\sqrt{101}}
\left[
|s_0\rangle+|s_1\rangle
+\sum_{m=0}^{32}\sum_{q=0}^{2}
e^{2\pi iq/3-i\theta d_q}|m,q\rangle
\right]
$$

and

$$
\rho_0
=|\Omega_{3,\theta}\rangle
\langle\Omega_{3,\theta}|.
$$

Then

$$
\rho_0\succeq0,\qquad
\mathrm{Tr}(\rho_0)=1,\qquad
\mathrm{Tr}(\rho_0^2)=1.
$$

The fixed singlets have explicitly zero phase and no qutrit label. Every basis
amplitude has magnitude \(1/\sqrt{101}\), so the initial basis probabilities
are uniform. Phase can influence a later observation only through a declared
noncommuting evolution or phase-sensitive observable.

If an exactly triality-invariant initial state is required, use the twirl

$$
\rho_{\mathrm{tri}}
=\frac13\sum_{a=0}^2
U_\tau^a\rho_0U_\tau^{-a},
$$

which satisfies

$$
[\rho_{\mathrm{tri}},U_\tau]=0.
$$

If `Ouroboros` is intended specifically as a closed 101-site ring, define

$$
R_{101}|j\rangle=|j+1\!\!\pmod{101}\rangle,
\qquad R_{101}^{101}=I,
$$

and

$$
L_\circ=2I-R_{101}-R_{101}^\dagger.
$$

The normalized ring term \(L_\circ/4\) is positive semidefinite with spectrum in \([0,1]\). In the compact 101 profile, a full 101-cycle generally does not commute with the \(2+33(3)\) triality decomposition. A nonzero ring coupling is therefore another explicit, controlled symmetry-breaking term.

## 11. Dimensionless generator and dynamics

On the qutrit sector define

$$
X_Q=0_2\oplus(I_{33}\otimes X_3)
$$

and the normalized qutrit hopping Laplacian

$$
\overline L_Q
=\frac23\left[
\Pi_Q-\frac12(X_Q+X_Q^\dagger)
\right].
$$

A general dimensionless Hermitian generator is

$$
\boxed{
K=
a_E\overline L_E
+a_Q\overline L_Q
+a_{\deg}V_{\deg}
+a_D\frac D2
+a_NQ
+a_\circ\frac{L_\circ}{4},
}
$$

where all \(a_\bullet\in\mathbb R\) are dimensionless and must be recorded in the model manifest.

The first three displayed terms commute with triality. The static curvature,
centered-number, and full-ring terms generally break it. The canonical v2
profile is

$$
\boxed{
K=\frac{11}{20}\overline L_E
+\frac14\overline L_Q
+\frac15V_{\deg}.
}
$$

These rational weights are authored model choices. The operators they weight
are graph- or qutrit-derived, but E8 does not determine the coefficients.

Closed continuous evolution uses a dimensionless parameter \(s\):

$$
\boxed{
\frac{d\rho}{ds}=-i[K,\rho].
}
$$

No SI time or acoustic frequency is implied. A downstream realization may
choose a tempo or clock, but that receiver-side choice is not part of ETQ-101.

For discrete dynamics, fix the operator order explicitly. The canonical Floquet convention is

$$
U_F=e^{-i\delta K}F_Q,
\qquad
\rho_{n+1}=U_F\rho_nU_F^\dagger,
$$

where

$$
F_Q=I_2\oplus(I_{33}\otimes F_3).
$$

The canonical dimensionless step is declared as

$$
\boxed{
\delta=\frac{2\pi}{303}.
}
$$

The rightmost factor acts first: the SCL phase kick, then the triality shift,
then the continuous-generator step. With \(K=0\), \(F_Q^3=I_{101}\). The
choice \(\delta=2\pi/303\) is part of the authored canonical profile; it is not
forced by E8.

ETQ-101 v2 does not claim that \(U_F\) has order 303. The fact that
\(F_Q^3=I_{101}\) does not establish a corresponding order for the product
\(e^{-i\delta K}F_Q\).

An optional open-system extension is

$$
\frac{d\rho}{ds}=-i[K,\rho]
+\sum_\ell\gamma_\ell
\left(
L_\ell\rho L_\ell^\dagger
-\frac12\{L_\ell^\dagger L_\ell,\rho\}
\right),
$$

where each \(\gamma_\ell\) is a dimensionless rate relative to \(s\). Such a
run must be labeled a GKSL/Lindblad simulation, not unitary qutrit logic.

## 12. Observables

For the two fixed roots and 33 qutrit orbits, define projectors \(\Pi_{\mathrm{fix},s}\) and \(\Pi_{m,q}\). Then

$$
p_{m,q}(s)=\mathrm{Tr}(\rho(s)\Pi_{m,q})
$$

are qutrit populations and

$$
\kappa(s)=\mathrm{Tr}(\rho(s)D)
$$

is aggregate SCL curvature.

Other useful observables are

$$
q_N(s)=\mathrm{Tr}(\rho(s)Q),
$$

$$
e_E(s)=\mathrm{Tr}(\rho(s)\overline L_E),
$$

and triality projectors

$$
P_r=\frac13\sum_{a=0}^2\zeta^{-ra}U_\tau^a,
\qquad r=0,1,2.
$$

If \([K,U_\tau]=0\), the sector weights

$$
w_r(s)=\mathrm{Tr}(\rho(s)P_r)
$$

are conserved under the continuous unitary dynamics.

## 13. Full-qutrit tensor extension

> **ETQ-303 v3.0.1 terminology note.** In this extension, scalars are in
> \(\mathbb C\) unless explicitly stated otherwise, all vector spaces are
> finite-dimensional, \(\dim(V)\) is algebraic vector-space dimension, and
> \(\otimes\) is the tensor product over \(\mathbb C\). “Dimension” does not
> mean physical spacetime dimension. The 8-dimensional \(E_8\) root space,
> rank-4 \(D_4\) subsystem, 101-state selected basis, and 303-state tensor basis
> are distinct mathematical notions and imply no physical ontology. This note
> clarifies terminology only and does not revise the normative ETQ-101 v2
> construction above.

Because 101 is not divisible by three, a qutrit cannot be a tensor factor of the entire 101-dimensional compact space.

If every one of the 101 modes must carry a full qutrit, use

$$
\boxed{
\mathcal H_{303}
=\mathcal H_{101}\otimes\mathbb C^3
\cong\mathbb C^{303}.
}
$$

Consequently,

$$
\dim(\mathcal H_{303})
=\dim(\mathcal H_{101})\dim(\mathbb C^3)
=101\times3
=303.
$$

Here 303 is the algebraic dimension of the finite event/state vector space and
the number of its basis-indexed states, not a claim of 303 physical dimensions.
The \(\mathbb C^3\) factor is the declared three-state, or qutrit-like, tensor
factor used by the protocol; the tensor product introduces no additional
physical ontology.

The original 101-dimensional state is then the reduced state

$$
\rho_{101}=\mathrm{Tr}_3(\rho_{303}).
$$

With a 101-cycle \(R_{101}\) and the phase-twisted qutrit cycle \(F_3\), define

$$
F_{303}=R_{101}\otimes F_3.
$$

Since \(101\) and \(3\) are coprime,

$$
F_{303}^{303}=I_{303},
$$

and its order is exactly 303. This is the clean tensor-profile meaning of a 101-state Ouroboros coupled to a qutrit triality cycle.

Attaching an independent qutrit to each of 101 sites would instead require

$$
(\mathbb C^3)^{\otimes101},
$$

whose dimension is \(3^{101}\); that is a different and vastly larger model.

## 14. Preserved quantities

For the continuous parameter-independent unitary dynamics
\(d\rho/ds=-i[K,\rho]\), the following are preserved:

- \(\mathrm{Tr}(\rho)\);
- Hermiticity and positive semidefiniteness of \(\rho\);
- purity \(\mathrm{Tr}(\rho^2)\);
- von Neumann entropy;
- expected generator value \(\mathrm{Tr}(\rho K)\); and
- triality-sector weights when \([K,U_\tau]=0\).

For the discrete Floquet update \(\rho\mapsto U_F\rho U_F^\dagger\), trace,
Hermiticity, positivity, purity, and von Neumann entropy are preserved because
\(U_F\) is unitary. However, \(\mathrm{Tr}(\rho K)\) is conserved only
when \([U_F,K]=0\), and triality-sector weights are conserved only when
\([U_F,U_\tau]=0\). The spectral-projector weights of \(U_F\), rather than
those of \(K\), are the natural invariants of a fixed Floquet step.

For GKSL evolution, trace and positivity are preserved by construction, but purity, entropy, energy, and triality weights need not be.

## 15. Required deterministic checks

The complete normative checklist for a conforming implementation is:

1. 240 unique E8 roots, each with doubled norm squared 8.
2. \(\tau^T\tau=I\), \(\tau^3=I\), and \(\tau R_{E_8}=R_{E_8}\).
3. Orbit decomposition \(12+76(3)=240\).
4. Selected dimension \(2+33(3)=101\).
5. Canonical basis and adjacency SHA-256 fixtures.
6. \(U_\tau^3=I\).
7. \([L_E,U_\tau]=0\).
8. Symmetry, zero row sums, connectivity, and positive semidefiniteness of \(L_E\).
9. \(X_3^3=Z_3^3=I\) and \(Z_3X_3=\zeta X_3Z_3\).
10. \(D=3(N-\Pi_Q)^2-2\Pi_Q\).
11. \(D_0+D_1+D_2=0\).
12. Unitarity of \(U_D\) and \(F_3^3=I\).
13. Normalization and explicit singlet phases of
    \(|\Omega_{3,\theta}\rangle\).
14. Exact degree-potential centering, scaling, and triality invariance.
15. Exact canonical generator coefficients and dimensionless step.
16. Hermiticity and dimensionlessness of the declared generator.
17. Bijection, inverse, lane ranges, and triality shift of the MIDI codebook.

The dependency-free tests verify the implemented structural, state,
degree-potential, generator-symmetry, triality-invariance, and codebook checks.
`npm run verify` additionally checks the
canonical v2 serialization and hashes, schema constants, the absence of the
removed forward anchors, and the immutable v1 identity fixture. The reference
source constructs \(K\), but a numerical matrix exponential/Floquet trajectory,
dynamics-to-event observation rule, and Standard MIDI File exporter remain
future work; the repository does not claim that they already exist.

## 16. References

- John C. Baez, [*The Octonions*](https://arxiv.org/abs/math/0105155), *Bulletin of the American Mathematical Society* 39 (2002), 145–205. Background on octonions, Spin(8) triality, and exceptional structures.
- Craig McRae, [*Exploring Triality Explicitly: Convenient bases for SO(8), Spin(1,7), and G2*](https://arxiv.org/abs/2502.14016) (2025). Explicit D4/Spin(8) triality context.
- Robert Feger and Thomas W. Kephart, [*LieART — A Mathematica Application for Lie Algebras and Representation Theory*](https://arxiv.org/abs/1206.6379) (2014). Representation tables and computational Lie-algebra conventions.
- Ashmeet Singh and Sean M. Carroll, [*Modeling Position and Momentum in Finite-Dimensional Hilbert Spaces via Generalized Pauli Operators*](https://arxiv.org/abs/1806.10134) (2020). Finite-dimensional generalized Pauli operators.
- Pierre-Philippe Dechant, [*The E8 geometry from a Clifford perspective*](https://arxiv.org/abs/1603.04805) (2016). E8 root geometry and Coxeter-plane constructions.
- Florian Grond and Jonathan Berger, “Parameter Mapping Sonification,” in
  *The Sonification Handbook*, Chapter 15, pp. 363–397 (2011). Mapping design,
  receiver dependence, and evaluation boundaries.
- Elvira Pirondini et al., [“A Spectral Method for Generating Surrogate Graph
  Signals”](https://doi.org/10.1109/LSP.2016.2594072), *IEEE Signal Processing
  Letters* 23(9), 2016. Graph-Fourier surrogate testing for node signals.
