# ETQ-101: E8-Root-Derived, D4-Triality Qutrit Sonification Model

**A deterministic mathematical model for E8-root-indexed, triality-structured
qutrit sonification.**

[![Tests](https://github.com/QSOLKCB/SONIFICATION/actions/workflows/tests.yml/badge.svg)](https://github.com/QSOLKCB/SONIFICATION/actions/workflows/tests.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)](https://www.python.org/)
[![License: MPL-2.0](https://img.shields.io/badge/License-MPL--2.0-blue.svg)](LICENSE)

SONIFICATION creates DAW-ready musical loops entirely from code and
mathematics. There are no samples, SoundFonts, SF2 files, hidden downloads, or
recorded excitations. Oscillators, modulation, noise-like material, string
excitation, envelopes, rhythm, panning, and mixing are all explicit procedural
functions.

Phase 1 is available both as a Python kernel and as a zero-dependency offline
browser app. Both editions provide additive synthesis, FM synthesis,
Karplus-Strong string modeling, a dark 432 Hz hybrid factory groove,
PCM16/PCM24 WAV export, canonical recipes, fingerprints, manifests, and replay
verification within their documented runtime boundaries.

> This is audible geometry and mathematical composition. It is not a claim
> that E8—or any other mapped structure—is physically present in nature.

## Why this project exists

[SPECTRAL](https://github.com/QSOLKCB/SPECTRAL) is the broader deterministic
sonification and provenance workbench. SONIFICATION complements it by putting
musical usefulness first: short loops, instruments, groove, tuning, layer
building, and later DAW/MIDI workflows.

[QEC](https://github.com/QSOLKCB/QEC) informs the insistence on explicit
contracts, replayable state, deterministic event mappings, and honest claim
boundaries. SONIFICATION does not present classical DSP as quantum computation.

## Offline browser app

The browser edition needs no install, local server, account, upload, or network
connection:

1. Open [`APP/index.html`](APP/index.html) directly in a current desktop browser.
2. Choose a voice, seed, loop length, tuning, sample rate, and WAV depth.
3. Select **Render offline loop**.
4. Play the result locally or download its WAV, manifest, recipe, and
   fingerprint.

Everything used by the app is committed under [`APP/`](APP/): classic local
scripts, bundled SHA-256, procedural DSP, PCM16/PCM24 RIFF packing, canvas
visualizers, and an offline self-test page. There are no `fetch` calls, remote
fonts, CDN assets, service workers, analytics, or upload paths.

Open [`APP/tests/index.html`](APP/tests/index.html) to run the browser checks, or
run the same engine suite with Node (no packages required):

```bash
node APP/tests/run.cjs
node APP/tests/dom-smoke.cjs
```

The browser ABI is `qsol-imc.browser-float64/v1`. Same inputs replay to the same
WAV bytes in the same app version and browser runtime. Browser and Python WAV
hashes are not promised to match because JavaScript engines and NumPy may
evaluate transcendental DSP differently. See
[`APP/README.md`](APP/README.md) for the exact boundary.

## Python kernel quick start

Requires Python 3.11 or newer.

```bash
git clone https://github.com/QSOLKCB/SONIFICATION.git
cd SONIFICATION
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Render the default four-bar, 128 BPM, 432 Hz hybrid loop:

```bash
python -m sonification generate
```

The default command writes a 24-bit WAV and its integrity-bound manifest to
`artifacts/`. The output stem contains the first twelve characters of the WAV
SHA-256, so exact replays are immediately recognizable.

Render all Phase 1 artifact types:

```bash
python -m sonification generate \
  --voice hybrid \
  --bpm 128 \
  --bars 8 \
  --a4 432 \
  --seed 2026 \
  --sample-rate 48000 \
  --bit-depth 24 \
  --peak-dbfs -6 \
  --export all \
  --output-dir artifacts \
  --name e8_foundry_seed
```

Phase 1 voice choices are:

ETQ-101 v1.0.0 formalizes an E8-root-derived graph model with an embedded
order-three D4 triality, 33 orbit-labelled direct-sum qutrit blocks plus two
fixed singlets, the ternary-curvature observable `[1, -2, 1]`, qutrit labels
`[0, 1, 2]`, phase `theta = pi/2`, optional golden-ratio modulation, and a
declared 432 Hz reference scale.

The construction is exact, deterministic, machine-verifiable, and explicit
about which parts are mathematical consequences and which are authored
sonification choices.

## Model at a glance

| Element | ETQ-101 definition |
|---|---|
| E8 | Exact standard set of 240 roots in doubled integer coordinates |
| Triality | Explicit order-three D4 action preserving the E8 root set |
| 101-state sector | Canonical triality-closed root-indexed graph space |
| Ternary curvature | `D3 = diag(1, -2, 1)` |
| Qutrit logic | Computational labels `[0, 1, 2]` with generalized Pauli operators `X3` and `Z3` |
| Phase | `theta = pi/2` |
| Golden ratio | `varphi = (1 + sqrt(5)) / 2`, kept distinct from the phase |
| Reference scale | `f0 = 432 Hz`, declared rather than derived from E8 |

The compact state space is

$$
\boxed{
\mathcal H_{101}
=\mathbb C^2
\oplus
\left(\mathbb C^{33}\otimes\mathbb C^3\right).
}
$$

This resolves the central arithmetic constraint: 101 is not divisible by
three, so the space cannot globally factor as `something x qutrit`. Instead it
contains **33 complete qutrit/triality orbits and two fixed singlets**.

The selected E8 roots label formal orthonormal graph states in
`ell^2(S_101)`. They are not claimed to be 101 linearly independent vectors in
R8 or a 101-dimensional representation of E8. The 33 qutrit blocks form a
direct sum, not 33 independent tensor-factor qutrits.

If every mode must carry a full qutrit, the model provides the tensor extension

$$
\mathcal H_{303}=\mathcal H_{101}\otimes\mathbb C^3.
$$

## Core qutrit and SCL algebra

For `zeta = exp(2 pi i / 3)`, the generalized Pauli operators satisfy

$$
X_3|q\rangle=|q+1\!\!\pmod 3\rangle,
\qquad
Z_3|q\rangle=\zeta^q|q\rangle,
$$

and

$$
X_3^3=Z_3^3=I,
\qquad
Z_3X_3=\zeta X_3Z_3.
$$

The SCL operator is

$$
D_3=\operatorname{diag}(1,-2,1),
$$

and the phase-twisted cycle

$$
F_3=X_3e^{-i\theta D_3}
$$

obeys `F3^3 = I` for every `theta`, including `theta = pi/2`, because the
accumulated three-step curvature is `1 - 2 + 1 = 0`.

## Dimensionally correct dynamics

Structural terms are assembled into a dimensionless Hermitian generator `K`.
The physical time scale is introduced only through

$$
\boxed{
H=\hbar\Omega_0K,
\qquad
\Omega_0=2\pi(432)\ \mathrm{s}^{-1}.
}
$$

Closed evolution is therefore

$$
\dot\rho=-i\Omega_0[K,\rho].
$$

This replaces the original scalar expression, which mixed a dimensionless
quantity with a term measured in inverse seconds. Only `1 - 2 + 1` vanishes in
that expression; the normalized trace term does not.

## ETQ-101 resources

| Resource | Purpose |
|---|---|
| [Mathematical model](docs/MATHEMATICAL_MODEL.md) | Normative construction, operators, dynamics, observables, and 303-state extension |
| [Sonification mapping](docs/SONIFICATION_MAPPING.md) | Static generator-spectrum mapping and deterministic render contract |
| [Claim boundaries](docs/CLAIM_BOUNDARIES.md) | Exact results, authored choices, and excluded physical claims |
| [Canonical contract](examples/etq-101.canonical.json) | Fixed v1.0.0 parameters and regression hashes |
| [JSON Schema](spec/etq-101.schema.json) | Machine-readable canonical schema |
| [Reference construction](src/etq-model.mjs) | Dependency-free E8, triality, graph, and qutrit implementation |
| [Model tests](tests/etq-model.test.mjs) | Algebraic, graph, phase, hash, and normalization tests |
| [Verifier](scripts/verify.mjs) | Canonical-contract and fixture verification |

## Canonical deterministic fixtures

| Fixture | Value |
|---|---:|
| Standard E8 roots | 240 |
| Triality-fixed roots | 12 |
| Triality three-cycles | 76 |
| Selected states | 101 |
| Selected qutrit orbits | 33 |
| Selected graph edges | 1,687 |
| Selected graph degree range | 22-55 |
| Basis SHA-256 | `97cfd1f087745422fd66d3640c7b86c3209593c4b53741018c08a5e9cdb15f6f` |
| Adjacency SHA-256 | `29ae0af5b1090c9de30f1efc25789060fb1791eb175d2afcd6888847f7fe6324` |
| Contract SHA-256 | `6577443641be02609c045ee0afc423c2be37bbe5ae83f671cbae304c0e9cb930` |

## Verify the model

The reference implementation has no runtime dependencies. Node.js 20 or newer
is used for its test runner and SHA-256 verification.

```bash
npm test
npm run verify
```

The verifier reconstructs the E8 roots, triality orbits, 101 selected labels,
and adjacency matrix from first principles, then checks the fixed fields and
cross-field relations in the canonical contract.

## Sonification status

The ETQ-101 static generator-spectrum PCM renderer is formally specified in
[the mapping document](docs/SONIFICATION_MAPPING.md), but is intentionally
marked **not yet implemented**. This repository does not claim an ETQ-101 WAV
artifact that it does not ship.

The repository also contains a separate, complete Python synthesis laboratory
for deterministic mathematical loop creation. It implements additive, FM, and
Karplus-Strong synthesis, canonical WAV export, manifests, and exact replay
verification.

**[Open the music-first synthesis laboratory ->](sonification/README.md)**

## Scientific boundary

A precise description of ETQ-101 is:

> A deterministic 101-dimensional E8-root-indexed graph truncation closed
> under an embedded D4 triality, with direct-sum qutrit blocks and an explicit
> sonification map.

ETQ-101 does **not** claim:

- a 101-dimensional representation of E8;
- that triality is an intrinsic outer symmetry of E8 rather than D4/Spin(8);
- that 432 Hz is physically selected by E8;
- that a mathematical qutrit simulation implies qutrit hardware; or
- that sonification validates a physical theory.

See [Claim Boundaries](docs/CLAIM_BOUNDARIES.md) for the complete distinction
between exact results, model definitions, sonification choices, and excluded
claims.

## Authorship, citation, and license

Created by **Trent Slade / QSOL-IMC**. Preferred citation metadata is provided
in [CITATION.cff](CITATION.cff), with archival metadata in
[.zenodo.json](.zenodo.json).

Licensed under the [Mozilla Public License 2.0](LICENSE). Covered source files
and modifications must remain available under MPL-2.0 when distributed, and
copyright and licence notices may not be removed or altered. See
[NOTICE](NOTICE), [AUTHORS.md](AUTHORS.md),
[CONTRIBUTING.md](CONTRIBUTING.md), and
[Rights and Archiving](docs/RIGHTS_AND_ARCHIVING.md).
