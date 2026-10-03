# 0031-FEAT — Step 10 evidence

## Status

**COMPLETE — 2026-10-02.**

Step 10 creates one mutable Files root for each **independent non-production
database dataset**. With the current normal developer override, the three local
launch modes are one durable `common` dataset, so the required candidate is:

```text
./data/database/common
    -> files-development-common
```

Production deliberately remains on:

```text
production database
    -> files
```

No Playbooks source change is required by this step because production is not
being moved.

## Implementation

The operational tooling is under:

```text
scripts/windows/0031-step10/
```

Normal command from the Diaries project root:

```bat
scripts\windows\0031-step10\seed-local-files-root.bat -ProductionWriteFreezeConfirmed
```

The script keeps the Step 8/9 write freezes as hard gates, requires the current
shared source to match the Step 8 SHA-256 baseline, excludes the reviewed
`.image-staging` control state, copies to a temporary sibling directory, verifies
the complete approved seed inventory, and only then promotes the copy to
`files-development-common`.

It never deletes the old `files` tree or the Step 8 rollback snapshot.

## Step 9 disposition carried into Step 10

The four `Thumbs.db` files classified in Step 9 as non-application metadata are
copied. This preserves all non-staging bytes exactly and does not make those
files part of the Image catalogue contract.

The reviewed zero-byte:

```text
.image-staging/catalogue.lock
```

is deliberately excluded. If `.image-staging` contains any other file, or if
the lock no longer matches the reviewed zero-byte identity, the script fails and
requires reconciliation/review before continuing.

## Completion evidence from the live run

A successful run writes a timestamped directory under `runtime/` containing:

```text
STEP10-CONSOLE.txt
STEP10-REPORT.json
STEP10-REPORT.md
SOURCE-FULL-SHA256.tsv
SOURCE-SEED-SHA256.tsv
TEMP-TARGET-SHA256.tsv
TARGET-SHA256.tsv
TARGET-POST-PROBE-SHA256.tsv
EXCLUDED-STAGING-SHA256.tsv
SOURCE-ACL.txt
TARGET-ACL.txt
ROBOCOPY.log
```

Step 10 can be closed when the runtime evidence proves:

- the source still exactly matches the Step 8 baseline;
- the target is `files-development-common` for the effective `common` database;
- source approved-seed and target SHA-256 inventories match exactly;
- `.image-staging` was deliberately excluded;
- the write/read/delete permission probe passed and left no file behind;
- the target permissions/ACL have been reviewed and are not unexpectedly more
  broadly writable than the old shared root; and
- neither the old production `files` tree nor the Step 8 rollback snapshot was
  deleted or overwritten.

The successful run is retained under `runtime/20261002-155755/`. It proved the
Step 8 source baseline still matched exactly, created and byte-for-byte verified
`files-development-common`, excluded only the reviewed zero-byte staging lock,
and passed the create/write/read/delete permission probe. The source and target
ACL captures were then reviewed and found equivalent; see
[`ACL-REVIEW.md`](ACL-REVIEW.md) and [`CLOSE-OUT.md`](CLOSE-OUT.md).

Both responder write paths remain frozen after Step 10. Step 11 performs the
configuration cut-over and non-destructive runtime-path verification.
