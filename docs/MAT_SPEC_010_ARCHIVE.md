# MAT-SPEC-010 v0.1.0 research archive

This archive is the complete external publication package for the final
numbered MAT-SPEC research profile. It materializes the previously logical
MAT-SPEC-010 archive index as actual bytes while preserving the scientific
limits recorded by MAT-SPEC-001 through MAT-SPEC-010.

## Immutable source identity

- Git repository: `https://github.com/QSOLKCB/SONIFICATION`
- Annotated tag: `mat-spec-010-v0.1.0`
- Peeled source commit: `9d12c6a5098f4edba972bb6b1067555d8f48f693`
- Version: `0.1.0`
- Expected archive filename: `MAT-SPEC-010-v0.1.0-research-archive.zip`

The archive workflow resolves and validates the annotated tag before using
`git archive` to obtain the exact frozen tree. The later publication tooling
does not modify the tagged source or any frozen MAT-SPEC result.

## Scientific objective and result boundary

The numbered programme tests deterministic preservation, transformation and
provenance of attributed helium data and published fit summaries. Its final
status is:

`NUMBERED_SERIES_CLOSED_AT_010_WITH_OPEN_SCIENTIFIC_GATES`

The archive establishes reproducibility of the declared computational
operations and their provenance receipts. It does not establish:

- independent helium-I/helium-II phase classification;
- an independently replicated physical experiment;
- a new critical exponent or a new physical law;
- calibrated cross-campaign uncertainty or covariance;
- human auditory discrimination;
- E8 symmetry in helium or a unification result; or
- physical authenticity merely from matching identifiers or hashes.

MAT-SPEC-008 admits one source-pinned processed measurement campaign and zero
eligible independent measurement pairs. MAT-SPEC-009 therefore executes 14
synthetic fail-closed controls and a prospective protocol, not a physical
classification experiment. MAT-SPEC-010 preserves those blocked gates.

## Evidence categories

The archive keeps different forms of evidence separate:

- `evidence/published-measurements/` contains the attributed neutron
  dispersion table and the selected Lipa-Chui processed calorimetry rows.
- `evidence/model-inputs/` contains published model-parameter table entries;
  these are not independent phase measurements.
- `evidence/evaluated-reference/` contains selectively transcribed
  Donnelly-Barenghi evaluated reference values.
- `evidence/fitted-values/` contains four published secondary fit summaries,
  not raw acquisition rows.
- `evidence/source-attribution/` contains source, experiment-family and claim
  inventories.
- `evidence/source-licences/` records redistribution decisions and source
  rights without relicensing third-party work.
- `evidence/secondary-literature/` cites works whose article or report bytes
  are not redistributed.
- `evidence/synthetic-fixtures/` contains the 14 negative controls, which are
  never admitted as physical evidence.

The NASA report and review/article PDFs are not included. Their citations and
source URLs are preserved. Small factual excerpts already present in the
repository remain attributed and are governed by the source-specific rights
record rather than a blanket relicensing claim.

## Archive contents

- `artifacts/MAT-SPEC-001/` through `artifacts/MAT-SPEC-010/` contain the
  actual generated JSON, CSV and symbolic MIDI artifact bytes.
- `source/repository/` contains every source, contract, method, test, policy
  and CI file listed by the frozen MAT-SPEC-010 repository index.
- `tests/` contains the canonical 123-test local receipt and exact post-merge
  GitHub Actions run/job identifiers.
- `provenance/archive-index-cross-check.json` maps all 63 logical predecessor
  identities to actual archived files and verifies their SHA-256 values.
- `provenance/archive-manifest.json` records byte sizes and SHA-256 values for
  every payload member other than the manifest and checksum file themselves.
- `provenance/SHA256SUMS` covers every other archive member, including the
  archive manifest.
- The Zenodo draft metadata and upload receipt remain beside the ZIP in the
  publication workflow so they can record the completed ZIP's non-circular
  byte size and SHA-256. A null record ID or DOI must not be interpreted as a
  published Zenodo record.

The two `.mid` files are symbolic Standard MIDI files from MAT-SPEC-001. They
are not sampled or rendered audio. No PCM, WAV, sampled-amplitude array,
synthesizer or audio encoder is used by the root research workflow.

## Computational reproduction

Requirements are Git, Python 3.11 or later, and the Python standard library.
`uv` is recommended only as a deterministic interpreter launcher.

```sh
git clone https://github.com/QSOLKCB/SONIFICATION.git
cd SONIFICATION
git fetch --tags origin
test "$(git rev-parse 'mat-spec-010-v0.1.0^{commit}')" = \
  "9d12c6a5098f4edba972bb6b1067555d8f48f693"

UV_CACHE_DIR=/tmp/qsol-mat-spec-uv \
  uv run --python 3.11 --no-project python \
  scripts/build_mat_spec_010_archive.py \
  --out dist/MAT-SPEC-010-v0.1.0-research-archive.zip

UV_CACHE_DIR=/tmp/qsol-mat-spec-uv \
  uv run --python 3.11 --no-project python \
  scripts/build_mat_spec_010_archive.py \
  --verify-only \
  --out dist/MAT-SPEC-010-v0.1.0-research-archive.zip
```

The builder runs all 123 `test_mat_spec*.py` tests and all ten original
profile builders from a temporary extraction of the tagged tree. It validates
every frozen source pin, parent artifact receipt and actual archived byte.

## Determinism

The ZIP uses:

- lexicographic member ordering;
- the fixed member timestamp `1980-01-01T00:00:00`;
- fixed regular-file mode `0644`;
- `ZIP_STORED`, avoiding compressor-version variability; and
- canonical sorted-key compact ASCII JSON with one terminal LF.

The build receipt records the actual Python and Git versions. Rebuilding with
the same committed publication tooling, frozen tag and toolchain produces the
same ZIP bytes. The verification pass performs a fresh extraction and checks
all internal SHA-256 entries.

## Provenance and original experiments

The archive preserves source attribution but does not elevate it into external
authentication. The original physical evidence categories are described in
the profile methods and source inventories. In particular:

- the Godfrin et al. dispersion table is an attributed published ancillary
  dataset with preserved original bytes and missing values;
- the Lipa-Chui excerpt contains 12 selected, gravity-corrected and averaged
  values from one experiment campaign, not raw instrument streams;
- the Donnelly-Barenghi table is an evaluated compilation;
- the Barmatz et al. rows are secondary fitted summaries; and
- the remaining source catalogue entries are literature records without
  admitted measurement-row packets.

Checksums demonstrate byte identity and detect mutation. They do not prove
source custody, authorship, cryptographic authenticity, experimental
independence, calibration or physical truth.

## DOI and publication state

The foundational identifier `10.5281/zenodo.24062652` is recorded as related
work for MAT-SPEC-001 and is not reused as this archive's identity. A new
Zenodo record ID or DOI is recorded only if Zenodo actually assigns it. Until
owner approval and publication, this package remains prepared but unpublished.

