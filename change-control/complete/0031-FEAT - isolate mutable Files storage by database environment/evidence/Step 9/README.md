# 0031-FEAT — Step 9 evidence

## Status

**COMPLETE — 2026-10-02.**

Step 9 reconciled each independent effective database dataset against the frozen pre-split shared `files` tree in read-only/dry-run mode:

```text
local common dataset  -> frozen shared .../files tree
production dataset    -> frozen shared .../files tree
```

The three normal local launch modes are one effective durable dataset while `local.env` selects `./data/database/common`, so they were correctly reconciled once rather than three times.

See [`CLOSE-OUT.md`](CLOSE-OUT.md) for the completion decision and [`DISPOSITION.md`](DISPOSITION.md) for the explicit treatment of the reported non-catalogue/staging entries.

## Result

Both reconciliations produced the same result:

```text
catalogued Image rows:       85
matching physical files:     85
missing physical files:      0
untracked physical files:     4
untracked supported images:  0
unsupported physical files:  4
metadata/checksum conflicts: 0
reconciliation conflicts:    0
.image-staging files:        1
```

The four unsupported entries are identical `Thumbs.db` Windows thumbnail caches in both runs. The one staging entry is the identical zero-byte `.image-staging/catalogue.lock`. Those five entries are explicitly reviewed and dispositioned; no repair is required.

## Runtime evidence retained here

```text
runtime/local-common-20261002-151207-console.txt
runtime/local-common-20261002-151207-exception-review.txt
runtime/production-20261002-153306-console.txt
runtime/production-20261002-153306-exception-review.txt
```

The original generated local runtime directory remains in the Step 9 `runtime` evidence tree on the Windows working copy. The production helper generated its raw runtime directory at:

```text
/home/richard/projects/diaries/data/0031-step9/production-20261002-153306/
```

The retained console transcript includes the generated production `STEP9-REPORT.md` contents and the subsequent exception inventory review.

## Implementation tooling

### Local/Windows

```text
scripts/windows/0031-step9/reconcile-local-shared-files.bat
```

The local wrapper preserves the Step 8 write freeze, requires exactly one local database container, validates the normal target dataset pair, starts from the Step-4 generated/effective responder configuration, temporarily selects the frozen pre-split `files` tree, invokes the existing 0024 reconciliation in dry-run mode, and inventories `.image-staging` separately.

### Production

```text
roles/diaries/files/sync/scripts/step9-reconcile-production.sh
```

The production helper requires the responder to remain stopped, PostgreSQL to remain running, and production `DIARIES_FILES_DIR=files`. It runs the same 0024 dry-run reconciliation in a disposable responder container and inventories `.image-staging` from the same `/data/files` mount.

## Source verification

Portable verification commands remain:

```text
python scripts/windows/validation/verify-0031-step9.py
python roles/diaries/tests/verify-0031-step9.py
bash -n roles/diaries/files/sync/scripts/step9-reconcile-production.sh
```

## Hand-off

Keep both responder write paths frozen. Step 10 may now seed the new non-production Files root from the verified shared source tree, following the explicit Step 9 staging/transient-content disposition rather than blindly propagating it.
