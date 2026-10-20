# 0037-FEAT — Step 7 source and integration verification

**Status:** OPEN — runner prepared, host execution and review outstanding.

## Purpose

Repeat the whole relevant Playbooks test surface after adding Step 6's guarded deletion command. Verify source syntax, established native manager regressions, Step 5 adversarial tests and Step 6 mock deletion tests. Check that guarded deletion is a separately invoked command not directly called by native prune or snapshot creation.

## Execution (Windows Cygwin)

From the Diaries repository root or any directory, execute:

```bash
bash "change-control/in-progress/0037-FEAT - unify legacy Snapper and timestamp snapshot retention/tests/step07-run-from-cygwin.sh"
```

Prerequisites: `ssh mango` works without interactive input for the streamed tests; `mango` has the Step 6 manager source at `/home/richard/playbooks/roles/snapshots/files/btrfs-snapshot-manager.py`. Source scripts `tests/step05-adversarial.py` and `tests/step06-guarded-regression.py` remain locally in this feature.

Output is streamed to the Cygwin terminal and captured under `evidence/Step 07/results.txt`. Any failure aborts the runner; a nonzero exit status means Step 7 is not satisfied. No temporary test scripts need transferring to `mango`. The remote Python compilation can regenerate a `__pycache__` under the Playbooks source (Python's ordinary cache); no temporary project test code is created.

## Acceptance

- Syntax and all previously passed regression suites PASS on actual `mango` source.
- No evidence of native `prune`/`run` behavioural changes.
- Guarded delete remains separate, requires explicit approval and `--execute`; simulated failures abort.
- Record source SHA-256, test output and any uncovered limitations; assess whether integration coverage is sufficient before formal close.
- Do not create approval policies, invoke live deletion, or deploy the Step 6 code to `mars`/`backup`.

## Limitations

Source checks cannot prove live deletion race safety, production scheduler stability or offsite receiver health. Those remain in later gates.
