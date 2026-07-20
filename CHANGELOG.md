# Changelog

## 3.0.0 — ETQ-303 exact event protocol

- Promoted the optional `H_303 = H_101 tensor C^3` extension into a separately
  named 303-state forward model without claiming 303 distinct E8 roots.
- Added an exact monomial step with support action
  `(j,a)->(j+1 mod 101,a+1 mod 3)` and Gaussian-unit phase labels `[3,2,3]`.
- Proved and exhaustively verified exact order 303 and a bijective CRT event
  traversal through all tensor addresses.
- Added the exact Cartesian graph lift `G_101 square C_3`: 303 vertices, 5,364
  edges, degree range 24-57, and one connected component.
- Made the canonical output a receiver-neutral 303-entry event document.
- Added deterministic JSON, CSV, NDJSON, GraphML, SVG, and symbolic MIDI
  receiver artifacts.
- Added integer-only canonical JSON, domain-separated hashes, an acyclic
  observation receipt, and a manifest-core receipt.
- Preserved the complete ETQ-101 v2 and v1 contracts and verifiers unchanged.
- Excluded floating eigensolver output, ring surrogates, sorted degree proxies,
  hertz, PCM, WAV, and empirical claims from v3 identity.

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
