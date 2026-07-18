# Tanner Graph Tuning Fork

**Profile:** `tanner-laplacian-frame-bin-v1`  
**Status:** Candidate mathematical kernel and derived ETQ-101 root-graph observation profile; canonical PCM intentionally remains null

This profile offers a forward alternative to an authored absolute reference by
using reproducible nominal sample-clock calibration. The declared graph
operator and ratio map determine interval ratios. The nominal playback clock
supplies the unavoidable unit of hertz.

ETQ-101 v1.0 and its 432 Hz mapping remain replayable as the explicitly legacy
`legacy-authored-432-v1` profile. This document does not rewrite that deposited
contract, and no canonical PCM realization is required by this profile.

## 1. Instrument identity

A tuning-fork instrument is the labelled sparse parity-check matrix

$$
H\in\mathbb F_p^{m\times n},\qquad p\in\{2,3\}.
$$

Its canonical entries are numeric lexicographic triples

$$
(\text{check},\text{variable},\text{coefficient}).
$$

GF(3) coefficients 1 and 2 therefore identify different instruments even when
their unweighted Tanner topology is the same. A future row-space or RREF hash
would describe code equivalence; it must remain separate from this labelled
instrument hash.

In this version the coefficients affect instrument identity but not the
support-only Laplacian pitch spectrum. Coefficient-distinct instruments may
therefore share the same pitches until a separately declared coefficient map
is introduced.

## 2. Pitch operator

Let $H_{\ne0}$ denote the binary support of the labelled matrix. With variable
nodes first and check nodes second, define

$$
A_T=
\begin{bmatrix}
0&H_{\ne0}^{\mathsf T}\\
H_{\ne0}&0
\end{bmatrix},
\qquad
L_T=D-A_T.
$$

$L_T$ is real symmetric and positive semidefinite. Its zero modes are DC or
disconnected-component modes and are omitted from pitch construction. For
every positive eigenvalue,

$$
r_k=\sqrt{\lambda_k}.
$$

These are dimensionless oscillator-mode ratios. Adjacent numerical
eigenvalues are grouped using the declared absolute and relative tolerance
rule. Each group is represented by the full projector

$$
P_G=\sum_{k\in G}|v_k\rangle\langle v_k|,
$$

not by an arbitrary individual eigenvector.

The square-root rule is an authored oscillator analogue: it is the normal-mode
rule for unit masses connected by unit-stiffness edges. It is not an intrinsic
acoustic law of a Tanner graph.

The API exposes raw eigenvectors and group bases for numerical diagnostics,
but they are not identity fields. A stable mode receipt uses only grouped
eigenvalues, multiplicities, and projectors from
`invariantPositiveEigenspaces`. Zero-mode classification occurs before
positive-mode clustering, so a deliberately broad grouping tolerance cannot
erase a positive eigenspace by joining it to DC.
Every derived result also records the resolved eigensolver, grouping,
orthonormality, and zero-mode tolerances in its `numerics` block. Overrides do
not silently reuse an unqualified numerical receipt.

For ETQ-101, [`deriveEtq101ClockTuning`](../src/etq101-tuning-fork.mjs)
applies the same rule to its positive-semidefinite E8 root-graph Laplacian. It
must not be applied directly to the canonical generator $K$, because the
signed golden cosine potential can make $K$ indefinite.

This ETQ bridge is therefore a derived **E8-root-graph observation profile**,
not a drop-in replacement for the canonical full-$K$ generator-spectrum map.
It omits the qutrit hopping term, golden potential, and initial-state spectral
weights. A future full-ETQ clock-bin profile should instead apply the same bin
selector to the existing positive pitch ratios
$r_\ell=2^{\varphi\xi_\ell}$ after the full $K$ reference eigensolver is fixed.

## 3. Exact frame-bin calibration

Declare a sample rate $F_s$, calibration frame count $N$, playback band
$[F_{\min},F_{\max}]$, and positive ratios with extrema
$r_{\min},r_{\max}$. The exact bin width is

$$
\Delta f=\frac{F_s}{N}.
$$

Feasible integer bins satisfy

$$
q_{\min}=\left\lceil\frac{F_{\min}}
{\Delta f\,r_{\min}}\right\rceil,
\qquad
q_{\max}=\left\lfloor\frac{F_{\max}}
{\Delta f\,r_{\max}}\right\rfloor.
$$

The `clock-bin-maximin-log-margin-v1` policy chooses the feasible integer $q$
that maximizes the smaller logarithmic margin to the two band edges. Its
continuous target is

$$
q_*=\frac{1}{\Delta f}
\sqrt{\frac{F_{\min}F_{\max}}{r_{\min}r_{\max}}}.
$$

The implementation finds the feasible floor and ceiling of $q_*$ without a
logarithm-based score comparison. Since logarithm is monotone, comparing the
two raw margin ratios is algebraically equivalent. If the two integer bins are
exactly tied, the smaller one wins. Frequencies are then

$$
\boxed{
f_{\mathrm{cal}}=q\frac{F_s}{N},
\qquad
f_k=f_{\mathrm{cal}}r_k.
}
$$

The anchor is an exact **nominal** frame bin and is serialized as a reduced
rational number. Irrational graph-derived frequencies generally are not
themselves DFT bins; their recorded ratios are the mathematical identity.
Physical acoustic frequencies remain subject to the accuracy of the playback
device's sample clock.

The playback band and bin-selection policy remain declared engineering
choices. The profile does not claim that E8 or a Tanner graph selects an
absolute audible frequency.

## 4. Nonbacktracking phase clock

For canonically ordered directed edges, the Hashimoto operator uses

$$
B_{ji}=1
$$

exactly when edge $i=(u,v)$ may continue to $j=(v,w)$ without immediately
returning to $u$.

$B$ is not used as the primary pitch operator because it is generally
non-Hermitian and can have complex modes. Its powers provide exact cyclic phase
clocks and its magnitudes or projectors may later control decay, brightness,
distortion, or graph-edge excitation.

## 5. Golden fixtures

The dependency-free test suite fixes seven invariants:

1. Tanner $P_5$: Laplacian modes contain $\varphi^{-2}$ and $\varphi^2$, so
   oscillator modes contain $\varphi^{-1}$ and $\varphi$.
2. Tanner $C_6$: $(B^2)^3=I$, giving an exact three-state/qutrit phase clock.
3. Tanner $C_8$: $(B^2)^4=I$, giving exact quadrature including $\pi/2$.
4. The $P_5$ tree: $B^4=0$, preventing false nonbacktracking resonance.
5. Shuffled sparse entries produce the same numeric lexicographic identity.
6. Rotating a degenerate orthonormal basis leaves its projector unchanged.
7. GF(3) coefficients 1 and 2 produce different instrument hashes despite
   identical unweighted topology.

An additional integration golden runs the actual 101-node selected E8 root
graph through eigenspace grouping and frame-bin calibration. At 48 kHz with a
960,000-frame calibration window and a declared 40–16,000 Hz band, it fixes
$q=3028$ and the exact anchor $757/5$ Hz. This is a regression fixture for the
declared profile, not a claim that 151.4 Hz is selected by E8.

The QEC sources reviewed while extracting these invariants are indexed in
[`qec_repo.json`](../qec_repo.json).

