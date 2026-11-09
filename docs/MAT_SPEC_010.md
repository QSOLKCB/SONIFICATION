# MAT-SPEC-010 v0.1.0 — Final numbered materials research evidence freeze

**MAT-SPEC-010 is the final numbered MAT-SPEC profile. There is no
MAT-SPEC-011.** Its purpose is a reproducible source-and-claim audit,
not an additional physics experiment or a claim of phase classification.

MAT-SPEC-001 through 009 established bounded claims about published
helium measurements, model input tables, evaluated references,
exact symbolic receivers, fitted uncertainties, experimental
lineage and missing independent evidence. The closing profile
records those claims and limitations without elevating them.

## Verified source basis

The builder calls the MAT-SPEC-009 builder, which recursively replays
MAT-SPEC-001..008 under existing source, contract, SHA-256 and
deterministic checks. The final builder hard-checks the seven
MAT-SPEC-009 output hashes, the predecessor manifest, and its blocked
physical gate. It then creates a logical index of *every earlier
artifact digest* using SHA-256 pin maps embedded in the existing
successor implementations. The profile does not modify old releases.

The inventory includes source data excerpts, attributions, profile
contracts, prior implementation modules, builders, tests, method
documents, root output policy and CI recipe. Inputs are regular
files read with no-follow controls, indexed by content SHA-256
and byte length. Each grade and nonclaim in the scientific claim
registry is frozen by source JSON and a separate implementation
constant; edit drift is rejected.

Original Git tags observed for MAT-SPEC-003 through 006 are
recorded. The others are tied to their original parent/merge commits
and artifact receipts. A merge SHA is **not** a release tag.
Foundational DOI 10.5281/zenodo.24062652 identifies MAT-SPEC-001 only.
MAT-SPEC-010 has no new DOI or automatically deposited archive.

## Scientific claim hierarchy

| Profile | Source and operation | Scientific scope |
|---|---|---|
| 001 | Measured neutron-dispersion table | Source-preserving symbolic mapping, not a new physical law |
| 002 | Measured reported-error intervals | Interval/sampling invariants, no calibrated covariance |
| 003 | Measured mode regions | Exploratory roton common support, incomplete physical windows remain limited |
| 004 | Eight published model-input temperature rows | Model-based exact closure, not independent phase measurements |
| 005 | Fourteen evaluated reference temperatures | Cross-lambda reference replay, null distinct from boundary zero |
| 006 | Twelve published, gravity-corrected averaged Lipa-Chui values | One original processed experimental campaign |
| 007 | Four secondary fit summaries | Published interval overlaps, not original raw-run replication |
| 008 | Ten source documents, four acquisitions | One source-pinned campaign; zero independent comparable pairs |
| 009 | Prospective protocol and fourteen synthetic denial controls | Structural rejection only; actual physical challenge BLOCKED |
| **010** | Full source/claim integrity index | Research series closed with open scientific admission gates |

The project has not conducted independently validated helium phase
classification, a new critical-exponent fit, human auditory
discrimination, an E8-in-helium result or unification.

## Deterministic archive *index* (not a deposited archive)

The executed inventory covers **63 pinned predecessor artifact identities**
across nine profiles and **68 hashed repository inputs** (source data,
code, tests, contracts, methods and policy). All seven MAT-SPEC-009
output hashes are separately pinned and required before 010 builds.

Eight final JSON output files:

- contract.json — frozen final contract and MAT-SPEC-010 stop rule
- claims.json — source and inference boundary registry for 001..009
- source-inventory.json — original measurement/model/review/gate source kinds
- archive-index.json — logical output SHA-256 receipts and hashed repository files
- closure-gate.json — end-of-series status and explicitly blocked physical gates
- handoff.json — SPARK/Ada then VANILLAJS Lean/ECMA work
- audit.json — coverage and numerical/nonclaim checks
- manifest.json — input, implementation and output SHA-256 receipts

The archive-index is **not** a ZIP/TAR or external Zenodo deposit.
Old logical artifact paths carry their SHA-256 values; they are
rebuildable and **not** re-emitted as archive bytes by this program.
The two MAT-SPEC-001 MIDI fingerprints refer to symbolic MIDI, not
rendered audio. All MAT-SPEC-010 runtime outputs are JSON. No PCM,
WAV, sampled amplitude buffers or sound synthesis are created.

## Reproduce locally

Python 3.11+, standard library, offline, preferably via uv:

    uv run --no-project python -m unittest discover -s tests -p 'test_mat_spec*.py' -v
    uv run --no-project python scripts/build_mat_spec_010.py --out dist/mat-spec-010
    sha256sum dist/mat-spec-010/*.json

The destination must be a fresh relative directory. POSIX output is
anchored and no-follow; existing destinations and non-JSON export
requests fail closed.

Closure status:
NUMBERED_SERIES_CLOSED_AT_010_WITH_OPEN_SCIENTIFIC_GATES.

This marks the *ten bounded research profiles* completed, not
independent experimental phase validation as successful.

## Post-merge publication procedure

1. Obtain independent code/scientific review, all six CI jobs on the exact
   PR head and post-merge CI on the final merge commit.
2. After green post-merge CI, tag the exact merge commit as
   mat-spec-010-v0.1.0. Do not overwrite any earlier source or tag.
3. Publish release notes and the archive-index checksum receipts.
4. Only if separately desired, build and validate a full external
   publication archive under an approved publication workflow and
   obtain a new DOI from the actual deposit. Do not predict a DOI.
5. No MAT-SPEC-011. New measurement work is a separately scoped programme.

See MAT_SPEC_010_HANDOFF.md for the subsequent SPARK/Ada and Lean/ECMA
proof obligations. Neither proof is executed in this profile.
