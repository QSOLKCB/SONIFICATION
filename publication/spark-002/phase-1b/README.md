# SPARK-002 Phase 1B - source-pinned historical GNATprove evidence

The seven original files in `receipts/` are owner-executed GNATprove receipts,
preserved byte-for-byte. `AUDIT.json` is derived metadata, not an original receipt.

## Scope and pinned identity

- Merged source: `6f0f1be1ba8885fa708d7328bcb92fbf4ecc324f`
- GNATprove: FSF 16.1.0; Alire 2.1.1; Why3 1.8.2+git; cvc5 1.3.2
- Strict owner-run proof: exit status 0; 9/9 reported checks proved
- 2 functional contract checks: `Compare_Readings` and `Audit`
- 7 termination checks: `Usable`, `Compare_Readings`, `Declared_Row_Valid`,
  `Compatible`, `Both_Phases`, `Packet_Eligible` and `Audit`
- 0 unproved; 0 justified; 0 reported pragma Assume statements
- No separately counted runtime checks; non-SPARK probe excluded

## Evidence verification

Run from a full-history SONIFICATION checkout:

    uv run --no-project python scripts/verify_spark_002_phase_1b_receipts.py
    uv run --no-project python -m unittest tests.test_spark_002_phase_1b_receipts -v

The offline verifier compares each of the seven receipt files with its pinned
SHA-256, verifies both original checksum manifests, checks the pinned Git
blobs rather than the current branch's source, and validates the summary
and derived audit metadata. CI runs these checks without invoking GNATprove.

## Claim boundary

The report only proves the generated verification conditions for declared
Ada/SPARK properties, not Python equivalence, independently authenticated
laboratory or measurement provenance, helium phase validation or a classifier.
The bounded 8-row partition predicates remain authored specifications.
MAT-SPEC-010 remains
`NUMBERED_SERIES_CLOSED_AT_010_WITH_OPEN_SCIENTIFIC_GATES`.
No frozen source, Phase 1A proof, release tag or Zenodo DOI is modified.
