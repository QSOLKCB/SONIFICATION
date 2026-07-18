# Repository instructions for AI agents

## Scope

These instructions apply to every automated coding agent working in this
repository.

The **root ETQ-101 system** means the ETQ model, contracts, tools, and workflows
outside the separate `APP/` and `sonification/` music-first laboratories.

### Covered root entrypoints and pipelines

The root policy explicitly covers:

- the ETQ implementation in `src/etq-model.mjs` and every present or future
  ETQ, Tanner-tuning, MIDI, event-table, or provenance module under `src/`;
- `scripts/verify.mjs` and every present or future root ETQ command under
  `scripts/`, including verification, export, migration, fixture-generation,
  or audit jobs;
- the `npm test` and `npm run verify` entrypoints declared in the root
  `package.json`, plus any future root `npm run` script that invokes an ETQ
  model, export, event-table, provenance, validation, or fixture workflow;
- canonical contracts and examples under `examples/`, schemas under
  `spec/`, root-model tests under `tests/`, and ETQ specifications under
  `docs/` whenever they define, invoke, or validate a runtime/export
  workflow; and
- any new or renamed tool, command, pipeline, notebook, or workflow outside
  `APP/` and `sonification/` that consumes the root ETQ model or produces
  artifacts from it.

If the scope of a new pipeline is uncertain, treat it as part of the root
ETQ-101 system until the repository owner explicitly excludes it. A pipeline
remains in scope whether it is run manually, from CI, from tests, or as an
intermediate helper for another root workflow. A more specific `AGENTS.md` may
add tighter local rules, but it must not relax the root output policy without
explicit written direction from the repository owner.

## Root ETQ-101 output policy

- Root ETQ runtime and export workflows may persist or return only:
  - Standard MIDI files: `.mid`
  - event or audit tables: `.csv`
  - deterministic contracts, manifests, and provenance records: `.json`
- PCM and rendered-audio generation in the root ETQ system is permanently
  disabled. Do not create, enable, restore, or invoke a root WAV renderer or
  export path.
- The audio-generation ban applies to the complete lifecycle, not only final
  exports or persisted artifacts. Root ETQ code must not create sampled-audio
  or PCM buffers in memory, write them to temporary files, caches, logs, or
  snapshots, embed them in fixtures, or pass them to an encoder, decoder,
  browser audio API, synthesizer, playback service, or analysis step that
  requires rendered audio.
- Frequency values, pitch ratios, event times, durations, velocities, MIDI
  messages, graph/matrix data, and other symbolic control data are allowed.
  Arrays of sampled waveform amplitudes or encoded audio bytes are not.
- Do not bypass the restriction by emitting another rendered-audio format.
  Prohibited root outputs include `.wav`, `.pcm`, `.aiff`, `.flac`,
  `.mp3`, `.ogg`, and equivalent encoded or raw audio.
- Canonical PCM/WAV fields and hashes must remain `null` and be described as
  intentionally disabled. Do not add a placeholder, synthetic fixture, or
  claimed canonical ETQ-101 audio artifact.
- Do not render root-generated MIDI to audio within the root ETQ workflow.
  MIDI is a symbolic event/control artifact; audible playback depends on the
  receiving synthesizer, sound library, and playback environment.
- Any proposal to change this policy requires explicit written approval from
  the repository owner.

## Separate music-first laboratories

The existing `APP/` and `sonification/` subprojects are separate
music-first synthesis laboratories. Their existing audio synthesis, playback,
and WAV-export features are outside the root ETQ-101 output policy.

Do not import, call, or relocate those features to circumvent the root policy,
and never describe their rendered audio as the canonical sound of ETQ-101.

## Development files and checks

The persisted-artifact allowlist applies to generated runtime/export artifacts,
not normal repository development or publication files. Source code, tests,
documentation, schemas, images, TeX, and archival PDFs may use the file types
appropriate to their purpose. The stricter ban on generating sampled audio
still applies in memory, temporary storage, caches, and test fixtures.

When changing a root ETQ export workflow:

- retain deterministic ordering and canonical serialization;
- record the mapping contract, inputs, configuration, implementation identity,
  and SHA-256 hashes in JSON provenance;
- treat CSV as an auditable event/data table rather than an audio format;
- test that only `.mid`, `.csv`, and `.json` runtime artifacts are emitted;
  and
- test that sampled-audio or rendered-audio requests fail explicitly instead
  of being buffered, silently redirected, or renamed.
