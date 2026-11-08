# SONIFICATION-MATERIALS-FEASIBILITY-001

**Measured helium spectra, symbolic sonification and the scope of E8 claims**

Exploratory note, 9 November 2026. Prepared for Trent Slade / QSOL-IMC with
ChatGPT/Codex assistance. This is a standalone feasibility audit, not a new
SONIFICATION release, an independently peer-reviewed paper, or a published DOI.

## Finding

SONIFICATION can support a defensible materials-sonification extension if a
physical-data adapter and an explicit receiver contract are added. Its existing
ETQ traversal and D4 covariant construction do not themselves predict the
properties of a material. The new adapter must begin with measured observables
or a declared physical model and preserve the features being investigated.

This note tests one small part of that proposal using published superfluid
helium data. It does not implement the adapter in the repository, generate
audio, recruit listeners, classify physical phases, or establish an E8 theory
of everything. Repository fixes are being handled separately by the user.

## Video reconnaissance

The requested Veritasium video is *I finally saw quantum mechanics with my own
eyes... (It's spookier than I expected)*:
https://www.youtube.com/watch?v=KfODG5REyss

The cloud browser exposed its expanded description and chapters, including
superfluidity at 28:41, Bose-Einstein condensates at 36:15, the superfluid fountain
at 46:20, Landau's phonon theory at 47:46, and helium freezing at 58:32.
Playback remained at 0:00; the transcript panel stalled, and transcript export
reported that no transcript was available. This is not a claim to have watched
or transcribed the full video. Physics claims below rely on primary literature.

## Executed experiment with published data

Source: H. Godfrin et al., *The dispersion relation of Landau elementary
excitations and the thermodynamic properties of superfluid 4He*, Physical
Review B 103, 104516 (2021), arXiv:2012.09067v1.

- Paper: https://arxiv.org/abs/2012.09067v1
- DOI: https://doi.org/10.1103/PhysRevB.103.104516
- Authors' data: https://arxiv.org/src/2012.09067v1/anc/DispersionAllPressures.txt
- Original data SHA-256: `15a56ccdd2f681de0e1d3d1517dc4641732dbef4e2d6153591154cc4b039b50a`
- Original encoding: UTF-16 with BOM. Original bytes are retained.

The table has seven pressures, 1,050 wavevector positions, 7,118 valid
energy/error pairs and 232 missing pairs. The paper describes measurements
below 100 mK. All these conditions are in the low-temperature superfluid
regime; this dataset does not by itself test the transition to normal helium.
The table contains processed experimental energies and reported errors, not
raw neutron detector counts and not new measurements made for this note.

The experimental mapping is `frequency_target_Hz = 400 * energy_meV`.
The factor 400 Hz/meV is authored, fixed across all pressures, and invertible.
It is not a naturally implied acoustic frequency or the unscaled quantum
transition frequency. Energy errors are multiplied by the same factor.

Using exact rational arithmetic on the published decimal strings, the script
passes all **7,118 energy roundtrips** and **7,118 ratios-to-reference checks**.
Exact manipulation of decimal representations does not eliminate measurement
uncertainty. These checks validate the numerical mapping only; there has been
no MIDI quantization, synthesizer validation or listening test.

For a comparison with the current D4-style rank rule, six wavevectors were
selected in advance of the rank calculation: 0.15, 0.50, 1.10, 1.60, 1.90 and
2.10 inverse angstroms. Their six energies were mapped to ranks minus half the
number of distinct values, rounded down. The resulting groups are:

| Pressures (bar) | Six rank offsets |
|---|---|
| 0, 0.51, 1.02, 2.01 | -3, -1, 2, 1, -2, 0 |
| 5.01, 10.01 | -3, 0, 2, 1, -2, -1 |
| 24.08 | -3, 0, 2, 1, -1, -2 |

Seven distinct tabulated six-point profiles therefore yield three rank
contours. This is a concrete information-loss example for that sampling and
rule. It is not a statement that complete helium spectra have only three
classes, nor that these labels are statistically distinguishable by listeners.
Uncertainty-driven rank swaps have not been analysed. These are not canonical
D4 covariant events: the ordering rule is reused as an explicit comparison.

The plot shows selected pressure curves, reported error bands and the common
frequency-target scale. Lines between data points are guides to the eye.
Windowed grid minima recorded in results.json are not fitted roton parameters.

## Physical quantities to map

| System | Suitable input | Scientific question |
|---|---|---|
| Ordinary solids | Measured or computed phonon frequencies, mode weights and linewidths with geometry and boundary conditions | Are mode shifts, gaps or damping changes retained? |
| Superfluid helium | Dispersion energy versus wavevector, dynamic structure factor, pressure and temperature | Are the phonon branch, maxon, roton minimum and their changes retained? |
| Superfluid transition | Temperature series plus an independently measured phase diagnostic such as superfluid fraction or second-sound response | Can the mapping expose an established transition in held-out measurements? |
| Quantum critical magnet | Spin-excitation spectrum versus field and temperature | Are model-predicted ratios and field dependence preserved? |
| Zero-temperature limit | A specified Hamiltonian and its ground-state response | Which predicted observables survive as temperature tends to zero? |

These are proposed experiments, not implemented capabilities or established
results of this note. Condensate fraction and superfluid fraction must not be
used as interchangeable input labels. Zero temperature does not imply the
absence of quantum fluctuations; a ground state can have an excitation
spectrum. Finite-temperature measurements and zero-temperature calculations
need distinct provenance. See NIST's discussion of zero-point motion:
https://www.nist.gov/si-redefinition/kelvin-introduction

## The useful E8 connection

R. Coldea et al., *Quantum criticality in an Ising chain: experimental evidence
for emergent E8 symmetry*, Science 327, 177 (2010), investigate cobalt niobate
near a magnetic critical point. Two low-energy modes approach the golden-ratio
relation predicted by the E8 model. This is a specific condensed-matter
application, distinct from claiming that E8 contains a theory of everything.

https://arxiv.org/abs/1103.3694
https://doi.org/10.1126/science.1180085

That experiment supplies a useful positive benchmark for a future physical
adapter. A ratio-preserving map retains the predicted ratio. A rank-only map
cannot: any two unequal positive energies have the same two rank classes.
Ordinary equal-tempered note rounding introduces another loss. The theoretical
golden ratio corresponds to about 833.0903 cents; rounding its interval to eight
semitones gives 800 cents, an error of -33.0903 cents. This numerical example is
not a reanalysis of the measured cobalt-niobate data.

A golden ratio by itself is not an identification of E8. The model, additional
spectral structure, response weights, field dependence and alternative
explanations must be assessed. The arbitrary eigenvalues of an E8-derived
selected-root graph are not the excitation energies of that magnet.

## The control paper and visualization site

The supplied tag archive belongs to J. Gregory Moxness's visualization and
model project. Its E8/H4 matrices and geometrical constructions can be assessed
as mathematics in their own right. A material's physical symmetry requires an
identified action on states or observables and testable dynamics; a geometric
resemblance or similar musical contour cannot establish that identification.

https://theoryofeverything.org/theToE/tags/e8/
https://theoryofeverything.org/theToE/author/

Jacques Distler and Skip Garibaldi's *There is no "Theory of Everything" inside
E8* is a representation-theoretic obstruction for a specified class of
embeddings of Lorentz and internal gauge symmetry into real or complex E8.
Their conditions include a compact internal group centralizing the Lorentz
group and restrictions on spin content; the required chiral fermion
representation cannot be obtained. The conclusion is not a ban on every
physical or mathematical use of E8. Sonification changes neither those
representations nor the obstruction. A proposal outside the theorem must
identify the changed assumption and independently recover the required physics.

https://arxiv.org/abs/0905.2658v3
https://doi.org/10.1007/s00220-010-1006-y

This is a theoretical consistency control. An experimental sonification study
also needs numerical and perceptual controls.

## Proposed next implementation

Add a separately versioned physical-data profile, provisionally MAT-SPEC-001,
with sample identity, units, temperature, pressure/field, wavevector grid,
uncertainties, source hashes and a mapping contract. Start with helium's
pressure dependence; add an independent temperature-series dataset before
making a normal-versus-superfluid claim. Keep a single physical reference
scale across conditions. Preserve zero-energy events explicitly instead of
silently taking logarithms of zero or assigning an arbitrary pitched note.

Compare three receivers: rank contour, common-scale frequency targets and a
declared quantized MIDI implementation. Audit ratio error, missing-data
handling and decoding before asking whether listeners can distinguish them.
Use matched controls: shuffled wavevector-energy associations, alternate
non-E8 spectra, known scale changes and blinded presentation. Physical-model
assessment, mapping verification and listener discrimination remain separate.

The existing five order-zero D4 rows can remain mathematical invariance
controls. They are not measurements of a material phase. The SONIFICATION
revision consulted was `5a9af7876dac3f55839f2a23d7655d70c2158990`; the prior
SONIFICATION-SPECTRA-001 study remains pinned to the separate archived tag
`d4-tia-v2.0.0`, commit `7aa6df165d0ad70297365dbf0d69072634ed4314`.
No repository files or published records were changed by this work.

The objects compared by the earlier study must retain their distinct meanings:

| Object | What it describes | What a materials extension must establish |
|---|---|---|
| Traversal spectrum | Eigenvalues of the finite traversal operator | Whether an independently defined physical process has this operator |
| Graph spectrum | Eigenvalues of the selected-root graph Laplacian | A justified dynamical matrix, masses and couplings before interpreting graph modes as vibrations |
| D4 covariant behaviour | Algebraic responses of the declared covariants across the six representatives | An identified physical symmetry action, rather than a similarity of names or contours |
| Material excitation spectrum | Measured response energies, weights and widths, or a specified Hamiltonian's predictions | Which features the chosen mapping preserves, with uncertainty and experimental conditions |

Even an exactly invertible energy-to-frequency map preserves only the encoded
observable. It does not encode the entire physical state. For a future claim of
covariance, define both a physical transformation g and its output action rho(g),
then test S(g.x) = rho(g).S(x). That is a proposed condition for the new map S,
not a result established by this audit. Wavevector-to-time ordering, response
weights, damping and the playback instrument also require declared mappings.

## Reproduce and attribution

`uv run --no-project python analyze.py` runs the standard-library audit and
regenerates results.json. The optional plot requires NumPy and Matplotlib;
it was produced with Python 3.12.14, NumPy 2.3.5 and Matplotlib 3.10.8.
No Node dependencies or network requests occur during the audit.

Original source data retain Godfrin and coauthors' attribution and the arXiv
submission's CC BY 4.0 licence. New analysis code follows MPL-2.0, as indicated
in analyze.py and plot.py; the explanatory note and plot are offered under
CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). The original data file
is unmodified; results.json and the figure are derived from it using the
declared mappings. LICENSE-MPL-2.0.txt contains the code licence. SHA256SUMS
covers every other file in the bundle. The audit was rerun and results.json
matched byte for byte.
Hashes establish byte identity. They do not establish physical truth.
