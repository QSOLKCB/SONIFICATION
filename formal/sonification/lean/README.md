# Execute the mathematical model audit

Use the actual Lean 4.19.0 binary and a new output directory:

```sh
python3 formal/sonification/lean/check.py \
  --lean /path/to/lean-4.19.0/bin/lean \
  --out /tmp/sonification-new-attempt \
  --baseline-commit FULL_REVIEWABLE_INPUT_COMMIT
```

The optional baseline argument compares every proof input to the designated Git
object. Omit it only for a development attempt. A PASS is execution evidence for
the named mathematical model, with Python refinement OPEN. It does not accept a
project claim automatically. New output directories are mandatory; original
logs are never overwritten.

The runner freshly compiles both model modules, the import root, and the typed
consumer/audit module. It requires the exact 217 originating declarations and
19 intended theorem names from this input version. Auto-generated kernel
results are present in the audit and do not inflate the intended theorem count.
Toolchain imports, individual source inputs, exact commands, raw logs, and every
declaration's transitive axioms are recorded. See `../SPECIFICATION.md` for the
scope and the treatment of compiler-generated unsafe auxiliaries.

`attempts/` contains append-only development diagnostics and source snapshots,
including unsuccessful elaboration and trust-audit attempts. Those snapshots
are archived development evidence, excluded from the active proof-module set.
They must not be presented as additional proved modules. The exact active set
is `Sonification/Intervals.lean`, `Sonification/OrderedIntervals.lean`,
`Sonification.lean`, and `Audit.lean`; adding another active `.lean` fails coverage.

`lakefile.toml` declares the same libraries for conventional local use. The
receipt runner invokes Lean explicitly and pins its effective version instead
of relying on a global `lake` or `elan` default. No downloaded dependencies,
NPM packages, or audio generation are used.
