# ETQ-303 formal publication files

The repository's canonical human-readable paper is stored by documentation
version under this directory. The original v3.0.0 paper was published on
Zenodo but was not tracked in the Git repository.

| Version | Treatment |
|---|---|
| v3.0.0 | Immutable original release at DOI `10.5281/zenodo.21455181`, Git tag `v3.0.0`, commit `6b55e51647226d1c248dc8d79f9ed9336241c2ac` |
| v3.0.1 | Terminology and exposition clarification only; no protocol, state, event, fixture, hash, implementation, or claim change |

The v3.0.0 archive identifies its original source and PDF with these SHA-256
hashes:

```text
120b248d0af5100aa9720fda971f0fbf5a5f0ee924e4d8be74a9a08e182412f2  ETQ-303_formal_model_v3.0.0.tex
1e81d6836afc75287c6f064835470a284c462b8b3c014bb2a2ca3c7ab2b96c63  ETQ-303_formal_model_v3.0.0.pdf
```

Those archived artifacts are not modified by v3.0.1.

## v3.0.1 files

- `v3.0.1/ETQ-303_formal_model_v3.0.1.tex` — canonical LaTeX source;
- `v3.0.1/ETQ-303_formal_model_v3.0.1.pdf` — generated PDF;
- `v3.0.1/ETQ-303_references.bib` — bibliography preserved from v3.0.0; and
- `v3.0.1/UPLOAD_SHA256SUMS.txt` — hashes of the tracked publication files.

## Build

The publication build requires `latexmk`, `pdflatex`, and `biber`, together
with the LaTeX packages declared in the source preamble. From the repository
root, run:

```bash
npm run build:paper
```

The script builds in a temporary directory outside the repository, sets a fixed
`SOURCE_DATE_EPOCH`, fails on unresolved LaTeX diagnostics, writes the PDF
beside its source, and regenerates `UPLOAD_SHA256SUMS.txt`. Generated LaTeX
auxiliary files are not tracked.

To verify the checksum manifest:

```bash
cd docs/etq-303/v3.0.1
sha256sum --check UPLOAD_SHA256SUMS.txt
```
