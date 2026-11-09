# MAT-SPEC-008 v0.1.0 — Experimental source acquisition audit

## Result

**BLOCKED_INSUFFICIENT_INDEPENDENT_MEASUREMENT_DATA.**

The project now records a bounded ten-document provenance inventory across
four published experimental acquisition campaigns and three laboratory
families. Only the MAT-SPEC-006 Lipa–Chui experiment currently contributes
**source-pinned original processed numerical rows** (12). The other three
campaigns have independently attributable publications but no verified
measurement-level row packets admitted to the SONIFICATION repository.

This is an actionable *negative scientific finding*, not a software failure.
It does not imply that the other experiments have no available data, or that
only one helium experiment exists. Their source rows have simply not yet
been independently acquired, validated and pinned as an eligible packet.

MAT-SPEC-008 is independently versioned and additive to the merged
MAT-SPEC-007 baseline. Published MAT-SPEC-001 through -007 contracts are not
modified. Foundational record DOI 10.5281/zenodo.24062652 remains assigned
to MAT-SPEC-001 alone.

## Provenance scope

Four reported acquisition campaigns:

| Campaign | Laboratory family | Source-bounded original measurement rows |
|---|---|---:|
| Ahlers 1971 SVP calorimetry | Bell | 0 |
| Gasparini–Moldover 1975 pure-He4 calorimetry | Minnesota | 0 |
| Lipa–Chui ground calorimetry 1983/1984 | Stanford | 12 processed, gravity-corrected and averaged |
| Lipa 1992 STS-52 orbital calorimetry | Stanford/JPL | 0 |

The four campaign pairs yield six possible comparisons, five between
different laboratory families. **Zero pairs** have source-pinned
measurement-level numerical records on both sides; consequently there is
no defensible independently replicated physical comparison.

Ten indexed documents are not ten experiments. Mueller et al. (1976)
also reported original pressurized thermal-expansion measurements, but
the particular SVP heat-capacity fit analyzed by MAT-SPEC-007 traces
earlier Ahlers data. We do not misclassify the entire Mueller paper as
a pure reanalysis. Gasparini–Gaeta (1978) reanalyzed the earlier study;
the 1994 NASA conference, 1996 PRL paper and 2003 PRB revision relate
to the same 1992 orbital campaign. The 1998 Donnelly–Barenghi
recommendations and 2007 Barmatz review are **compilations**, not new
original run datasets.

## Primary source references

- Ahlers (1971), *Heat Capacity near the Superfluid Transition in He4 at
  Saturated Vapor Pressure*, DOI 10.1103/PhysRevA.3.696.
- Mueller, Ahlers & Pobell (1976), *Thermal expansion coefficient, scaling,
  and universality...*, DOI 10.1103/PhysRevB.14.2096.
- Gasparini & Moldover (1975), *Specific heat of He4 and He3-He4 mixtures
  at their lambda transition*, DOI 10.1103/PhysRevB.12.93.
- Gasparini & Gaeta (1978), *Universality of the specific heat of
  He3-He4 mixtures at the lambda transition*, DOI 10.1103/PhysRevB.17.1466.
- Lipa & Chui (1983), *Very high resolution heat-capacity measurements near
  the lambda point of helium*, DOI 10.1103/PhysRevLett.51.2291;
  experimenters' tabulated data included in NASA-CR-177037, Appendix A
  (NASA document 19860021083).
- Lipa et al. (1994), original STS-52 orbital experiment conference summary,
  NASA document 19950007794. Follow-up articles: DOI
  10.1103/PhysRevLett.76.944 (1996) and
  10.1103/PhysRevB.68.174518 (2003); same spaceflight campaign.
- Donnelly & Barenghi (1998), evaluated reference compilation,
  DOI 10.1063/1.556028.
- Barmatz et al. (2007), experimental fit-summary review,
  DOI 10.1103/RevModPhys.79.1.

## What is actually verified?

MAT-SPEC-008 replays the full MAT-SPEC-001–007 artifact chain and
requires its seven prior ancestors' hash and contract checks. It parses
the original MAT-SPEC-006 source-pinned twelve-row calorimetry file,
cross-references the four MAT-SPEC-007 published fit campaigns, and
checks that a derived fit or compilation cannot silently count as
another independent measurement.

The source catalogue records bibliographic lineage, not authenticated
run-level acquisition evidence for the missing experiments. Reported
fit-parameter errors from MAT-SPEC-007 are not interchangeable with
per-row heat-capacity measurement errors. Likewise, table-side temperature
context labels are not independent phase diagnostics.

### Admission and future original measurement packet preflight

Independent phase/receiver validation requires:

1. At least two demonstrably distinct experiment-run acquisitions, with
   source-pinned original numerical rows and source identities.
2. Documented physical conditions and calibrated **per-row measurement errors**.
3. Independently measured physical diagnostics, not labels assigned from
   temperature thresholds or the original table heading.
4. Confirmed experiment-family independence and a preregistered
   source-separated held-out evaluation (MAT-SPEC-009 only after admission).
5. Preservation of missing values, exact source units and original origin.

A reusable Python preflight rejects duplicate/blank identities, reused
run identifiers, forged primary status, synthetic measurements and missing
uncertainties. Even a record that passes all structural checks returns
`STRUCTURAL_ONLY_UNAUTHENTICATED`, **never empirical admission**.
Synthetic positive/negative examples are unit-test controls, not physics.

The present physical gate explicitly reports no classifier, no p-values,
no measured two-campaign phase classification accuracy, and no
independent held-out result. This is not a claim of failed physical
replication or a falsification of superfluidity.

## Output and reproducibility

Seven data/decision artifacts plus manifest (eight total):

- `contract.json`: v0.1.0 immutable analysis contract
- `source-catalogue.json`: ten attributed research documents
- `campaigns.csv`: four acquisition campaign source-status records
- `candidate-pairs.csv`: six inter-campaign comparison eligibility decisions
- `measurement-audit.json`: evidence counts from source-pinned documents
- `admission.json`: scientifically blocked decision and reasons
- `protocol.json`: prerequisites for future 009 data admission
- `manifest.json`: parent, input, implementation and output identities

Python 3.11+ standard library, no project dependency or network:

```sh
uv run --no-project python -m unittest discover -s tests -p 'test_mat_spec*.py' -v
uv run --no-project python scripts/build_mat_spec_008.py --out dist/mat-spec-008
```

Fresh no-follow, no-overwrite POSIX output directories and strictly JSON/CSV
artifacts. No root MIDI playback, PCM buffers or sampled audio are generated.

## Programme boundary

The numbered materials programme still terminates at MAT-SPEC-010.
MAT-SPEC-009 is an explicitly gated experiment: if independent physical
measurement packets cannot be obtained, it must publish an executable
negative finding rather than a fabricated phase score. MAT-SPEC-010
will freeze the final series and hand over to separately versioned
SPARK/Ada verification and the existing VANILLAJS Lean/ECMAScript repair.
