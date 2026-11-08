# MAT-SPEC-002 v0.1.0 — Conservative interval and sampling controls

MAT-SPEC-002 is an **additive, experimental successor** to the archived
MAT-SPEC-001 v1.0.0 implementation in SONIFICATION PR #22 (merge commit
195b325097cd01f16e9ca909edd95482d4863c27), archived in the MAT-SPEC-001 record at DOI
10.5281/zenodo.24062652. The seven MAT-SPEC-001 runtime artifacts, frozen
mapping, published source bytes and feasibility study are **not modified**.
This successor has **no assigned DOI**.

## Research question

Do pressure-dependent helium excitation differences remain distinguishable
under the *reported error intervals*, and how sensitive are rank/MIDI contour
collisions to a different, mechanically defined wavevector selection?

The original Godfrin et al. source includes seven pressures, 1,050 aligned
wavevectors, 7,118 energy/error pairs and 232 missing pairs. All measurements
are in the low-temperature superfluid regime, not across a phase transition.

### Full-grid interval comparison (QEC / SPECTRAL / GALAXY)

For every two pressures at matched wavevector, form the closed interval
[E - errE, E + errE]. Classify as a_below_b, b_below_a, overlap (including
touching boundaries), or missing. This yields 21 × 1,050 = 22,050
pressure/q comparisons, with missing positions explicitly counted.
Exact rational arithmetic on the published decimal representations avoids
floating threshold drift. *Nonoverlap of reported error intervals is not a
significance test*: the authors' reported errors have not been modeled as a
specific confidence distribution; covariance and systematic errors are unknown.

A streaming reduction uses 128-row tiles, storing only 21 summaries and one
hash state at a time beyond the already materialized MAT-SPEC-001 observations.
The status sequence is domain-separated and SHA-256 committed. Parity tests
replay the same table at tile sizes 1, 128, 137 and 1,050; the counts and
receipts must remain identical. This takes GALAXY's exact streaming/reduce/
discard *method*, not its gravitational physics. It uses SPECTRAL's strict
reference-versus-optimized parity discipline without any data smoothing.

### Metamorphic and invariant controls (QEC / OPT)

Every comparable pair is recomputed under the positive factor-two energy/error
scale and with pressure order reversed. The former must preserve interval
classification; the latter must swap the direction of nonoverlap while retaining
overlap. Any violation fails the audit. The count of comparisons is explicit.

OPT-INV-001 motivates **reuse only after equivalence is established**:
the same comparison witness can account for the common-scale (400 Hz/meV)
representation because positive linear rescaling preserves interval ordering.
No cache of mutable paths, floating approximation, acceleration or claimed
speedup is introduced.

### Bounded uniform-floor sampling (GLUBALL)

GLUBALL-SAMPLING-V1 supplies the **engineering mechanism**
logical(i) = floor(i × 1050 / R), for R = 6, 12, 24, 48.
It uses exact integer indexing, never q interpolation or data-dependent
cherry-picking. Each sampled control reports missing selections, pressures
eligible for complete contour comparison, and exact common-scale / rank /
quantized-MIDI pairwise collisions. Lane i mod 3 is execution metadata only:
it is neither D4 triality nor a physical ternary symmetry.

The original MAT-SPEC-001 authored six-q choice remains untouched and is
**not** silently replaced by uniform-floor sampling.

### Epistemic gates (UFF)

Numerical separation != calibrated statistical discrimination != blinded
listener discrimination != physical phase classification != E8 identification.

- Computational outputs: independently replayable numerical checks and receipts.
- Physical source: processed, attributed superfluid-helium observations.
- Unmeasured: temperature-dependent normal/superfluid classification, observer
  discrimination, independent replication, cobalt-niobate E8 model fitting.
- A domain-separated hash proves neither chronology nor unbiased experimental
  design, and does not authenticate the underlying measurement.

No graph Laplacian or D4 covariant is identified with a helium Hamiltonian.
SPECTRAL filters, GLUBALL knot geometry, GALAXY dynamics and UFF astrophysics
are **not transferred** into material dynamics.

## Reproduction

Python 3.11+, standard library, offline; Linux/POSIX filesystem export.

    uv run --no-project python -m unittest discover -s tests -p 'test_mat_spec*.py' -v
    uv run --no-project python scripts/build_mat_spec_002.py --out dist/mat-spec-002

The output directory must be fresh. Output allowlist:

- contract.json — successor interpretation, source identity and limits
- pressure-pairs.csv — 21 matched-q interval comparison records and stream digests
- sampling.json — four deterministic sampling sensitivity controls
- audit.json — conservation, metamorphic checks and nonclaims
- manifest.json — parent v1 output hashes, successor hashes, implementation identity

All are JSON/CSV. No MIDI is changed and no PCM/WAV/audio samples are generated.
The manifest excludes its own digest. Source or parent contract integrity is
verified by rebuilding the pinned MAT-SPEC-001 ancestor.

## Donor attribution / transfer boundaries

- QSOLKCB/QEC: deterministic invariant, layered observation, fail-closed checks.
- QSOLKCB/OPT: OPT-INV-001, invariant-driven reuse after equivalence checks.
- QSOLKCB/SPECTRAL: SONIFICATION/benchmarks/BOXCAR.md exactness/fallback discipline;
  its numerical smoothing and audio synthesis are intentionally not used.
- QSOLKCB/GALAXY: docs/CPU-MEMORY-WALL.md exact stream/reduce/discard and tile parity.
- QSOLKCB/GLUBALL: docs/SAMPLING.md exact uniform-floor logic and metadata boundary.
- QSOLKCB/UFF: docs/UFF_FORMAL_ASSURANCE_V5.2.md and docs/NONCLAIM_CALIBRATION.md
  separate replay verified software from empirical/physical claims.

The source implementation is independently written against these contracts.
