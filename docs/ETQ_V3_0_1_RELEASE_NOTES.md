# ETQ-303 v3.0.1 — terminology and exposition clarification

ETQ-303 v3.0.1 is a documentation-only patch to the exact protocol archived as
v3.0.0. It responds to reader feedback by removing any possible ambiguity
between algebraic vector-space dimension and physical spacetime dimension.

## Clarifications

- Added a “Notation and conventions” subsection declaring complex scalars,
  finite-dimensional state spaces, algebraic `dim(V)`, tensor products over
  `C`, and the domains on which operators act.
- Made the tensor construction and its dimension explicit:

  \[
  \mathcal H_{303}=\mathcal H_{101}\otimes\mathbb C^3,
  \qquad
  \dim(\mathcal H_{303})
  =\dim(\mathcal H_{101})\dim(\mathbb C^3)
  =101\times3
  =303.
  \]

- Stated that 303 is the dimension of the finite event/state vector space and
  the number of basis-indexed states, not a claim of 303 physical dimensions.
- Clarified that `E8` is realized in an 8-dimensional Euclidean root space,
  `D4` has algebraic rank 4, ETQ-101 contains 101 selected basis states, and
  ETQ-303 contains 303 tensor states.
- Added the canonical v3.0.1 LaTeX source, generated PDF, build instructions,
  and publication-file checksums to the repository.

## Change boundary

No mathematical construction, equation of motion, operator, state ordering,
event ordering, canonical JSON, schema, deterministic receiver, fixture,
checksum, implementation identity, test behavior, or scientific claim was
changed. The protocol's machine-readable identity remains v3.0.0.

The original Git tag `v3.0.0`, commit
`6b55e51647226d1c248dc8d79f9ed9336241c2ac`, and Zenodo DOI
`10.5281/zenodo.21455181` remain immutable.

## Zenodo v3.0.1 upload set

Replace the prior paper source and PDF with:

- `ETQ-303_formal_model_v3.0.1.tex`;
- `ETQ-303_formal_model_v3.0.1.pdf`; and
- regenerated `UPLOAD_SHA256SUMS.txt`.

Retain the unchanged `ETQ-303_references.bib`,
`ETQ-303_data_table_v3.0.0.xlsx`, and
`ETQ-303_parameter_table_v3.0.0.csv` under their existing names because they
describe the unchanged v3.0.0 protocol and data identity. If a convenience
archive is desired, rebuild it as `ETQ-303_Zenodo_Submission_v3.0.1.zip`
without altering those retained data files.
