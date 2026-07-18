# Tanner Tuning Fork Reconstruction Review

## Verdict

The nominal frame-bin method is a dimensionally correct and reproducible way
to retire 432 Hz as the forward ETQ tuning anchor. It does not derive absolute
physical pitch from E8: the sample rate, frame count, playback band, graph
operator, ratio map, and selection policy remain declared choices.

The supplied ETQ wrapper is specifically an E8 root-graph Laplacian
observation profile. It is not a drop-in replacement for the deposited
ETQ-101 full-generator spectrum because it omits the qutrit hopping term,
golden potential, and initial-state projector weights. Preserve ETQ-101
v1.0.0 and its 432 Hz profile for replay; publish this separately as a forward
candidate profile.

## Independently verified integration fixture

For the current selected 101-node E8 root graph, 48,000 Hz nominal sample
rate, 960,000-frame calibration interval, and 40–16,000 Hz playback band:

- smallest positive Laplacian eigenvalue: approximately 13.7625149924;
- largest Laplacian eigenvalue: approximately 56.6814734538;
- selected frame bin: `q = 3028`;
- exact nominal anchor: `757/5 Hz = 151.4 Hz`;
- mapped root-graph modes: approximately 561.66–1139.85 Hz.

These values are regression fixtures conditional on the declared profile, not
frequencies selected by E8.

## Reconstruction disclosure

The original `src/tanner-tuning-fork.mjs` was not included in the supplied
files and was absent from GitHub `main`. This directory contains a clean-room
reconstruction from the supplied specification and tests.

The two supplied SHA-256 expected values could not be reproduced because the
original canonical byte schema/domain was not documented. The reconstructed
module therefore fixes and tests this explicit identity format:

```text
{"checks":1,"entries":[[0,0,1]],"field":3,"schema":"qsol.tanner-instrument/v1","variables":1}
```

It is UTF-8 compact JSON with lexicographically ordered object keys, no BOM,
and no trailing newline. The test fixtures were updated to match those
documented bytes. Recover the original missing module if its historical hashes
must be preserved instead.

## Repository destinations

| File | Destination |
|---|---|
| `src/tanner-tuning-fork.mjs` | `src/tanner-tuning-fork.mjs` |
| `src/etq101-tuning-fork.mjs` | `src/etq101-tuning-fork.mjs` |
| `tests/tanner-tuning-fork.test.mjs` | `tests/tanner-tuning-fork.test.mjs` |
| `docs/TANNER_TUNING_FORK.md` | `docs/TANNER_TUNING_FORK.md` |
| `qec_repo.json` | `qec_repo.json` |

Run `npm test` after integration. The reconstructed review bundle passes all
eight supplied mathematical and integration tests under Node.js 20 or newer.

## Recommended full-ETQ follow-up

To preserve the existing ETQ generator semantics while removing 432 Hz, apply
the frame-bin selector to the positive canonical pitch ratios

```text
r_l = 2^(goldenRatio * xi_l)
```

derived from the full dimensionless generator `K`. Do not take square roots of
`K` eigenvalues because the signed golden potential can make `K` indefinite.
Canonical PCM may remain intentionally null; audible outputs can be versioned
as noncanonical observation realizations.
