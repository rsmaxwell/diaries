# 0031-FEAT — Step 16 evidence

## Status

**COMPLETE — 2026-10-03.**

Step 16 — **Full regression, rollback rehearsal and feature close-out** — is
complete. The final exact-candidate regression and the disposable
restore/reconciliation rehearsal both passed, the acceptance matrix has no
remaining gap, and 0031-FEAT is closed.

The two commands used for the final evidence were:

```text
scripts\windows\0031-step16\run-final-regression.bat
scripts\windows\0031-step16\rehearse-common-restore.bat
```

The regression sealed the exact Diaries + Playbooks candidate and exercised the
source/application regression. The rehearsal restored the frozen Step 8
`common` database backup into disposable PostgreSQL and reconciled it read-only
against the intended `files-development-common` root without overwriting the
live common database.

## Why existing Steps 13–15 are reused

Step 16 does not repeat production mutation merely to produce another log:

- Step 13 already proves an authenticated local common upload, cross-mode observation, supported delete, stable `/files/...` serving and byte-for-byte unchanged production Image rows/Files inventory.
- Step 14 already proves the explicit production selector is deployed, the stack is healthy/non-destructive, `/files/...` serving remains correct, production reconciliation remains clean and the independent non-production Files roots did not change across production activation.
- Step 15 already makes the matched database/Files invariant normal operating documentation.

The missing Step 16-specific proof is therefore the exact-candidate full regression plus the requested restore/reconciliation rehearsal.

## New Step 16 tooling

Under `scripts/windows/0031-step16/`:

- `run-final-regression.bat` / `.ps1` — runs all current 0031 Diaries validators locally and the existing Playbooks validators remotely over SSH on `mango`, temporary precedence/mismatch fixtures, the full Gradle Java test suite and Angular client build; captures the final effective path map and SHA-256 identities of the release candidate.
- `rehearse-common-restore.bat` / `.ps1` — checksum-pins and restores the Step 8 common dump into disposable PostgreSQL, points only that disposable database at `files-development-common`, then runs 0024 reconciliation in dry-run mode and requires 85 catalogue matches with zero conflicts.
- `README.md` — operating notes and safety model.

The Step 16-specific portable source gate lives in the Diaries repository:

```text
python scripts/windows/validation/verify-0031-step16.py
```

The Playbooks side reuses the existing 0031 validators in `/home/richard/playbooks/roles/diaries/tests` and executes them remotely on `mango`; Step 16 does not create or require a duplicate Windows Playbooks checkout.

## Authoritative successful runtime evidence

The final exact-candidate regression is:

```text
runtime/final-regression-20261003-104658
```

It passed the local Diaries 0031 source/contract gates, the existing production
Playbooks 0031 validators remotely on `mango`, the full Java responder/web test
suite (`BUILD SUCCESSFUL`) and the Angular production build. Its source-identity
files seal the corrected Step 16 runner and restore-rehearsal script.

The final rollback/restore rehearsal is:

```text
runtime/restore-rehearsal-20261003-104511
```

It checksum-verified the preserved Step 8 common dump, restored it into
disposable PostgreSQL, and reconciled that restored database read-only against:

```text
files-development-common
```

The rehearsal ended:

```text
PASS: Step 16 disposable common-dataset restore/reconciliation rehearsal succeeded.
```

The two supplied console transcripts are retained at this Step 16 level as
supplemental evidence; the detailed authoritative files remain inside the two
runtime directories.

## Close-out rule

Both runs passed on 2026-10-03. `ACCEPTANCE-MATRIX.md` has no pending row,
`CLOSE-OUT.md` records the completed decision, and this feature is moved from
`change-control/in-progress` to `change-control/complete` while preserving the
runtime evidence directories intact.
