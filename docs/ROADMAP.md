# Implementation roadmap

Each phase must remain runnable and tested. Later phases extend the contracts;
they do not retroactively relabel Phase 1 artifacts.

## Root ETQ-101 v2 — symbolic MIDI profile (implemented)

- exact selected-root graph, stable 101-state basis, and D4 triality action;
- trace-zero selected-graph degree potential, dimensionless generator
  constructor, and specified Floquet dynamics;
- bijective low/mid/high ternary MIDI note codebook plus two fixed bookends;
- canonical v2 JSON contract, schema, hashes, and verification scripts;
- immutable legacy-v1 specification-identity fixtures and explicit claim
  boundaries;
- MIDI, CSV, and JSON root artifacts only, with no PCM or audio renderer.

The v2 codebook is implemented. A future dynamics-to-event mapping and `.mid`
exporter require their own versioned contract and perceptual evaluation; they
must not silently inherit the separate audio laboratories' clocks or tunings.

The remaining phases in this document apply only to the independent `APP/` and
`sonification/` audio laboratories.

## Audio laboratory Phase 1 — deterministic loop kernel (implemented)

- validated configuration and note-event contracts;
- deterministic math sources and private PRNG streams;
- additive, FM, and Karplus-Strong synthesis;
- circular event rendering for true loop tails;
- PCM16/PCM24 WAV export;
- canonical recipe, audio fingerprint, observation contract, and manifest;
- headless `generate` and `verify` commands;
- determinism, DSP, math, provenance, WAV, and CLI tests.

## Audio laboratory Phase 2 — mathematical musical systems

- exact 240-root E8 registry and stable root ordering;
- projection, triality, golden-ratio, Pi/2, Fibonacci, Euclidean, and hybrid
  mappings, each explicitly authored and unrelated to the ETQ v2 generator;
- modal metallic percussion, more synth models, richer rhythm generators;
- JSON preset schema and initial industrial/dark factory library;
- selectable tuning systems, including Phi-derived 833-cent and E8-projected
  scales.

## Audio laboratory Phase 3 — interactive laboratory

- local Gradio interface;
- multi-layer instrument builder and parameter bindings;
- waveform, spectrogram, piano-roll, attractor, and E8 projection views;
- render/preview transport, cache, stems, and export controls.

## Audio laboratory Phase 4 — advanced models and interoperability

- cellular automata, L-systems, qutrit sequencing, safe expressions;
- Lorenz, Rossler, Kuramoto, double-pendulum, and additional physical models;
- microtonal MIDI with pitch-bend/channel allocation;
- QEC event hooks and SPECTRAL-compatible lineage bundles;
- performance profiling and optional Numba hot paths.

The proposed mature tree is documented in the root README. Files are added only
when their phase has an implementation and tests; the repository avoids empty
placeholder modules.
