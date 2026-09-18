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

## Root D4-TIA-15 v1.0.0 — triality-invariant algebra sonification (implemented)

- separately versioned profile over the published 15-generator minimal basis;
- exact preservation of \(d_a,d_b,m,k,\omega\) and derived
  \(d=d_a+d_b\);
- identity-transfer receiver projection: \(m\) to onset tick, \(d\) to
  duration, \(k\) to MIDI note, and \(\omega\) to MIDI channel;
- unchanged \(d_a,d_b\) retained in JSON/CSV and MIDI track metadata;
- 15 generator tracks plus one metadata track, with no canonical tempo;
- canonical JSON contract and fixture, schema, lossless event document, CSV,
  symbolic MIDI, implementation identity, and SHA-256 manifest; and
- fail-closed root build restricted to JSON, CSV, and MIDI.

The mapping is explicitly authored even though its transfers are identities:
the mathematics does not declare modular weight to be pitch or covariant order
to be channel. Tuning, timbre, loudness, wall-clock tempo, PCM, and rendered
audio remain outside profile identity. ETQ-101 v2 and ETQ-303 v3 are unchanged.


## Root D4-TIA-COV v0.1.0 — exact covariant algebra engine (implemented)

- exact sparse polynomial arithmetic over reduced rational numbers;
- Sakai's binary quadratic/cubic convention and normalized transvectant;
- exact construction of the 15 generators in Theorem 5.2;
- exact verification of the cubic syzygy
  (2Q^2+P^3+g^2D_g=0);
- grades ((d_a,d_b,omega)) derived from the actual symbolic covariants,
  followed by derived (d,m,k) and comparison with the literature ledger; and
- canonical sparse-polynomial term counts and SHA-256 fixtures.

This phase changes no MIDI/event mapping. It turns the literature ledger into
executable mathematics before any further auditory interpretation.

## Sequenced D4-TIA research follow-up

The remaining D4-TIA sequence is intentionally ordered:

1. **D4/F4 (S_3) orbit + equivariance harness** — next.
2. **D4-TIA-15 v2** — sonify evaluated covariants/orbits while testing
   equivariance before invariant projection.
3. **Freeze/tag/archive** the resulting research line and then update Zenodo.

Do not skip directly to a new receiver mapping before the equivariance harness
exists and is tested.

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
