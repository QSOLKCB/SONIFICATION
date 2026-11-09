# MAT-SPEC-005 v0.1.0 — Two-sided helium reference and independent-witness gate

## Distinguishing physical phase evidence from classification accuracy

This independent, additive profile extends the frozen MAT-SPEC-001–004 series
without modifying any ancestor implementation, mapping, dataset or DOI.
The **MAT-SPEC-001 record DOI 10.5281/zenodo.24062652** remains associated
with MAT-SPEC-001 only. MAT-SPEC-005 has **no new DOI**.

For the first time in the series, we analyze a reference whose **measured
thermophysical properties span both sides of the lambda transition**, instead
of a helium-II-only parameter table. A physical phase transition is already
established in the external literature; this profile does **not** claim to
discover or independently reproduce it from a classifier.

### Physical source and licensing

Donnelly, R. J., and Barenghi, C. F., *The Observed Properties of Liquid
Helium at the Saturated Vapor Pressure*, Journal of Physical and Chemical
Reference Data **27**, 1217–1274 (1998), DOI 10.1063/1.556028.

Official NIST-hosted PDF: https://srd.nist.gov/jpcrdreprint/1.556028.pdf
Newcastle presentation: https://www.mas.ncl.ac.uk/helium/

The data are **experiment-derived, evaluated reference recommendations**,
including spline-based values from a literature compilation. They are not
original sensor readings, individually replicated rows, directly reported
error intervals or an experimental dataset newly collected by QSOL-IMC.

Precisely 14 rows from the following published recommendation tables are
transcribed as numerical facts, with original units and printed representation:

- Table 3.3, first sound speed, printed page 1230, both sides of lambda.
- Table 4.3, second sound speed, printed page 1233, helium-II only.
- Table 7.4, heat capacity, printed page 1241, both sides of lambda.

Original AIP/ACS publication rights remain with their holders. No claim is
made that the original paper is CC BY or that the entire PDF can be relicensed.
All provenance lives next to the excerpt's source file. The 14-row excerpt
and its source checksum are frozen for the v0.1.0 contract.

### Experimental conditions and labels

The reference concerns helium-4 along the **saturated vapour pressure** line,
using the ITS-90 temperature scale and the published context lambda point
T_lambda = **2.1768 K**.

The sample contains nine rows below, one at the published lambda reference,
and four above. The resulting `CONTEXT_HE_II` and `CONTEXT_HE_I` tags are
**derived solely from published temperature context**. They are not independent
per-row sensor-assigned phase labels and are not eligible targets for a
blind classifier validation. No hidden threshold classifier is trained.

### Strict missingness / zero separation

At the lambda reference, Table 4.3 lists recommended second-sound speed
`0.000E+0`: it is a *boundary/limit value*, not a new observed
detector result. The sound receiver preserves this explicit zero as unpitched.

For T>T_lambda, second-sound values are **not tabulated** by Table 4.3.
The resulting values are null/OUTSIDE_RECOMMENDED_DOMAIN, **not zero** and not
proof of a measured above-transition non-detection.

Table 7.4 marks heat capacity *undefined* exactly at lambda (represented as
null), and provides no entry at the selected T=2.1800 K (also null but a
different missingness status). Both remain distinct from true zero.

For all three observables, per-row experimental uncertainty and covariance
are **not reported in these recommended tables**. They remain null.
Significant digits in the printed recommendations are not substituted as
experimental error bars. No confidence level, p-value or statistical phase
separation is reported.

### Exact numerical comparison

At T=2.1767 K and T=2.1769 K, the selected recommended values are:

| Observable | Below lambda | Above lambda | Above-minus-below |
|---|---:|---:|---:|
| First sound speed (m/s) | 217.5 | 217.8 | +0.3 |
| Heat capacity (J/mol K) | 66.40 | 45.69 | -20.71 |
| Second sound speed (m/s) | 0.9809 | null | Ineligible |

These are changes between **recommended values**, not a discontinuity
measured by one continuous experiment. The heat-capacity value *at* lambda
is explicitly undefined. No inference is made about a critical exponent.

### Receiver separation

We assign **three independent, authored positive scales**:
- first sound u1 (m/s): 2 Hz per m/s;
- second sound u2 (m/s): 40 Hz per m/s;
- heat capacity Cs (J/mol K): 16 Hz per (J/mol K).

Each conversion is exactly reversible on the source decimal strings.
The resulting Hz targets are **symbolic control values**, not a conversion
of the measured speed/capacity to the actual sound frequency in helium.
No feature from one unit system is silently substituted for another.

Nearest 12-tone equal-temperament MIDI pitch (A4=440 Hz) is an intentionally
lossy receiver. In particular, the 14 first-sound rows collapse to one
symbolic MIDI pitch even though they contain distinct reported speeds.

Executed source-pinned summaries: 14 first-sound rows represent eight distinct
reported speed values but collapse to **one** MIDI pitch (91 colliding row pairs).
The 12 heat-capacity rows represent 12 distinct values but only **eight** MIDI
pitches (five colliding pairs). The nine positive second-sound values map to
nine distinct MIDI pitches; the tenth tabulated row is the **unpitched lambda
boundary zero**, not a tenth MIDI note. Of the two nearest cross-lambda
rows, first sound maps to [69,69] but heat capacity to [84,78]. These
outcomes describe the authored symbolic receiver, not listening behaviour.

No MIDI playback, PCM buffer, WAV or audible synthesis is produced.

### Experimental evidence hierarchy

- `cross_transition_reference: REPLAY_VERIFIED`: exact extraction/receiver
  identities match this frozen excerpt; both sides of lambda occur in
  evaluated reference tables.
- `independent_phase_witness: BLOCKED_INSUFFICIENT_INDEPENDENCE_AND_UNCERTAINTY`:
  the tables are one evaluated compilation, the temperature-context labels are
  not independent phase observations, above-lambda second-sound non-detection
  is **not tabulated**, per-row uncertainties are missing, and no separate
  preregistered training/held-out physical experiment exists.
- No phase accuracy, listener discrimination, critical exponent, or E8 result
  is calculated or inferred.

More independent measurements are required to earn the higher evidence gate.
The code rejects any injection of purported independently witnessed phase
labels into this frozen source profile.

### Files, verification, provenance

Python >=3.11, standard library, offline and symbolic-only.

```sh
uv run --no-project python -m unittest discover -s tests -p 'test_mat_spec*.py' -v
uv run --no-project python scripts/build_mat_spec_005.py --out dist/mat-spec-005
```

Outputs: `contract.json`, `observations.json`,
`receiver-controls.csv`, `crossing.json`,
`phase-gate.json`, `audit.json`, `manifest.json`.

The directory must be new. POSIX descriptor-anchored no-follow writes and the
fixed JSON/CSV allowlist retain the MAT-SPEC root security boundary.
SHA-256 receipts bind the source, config, implementation, all seven new
outputs and the frozen MAT-SPEC-004 parent results, themselves recursively
anchored to the v001–003 ancestors. The manifest excludes its own digest.
Hashing is evidence of identity, not correctness of the physical experiment.

The explanatory documentation is new CC BY 4.0 research prose; new code
remains MPL-2.0; the original factual source retains its own attribution
and rights.
