# Determinism contract

> **Scope:** this document describes the separate `sonification/` Python audio
> laboratory. It does not define the root ETQ-101 v2 contract, which is
> MIDI-only and has no PCM/WAV render identity.

The audio laboratory's Phase 1 uses the render ABI
`sonification.float64-numpy/v1`.

Within the same released SONIFICATION version, recorded Python and NumPy
versions, OS family, machine architecture, parameters, seed, and source tree, a
render is expected to reproduce the same quantized PCM, WAV bytes, recipe hash,
fingerprint, contract, and manifest. The test suite compares immediate replays
and independent CLI processes.

The identity path is:

```text
validated parameters + explicit event plan + seed
  -> canonical recipe + domain-separated recipe hash
  -> float64 DSP
  -> explicit peak target and symmetric PCM quantization
  -> canonical little-endian RIFF/WAVE bytes
  -> exact PCM/WAV hashes + bounded fingerprint
  -> observation contract
  -> manifest core + manifest-core receipt
```

No timestamp, filename, output directory, process ID, global PRNG state,
wall-clock value, audio device, or playback state enters render identity.

## Exact scope

NumPy transcendental functions and floating-point reductions can differ in the
last bits across CPU architectures, math libraries, or NumPy releases. Phase 1
therefore makes two separate promises:

1. **Same recorded runtime identity:** bit-identical quantized output is the
   tested target.
2. **Different conforming runtimes:** the intended signal is numerically and
   spectrally equivalent within normal float64 tolerance, but identical WAV
   hashes are not promised.

A future Canonical Strict integer DSP ABI may narrow that second boundary. It
will use a separate domain and can never be silently conflated with this ABI.

## Hash domains

Canonical JSON uses UTF-8, lexically sorted keys, compact separators, no NaN or
infinity, and one final newline. Identity objects use independent SHA-256
domains:

```text
SONIFICATION/RECIPE/v1\0
SONIFICATION/FINGERPRINT/v1\0
SONIFICATION/CONTRACT/v1\0
SONIFICATION/MANIFEST-CORE/v1\0
```

The manifest does not claim to hash its own final bytes. Its
`manifest_core_sha256` checks the integrity of the core before that receipt
field is added, preventing a circular self-hash. These are unkeyed integrity
receipts, not signatures or proof of authorship.

Unsigned 64-bit seeds are serialized as `0x` followed by exactly sixteen
lowercase hexadecimal digits. This preserves all seed bits when a manifest is
read by a browser whose exact JSON integer range ends at `2**53 - 1`.

## Entropy discipline

Phase 1 never calls `numpy.random`, Python's global `random`, an operating
system entropy API, or a clock. Stochastic-looking control and Karplus-Strong
excitation come from the versioned SplitMix64 stream and deterministic
mathematical functions. Component seeds are derived from the global seed and
stable track/event lanes.
