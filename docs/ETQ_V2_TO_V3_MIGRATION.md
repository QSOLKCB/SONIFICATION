# ETQ-101 v2 to ETQ-303 v3 Migration

## Preserved unchanged

- standard 240-root E8 construction;
- embedded order-three D4 triality;
- lexicographic `2 + 33*3 = 101` selector;
- 101-site selected-root adjacency;
- exact degree potential and v2 hashes;
- v2 symbolic MIDI codebook;
- v1 and v2 archival identities.

## New in v3

- `H_303 = H_101 tensor C^3` becomes a named forward extension;
- the external fibre is explicit and separate from v2 internal triality labels;
- the declared product step has an exact single 303-state support orbit;
- canonical output is a receiver-neutral event document;
- `G_303 = G_101 square C_3` supplies exact graph context;
- JSON, CSV, graph-JSON, atlas-JSON, and MIDI receivers share one commitment;
- all persisted root artifacts use only `.json`, `.csv`, or `.mid`;
- domain-separated receipts bind a normalized v3 implementation source bundle;
- generated contracts use the adjacent bundled schema;
- output generation rejects unsafe or nonempty directories instead of deleting
  them recursively.

## Breaking semantic change

V2's forward identity was a 101-state model with a symbolic MIDI codebook. V3's
forward identity is a 303-state event protocol. V2 is not silently rewritten:
its source tag, Zenodo DOI, contract, schema, fixtures, and verifiers remain
preserved.

## API map

| V2 | V3 |
|---|---|
| `src/etq-model.mjs` | preserved base model |
| `buildTernaryMidiCodebook()` | reused by the optional MIDI receiver |
| optional `H_303` appendix | `src/etq-v3-core.mjs` forward state space |
| no dynamics-to-events rule | exact 303-event CRT traversal |
| MIDI as implemented observation codebook | receiver-neutral event document first |
| v2 contract hash | embedded immutable lineage fixture |
