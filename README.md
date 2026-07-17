# QSOL SONIFICATION

**Music-first deterministic sonification laboratory for mathematical loop creation.**

[![Tests](https://github.com/QSOLKCB/SONIFICATION/actions/workflows/tests.yml/badge.svg)](https://github.com/QSOLKCB/SONIFICATION/actions/workflows/tests.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

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
├── APP/
│   ├── index.html
│   ├── styles.css
│   ├── js/                     # DSP, WAV, hashing, provenance, UI
│   └── tests/                  # direct-file and Node self-tests
├── docs/
│   ├── DETERMINISM.md
│   ├── ROADMAP.md
│   └── SCIENTIFIC_BOUNDARIES.md
├── examples/
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
│   └── test_synthesis.py
├── CHANGELOG.md
├── LICENSE
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
node APP/tests/run.cjs
node APP/tests/dom-smoke.cjs
```

The suite checks PRNG known answers, chunked math-source equivalence,
instrument repeatability, seed isolation, WAV layout and quantization,
canonical hashing, tamper detection, exact repeated renders, CLI generation,
manifest replay, browser uint64 boundaries, short-PCM fingerprints, offline WAV
packing, and deterministic browser replays.

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

## License

MIT. See [LICENSE](LICENSE).

Created by **Trent Slade / QSOL-IMC**.
