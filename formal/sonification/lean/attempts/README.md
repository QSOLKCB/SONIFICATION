# Append-only attempt ledger

All `*.stdout` and `*.stderr` files are original prover outputs retained from
development. Some early shell wrappers ended by displaying a log: their wrapper
exit status was zero even when Lean reported errors. For attempts 001–016,
018–023, the prover exit code was not separately captured and remains UNKNOWN;
errors in their raw logs make them unsuccessful or diagnostic attempts, never
accepted proof receipts. Source snapshots are retained when they were captured;
the first failed input was not separately snapshotted. Do not infer a complete
input closure for those early diagnostics.

Attempts 017 and 020 use Python subprocess records with actual prover exit codes.
017 failed at the initial all-declaration trust audit. 020 preserved an
unsuccessful experiment with disabling Lean's new compiler; compiler auxiliaries
were still present. No mathematical theorem was weakened to resolve these
failures. Later audits explicitly separate unsafe compiler auxiliaries and
logical dependencies.

024-checked and 025-checked are complete fresh-run development records from
`check.py`, with exact command argv, per-step exit codes, source hashes, original
stdout/stderr, actual executable identity, imported toolchain module hashes,
complete declaration lists, and the 19 intended theorem IDs. They lack an
external reviewed baseline commit and do not accept production refinement.
The current runner source has passed Ruff; 025 records its formatted version.

Diagnostic counts are not proof counts. The 19 intended mathematical results
and the additional generated declarations are separately enumerated. Later
reviewed runs belong in new directories and must preserve these originals.
