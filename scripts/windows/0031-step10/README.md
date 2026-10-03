# 0031-FEAT Step 10 Windows tooling

These scripts implement **Step 10 — Create one Files root per independent
non-production database dataset**.

For the normal developer configuration, `local.env` selects the paired common
local dataset:

```text
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

Therefore Step 10 creates **one** candidate root:

```text
.../diaries-content/files-development-common
```

It does not create three copies merely because there are three local launch
modes. If `local.env` is absent and the committed isolated defaults are in use,
run the script once for each independent mode/dataset that actually needs a
candidate Files root.

## Safety contract

Both the local and production responder write freezes from Steps 8–9 must still
be in force. The old shared tree remains the production Files root during this
step, so the script requires explicit confirmation that the production freeze is
still active.

The script refuses to:

- run while a known local responder container is running;
- run while TCP/8081 is listening for a direct Windows responder;
- accept an invalid database/Files pair;
- use `files` as a non-production target;
- merge into or overwrite an existing target root;
- seed from a source that no longer exactly matches the Step 8
  `SOURCE-SHA256.tsv` baseline; or
- proceed if `.image-staging` no longer matches the Step 9 reviewed disposition.

## Normal common-local run

From the Diaries project root:

```bat
scripts\windows\0031-step10\seed-local-files-root.bat -ProductionWriteFreezeConfirmed
```

The default `-Mode local-docker-build` is only used to resolve the effective
configuration. With the normal `local.env` override, all three local modes resolve
to the same `common` database and `files-development-common` target.

To resolve another active isolated default explicitly:

```bat
scripts\windows\0031-step10\seed-local-files-root.bat ^
  -Mode development-infrastructure ^
  -ProductionWriteFreezeConfirmed
```

Do not run this three times when `local.env` selects the common dataset: after
the first successful common run the target exists, and later runs deliberately
refuse to merge into it.

## Copy and verification behaviour

The script:

1. resolves the effective `DIARIES_DB_DATA_DIR` + `DIARIES_FILES_DIR` pair;
2. verifies the local responder write freeze and requires explicit production
   freeze confirmation;
3. locates the newest valid Step 8 snapshot under `.0031-backups` unless
   `-Step8SnapshotParent` is supplied;
4. creates a complete SHA-256 inventory of the current shared source and requires
   an exact match with Step 8 `SOURCE-SHA256.tsv`;
5. enforces the Step 9 staging disposition: absent staging is accepted, or the
   only file may be the reviewed zero-byte `.image-staging/catalogue.lock`;
6. builds the approved seed inventory from the whole source **except
   `.image-staging`**;
7. copies to a temporary sibling root with `robocopy /E /COPY:DAT /DCOPY:DAT
   /XJ`, excluding `.image-staging`;
8. requires a complete SHA-256 match between the approved seed inventory and the
   temporary copy;
9. promotes that verified temporary root to the configured final leaf only after
   verification succeeds;
10. performs a create/write/read/delete permission probe in the new root and
    proves the probe leaves the SHA-256 inventory unchanged; and
11. captures source/target ACL/SDDL information for operator review.

The four Step 9 `Thumbs.db` files are copied. They were explicitly classified as
non-application metadata, but copying them is harmless and lets the new root be
an exact copy of all non-staging source bytes. The transient
`.image-staging/catalogue.lock` is deliberately not copied.

The original shared `files` tree and the Step 8 rollback snapshot are never
deleted by this tooling.

## Evidence

A timestamped evidence directory is created under:

```text
change-control/in-progress/0031-FEAT - isolate mutable Files storage by database environment/
  evidence/Step 10/runtime/YYYYMMDD-HHMMSS/
```

It contains the source/target SHA-256 inventories, robocopy log, ACL captures,
console transcript and `STEP10-REPORT.json` / `.md`.

A successful script run means the candidate root has been created and verified.
Before Step 10 is formally closed, review `SOURCE-ACL.txt` and `TARGET-ACL.txt`
(or the equivalent NAS permissions) to confirm the new root is not unexpectedly
more broadly writable than the old root. Step 11 then verifies the actual
responder runtime against the new root while destructive lifecycle testing is
still deferred.
