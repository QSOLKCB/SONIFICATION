# Tanner Graph Tuning Fork

**Profile:** `tanner-laplacian-frame-bin-v1`  
**Status:** Auxiliary, noncanonical graph-calibration experiment

This profile studies reproducible nominal sample-clock calibration for Tanner
and selected-root graph spectra. The declared graph operator and ratio map
determine interval ratios; an explicitly supplied nominal clock provides the
unit of hertz. It is not the root ETQ-101 mapping.

Root ETQ-101 v2 uses a symbolic low/mid/high MIDI codebook and declares no
sample clock, absolute frequency, PCM realization, or frame-bin calibration.
ETQ-101 v1.0 remains preserved as an immutable specification-identity fixture;
its originally unimplemented renderer is not claimed to be replayable. This
document changes neither contract.

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
applies the same rule to the positive-semidefinite selected E8 root-graph
Laplacian as an auxiliary experiment. It must not be substituted for the
canonical v2 generator $K$ or the v2 symbolic MIDI codebook.

This bridge is therefore a derived **E8-root-graph calibration experiment**,
not a forward ETQ mapping. It omits the qutrit hopping term, degree potential,
ternary/SCL state, and low/mid/high lane codebook. No transformation from its
spectral ratios or frame bins into canonical ETQ-101 v2 events is defined.

## 3. Exact frame-bin calibration (auxiliary only)

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
absolute audible frequency. These quantities belong only to this auxiliary
calibration experiment; root ETQ-101 v2 has no playback clock or hertz layer.

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

## 5. Mathematical and regression fixtures

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

The $P_5$ occurrence of $\varphi$ is solely an exact algebraic identity of that
test graph. It is unrelated to the authored golden-ratio phase/pitch
modulation removed from forward ETQ-101 v2, and it does not enter the v2 state,
generator, MIDI mapping, or timing.

An additional integration regression runs the actual 101-node selected E8 root
graph through eigenspace grouping and frame-bin calibration. At 48 kHz with a
960,000-frame calibration window and a declared 40–16,000 Hz band, it fixes
$q=3028$ and the exact anchor $757/5$ Hz. This is a regression fixture for the
auxiliary profile, not a claim that 151.4 Hz is selected by E8 and not an ETQ
v2 clock.

The QEC sources reviewed while extracting these invariants are indexed in
[`qec_repo.json`](../qec_repo.json).
