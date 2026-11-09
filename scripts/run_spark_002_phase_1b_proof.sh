#!/usr/bin/env bash
# SPDX-License-Identifier: MPL-2.0
# Owner-executed only. Never authorize a self-hosted PR workflow implicitly.
set -euo pipefail

REPO="$(git -C "$(dirname "$0")/.." rev-parse --show-toplevel)"
ALR_NEW="${ALR_NEW:-$HOME/.local/opt/alire-2.1.1/bin/alr}"
ALR_PROJECT="${ALR_PROJECT:-$HOME/qsol_spark_prover}"
BASE="${SPARK_002_RECEIPTS:-$HOME/spark-proof-receipts}"
SCOPE="verification/spark002/phase1b"
PROJECT="$REPO/$SCOPE/spark_002_partition.gpr"

[[ -x "$ALR_NEW" ]] || { echo "Alire not found: $ALR_NEW" >&2; exit 2; }
[[ -d "$ALR_PROJECT" ]] || { echo "Alire project missing: $ALR_PROJECT" >&2; exit 2; }
[[ -f "$PROJECT" ]] || { echo "SPARK-002 Phase 1B GPR missing" >&2; exit 2; }

# No dirty or untracked source may masquerade as the recorded HEAD.
for name in spark_002_partition.ads spark_002_partition.adb spark_002_partition.gpr; do
  git -C "$REPO" ls-files --error-unmatch -- "$SCOPE/$name" >/dev/null
  git -C "$REPO" diff --quiet HEAD -- "$SCOPE/$name" || {
    echo "Source differs from recorded HEAD: $name" >&2; exit 2;
  }
done

mkdir -p "$BASE"
RECEIPT="$(mktemp -d "$BASE/SPARK-002-1B-XXXXXXXX")"
chmod 700 "$RECEIPT"
git -C "$REPO" rev-parse HEAD > "$RECEIPT/SOURCE_COMMIT.txt"
(
  cd "$REPO"
  sha256sum "$SCOPE/spark_002_partition.ads" \
    "$SCOPE/spark_002_partition.adb" \
    "$SCOPE/spark_002_partition.gpr" > "$RECEIPT/SOURCES.sha256"
)
(
  cd "$ALR_PROJECT"
  "$ALR_NEW" --version
  "$ALR_NEW" exec -- gnatprove --version
) > "$RECEIPT/TOOLCHAIN.txt" 2>&1

SUMMARY="$REPO/$SCOPE/obj/gnatprove/gnatprove.out"
if [[ -f "$SUMMARY" ]]; then
  cp -- "$SUMMARY" "$RECEIPT/PREVIOUS_SUMMARY.txt"
  rm -- "$SUMMARY"
fi

# Preserve failed proof attempts; strict exit code is never masked by tee.
set +e
(
  cd "$ALR_PROJECT" || exit 2
  "$ALR_NEW" exec -- gnatprove -P "$PROJECT" \
    --mode=all --level=2 --report=statistics \
    --checks-as-errors=on --warnings=error --proof-warnings=on
) > "$RECEIPT/PROOF.log" 2>&1
status=$?
set -e
cat "$RECEIPT/PROOF.log"
printf 'SPARK-002 Phase 1B GNATprove exit status: %s\n' "$status" \
  | tee "$RECEIPT/RESULT.txt"
if [[ -f "$SUMMARY" ]]; then
  cp -- "$SUMMARY" "$RECEIPT/GNATPROVE_SUMMARY.txt"
fi
(
  cd "$RECEIPT"
  find . -maxdepth 1 -type f ! -name SHA256SUMS -printf '%f\n' \
    | LC_ALL=C sort | xargs -r sha256sum > SHA256SUMS
  sha256sum --check --strict SHA256SUMS
)
echo "Evidence retained: $RECEIPT"
exit "$status"
