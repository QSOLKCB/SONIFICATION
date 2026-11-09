# SPARK-001 — Bounded exact numerical verification pilot

The MAT-SPEC programme ended at MAT-SPEC-010. This is a new
**software-verification** stream; no MAT-SPEC-011 or revised helium
phase-classifier claim is introduced.

## Bounded semantics

* SPARK_Mode unit: verification/spark/spark_core.ads/.adb.
* Exact signed integer **hundredths**, range -999999 to +999999, no floating-point.
  This is intentionally narrower than arbitrary-precision rational arithmetic.
* Parse_Cents: optional minus, one to four whole digits, mandatory decimal
  point and exactly two fractional digits. Negative zero canonicalizes to
  integer zero; malformed values and overflow are rejected.
* Closed interval Compare: BELOW, ABOVE, OVERLAP (including touching),
  MISSING. Absent/invalid remain distinct from measured/limit-zero.
* Fixed-width campaign, lab, acquisition-run, document, measurement-hash,
  diagnostic-hash, event, and partition separation. ID comparison does not
  cryptographically authenticate the claimed source evidence.

The Ada CLI (spark_probe.adb) is a separate demonstration wrapper outside
SPARK_Mode. The Python stdlib oracle exercises fixed-seed adversarial
vectors and checks the native results. No network or runtime dependencies
are needed once GNAT 13 is installed.

## Evidence levels

| Contract | Method | Status |
|---|---|---|
| SPARK source contracts | Ada pre/postconditions and expression functions | Authored, not proof |
| Ada compiler | Ubuntu 24.04 GNAT 13, compile under CI | Verify CI result |
| Behavior | Ada CLI against independent Python reference | Verify CI result |
| Formal VC discharge | GNATprove with pinned version/assumptions | **NOT_EXECUTED until a real prover run** |
| Independent physics | Original experiments, uncertainties, phase witnesses | Remains BLOCKED |

An Ada compilation and 300+ differential vectors do not certify universal
correctness or prove any properties of helium. GNATprove must be executed
and its exact proof obligations/assumptions retained before describing the
software as formally proved.

## Reproduction on Linux

From the SONIFICATION checkout, with GNAT 13 already installed:

    mkdir -p /tmp/qsol-spark-001
    cd /tmp/qsol-spark-001
    gnatmake-13 -gnat2022 -gnata -I/path/to/SONIFICATION/verification/spark \
      /path/to/SONIFICATION/verification/spark/spark_probe.adb \
      -o /tmp/qsol-spark-001/spark_probe

    cd /path/to/SONIFICATION
    uv run --no-project python scripts/verify_spark_001.py \
      --exe /tmp/qsol-spark-001/spark_probe

Run a separately installed GNATprove (with a compatible GNAT):

    mkdir -p verification/spark/obj
    gnatprove -P verification/spark/spark_core.gpr \
      --mode=all --level=2 --report=statistics \
      --checks-as-errors=on --warnings=error --proof-warnings=on

The dedicated workflow (.github/workflows/spark-001-proof.yml) is
**workflow_dispatch only** and guarded for reviewed main, the explicit
owner authorizer, and the trusted qsol-rtx5060ti runner label.
It refuses absent tools and retains the executed logs locally in a
new immutable-by-path run directory; uploading evidence requires a
second explicit opt-in. It does not run automatically on pull requests
or unmerged branches.

By default GNATprove can exit **zero despite unproved check messages or
warnings**. This verification workflow uses `--checks-as-errors=on` and
`--warnings=error` (plus `--proof-warnings=on`) so those conditions
cause a **nonzero exit**. Bash `set -o pipefail` propagates this through
`tee`; `steps.prove.conclusion` records failure rather than success.
The PROOF.log is included in the source/toolchain SHA-256 receipt even
when obligations are not discharged. This is strict proof admission,
not a guarantee that an empty proof obligation set proves useful code.

If the prover is missing, a VC is unproved, or any assumption is unresolved,
mark the result UNPROVED. Do not replace failed proof with successful tests.
Capture the exact compiler/prover versions, proof logs, and full source SHA.

The module does not create or buffer PCM, WAV, audio waveforms or synth output.
The root ETQ audio prohibition stays unchanged.

## After this pilot

Next: actual GNATprove execution and proof hardening, then a separate
QSOLKCB/VANILLAJS Lean-to-ECMAScript refinement repair. The latter
must retain the Q16-FORMAL-002 historical seals and the existing
REFINEMENT_OPEN status until scoped proof is executed.
