# Rights, Public Hosting, and Archiving

**Status:** Operational guidance, not legal advice  
**Licence:** QSOL-IMC Core Model Proprietary Source-Viewing Licence 1.0

## What the repository licence does

The current `LICENSE` reserves all rights in the protectable original code,
text, diagrams, selections, arrangements, fixtures, audio mappings, and other
expression added under it. It grants only narrow source-viewing permission and
does not grant a general right to execute, research, copy, modify, redistribute,
commercialise, or use the materials for AI or machine-learning purposes.

The initial repository revision was published under MIT. A later licence
change cannot retract MIT rights already granted in that earlier MIT-covered
revision. The proprietary licence applies prospectively to the newly added
ETQ-101 model and other material first published under it.

## Public GitHub is source-visible, not secret

A custom repository licence does not override rights separately granted by the
owner through GitHub's terms. In particular, public-repository hosting carries
service-level rights relating to access and forking, and GitHub's current terms
contain separate provisions for GitHub and its affiliates to process hosted
content, including for AI and machine-learning purposes. See the
[GitHub Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service)
and [GitHub's repository-licensing guidance](https://docs.github.com/articles/licensing-a-repository).

Accordingly:

- the repository is proprietary and source-visible, not confidential;
- the repository licence restricts downstream permissions to the extent the
  owner controls them;
- it cannot cancel GitHub's separate platform rights; and
- a private repository plus signed access agreements is materially stronger if
  secrecy is the primary goal.

No repository-visibility change is implied by this document.

## Copyright does not monopolise mathematics

Australian copyright arises automatically in qualifying original expression,
but it does not confer ownership of abstract ideas, facts, mathematical truths,
scientific principles, or independently created methods. ETQ-101's original
specification, code, concrete selector, compilation, fixtures, and mapping may
be protected to the extent the law permits; E8, D4 triality, qutrit algebra,
the golden ratio, pi, and 432 Hz are not privately owned by this project.

See the Australian Attorney-General's
[copyright basics](https://www.ag.gov.au/rights-and-protections/copyright/copyright-basics)
and the [Copyright Act 1968 (Cth)](https://www.legislation.gov.au/C1968A00063/latest/text).
Statutory exceptions and non-excludable rights remain unaffected.

## Patent and trade-secret boundary

Public disclosure is generally inconsistent with trade-secret treatment and
can affect patent strategy and filing deadlines. This licence grants no patent
rights, but a copyright licence alone does not create patent protection. If
patentability, confidential know-how, ownership-chain evidence, or commercial
exclusivity matters, obtain advice from a qualified Australian IP lawyer before
making additional technical disclosure.

## Zenodo record policy

The repository includes [`.zenodo.json`](../.zenodo.json) configured for a
`restricted` file deposit and the `other-closed` rights label. A future Zenodo
record should keep file access restricted, require a separately signed written
agreement, and include the repository `LICENSE` in the deposit.

Restricted files do not make the record private: Zenodo exposes bibliographic
metadata publicly, and metadata has separate reuse terms. Keep confidential or
patent-sensitive implementation detail out of the title, abstract, keywords,
and public notes. Review Zenodo's current
[access controls](https://help.zenodo.org/docs/deposit/about-records/),
[licences and rights guidance](https://help.zenodo.org/docs/deposit/describe-records/licenses/),
and [`.zenodo.json` guidance](https://help.zenodo.org/docs/github/describe-software/zenodo-json/)
before publishing a deposit.

## Before a formal release

1. Confirm that `Trent Slade` is the correct legal copyright-owner name and
   record any assignment to a company or other entity.
2. Obtain provenance confirmations for every third-party contribution.
3. Have Australian IP counsel review the licence, patent-disclosure position,
   and any contributor or access agreement.
4. Tag the exact release and archive that tag, not a moving branch.
5. Record the Git commit, ETQ contract hash, basis hash, adjacency hash, and the
   archive DOI together.
