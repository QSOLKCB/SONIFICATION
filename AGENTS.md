# Repository instructions for AI agents

## Scope

These instructions apply to every automated coding agent working in this
repository.

The **root ETQ-101 system** means the ETQ model, contracts, tools, and workflows
outside the separate `APP/` and `sonification/` music-first laboratories. It
includes root-level tools and the ETQ material in `src/`, `scripts/`,
`spec/`, `examples/`, `tests/`, and `docs/`.

A more specific `AGENTS.md` may add tighter local rules, but it must not relax
the root output policy without explicit written direction from the repository
owner.

## Root ETQ-101 output policy

- Root ETQ runtime and export workflows may generate only:
  - Standard MIDI files: `.mid`
  - event or audit tables: `.csv`
  - deterministic contracts, manifests, and provenance records: `.json`
- PCM and rendered-audio generation in the root ETQ system is permanently
  disabled. Do not create, enable, restore, or invoke a root WAV renderer or
  export path.
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

The output allowlist applies to generated runtime/export artifacts, not normal
repository development or publication files. Source code, tests,
documentation, schemas, images, TeX, and archival PDFs may use the file types
appropriate to their purpose.

When changing a root ETQ export workflow:

- retain deterministic ordering and canonical serialization;
- record the mapping contract, inputs, configuration, implementation identity,
  and SHA-256 hashes in JSON provenance;
- treat CSV as an auditable event/data table rather than an audio format;
- test that only `.mid`, `.csv`, and `.json` runtime artifacts are emitted;
  and
- test that rendered-audio requests fail explicitly instead of being silently
  redirected or renamed.
