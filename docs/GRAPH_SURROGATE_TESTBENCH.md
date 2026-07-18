# ETQ-101 Graph-Surrogate Statistical Testbench

**Status:** Method specification; not yet implemented  
**Scope:** Optional validation of node-valued ETQ observations  
**Not part of:** The canonical MIDI codebook or any physical claim

## 1. Purpose

The testbench supplies a topology-aware null comparison for a signal observed
on the selected 101-node E8 root graph. It adapts the graph-Fourier surrogate
method of Pirondini et al. while making degenerate-eigenspace handling explicit.

It answers a conditional statistical question:

> Is a preregistered statistic of this node signal unusual relative to graph
> surrogates that preserve its grouped graph-spectral power?

It does not test whether E8, triality, qutrits, or the MIDI mapping are
physically real or uniquely correct.

## 2. Applicability

Let \(x\in\mathbb R^{101}\) be a scalar graph signal. Suitable examples include:

- basis populations after a declared dimensionless evolution step;
- node-local curvature contributions;
- an imported measurement already aligned to the canonical basis; or
- a future velocity or activity vector before MIDI quantization.

The method does not apply directly to:

- the adjacency or eigenvalue list itself;
- GF(3) edge coefficients without an explicit edge-space construction;
- the non-Hermitian Hashimoto operator;
- a MIDI codebook that contains no observed node signal; or
- rendered audio.

Sign reconstruction does not generally preserve nodewise nonnegativity or the
probability simplex. When the input is a population vector, its surrogates are
auxiliary real graph signals, not physically admissible population states. A
claim requiring admissible populations needs a separately specified
simplex-preserving null.

## 3. Graph Fourier decomposition

For the real symmetric combinatorial Laplacian

$$
L_E=D_G-W,
$$

where \(D_G=\operatorname{diag}(W\mathbf 1)\) is the graph degree matrix,
not the ETQ ternary-curvature operator \(D\).

write its grouped spectral resolution as

$$
L_E=\sum_g\lambda_gP_g,
$$

where \(P_g\) is the projector onto the complete eigenspace group selected by
the declared absolute and relative tolerance rule.

Using projectors prevents a numerical eigensolver's arbitrary rotation inside
a degenerate eigenspace from changing the testbench identity.

## 4. Basis-independent sign surrogates

Separate the connected-graph DC component or center the signal. For a sign
vector \(s_g\in\{-1,+1\}\), define

$$
\boxed{
\widetilde x_s
=P_{\mathrm{DC}}x
+\sum_{g\ne\mathrm{DC}}s_gP_gx.
}
$$

One sign is applied to a complete grouped eigenspace, not independently to
arbitrary basis vectors inside it. This construction preserves:

- the DC component;
- \(\lVert P_gx\rVert_2^2\) for every group;
- total Euclidean energy; and
- graph quadratic energy \(x^TL_Ex\), up to recorded numerical tolerance.

An optional richer profile may apply a seeded orthogonal rotation inside a
degenerate group. Such a profile requires a separately specified deterministic
PRNG, orthogonalization ABI, sign convention, and receipt.

## 5. Null hypothesis

The grouped-sign family defines a conditional **sign-symmetry null**: given the
observed grouped graph-power spectrum, each non-DC eigenspace component is
treated as exchangeable with its negative. This is narrower than the claim
that it samples every graph-stationary signal.

The null is deliberately stronger than a naive node permutation because it
preserves topology-conditioned correlation structure. Its conclusions remain
conditional on:

- the selected 101-node graph;
- Laplacian choice and normalization;
- eigenspace grouping tolerances;
- signal centering and DC policy;
- surrogate generator; and
- preregistered statistic.

## 6. Statistics that cannot be tested

Any statistic determined only by grouped spectral magnitudes is invariant
across these surrogates and therefore unsuitable as the test statistic. This
includes:

- grouped band energy;
- graph spectral centroid based only on power;
- \(x^TL_Ex\);
- Euclidean norm; and
- any quadratic spectral filter energy
  \(\sum_g h(\lambda_g)\lVert P_gx\rVert_2^2\).

These quantities are useful preservation diagnostics, not evidence against
the null.

## 7. Candidate preregistered statistics

Statistics that can change under sign-surrogate reconstruction include:

- correlation with an independently declared target pattern;
- triality-orbit alignment;
- same/different-class edge mixing;
- an \(L^1\) graph total-variation statistic;
- motif or support-overlap scores;
- spatial concentration or peak localization; and
- register-transition or run-length statistics after a separately declared
  quantizer.

If a continuous surrogate is converted back to low/mid/high labels, thresholds
or rank-based histogram matching must be fixed before testing. Quantization
generally changes the preserved spectrum and requires before/after diagnostics.

## 8. Finite-sample procedure

A conforming test records a surrogate count \(B\), deterministic seed, sign
domain, and one- or two-sided alternative. It must also report the number of
non-DC groups and whether draws repeat or enumerate the finite sign family.
For a one-sided statistic \(T\), use

$$
p=\frac{1+\#\{b:T(\widetilde x_b)\ge T(x)\}}{B+1}.
$$

This is an exact Monte Carlo randomization p-value only when the observed
signal is exchangeable under the declared sign-group action and the sampling
scheme satisfies the randomization-test assumptions. Without that scientific
assumption, report the same quantity as a **surrogate reference tail area** or
stress-test score, not an exact inferential p-value.

Use at least 999 surrogates for a nominal \(10^{-3}\) p-value resolution.
Report the observed statistic, null interval, effect size, corrected p-value,
and every excluded or failed surrogate. Multiple features require a declared
correction or preregistered hierarchy.

Determinism requires:

- a versioned PRNG and seed encoding;
- canonical group order;
- fixed DC behavior;
- exact sign-bit derivation;
- numeric ABI and tolerance receipt;
- input-signal hash;
- per-test configuration hash; and
- result JSON/CSV hashes.

No wall-clock entropy is permitted.

## 9. Recommended null ladder

One null cannot answer every structural question. A useful comparison ladder
is:

| Null | Conditional question |
|---|---|
| Ternary-label permutation | Is the statistic explained by class counts alone? |
| Grouped graph-spectral sign surrogate | Is it explained by the observed graph-power spectrum? |
| Degree-preserving edge rewiring | Does the selected topology matter beyond degrees? |
| Triality/orbit-preserving shuffle | Does within-model orbit alignment matter? |

Only the second row is the Pirondini-style surrogate. The other nulls are
separately authored ETQ stress tests and need independent specifications.

## 10. Relationship to the Tanner modules

The existing Tanner tuning-fork code already supplies most mathematical
prerequisites:

- real symmetric Laplacian construction;
- deterministic cyclic-Jacobi eigenpairs;
- tolerance-qualified eigenspace grouping; and
- invariant projectors for degenerate modes.

It does not yet implement graph-signal transforms, grouped sign generation,
inverse reconstruction, statistics, or finite-sample inference. Adding those
features must not reactivate frame-bin pitch calibration or any root audio
path.

## 11. Claim boundary

Supported wording:

> The graph-spectral surrogate test constructs a topology-aware grouped
> spectral-sign reference family that preserves grouped graph-spectral power
> while altering spectral sign arrangement. Inferential results require the
> declared sign-exchangeability null and remain conditional on the selected
> graph.

Do not claim that null rejection:

- proves the physical existence of ETQ or E8 dynamics;
- validates qutrit or triality ontology;
- selects low/mid/high MIDI bands;
- establishes a preferred acoustic tuning;
- measures QEC performance; or
- replaces a listener study.

For a deterministic constructed model with no empirical input, call the
results **conditional null comparisons** or **stress tests**, not empirical
confirmation.

## 12. References

- Elvira Pirondini, Anna Vybornova, Martina Coscia, and Dimitri Van De Ville,
  “A Spectral Method for Generating Surrogate Graph Signals,” *IEEE Signal
  Processing Letters* 23 (2016), 1275–1278,
  DOI: `10.1109/LSP.2016.2594072`.
- Elvira Pirondini et al., “Network Data on the Statistical Testbench,”
  *IEEE Brain*, 24 January 2017.
- David I. Shuman et al., “The Emerging Field of Signal Processing on Graphs,”
  *IEEE Signal Processing Magazine* 30 (2013), 83–98.
