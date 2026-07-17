# Changelog

## Unreleased — QSOL-IMC Offline App

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

## 0.1.0 — Phase 1

- Added the deterministic mathematical loop kernel.
- Added additive, FM, and deterministic Karplus-Strong instruments.
- Added a sample-free hybrid factory composition at 432 Hz by default.
- Added PCM16/PCM24 WAV, recipe, fingerprint, and manifest export.
- Added replay verification and exact same-runtime determinism tests.
