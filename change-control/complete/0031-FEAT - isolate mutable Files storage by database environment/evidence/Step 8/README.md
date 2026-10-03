# 0031-FEAT — Step 8 evidence

## Status

**SOURCE IMPLEMENTATION COMPLETE — RUNTIME CAPTURE PENDING — 2026-10-02.**

The Step 8 operating tooling is now implemented for both the Windows/local and
production/Playbooks sides. The real PostgreSQL dumps and NAS snapshot cannot be
created in the source-packaging environment because it has no access to the live
Windows Docker databases, `pluto`, or the NAS.

Step 8 must therefore remain **open** until the supplied scripts are run against
the frozen live environments and their runtime evidence is retained here.

## Safety model

All mutable catalogue file operations are responder-owned. Step 8 freezes writes
by stopping the responder while deliberately leaving PostgreSQL available for
`pg_dump`.

The expected capture order is:

```text
1. Freeze local responders.
2. Freeze the production responder.
3. Back up the one effective local database dataset (normally common).
4. Back up the production database.
5. Snapshot the old shared physical Files root named files.
6. Keep both responder write paths frozen for Step 9 reconciliation.
```

No script deletes, renames, or repoints the live `files` directory. No new live
`files-development-*` root is created by Step 8.

## Important pre-split identity distinction

Steps 3 and 4 already configured the future common-local selector:

```text
DIARIES_FILES_DIR=files-development-common
```

but Step 8 is preserving the **pre-migration source tree** that both independent
databases historically relied on:

```text
.../diaries-content/files
```

The local Step-8 manifest records both values. This prevents the Step-7 database
sidecar's configured target selector from being mistaken for the source of the
pre-split rollback bytes.

## Windows/local tooling

Implemented under:

```text
scripts/windows/0031-step8/
```

The tools:

- stop known local Docker responder containers;
- block if TCP/8081 is still listening, catching a direct Windows responder;
- require exactly one local Diaries DB container for database capture;
- reuse the Step-7 binary database backup helper;
- record the old shared `files` source separately from the configured target
  Files selector;
- require explicit confirmation that production is frozen before copying Files;
- inspect `.image-staging` before the copy;
- copy the entire rollback tree with `robocopy`;
- generate complete SHA-256 source and snapshot inventories and require them to
  compare identically; and
- keep large inventory files beside the NAS snapshot rather than in Git.

## Production tooling

Implemented by the Playbooks `roles/diaries/files/sync/scripts/` directory:

```text
step8-freeze-writes.sh
step8-capture-production-database-backup.sh
```

The freeze helper stops only `diaries-responder`, verifies it remains stopped,
and verifies PostgreSQL is still running. The capture helper refuses to run if
the responder has restarted, asserts that production still selects the frozen
Step-2 source name `files`, reuses the Step-7 database backup helper, hashes the
dump and sidecar, and records runtime image/source identity.

## 2026-10-02 listener-check correction

The first live Windows freeze attempt proved both known Docker responder containers
were already stopped, but `Get-NetTCPConnection` failed while querying TCP/8081
through CIM in the non-elevated PowerShell session. The Step 8 Windows tooling was
therefore corrected to use
`System.Net.NetworkInformation.IPGlobalProperties.GetActiveTcpListeners()` for the
listener guard. The same correction is used by the freeze, local database-backup,
and shared-Files snapshot scripts so all three enforce the same write-freeze check
without relying on the privileged CIM query.

This correction does not relax the Step 8 invariant: any listener on TCP/8081 still
blocks the freeze/backup/snapshot sequence.

## Verification performed during implementation

Portable source verification:

```text
python scripts/windows/validation/verify-0031-step8.py
python roles/diaries/tests/verify-0031-step8.py
```

The production shell helpers also pass:

```text
bash -n roles/diaries/files/sync/scripts/step8-freeze-writes.sh
bash -n roles/diaries/files/sync/scripts/step8-capture-production-database-backup.sh
```

Captured implementation-time output is retained in this directory after
packaging.

## Runtime evidence required to close Step 8

Retain at least:

```text
local-write-freeze-*.txt
local-database-backup-*.txt
local-database-backup-*.json
production-write-freeze-*.txt
production-database-backup-*.txt
production-database-backup-*.json
shared-files-snapshot-*.txt
shared-files-snapshot-*.json
```

Also retain the actual database dumps/Step-7 sidecars in their normal backup
locations and the NAS snapshot directory containing its full source/destination
SHA-256 inventories and staging review.

Step 8 can be closed when these prove:

```text
local writes frozen
production writes frozen
one backup per independent non-production database dataset
production database backup
old shared Files rollback snapshot
source/snapshot inventories identical
.image-staging reviewed
all database + Files identities recorded
```

At that point rollback can restore the independent database contents together
with the known pre-split Files snapshot, and Step 9 can proceed without reopening
mutable writes.
