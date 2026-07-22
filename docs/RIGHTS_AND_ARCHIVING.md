# Authorship, Licensing, and Archiving

## Authorship goal

This project permits reuse while keeping origin and changes visible. Trent
Slade / QSOL-IMC is identified as the original creator in [`NOTICE`](../NOTICE),
[`AUTHORS.md`](../AUTHORS.md), and [`CITATION.cff`](../CITATION.cff).

The repository uses the
[Mozilla Public License 2.0](https://www.mozilla.org/MPL/2.0/). MPL-2.0 allows
use, modification, and commercial distribution, but distribution of covered
source files and modifications must remain under MPL-2.0, their Source Code
Form must be available, and the substance of copyright and licence notices may
not be removed or altered. Separate files in a larger work may use other terms.

This strikes the intended balance: other people may build on the work, but they
must preserve the original notices and cannot honestly present Trent Slade's
covered source or text as solely their own creation.

## What the licence cannot monopolise

Copyright protects original expression, not abstract ideas, facts,
mathematical truths, scientific principles, or independently created methods.
The project claims authorship of its original specification, code, concrete
selector, compilation, fixtures, symbolic mappings, separate-laboratory audio
mappings, and documentation—not private ownership of E8, D4 triality, qutrit
algebra, the golden ratio, pi, or conventional reference-frequency values.
The golden ratio and 432 Hz appear only in legacy or separate-laboratory
material, not as forward ETQ-101 v2 anchors.

Australian copyright generally arises automatically in qualifying original
expression. See the Australian Attorney-General's
[copyright basics](https://www.ag.gov.au/rights-and-protections/copyright/copyright-basics)
and the [Copyright Act 1968 (Cth)](https://www.legislation.gov.au/C1968A00063/latest/text).

## Licence history

An earlier repository revision was released under the MIT License. Rights
already granted for that revision remain valid. The branch introducing ETQ-101
changes the current project to MPL-2.0 prospectively; it does not attempt to
withdraw the earlier MIT grant.

## Citation and provenance

When using the repository in research, software, recordings, articles, or
presentations:

1. retain `LICENSE` and applicable source notices as MPL-2.0 requires;
2. retain `NOTICE` when redistributing the project as a whole;
3. identify modifications accurately; and
4. cite the project using `CITATION.cff` and a DOI for the same released
   version, once available.

Git hashes, ETQ contract hashes, basis hashes, adjacency hashes, release tags,
and archive DOIs should be recorded together. Hashes show artifact identity;
they do not by themselves prove legal authorship.

## Zenodo record policy

The repository includes [`.zenodo.json`](../.zenodo.json) for the current open
software deposit under MPL-2.0. Version-specific archives must remain distinct:

- ETQ-101 v2.0.0: `10.5281/zenodo.21432511`;
- ETQ-303 v3.0.0: `10.5281/zenodo.21455181`; and
- ETQ-303 v3.0.1: documentation-only clarification, with its version DOI to be
  added after Zenodo publishes the new version.

For each new version:

1. archive an immutable release tag, not a moving branch;
2. preserve prior version tags, files, and DOI metadata unchanged;
3. confirm creator spelling, affiliation, and verified ORCID metadata;
4. regenerate checksums for every changed publication artifact;
5. confirm the new version DOI back into `CITATION.cff` and release notes; and
6. verify Zenodo's current rights field in the draft interface.

Zenodo record metadata remains separately reusable under Zenodo's metadata
terms. Keep the public record accurate and avoid claiming that the archive DOI
validates the model's scientific interpretation.
