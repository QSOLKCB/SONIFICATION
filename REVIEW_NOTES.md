# ETQ-101 v2 Reviewer Notes

## Disposition of the two disputed anchors

ETQ-101 v2.0.0 does not ask reviewers to accept either golden-ratio
modulation or a 432 Hz reference. Both have been removed from the forward
state, generator, dynamics, and note map.

This is a breaking profile revision, not a reinterpretation of v1.0.0. The
DOI-linked v1 contract remains available as an exact historical specification
identity at
`examples/etq-101.canonical.json`, with its original schema and payload hash:

```text
6577443641be02609c045ee0afc423c2be37bbe5ae83f671cbae304c0e9cb930
```

The v2 verifier checks that legacy fixture separately. This preserves contract
identity, not an executable render that v1 never implemented. Preservation of
v1 does not make its tuning choices part of the v2 claim.

## Forward mathematical profile

The replacement for the former modulation term is the exact centered degree
potential of the declared 101-node selected root graph. For vertex degree
\(d_j\),

$$
\boxed{
(V_{\deg})_{jj}=\frac{101d_j-3374}{2181}.
}
$$

For the canonical selector, the graph has 1,687 edges, degree sum 3,374,
mean degree \(3374/101\), minimum degree 22, and maximum degree 55. The
integer numerators sum to zero and have maximum absolute value 2,181.
Consequently \(V_{\deg}\) has exactly zero trace and operator norm one. Its
entries are constant on triality orbits, so it commutes with the canonical
triality permutation.

These facts should not be overread. The potential is a consequence of the
standard E8 roots **after** the embedded triality, coordinate convention, and
lexicographic `2 + 33*3` selector have been declared. It is not an invariant
of the complete E8 root system. The graph Laplacian already contains degree
information, so this on-site contrast is not independent structural evidence.
Choosing to include it, and assigning it coefficient \(1/5\), remain authored
model choices.

The v2 generator is

$$
K=\frac{11}{20}\overline L_E
 +\frac14\overline L_Q
 +\frac15V_{\deg}.
$$

Every term and coefficient is dimensionless. Continuous evolution is stated
as

$$
\frac{d\rho}{ds}=-i[K,\rho],
$$

where \(s\) is dimensionless. The discrete profile uses

$$
U_F=e^{-i\delta K}F_Q,
\qquad
\delta=\frac{2\pi}{303}.
$$

The value of \(\delta\), like the generator coefficients, is reproducible but
authored. No physical time scale, angular-frequency scale, or conversion to
hertz is present.

## Ternary MIDI codebook

The forward observation map is a reversible symbolic code for the declared
decomposition

$$
\mathcal H_{101}=\mathbb C^2\oplus
(\mathbb C^{33}\otimes\mathbb C^3).
$$

The two fixed singlets map to MIDI note numbers 13 and 113. For orbit
\(m\in\{0,\ldots,32\}\) and qutrit label \(q\in\{0,1,2\}\),

$$
\boxed{M(m,q)=14+33q+m.}
$$

| Cyclic label | Authored display name | MIDI note range |
|---:|---|---:|
| 0 | low | 14--46 |
| 1 | mid | 47--79 |
| 2 | high | 80--112 |

This map is a 101-entry bijection. On the 99-note qutrit interior, triality is
addition of 33 modulo 99. Those are exact coding properties; they do not turn
the cyclic labels into an intrinsic energy ordering. The orbit order is a
lexicographic enumeration rather than a measured magnitude, and the two
singlet bookends are code boundaries rather than spectral extrema.

A MIDI note number does not determine acoustic frequency, temperament,
soundfont, timbre, loudness, or listener grouping. Receiver tuning and
rendering are external and non-normative. The current v2 implementation fixes
and hashes only the basis codebook. It does not yet claim a dynamics-to-event
mapping or a Standard MIDI File exporter.

## Role of the Tanner `.mjs` modules

The Tanner modules are useful auxiliary graph-numerics infrastructure. They
provide deterministic Laplacian construction, eigenspace grouping, a
cyclic-Jacobi eigensolver, and invariant projectors for degenerate modes.
Those components can support graph-signal diagnostics and the proposed
surrogate testbench.

Their frame-bin calibration is not the v2 ETQ observation map and does not
derive a pitch from E8. Any sample rate, frame count, playback range, or
frequency selection in that auxiliary profile remains declared. Likewise,
any golden-ratio identity retained as a Tanner regression fixture does not
enter the v2 state, generator, dynamics, or MIDI codebook. The Tanner modules
must therefore be cited as auxiliary calibration or numerical research, not
as evidence for a canonical ETQ frequency.

## Statistical and perceptual validation are separate

The proposed graph-spectral surrogate test is a conditional null comparison
for a node-valued signal on the selected 101-node graph. Grouped eigenspace
projectors avoid arbitrary numerical rotations inside degenerate eigenspaces.
A grouped-sign surrogate preserves the DC component, grouped graph-spectral
power, Euclidean norm, and graph quadratic energy while changing spectral
sign arrangement.

This method can test a preregistered, non-invariant statistic such as template
correlation, triality-orbit alignment, edge mixing, \(L^1\) graph variation,
or localization. It cannot use grouped spectral energy, \(x^TL_Ex\), or the
Euclidean norm as the test statistic because those quantities are preserved by
construction. It also does not directly test the adjacency, the MIDI codebook,
graph eigenvalues, GF(3) edge labels, or the non-Hermitian Hashimoto operator.

Null rejection would mean only that the chosen node signal is unusual under
the declared graph-conditioned surrogate family. It would not validate E8,
qutrit ontology, the selector, the MIDI ordering, or a physical theory. For
constructed data, the appropriate wording is **conditional null comparison**
or **stress test**, not empirical confirmation.

Perceptual validation addresses a different question: whether listeners can
decode the authored low/mid/high display under a fixed receiver setup. A
credible study should freeze the mapping after pilot work, use naive
listeners, counterbalance polarity and spacing, and report three-class
confusion matrices, accuracy, reaction time, training, receiver settings, and
relevant subgroup analyses. Success would validate only the tested display
task and realization.

## Deterministic receipts

The forward profile is identified by the following SHA-256 receipts:

| Object | SHA-256 |
|---|---|
| Selected basis | `97cfd1f087745422fd66d3640c7b86c3209593c4b53741018c08a5e9cdb15f6f` |
| Selected adjacency | `29ae0af5b1090c9de30f1efc25789060fb1791eb175d2afcd6888847f7fe6324` |
| Degree-potential numerators | `517b9b86e07a1788cabc446be93e573d21719af3c1e0eeaedae00b81689c4468` |
| Ternary MIDI codebook | `9a3196255e92bbc6857576e410a852dc66cd0354f27185fb2bede5b99f76e304` |
| v2 contract payload | `d17e4e104bae41e649f1589467fb8122eb42fc9be4298110f4c21753580b3eab` |

Hashes establish identity under the declared serialization rules. They do not
establish scientific validity, physical realization, or naturalness of an
authored parameter.

## Direct answers to likely reviewer objections

| Objection | Response |
|---|---|
| “Why should the golden ratio appear?” | It does not appear in the v2 forward profile. |
| “Why should E8 select 432 Hz?” | It does not. V2 defines no absolute frequency. |
| “Is the degree potential E8-derived?” | It is exactly derived from the **selected** root graph; the selector, inclusion of the term, and coefficient are declared. |
| “Are low/mid/high intrinsic qutrit levels?” | No. They are reversible display labels for a cyclic set. |
| “Does MIDI specify the sound?” | No. The receiver determines tuning and acoustics. |
| “Do the Tanner frame bins rescue a canonical pitch?” | No. They form an auxiliary declared calibration profile. |
| “Would a surrogate p-value validate ETQ?” | No. It answers only a conditional statistical question for a preregistered node-signal statistic. |
| “Would a listener study validate the mathematics?” | No. It tests usability of one fixed sonification realization. |

The defensible forward claim is therefore limited to a deterministic
E8-root-derived, D4-triality-closed 101-state graph model with an exact
selected-graph degree potential and a reversible symbolic ternary MIDI
codebook.
