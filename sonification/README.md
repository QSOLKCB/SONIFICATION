# Music-First Deterministic Sonification Laboratory

**Procedural, reproducible mathematical loop creation for DAW-ready audio.**

[![Tests](https://github.com/QSOLKCB/SONIFICATION/actions/workflows/tests.yml/badge.svg)](https://github.com/QSOLKCB/SONIFICATION/actions/workflows/tests.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)](https://www.python.org/)
[![License: MPL-2.0](https://img.shields.io/badge/License-MPL--2.0-blue.svg)](../LICENSE)

The `sonification` package creates DAW-ready musical loops entirely from code
and mathematics. There are no samples, SoundFonts, SF2 files, hidden downloads,
or recorded excitations. Oscillators, modulation, noise-like material, string
excitation, envelopes, rhythm, panning, and mixing are explicit procedural
functions.

Phase 1 is a complete, runnable deterministic kernel: additive synthesis, FM
synthesis, Karplus-Strong string modelling, a dark 432 Hz hybrid factory
groove, PCM16/PCM24 WAV export, canonical recipes, fingerprints, manifests, and
replay verification.

> This is audible geometry and mathematical composition. It is not a claim
> that E8—or any other mapped structure—is physically present in nature.

## Why this laboratory exists

[SPECTRAL](https://github.com/QSOLKCB/SPECTRAL) is the broader deterministic
sonification and provenance workbench. This laboratory complements it by
putting musical usefulness first: short loops, instruments, groove, tuning,
layer building, and later DAW/MIDI workflows.

[QEC](https://github.com/QSOLKCB/QEC) informs the insistence on explicit
contracts, replayable state, deterministic event mappings, and honest claim
boundaries. The laboratory does not present classical DSP as quantum
computation.

## Relationship to ETQ-101

[ETQ-101](../README.md) is the repository's primary formal mathematical model.
This Python package is the existing runnable music-first synthesis engine.
Their responsibilities are deliberately separate:

| Layer | Current responsibility |
|---|---|
| ETQ-101 | E8-root-derived graph, embedded D4 triality, qutrit/SCL algebra, canonical contract, and specified spectral sonification map |
| Python laboratory | Instruments, event construction, mixing, WAV export, manifests, fingerprints, and exact replay verification |

The ETQ-101 static PCM renderer remains specified but not yet implemented. The
Phase 1 WAV engine is real and runnable, but its output must not be described as
an ETQ-101 render until that mapping is implemented explicitly.

## Quick start

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

The command writes a 24-bit WAV and its integrity-bound manifest to
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
- `fm` — oversampled two-operator FM with deterministic FIR decimation; and
- `karplus` — fractional-delay Karplus-Strong with mathematical excitation.

`--name` changes filenames only; it never enters render identity. Use
`--verbose` for track-level render logging.

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
re-rendered WAV identity differs. Named artifacts are not overwritten by
default; add `--force` only when you intend to atomically replace files with
the same names.

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

Every public instrument is independently usable:

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

## What Phase 1 synthesizes

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

The string model uses a fractional delay, feedback below unity, a
brightness-weighted two-point loop filter, pick-position comb, and DC blocker.
Its excitation is generated from indexed SplitMix64 values and mathematical
tones—not from a stored pluck, noise sample, or external file.

### Loop construction

Events are measured in quarter-note beats and converted into integer frame
positions. Release tails are folded into the loop buffer circularly. The tail
of the final event therefore contributes mathematically to the start of the
next repetition instead of being silently truncated.

The Phase 1 patterns are explicit musical fixtures. Phi, Fibonacci, Euclidean,
qutrit, attractor, cellular-automata, and E8-driven rhythm generation can later
arrive behind the same event contract.

## Determinism and provenance

Phase 1 uses `sonification.float64-numpy/v1`.

```text
same SONIFICATION version and recorded Python/NumPy/OS/machine identity
+ same normalized parameters and event plan
+ same unsigned 64-bit seed
= same PCM, WAV, hashes, fingerprint, contract, and manifest
```

The renderer excludes timestamps, output paths, filenames, playback state,
audio devices, process IDs, and global random state from the identity path.
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
digital signatures and do not prove who created an artifact. See
[the determinism contract](../docs/DETERMINISM.md) for exact scope and
cross-runtime limits.

## Exported artifacts

| Artifact | Purpose |
|---|---|
| `*.wav` | Mono/stereo little-endian PCM16 or PCM24 audio; the Phase 1 composer exports stereo. |
| `*.manifest.json` | Complete recipe, fingerprint, render contract, lineage, claim boundary, and manifest-core receipt. |
| `*.recipe.json` | Identity-bearing render inputs without observations. |
| `*.fingerprint.json` | PCM/WAV hashes, level observations, stereo correlation, RMS envelope, and chunk hashes. |

JSON is UTF-8, key-sorted, compact, finite-only, and newline-terminated.

## Run the Python tests

From the repository root:

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

New instruments implement the `Instrument` contract:

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

New rhythm systems implement `RhythmGenerator` and return ordered `NoteEvent`
values. Every DSP-affecting constant belongs in the identity contract; caches,
plots, UI state, and filenames do not.

The planned architecture and later-phase commitments are documented in the
[roadmap](../docs/ROADMAP.md).

## Performance and safety

Phase 1 uses NumPy vectorization for oscillators and envelopes. The
Karplus-Strong recurrence is intentionally scalar and inspectable. A default
four-bar loop generally renders in a few seconds; 8-16 bar hybrid loops may
take longer depending on CPU and sample rate.

Explicit frame and note-work budgets reject pathological configurations before
their largest arrays are allocated. These are safety limits, not musical
recommendations.

## Authorship and license

Created by **Trent Slade / QSOL-IMC** and licensed under the
[Mozilla Public License 2.0](../LICENSE). Covered source files and modifications
must remain available under MPL-2.0 when distributed, and copyright and licence
notices may not be removed or altered.

See [NOTICE](../NOTICE), [AUTHORS.md](../AUTHORS.md), and
[CITATION.cff](../CITATION.cff) for provenance and preferred citation.
