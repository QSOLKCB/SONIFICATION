#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
paper_dir="$project_root/docs/etq-303/v3.0.1"
tex_name="ETQ-303_formal_model_v3.0.1.tex"
pdf_name="ETQ-303_formal_model_v3.0.1.pdf"
bib_name="ETQ-303_references.bib"
checksum_name="UPLOAD_SHA256SUMS.txt"

for command_name in latexmk pdflatex biber sha256sum; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "required publication-build command not found: $command_name" >&2
    exit 1
  fi
done

build_dir="$(mktemp -d /tmp/etq303-paper-v3.0.1.XXXXXX)"
cleanup() {
  rm -rf -- "$build_dir"
}
trap cleanup EXIT

export TZ=UTC
export SOURCE_DATE_EPOCH=1784678400
export FORCE_SOURCE_DATE=1
export TEXINPUTS="$paper_dir:"
export BIBINPUTS="$paper_dir:"

(
  cd "$paper_dir"
  latexmk \
    -pdf \
    -interaction=nonstopmode \
    -halt-on-error \
    -file-line-error \
    -outdir="$build_dir" \
  "$tex_name"
)

log_file="$build_dir/${tex_name%.tex}.log"
if grep -Eiq \
  'LaTeX Warning|Package .* Warning|Overfull \\[hv]box|undefined|multiply defined|duplicate label|Empty bibliography|Please \(re\)run' \
  "$log_file"; then
  echo "publication build completed with unresolved LaTeX diagnostics:" >&2
  grep -Ein \
    'LaTeX Warning|Package .* Warning|Overfull \\[hv]box|undefined|multiply defined|duplicate label|Empty bibliography|Please \(re\)run' \
    "$log_file" >&2
  exit 1
fi

cp "$build_dir/$pdf_name" "$paper_dir/$pdf_name"

(
  cd "$paper_dir"
  sha256sum "$pdf_name" "$tex_name" "$bib_name" > "$checksum_name.tmp"
  mv "$checksum_name.tmp" "$checksum_name"
)

echo "built $paper_dir/$pdf_name"
echo "updated $paper_dir/$checksum_name"
