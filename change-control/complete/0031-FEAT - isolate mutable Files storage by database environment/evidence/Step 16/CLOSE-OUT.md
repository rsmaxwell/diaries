# 0031-FEAT — Step 16 close-out

**Decision:** COMPLETE — 2026-10-03

Step 16 and 0031-FEAT are closed. The two required final runtime captures both
passed, after the Step 16 harness was corrected for the actual Playbooks
location on `mango` and for Windows PowerShell 5.1 native-stderr handling.

## Authoritative final regression

```text
runtime/final-regression-20261003-104658
```

The final sealing run proved:

- the Playbooks SSH/repository preflight on `mango` passed;
- all accumulated Diaries 0031 source/contract validators passed;
- all existing production Playbooks 0031 validators passed remotely from
  `/home/richard/playbooks`;
- isolated local defaults, the paired common override, and one-sided mismatch
  rejection passed;
- the full Java responder/web test suite completed with `BUILD SUCCESSFUL`;
- the Angular production build completed successfully;
- the final Diaries and Playbooks source identities were captured.

The console run ended:

```text
PASS: 0031-FEAT Step 16 final source/application regression completed.
```

## Authoritative restore/rollback rehearsal

```text
runtime/restore-rehearsal-20261003-104511
```

The rehearsal used the preserved Step 8 local-common database backup:

```text
data/database-backups/common/diaries-common-step8-premigration-20261002-142614.dump
```

and the intended mutable Files root:

```text
files-development-common
```

The backup was restored into disposable PostgreSQL rather than over the live
local database. The 0024 reconciliation ran in dry-run mode against the restored
database/Files pair, Gradle completed with `BUILD SUCCESSFUL`, and the script
ended:

```text
PASS: Step 16 disposable common-dataset restore/reconciliation rehearsal succeeded.
```

The temporary PostgreSQL/configuration resources are cleanup-only rehearsal
state and are not part of the durable evidence.

## Acceptance decision

`ACCEPTANCE-MATRIX.md` maps every acceptance criterion in the 0031 feature README
to evidence from Steps 1–16. There is no remaining pending acceptance row.

In particular, the completed feature establishes that:

- production and non-production mutable Files are physically isolated;
- each independent persisted database dataset has an explicit matching mutable
  Files root;
- the three normal local launch modes may intentionally share only the approved
  `common` + `files-development-common` pair;
- crossed, one-sided or production-root local selections fail validation;
- Docker keeps `/data/files` stable while the physical NAS root varies;
- `/files/...` and persisted `Image.relativePath` remain environment-neutral;
- database backup/restore is explicitly database-only unless the matching Files
  side is also preserved and verified;
- rollback never automatically merges divergent Files roots.

Steps 13 and 14 remain the authoritative runtime proof for local Image lifecycle
isolation from production and for the explicit non-destructive production
deployment. Step 16 intentionally reused that evidence instead of introducing
another production Image mutation merely for close-out.

## Non-blocking follow-ups retained

The Step 13 close-out recorded two follow-ups that remain outside 0031:

1. revisit a bounded complete retained-snapshot protocol after the current TODO
   features are complete;
2. separately redact signin credentials/tokens from responder MQTT-RPC
   diagnostic logging.

Neither follow-up weakens the completed database/Files isolation invariant.

## Administrative closure

The feature directory is moved intact from:

```text
change-control/in-progress/0031-FEAT - isolate mutable Files storage by database environment
```

to:

```text
change-control/complete/0031-FEAT - isolate mutable Files storage by database environment
```

The move preserves the Step 16 runtime evidence. The `LATEST-FINAL-REGRESSION`
and `LATEST-RESTORE-REHEARSAL` pointers are rewritten to their new complete-path
locations by the close-out apply script.

No application runtime, database rows, Image bytes, production Files bytes or
MQTT retained state are changed by this administrative close-out.
