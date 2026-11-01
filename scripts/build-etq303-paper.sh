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

if [[ -L "$paper_dir" || ! -d "$paper_dir" ]]; then
  echo "publication directory must be a real directory" >&2
  exit 1
fi
for final_name in "$pdf_name" "$checksum_name"; do
  if [[ -L "$paper_dir/$final_name" ]]; then
    echo "publication destination is a symbolic link: $final_name" >&2
    exit 1
  fi
done

build_dir="$(mktemp -d /tmp/etq303-paper-v3.0.1.XXXXXX)"
stage_dir="$(mktemp -d "$paper_dir/.etq303-publish.XXXXXXXX")"
cleanup() {
  rm -rf -- "$build_dir" "$stage_dir"
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

# Build publication bytes in a private, unpredictable directory. Atomic
# renames replace directory entries rather than following target symlinks.
cp -- "$build_dir/$pdf_name" "$stage_dir/$pdf_name"
for name in "$pdf_name" "$tex_name" "$bib_name"; do
  source_file="$paper_dir/$name"
  if [[ "$name" == "$pdf_name" ]]; then source_file="$stage_dir/$pdf_name"; fi
  digest="$(sha256sum "$source_file")"
  printf '%s  %s\n' "${digest%% *}" "$name"
done > "$stage_dir/$checksum_name"

for name in "$pdf_name" "$checksum_name"; do
  if [[ -L "$paper_dir/$name" ]]; then
    echo "publication destination became a symbolic link: $name" >&2
    exit 1
  fi
done
mv -fT -- "$stage_dir/$pdf_name" "$paper_dir/$pdf_name"
mv -fT -- "$stage_dir/$checksum_name" "$paper_dir/$checksum_name"

echo "built $paper_dir/$pdf_name"
echo "updated $paper_dir/$checksum_name"
