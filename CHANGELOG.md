# Changelog

## 2.0.0 — ETQ-101 forward profile

- Removed the golden-ratio modulation and declared 432 Hz scale from the
  forward ETQ state, generator, dynamics, and sonification mapping.
- Replaced the former diagonal modulation with an exact, trace-zero degree
  potential derived from the selected 101-vertex graph.
- Made ETQ evolution dimensionless and specified the canonical Floquet step
  without an audio-rate clock.
- Added a bijective symbolic MIDI codebook: two fixed singlet bookends and
  33-note low, mid, and high lanes for the three triality positions.
- Added explicit mathematical, sonification, statistical-testbench, and claim
  boundaries; MIDI receiver choices remain outside the canonical contract.
- Preserved the DOI-linked v1.0.0 contract, schema, and hashes as immutable
  specification-identity fixtures.
- Restricted the root ETQ runtime to MIDI, CSV, and JSON artifacts; PCM and
  rendered audio remain confined to the separate audio laboratories.

## Unreleased — separate `APP/` audio laboratory

- Added a zero-dependency HTML/CSS/JavaScript sonification workbench that opens
  directly from `APP/index.html` without a server or network connection.
- Added browser-native additive, FM, Karplus-Strong, and hybrid rendering,
  playback, canvas inspection, PCM16/PCM24 WAV export, and JSON receipts.
- Added exact BigInt uint64 seeds, bundled SHA-256, canonical browser
  provenance, resource preflight limits, and direct-file/Node self-tests.
- Hardened fractal lattice interpolation so a uint64 right neighbor is
  validated before addition.
- Capped RMS envelope buckets by available PCM frames for one-frame and other
  short fingerprints.

## 0.1.0 — separate Python audio laboratory, Phase 1

- Added the deterministic mathematical loop kernel.
- Added additive, FM, and deterministic Karplus-Strong instruments.
- Added a sample-free hybrid factory composition at 432 Hz by default.
- Added PCM16/PCM24 WAV, recipe, fingerprint, and manifest export.
- Added replay verification and exact same-runtime determinism tests.
