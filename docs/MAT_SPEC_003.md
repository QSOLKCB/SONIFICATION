# MAT-SPEC-003 v0.1.0 — Physical Mode Discrimination

This is an independently versioned **symbolic and observational** research
profile following MAT-SPEC-001 v1.0.0 and MAT-SPEC-002 v0.1.0.
The parent DOI is **10.5281/zenodo.24062652**, belonging to the MAT-SPEC-001
record. MAT-SPEC-003 has no assigned DOI. It neither changes the previous
published source data nor rewrites any existing parent runtime artifacts.

## Scientific question and source

The dispersion of superfluid helium-4 has a low-q phonon region, a broad
maxon maximum around 1 inverse angstrom and a roton minimum near 2 inverse
angstroms. We ask whether *declared finite-window feature descriptors* differ
between reported pressures and whether their distinctions survive the exact,
rank and 12-tone equal-temperament symbolic receivers.

Reference: Godfrin et al., **Physical Review B 103, 104516 (2021)**,
DOI 10.1103/PhysRevB.103.104516 (arXiv:2012.09067v1).
Supplementary context: NIST Collective Excitations of Superfluid Helium (2019),
which describes phonons below q ~0.7, maxons around q ~1.1 and rotons near
the minimum.

These are processed neutron-scattering dispersion energies and reported errors
at seven pressures, all at low temperature in the superfluid regime.
They contain neither a normal-state temperature series nor the dynamical
response weight/linewidth needed for fitted excitation lifetimes. No claim of
a temperature-driven phase transition or an E8 identification follows.

## Declared descriptor windows (q in inverse angstrom)

| Descriptor | Primary window | Alternate narrower window |
|---|---|---|
| Phonon-region unweighted, through-origin slope | 0.150–0.450 | 0.150–0.300 |
| Maxon-like nominal maximum | 0.750–1.400 | 0.900–1.250 |
| Roton-like nominal minimum | 1.600–2.150 | 1.800–2.050 |

The primary and alternate windows are **authored controls** in
`spec/mat-spec-003.v0.1.json`. They are not inferred from
the dataset and cannot silently change without violating the code/contract
identity test. The word "mode" is a convenient label for a *finite-grid
descriptor*, not a Hamiltonian eigenmode or a fitted quasiparticle parameter.

For phonon window points (q_i, E_i, err_i), use an unweighted
zero-intercept slope proxy:

    s = sum(q_i E_i) / sum(q_i^2)
    d = sum(q_i err_i) / sum(q_i^2)
    slope interval = [s - d, s + d] in meV·angstrom

This is **not** the physical q→0 sound-speed limit or an independent estimate
of sound velocity. The reported-error interval is a deterministic box bound
with no covariance or probability assumption, not a confidence interval.

For the maxon candidate, the finite-grid energy bounds are:

    L_max = max_i (E_i - err_i)
    U_max = max_i (E_i + err_i)

For the roton candidate:

    L_min = min_i (E_i - err_i)
    U_min = min_i (E_i + err_i)

The nominal extremum uses the observed published decimal energies.
Ties select the smallest q. A q is a **possible** extremum position when its
reported interval could attain the extremum. A **unique certified q** requires
strict separation from every other observed position and *no missing rows in
the declared window*. Positions are not interpolated or fitted.
If the nominal optimum is at a window edge, the result explicitly says so.

If any row in a window is missing, the observed-only descriptor is marked
PARTIAL and is **not eligible** for cross-pressure interval comparisons.
A wholly missing window is MISSING. A complete window is COMPLETE.

## Physical and symbolic controls

The 21 pressure pairs are compared for each of three descriptors: **63**
declared comparisons, each classified as strictly a_below_b, strictly
b_below_a, closed-interval overlap, or INELIGIBLE. Touching intervals overlap.
Nonoverlap is *not a significance test*, and overlap does not prove identity.

For each pressure with complete maxon/roton windows:
- report the maxon-minus-roton energy gap and its interval;
- conservatively bound the ratio E_max/E_rot when the roton lower bound >0;
- compare nominal maxon/roton *energy* tuples via exact 400 Hz/meV targets,
  two-value dense rank offsets and ordinary nearest 12-TET MIDI note numbers.

The phonon *slope* has different units, so it is never fed into the energy
receiver as if it were a measured energy. Mode positions q are preserved
separately; the symbolic two-note receiver does **not** encode them.
No MIDI file, waveform, timing or audition is produced by MAT-SPEC-003.

Alternate narrower windows are a sensitivity control, *not an independent
replication*. Positive multiplication of both E and errE by two must double
each descriptor/bound while preserving q candidates and completeness. Synthetic
tests include missing observations, exact interval contact, duplicate extrema,
negative energy/scale rejection and q-energy permutation. None is new physics.

## Determinism, provenance and boundaries

MAT-SPEC-003 first invokes MAT-SPEC-002 to validate the original MAT-SPEC-001
seven-output SHA-256 baseline and the MAT-SPEC-002 receipt. It additionally
requires equality against the five explicit MAT-SPEC-002 output SHA-256
pins captured from merged-main CI. It also records its own frozen contract,
implementation and symbolic output files. SHA-256 is an identity witness, not
a proof of measurement correctness, audit chronology or scientific truth.

All runtime outputs are ASCII JSON/CSV; standard-library Python 3.11+;
no network and no root waveform buffers. POSIX anchored no-follow output
requires a fresh destination; unsafe file destinations and unsupported audio
are rejected. The six outputs are:

- `contract.json` — frozen descriptor settings and claim scope;
- `features.csv` — 21 declared (pressure, descriptor) summaries;
- `feature-intervals.json` — candidate q sets and interval bounds;
- `pressure-discrimination.csv` — 63 pressure/descriptor comparisons;
- `controls.json` — alternative windows, feature ratios, receiver collisions, nonclaims;
- `manifest.json` — ancestor, parent, implementation and output SHA-256 receipts.

Run:

```sh
uv run --no-project python -m unittest discover -s tests -p 'test_mat_spec*.py' -v
uv run --no-project python scripts/build_mat_spec_003.py --out dist/mat-spec-003
```

## Scientific gates and next steps

- **Reproducible numerical descriptor:** tested in CI, check actual job result.
- **Systematic/fit uncertainties:** not modeled; reported ±errE only.
- **Hydrodynamic sound-speed extrapolation:** not performed.
- **Independent temperature/phase data:** absent.
- **Blinded listener discrimination:** not tested.
- **Cobalt-niobate E8 spectral fitting:** not performed.
- **Universal physical model / theory of everything:** not claimed.

A subsequent phase requires separately attributed temperature-series observations
and an independent superfluid-fraction/second-sound diagnostic before even
attempting a normal-to-superfluid phase classifier. Measured cobalt-niobate
response curves and explicit alternative models would be needed for an E8 test.
