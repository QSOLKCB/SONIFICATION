# QSOL SONIFICATION

**Music-first deterministic sonification laboratory for mathematical loop creation.**

[![Tests](https://github.com/QSOLKCB/SONIFICATION/actions/workflows/tests.yml/badge.svg)](https://github.com/QSOLKCB/SONIFICATION/actions/workflows/tests.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)](https://www.python.org/)
[![License: MPL-2.0](https://img.shields.io/badge/License-MPL--2.0-blue.svg)](LICENSE)

SONIFICATION creates DAW-ready musical loops entirely from code and
mathematics. There are no samples, SoundFonts, SF2 files, hidden downloads, or
recorded excitations. Oscillators, modulation, noise-like material, string
excitation, envelopes, rhythm, panning, and mixing are all explicit procedural
functions.

Phase 1 is a complete, runnable deterministic kernel: additive synthesis, FM
synthesis, Karplus-Strong string modeling, a dark 432 Hz hybrid factory groove,
PCM16/PCM24 WAV export, canonical recipes, fingerprints, manifests, and replay
verification.

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

## ETQ-101 core mathematical model

The repository now includes **ETQ-101 v1.0.0**, a formal E8-root-derived
sonification model with an embedded order-three D4 triality, 33 orbit-labelled
direct-sum qutrit blocks plus two fixed singlets, the ternary-curvature
observable `[1, -2, 1]`, qutrit labels `[0, 1, 2]`, phase `theta = pi/2`,
golden-ratio modulation, and a declared 432 Hz reference scale.

The 101 selected E8 roots are graph labels for formal orthonormal states in
`ell^2(S_101)`; they are not claimed to be 101 independent vectors in R8 or a
101-dimensional representation of E8. The 33 qutrit blocks form a direct sum,
not 33 independent tensor-factor qutrits.

| ETQ-101 resource | Purpose |
|---|---|
| [Mathematical model](docs/MATHEMATICAL_MODEL.md) | Normative construction, operators, dynamics, and 303-state extension |
| [Sonification mapping](docs/SONIFICATION_MAPPING.md) | Static generator-spectrum mapping and deterministic render contract |
| [Claim boundaries](docs/CLAIM_BOUNDARIES.md) | Exact results, authored choices, and excluded physical claims |
| [Canonical contract](examples/etq-101.canonical.json) | Fixed v1.0.0 parameters and regression hashes |
| [JSON Schema](spec/etq-101.schema.json) | Exact machine-readable canonical schema |
| [Reference construction](src/etq-model.mjs) | Dependency-free E8/triality/qutrit implementation |

The static PCM renderer is specified but intentionally marked not yet
implemented; the repository does not claim a WAV artifact that it does not
ship. Verify the implemented ETQ algebra, graph, schema, and hashes with:

```bash
npm test
npm run verify
```

## Phase 1 quick start

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

- `hybrid` — FM bass, harmonic-glass additive voice, and deterministic wire;
- `additive` — guard-banded harmonic partial synthesis;
- `fm` — oversampled two-operator FM with deterministic FIR decimation;
- `karplus` — fractional-delay Karplus-Strong with mathematical excitation.

`--name` changes filenames only. It never enters render identity. Use
`--verbose` to expose track-level render logging.

## Verify a render

The manifest contains every identity-bearing parameter and the event plan.
Check its internal hash chain, re-render it, and compare exact output:

```bash
python -m sonification verify artifacts/e8_foundry_seed.manifest.json
```

A successful replay reports:

```text
PASS verified <64-character WAV SHA-256>
```

Verification fails closed if the manifest core, recipe, runtime contract, or
re-rendered WAV identity differs.

Named artifacts are not overwritten by default. Add `--force` only when you
intend to atomically replace files with the same names.

## Python API

```python
from pathlib import Path

from sonification.config import LoopConfig
from sonification.core.provenance import canonical_json_bytes
from sonification.renderer import render_loop

config = LoopConfig(
    tempo_bpm=128.0,
    bars=4,
    sample_rate=48_000,
    bit_depth=24,
    tuning_a4_hz=432.0,
    seed=0x2026,
    voice_mode="hybrid",
)
result = render_loop(config)

Path("loop.wav").write_bytes(result.wav_bytes)
Path("loop.manifest.json").write_bytes(canonical_json_bytes(result.manifest))
print(result.wav_sha256)
```

Every public instrument is also independently usable:

```python
from sonification.core.synthesis import KarplusStrong

pluck = KarplusStrong().synthesize(
    frequency_hz=108.0,
    duration_seconds=0.5,
    velocity=0.8,
    sample_rate=48_000,
    seed=42,
)
```

## What Phase 1 actually synthesizes

### Additive voice

The additive instrument sums an explicit partial set:

```text
x(t) = envelope(t) * sum_k a_k sin(2 pi f r_k t + phase_k)
```

Partials outside the configured Nyquist guard band are dropped. Seed-derived
phases give each event a reproducible onset without accessing global entropy.

### FM voice

The FM instrument uses a bounded two-operator phase equation:

```text
x(t) = envelope(t) * sin(2 pi f_c t + I(t) sin(2 pi f_m t + phi_m) + phi_c)
```

It renders at a fixed oversampling factor, bounds deviation against the
internal Nyquist guard, applies a versioned windowed-sinc FIR, and decimates to
the requested rate.

### Karplus-Strong wire

The string model uses a fractional delay, stable feedback below unity, a
brightness-weighted two-point loop filter, pick-position comb, and DC blocker.
Its excitation is generated from indexed SplitMix64 values and mathematical
tones—not from a stored pluck, noise sample, or external file.

### Loop construction

Events are measured in quarter-note beats and converted into integer frame
positions. Release tails are folded into the loop buffer circularly. The tail
of the last event therefore becomes the mathematically correct contribution at
the beginning of the next repetition instead of being silently truncated.

The Phase 1 patterns are deliberately explicit musical fixtures. Phi,
Fibonacci, Euclidean, qutrit, attractor, cellular-automata, and E8-driven rhythm
generation arrive behind the same event contract in later phases.

## Determinism and provenance

Phase 1 uses `sonification.float64-numpy/v1`.

```text
same SONIFICATION version and recorded Python/NumPy/OS/machine identity
+ same normalized parameters and event plan
+ same unsigned 64-bit seed
= same PCM, WAV, hashes, fingerprint, contract, and manifest
```

The renderer never places timestamps, output paths, filenames, playback state,
audio devices, process IDs, or global random state in the identity path.
Unsigned 64-bit seeds are stored as fixed-width hexadecimal strings so no bits
are lost when a manifest crosses into JavaScript.

Identity is domain-separated:

```text
SONIFICATION/RECIPE/v1\0
SONIFICATION/FINGERPRINT/v1\0
SONIFICATION/CONTRACT/v1\0
SONIFICATION/MANIFEST-CORE/v1\0
```

The chain is acyclic:

```text
configuration + event plan + instrument contracts
  -> recipe
  -> float64 render
  -> explicit PCM quantization + canonical WAV
  -> fingerprint
  -> observation contract
  -> manifest core
  -> manifest-core receipt
```

These unkeyed hashes establish integrity and internal consistency; they are not
digital signatures and do not prove who created an artifact. The manifest does
not pretend to contain an ordinary hash of all its own final
bytes. See [the determinism contract](docs/DETERMINISM.md) for exact scope and
cross-runtime limits.

## Exported artifacts

| Artifact | Purpose |
|---|---|
| `*.wav` | Mono/stereo little-endian PCM16 or PCM24 audio; Phase 1 composer exports stereo. |
| `*.manifest.json` | Complete recipe, fingerprint, render contract, lineage, claim boundary, and manifest-core receipt. |
| `*.recipe.json` | Identity-bearing render inputs without observations. |
| `*.fingerprint.json` | PCM/WAV hashes, level observations, stereo correlation, RMS envelope, and chunk hashes. |

JSON is UTF-8, key-sorted, compact, finite-only, and newline-terminated.

## Current repository tree

```text
SONIFICATION/
├── .github/workflows/tests.yml
├── docs/
│   ├── CLAIM_BOUNDARIES.md
│   ├── DETERMINISM.md
│   ├── MATHEMATICAL_MODEL.md
│   ├── RIGHTS_AND_ARCHIVING.md
│   ├── ROADMAP.md
│   ├── SCIENTIFIC_BOUNDARIES.md
│   └── SONIFICATION_MAPPING.md
├── examples/
│   ├── etq-101.canonical.json
│   └── generate_basic_loop.py
├── sonification/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── composition.py
│   ├── config.py
│   ├── renderer.py
│   └── core/
│       ├── audio.py
│       ├── provenance.py
│       ├── tuning.py
│       ├── math/
│       │   ├── base.py
│       │   ├── constants.py
│       │   ├── prng.py
│       │   └── sources.py
│       ├── sequencing/
│       │   ├── base.py
│       │   ├── events.py
│       │   └── grid.py
│       └── synthesis/
│           ├── additive.py
│           ├── base.py
│           ├── envelopes.py
│           ├── fm.py
│           ├── karplus_strong.py
│           └── oscillators.py
├── tests/
│   ├── conftest.py
│   ├── test_audio.py
│   ├── test_cli.py
│   ├── test_config.py
│   ├── test_prng_and_sources.py
│   ├── test_provenance.py
│   ├── test_renderer.py
│   ├── etq-model.test.mjs
│   └── test_synthesis.py
├── scripts/
│   └── verify.mjs
├── spec/
│   └── etq-101.schema.json
├── src/
│   └── etq-model.mjs
├── .zenodo.json
├── AUTHORS.md
├── CHANGELOG.md
├── CITATION.cff
├── CONTRIBUTING.md
├── LICENSE
├── NOTICE
├── package.json
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

`__init__.py` files are omitted from the diagram where they add no visual
information.

## Complete proposed mature tree

This is the intended architecture through Phase 4. Items marked **later** are
design commitments, not claims that empty placeholder modules already exist.

```text
SONIFICATION/
├── sonification/
│   ├── core/
│   │   ├── math/
│   │   │   ├── e8.py                 # later: exact 240-root registry
│   │   │   ├── projections.py        # later: 2D/3D/4D/custom maps
│   │   │   ├── triality.py           # later
│   │   │   ├── sequences.py          # later: Phi/Fibonacci/primes/Collatz
│   │   │   ├── attractors.py         # later: fixed-step dynamical systems
│   │   │   ├── cellular.py           # later: cellular automata
│   │   │   ├── lsystems.py           # later
│   │   │   └── expressions.py        # later: restricted expression AST
│   │   ├── synthesis/
│   │   │   ├── additive.py
│   │   │   ├── fm.py
│   │   │   ├── karplus_strong.py
│   │   │   ├── virtual_analog.py     # later
│   │   │   ├── modal.py              # later: drums/metal/membranes
│   │   │   ├── waveguide.py          # later
│   │   │   ├── filters.py            # later
│   │   │   └── effects.py            # later
│   │   ├── sequencing/
│   │   │   ├── events.py
│   │   │   ├── euclidean.py          # later
│   │   │   ├── polyrhythm.py         # later
│   │   │   ├── attractor_rhythm.py   # later
│   │   │   └── qutrit.py             # later
│   │   ├── audio.py
│   │   ├── composer.py               # later: general multi-track graph
│   │   ├── mixer.py                  # later
│   │   ├── midi.py                   # later
│   │   ├── provenance.py
│   │   └── tuning.py
│   ├── lab/
│   │   ├── app.py                    # later: Gradio laboratory
│   │   ├── cache.py                  # later
│   │   ├── transport.py              # later
│   │   └── visualizers.py            # later
│   ├── presets/
│   │   ├── schema.json               # later
│   │   ├── e8_industrial_groove.json # later
│   │   └── phi_fibonacci_wire.json   # later
│   ├── cli.py
│   ├── composition.py
│   ├── config.py
│   └── renderer.py
├── examples/
│   ├── generate_basic_loop.py
│   ├── custom_instrument.py           # later
│   ├── qec_event_mapping.py           # later
│   └── batch_render.py                # later
├── tests/
│   ├── fixtures/                      # later known-answer contracts
│   ├── test_prng_and_sources.py
│   ├── test_synthesis.py
│   ├── test_determinism.py
│   ├── test_provenance.py
│   ├── test_cli.py
│   └── test_midi.py                   # later
├── docs/
├── pyproject.toml
└── README.md
```

## Run the tests

```bash
python -m pip install -e .[dev]
python -m pytest
python -m ruff check .
```

The suite checks PRNG known answers, chunked math-source equivalence,
instrument repeatability, seed isolation, WAV layout and quantization,
canonical hashing, tamper detection, exact repeated renders, CLI generation,
and manifest replay.

## Extending Phase 1

New instruments implement:

```python
from sonification.core.synthesis import Instrument

class MyInstrument(Instrument):
    def synthesize(
        self,
        *,
        frequency_hz: float,
        duration_seconds: float,
        velocity: float,
        sample_rate: int,
        seed: int,
    ):
        ...

    def to_identity_dict(self):
        ...
```

New rhythm systems implement `RhythmGenerator` and return ordered
`NoteEvent` values. Every DSP-affecting constant belongs in the identity
contract; caches, plots, UI state, and filenames do not.

## Performance notes

Phase 1 uses NumPy vectorization for oscillators and envelopes. The
Karplus-Strong recurrence is intentionally scalar and inspectable. A default
four-bar loop generally renders in a few seconds; 8–16 bar hybrid loops can take
longer depending on CPU and sample rate. Later profiling will identify stable
Numba acceleration points; Numba is not required for correctness.

Explicit frame and note-work budgets reject pathological configurations before
their largest arrays are allocated. These are safety limits, not musical
recommendations.

## Authorship and license

Created by **Trent Slade / QSOL-IMC** and licensed under the
[Mozilla Public License 2.0](LICENSE). Reuse is welcome, but covered source
files and modifications must remain available under MPL-2.0 when distributed,
and copyright and license notices may not be removed or altered.

See [NOTICE](NOTICE), [AUTHORS.md](AUTHORS.md), and [CITATION.cff](CITATION.cff)
for explicit provenance and preferred citation.
