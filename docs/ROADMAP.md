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

## Root D4/F4 triality literature bridge — implemented

- exact factorization of the existing ETQ four-coordinate triality matrix as
  `A = w_S w_T` in Sakai's published (W(F_4)/W(D_4)\cong S_3) convention;
- safe-integer tests for the two involutions and their order-three product;
- exact trigrading equations for D4 triality invariants;
- a machine-readable ledger of the 15 minimal quadratic/cubic joint
  covariants; and
- explicit boundaries separating the published invariant theory from ETQ's
  authored selector, qutrit factor, receiver mapping, and protocol identity.

This bridge is noncanonical context. It changes no v2/v3 fixture, event
ordering, implementation identity, or receiver artifact.

## Future root research profile — triality-invariant algebra sonification

A later separately versioned profile may use the 15-generator invariant basis
as a finite symbolic source object. Before any auditory mapping is canonical it
must preserve and test the published grading relations, define its event
semantics and provenance, and remain within the root MIDI/CSV/JSON output
policy. No tempo, acoustic tuning, timbre, or rendered audio may enter root ETQ
identity.

The remaining numbered phases below apply only to the independent `APP/` and
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
