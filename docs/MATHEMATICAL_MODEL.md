# ETQ-101 Mathematical Model

**Version:** 1.0.0  
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
- optional golden-ratio modulation; and
- a declared 432 Hz time and sonification reference.

The precise claim is:

> **ETQ-101 is a deterministic 101-dimensional root-indexed graph truncation derived from E8, closed under a D4 triality embedded in E8, with 33 direct-sum qutrit/triality blocks and two fixed singlets.**

It is not a 101-dimensional representation of the E8 Lie group or Lie algebra. It is an authored effective model whose basis selector, operators, units, observables, and sonification map are explicit and testable.

## 1. Correction of the proposed scalar equation

Use separate symbols for three unrelated constants:

$$
\theta=\frac{\pi}{2},\qquad
\varphi=\frac{1+\sqrt5}{2},\qquad
\zeta=e^{2\pi i/3}.
$$

Here \(\theta\) is a phase, \(\varphi\) is the golden ratio, and \(\zeta\) is the primitive qutrit root of unity. Define

$$
f_0=432\ \mathrm{Hz},\qquad
\Omega_0=2\pi f_0=864\pi\ \mathrm{s}^{-1}.
$$

The supplied expression has the form

$$
\theta^2\left[
\operatorname{Tr}(\rho)-\frac12(1-2+1)
\right]
+\frac{\Omega_0}{101}
\left(\frac{2\pi}{\theta}\right)^2=0.
$$

Because

$$
1-2+1=0
$$

and a density operator is normalized by \(\operatorname{Tr}(\rho)=1\), the expression becomes

$$
\theta^2+
\frac{\Omega_0}{101}
\left(\frac{2\pi}{\theta}\right)^2.
$$

At \(\theta=\pi/2\), this is

$$
\frac{\pi^2}{4}
+\frac{13824\pi}{101}\ \mathrm{s}^{-1}.
$$

It cannot equal zero as written. More importantly, it adds a dimensionless number to an angular frequency. Only the ternary sum vanishes; the first term does **not** vanish.

If a scalar zero condition is aesthetically useful, a dimensionless calibration residual may be defined instead:

$$
\begin{aligned}
\mathcal R(\rho,\Omega)
={}&\theta^2\bigl(\operatorname{Tr}\rho-1\bigr)^2
+\frac16\bigl(\operatorname{Tr}(\rho D)\bigr)^2\\
&+\frac12\bigl(\operatorname{Tr}(\rho Q)\bigr)^2
+\frac1{101}\left(\frac{\Omega}{\Omega_0}-1\right)^2
\ge 0.
\end{aligned}
$$

Then \(\mathcal R=0\) expresses normalization, aggregate ternary balance, aggregate centered-qutrit balance, and exact frequency calibration. It is a declared constraint—not an equation of motion or a physical law. Positivity and Hermiticity of \(\rho\) remain separate axioms.

## 2. Notation

| Symbol | Meaning | Units |
|---|---|---|
| \(\theta\) | SCL phase, canonically \(\pi/2\) | rad (dimensionless) |
| \(\varphi\) | Golden ratio \((1+\sqrt5)/2\) | dimensionless |
| \(\zeta\) | Qutrit root of unity \(e^{2\pi i/3}\) | dimensionless |
| \(f_0\) | Declared reference frequency, 432 Hz | Hz |
| \(\Omega_0\) | \(2\pi f_0\) | rad s\(^{-1}\) |
| \(\mathcal H_{101}\) | Compact ETQ-101 state space | — |
| \(\rho\) | Density operator on the selected state space | — |
| \(U_\tau\) | Embedded order-three triality action | — |
| \(D\) | SCL ternary-curvature observable | — |
| \(N\) | Qutrit number-label observable | — |
| \(K\) | Dimensionless Hermitian generator | — |
| \(H=\hbar\Omega_0K\) | Hamiltonian when a physical-energy notation is wanted | energy |

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
=\operatorname{span}_{\mathbb C}\{|r\rangle:r\in S_{101}\},
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
N_3=\operatorname{diag}(0,1,2),
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
\left(I_{33}\otimes\operatorname{diag}(-1,0,1)\right).
$$

## 7. The SCL ternary-curvature operator

The three coefficients `[1, -2, 1]` have two related but distinct uses.

As a row stencil acting on three scalar samples,

$$
\Delta^2a=a_0-2a_1+a_2.
$$

As a qutrit observable,

$$
D_3=\operatorname{diag}(1,-2,1).
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
\kappa(\rho)=\operatorname{Tr}(\rho D).
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
=\operatorname{diag}(-i,-1,-i).
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
L_E=\operatorname{diag}(W\mathbf1)-W.
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

## 10. Ouroboros state and optional ring

`Ouroboros` is a declared ETQ model name, not a standard mathematical state class.

Let \(d_j\) be the \(j\)-th diagonal entry of \(D\). Define the golden-phase state

$$
|\Omega_{\varphi,\theta}\rangle
=\frac1{\sqrt{101}}
\sum_{j=0}^{100}
\exp\!\left(
\frac{2\pi i j}{\varphi}-i\theta d_j
\right)|j\rangle
$$

and

$$
\rho_0
=|\Omega_{\varphi,\theta}\rangle
\langle\Omega_{\varphi,\theta}|.
$$

Then

$$
\rho_0\succeq0,\qquad
\operatorname{Tr}(\rho_0)=1,\qquad
\operatorname{Tr}(\rho_0^2)=1.
$$

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

For orbit projectors \(\Pi_m\), define a triality-invariant golden potential

$$
V_\varphi
=0_2\oplus
\sum_{m=0}^{32}
\cos\!\left(\frac{2\pi m}{\varphi}+\theta\right)\Pi_m.
$$

A general dimensionless Hermitian generator is

$$
\boxed{
K=
a_E\overline L_E
+a_Q\overline L_Q
+a_\varphi V_\varphi
+a_D\frac D2
+a_NQ
+a_\circ\frac{L_\circ}{4},
}
$$

where all \(a_\bullet\in\mathbb R\) are dimensionless and must be recorded in the model manifest.

The first three displayed terms commute with triality. The static curvature, centered-number, and full-ring terms generally break it. The canonical example keeps those static coefficients at zero and applies the SCL operator as the covariant phase drive instead.

Use the declared angular reference to define

$$
\boxed{
H=\hbar\Omega_0K,
\qquad
\Omega_0=2\pi(432)\ \mathrm{s}^{-1}.
}
$$

Closed evolution is

$$
\dot\rho=-i\Omega_0[K,\rho].
$$

All terms inside \(K\) are dimensionless, so there is no unit mismatch.

For discrete dynamics, fix the operator order explicitly. The canonical Floquet convention is

$$
U_F=e^{-i\tau K}F_Q,
\qquad
\rho_{n+1}=U_F\rho_nU_F^\dagger,
\qquad
\tau=\Omega_0\Delta t,
$$

where

$$
F_Q=I_2\oplus(I_{33}\otimes F_3).
$$

The canonical dimensionless step and physical timestep are declared as

$$
\boxed{
\tau=\frac{2\pi}{303},
\qquad
\Delta t=\frac{\tau}{\Omega_0}
=\frac{1}{303\cdot432}\ \mathrm{s}.
}
$$

The rightmost factor acts first: the SCL phase kick, then the triality shift,
then the continuous-generator step. With \(K=0\), \(F_Q^3=I_{101}\). The
choice \(\tau=2\pi/303\) is part of the authored canonical profile; it is not
forced by E8.

The canonical `generator-spectrum-v1` audio profile is separate from this
Floquet update: it diagonalizes the dimensionless generator \(K\) and does not
claim that \(U_F\) has order 303, diagonalize \(U_F\), or integrate a trajectory
\(\rho_n\).

An optional open-system extension is

$$
\dot\rho=-i\Omega_0[K,\rho]
+\sum_\ell\gamma_\ell
\left(
L_\ell\rho L_\ell^\dagger
-\frac12\{L_\ell^\dagger L_\ell,\rho\}
\right),
$$

where \(\gamma_\ell\) has units s\(^{-1}\). Such a run must be labeled a GKSL/Lindblad simulation, not unitary qutrit logic.

## 12. Observables

For the two fixed roots and 33 qutrit orbits, define projectors \(\Pi_{\mathrm{fix},s}\) and \(\Pi_{m,q}\). Then

$$
p_{m,q}(t)=\operatorname{Tr}(\rho(t)\Pi_{m,q})
$$

are qutrit populations and

$$
\kappa(t)=\operatorname{Tr}(\rho(t)D)
$$

is aggregate SCL curvature.

Other useful observables are

$$
q_N(t)=\operatorname{Tr}(\rho(t)Q),
$$

$$
e_E(t)=\operatorname{Tr}(\rho(t)\overline L_E),
$$

and triality projectors

$$
P_r=\frac13\sum_{a=0}^2\zeta^{-ra}U_\tau^a,
\qquad r=0,1,2.
$$

If \([K,U_\tau]=0\), the sector weights

$$
w_r(t)=\operatorname{Tr}(\rho(t)P_r)
$$

are conserved under the continuous unitary dynamics.

## 13. Full-qutrit tensor extension

Because 101 is not divisible by three, a qutrit cannot be a tensor factor of the entire 101-dimensional compact space.

If every one of the 101 modes must carry a full qutrit, use

$$
\boxed{
\mathcal H_{303}
=\mathcal H_{101}\otimes\mathbb C^3
\cong\mathbb C^{303}.
}
$$

The original 101-dimensional state is then the reduced state

$$
\rho_{101}=\operatorname{Tr}_3(\rho_{303}).
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

For the continuous time-independent unitary dynamics
\(\dot\rho=-i\Omega_0[K,\rho]\), the following are preserved:

- \(\operatorname{Tr}(\rho)\);
- Hermiticity and positive semidefiniteness of \(\rho\);
- purity \(\operatorname{Tr}(\rho^2)\);
- von Neumann entropy;
- expected generator value \(\operatorname{Tr}(\rho K)\); and
- triality-sector weights when \([K,U_\tau]=0\).

For the discrete Floquet update \(\rho\mapsto U_F\rho U_F^\dagger\), trace,
Hermiticity, positivity, purity, and von Neumann entropy are preserved because
\(U_F\) is unitary. However, \(\operatorname{Tr}(\rho K)\) is conserved only
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
13. Normalization of \(|\Omega_{\varphi,\theta}\rangle\).
14. Hermiticity and unit consistency of the declared generator.

The dependency-free reference tests currently verify items 1–13 at the
structural/operator level. The canonical coefficients, timestep, model
relations, serialization rules, and regression fixtures are checked by
`npm run verify`. Construction and eigensolver-level validation of a complete
numeric \(K\), \(U_F\), and audio render remain future reference-renderer work;
the repository does not claim those artifacts already exist.

## 16. References

- John C. Baez, [*The Octonions*](https://arxiv.org/abs/math/0105155), *Bulletin of the American Mathematical Society* 39 (2002), 145–205. Background on octonions, Spin(8) triality, and exceptional structures.
- Craig McRae, [*Exploring Triality Explicitly: Convenient bases for SO(8), Spin(1,7), and G2*](https://arxiv.org/abs/2502.14016) (2025). Explicit D4/Spin(8) triality context.
- Robert Feger and Thomas W. Kephart, [*LieART — A Mathematica Application for Lie Algebras and Representation Theory*](https://arxiv.org/abs/1206.6379) (2014). Representation tables and computational Lie-algebra conventions.
- Ashmeet Singh and Sean M. Carroll, [*Modeling Position and Momentum in Finite-Dimensional Hilbert Spaces via Generalized Pauli Operators*](https://arxiv.org/abs/1806.10134) (2020). Finite-dimensional generalized Pauli operators.
- Bertram Kostant, [*Experimental evidence for the occurrence of E8 in nature and the radii of the Gosset circles*](https://arxiv.org/abs/1003.0046) (2010). E8 roots, Coxeter-plane circles, and the specific golden-ratio relation discussed there.
- Pierre-Philippe Dechant, [*The E8 geometry from a Clifford perspective*](https://arxiv.org/abs/1603.04805) (2016). E8 root geometry and Coxeter-plane constructions.
