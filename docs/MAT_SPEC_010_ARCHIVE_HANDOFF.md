# MAT-SPEC-010 post-release archival handoff

This handoff preserves the immutable GitHub release and separately corrects a
source-packaging omission for the proposed Zenodo deposit. It does not change
the MAT-SPEC-010 tag, release asset, generated scientific artifacts, admission
outcomes or claim boundaries.

## Immutable release verification

- Release ID: `439286691`
- Tag: `mat-spec-010-v0.1.0`
- Peeled commit: `9d12c6a5098f4edba972bb6b1067555d8f48f693`
- Published asset: `MAT-SPEC-010-v0.1.0-research-archive.zip`
- Bytes: `3161581`
- SHA-256:
  `c135f24c4a51a91444e2645c4850f326620dc54cb95b3b98d9bbae6d59235993`
- Reproduction status: `VERIFIED_REPRODUCIBLE`

The asset was downloaded afresh from GitHub into an isolated directory. Before
extraction, a standard-library inventory rejected unsafe paths, duplicate
members, symlinks, non-regular entries, encryption, unexpected compression,
non-canonical timestamps or modes, implausible sizes and CRC failures. The
validated archive contained 168 regular members in lexical order, all stored
with timestamp `1980-01-01T00:00:00` and mode `0100644`. Its 167-entry
`provenance/SHA256SUMS` and 166-record archive manifest were verified.

The original packaging implementation was not assumed to exist at the tag. Its
two exact files were recovered only after the archive safety and checksum
checks established their provenance:

- `tooling/build_mat_spec_010_archive.py`:
  `61c384e7057c58f048ee44c4dd21e7da8ec09264562eb61fdcb4816b489ca94a`
- `tooling/mat_spec_010_archive.py`:
  `f010e16e4a82a5a8df0af3b40a973dc3bf8bd36a7914e2b6d0ebb0538dc67ed1`

Those recovered bytes were run twice with separate detached Git worktrees,
publication roots, UV caches, temporary source extractions and output paths.
Both worktrees resolved the exact tag to the required commit. Both outputs were
byte-for-byte identical to each other and to the downloaded immutable asset,
including ZIP member order, compression method, timestamps, permissions and
all payload bytes.

## Post-release source-packaging correction

The immutable asset materializes all 68 files declared by the frozen logical
source index. That index omitted `materials/__init__.py`, even though
`materials/mat_spec.py` imports `__version__` from it and includes it in the
implementation identity. Consequently, the original deposited
`source/repository/` subtree is not a standalone importable Python package.
This is a packaging-completeness defect, not a change to a scientific result.

The separate corrected package is:

`MAT-SPEC-010-v0.1.0-zenodo-deposit.zip`

Its post-release builder starts from the verified release payload, resolves the
same annotated tag and exact commit, and adds only the exact pinned initializer
plus explicit correction provenance and handoff tooling. The initializer pin
is:

- bytes: `133`
- SHA-256:
  `1a7d56f6231fc6ae77ef7701785939aca31327719ae85a31b0ebe32c7ce90055`

The corrected package retains the immutable release filename, size and digest
as its parent identity. It uses a different filename and digest so it cannot be
mistaken for, or overwrite, the GitHub release asset.

## Build and verification

The repository must contain the annotated source tag. A full checkout or an
explicit tag fetch is required.

```sh
UV_CACHE_DIR=/tmp/qsol-mat-spec-handoff-uv \
  uv run --python 3.11 --no-project python \
  scripts/build_mat_spec_010_handoff.py \
  --out /tmp/MAT-SPEC-010-v0.1.0-zenodo-deposit.zip

UV_CACHE_DIR=/tmp/qsol-mat-spec-handoff-uv \
  uv run --python 3.11 --no-project python \
  scripts/build_mat_spec_010_handoff.py \
  --verify-only \
  --out /tmp/MAT-SPEC-010-v0.1.0-zenodo-deposit.zip
```

The corrected builder runs the frozen 123-test suite and all ten original
profile builders from a temporary extraction of the pinned tag. Its tests also
materialize the packaged `materials` source in a clean directory and import it
without recovering any additional source.

## Publication and scientific boundary

The corrected package and metadata are prepared locally for a new, independent
Zenodo Dataset draft. No upload, record creation, DOI reservation or Zenodo
publication is authorized by this handoff. Owner approval remains mandatory.

Neither the verified reproduction nor the packaging correction establishes an
independent helium phase classification, independent physical replication,
calibrated uncertainty, auditory validation, E8 physics or a new physical law.
