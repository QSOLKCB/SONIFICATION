#!/usr/bin/env bash
# SPDX-License-Identifier: MPL-2.0
# Manual, owner-executed proof receipt; never triggered on unreviewed PR code.
set -euo pipefail

REPO="$(git -C "$(dirname "$0")/.." rev-parse --show-toplevel)"
ALR_NEW="${ALR_NEW:-$HOME/.local/opt/alire-2.1.1/bin/alr}"
ALR_PROJECT="${ALR_PROJECT:-$HOME/qsol_spark_prover}"
BASE="${SPARK_002_RECEIPTS:-$HOME/spark-proof-receipts}"
PROJECT="$REPO/verification/spark002/spark_002_core.gpr"

[[ -x "$ALR_NEW" ]] || { echo "Alire executable not found: $ALR_NEW" >&2; exit 2; }
[[ -d "$ALR_PROJECT" ]] || { echo "Alire project not found: $ALR_PROJECT" >&2; exit 2; }
[[ -f "$PROJECT" ]] || { echo "SPARK-002 GPR not found: $PROJECT" >&2; exit 2; }

for name in spark_002_core.ads spark_002_core.adb spark_002_core.gpr; do
  git -C "$REPO" diff --quiet HEAD -- "verification/spark002/$name" || {
    echo "Tracked source differs from HEAD: $name" >&2; exit 2;
  }
done

mkdir -p "$BASE"
RECEIPT="$(mktemp -d "$BASE/SPARK-002-XXXXXXXX")"
chmod 700 "$RECEIPT"
git -C "$REPO" rev-parse HEAD > "$RECEIPT/SOURCE_COMMIT.txt"
(
  cd "$REPO"
  sha256sum verification/spark002/spark_002_core.ads \
    verification/spark002/spark_002_core.adb \
    verification/spark002/spark_002_core.gpr \
    > "$RECEIPT/SOURCES.sha256"
)
(
  cd "$ALR_PROJECT"
  "$ALR_NEW" --version
  "$ALR_NEW" exec -- gnatprove --version
) > "$RECEIPT/TOOLCHAIN.txt" 2>&1

# Preserve a failing proof log as first-class evidence. GNATprove's return
# status is captured before any receipt generation replaces it.
set +e
(
  cd "$ALR_PROJECT" || exit 2
  "$ALR_NEW" exec -- gnatprove \
    -P "$PROJECT" \
    --mode=all --level=2 --report=statistics \
    --checks-as-errors=on --warnings=error --proof-warnings=on
) > "$RECEIPT/PROOF.log" 2>&1
status=$?
set -e
cat "$RECEIPT/PROOF.log"
printf 'SPARK-002 GNATprove exit status: %s\n' "$status" \
  | tee "$RECEIPT/RESULT.txt"
SUMMARY="$REPO/verification/spark002/obj/gnatprove/gnatprove.out"
if [[ -f "$SUMMARY" ]]; then
  cp "$SUMMARY" "$RECEIPT/GNATPROVE_SUMMARY.txt"
fi
(
  cd "$RECEIPT"
  sha256sum SOURCE_COMMIT.txt SOURCES.sha256 TOOLCHAIN.txt PROOF.log RESULT.txt \
    > SHA256SUMS
  if [[ -f GNATPROVE_SUMMARY.txt ]]; then
    sha256sum GNATPROVE_SUMMARY.txt >> SHA256SUMS
  fi
  sha256sum -c SHA256SUMS
)
printf 'Evidence: %s\n' "$RECEIPT"
exit "$status"
