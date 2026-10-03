# 0031-FEAT — Step 10 close-out

**Decision:** COMPLETE — 2026-10-02

Step 10 — **Create one Files root per independent non-production database
dataset** — is closed.

With the normal local override, all three local launch modes consume the same
durable `common` database dataset, so exactly one candidate Files root was
required and created:

```text
./data/database/common
    -> files-development-common
```

Production remains on the existing `files` root and was not copied to a new
production root.

## Successful live seed

The successful Windows run is retained as:

```text
runtime/20261002-155755/STEP10-CONSOLE.txt
```

The run used the workstation's mapped `P:` NAS drive because the default
`\\nas.localdomain\photo\...` UNC route was not accessible from that Windows
session. The explicit source and target paths were:

```text
P:\nancy-and-ronald-maxwell\documents\sea-captains-chest\diaries-content\files
P:\nancy-and-ronald-maxwell\documents\sea-captains-chest\diaries-content\files-development-common
```

The run proved:

```text
Effective database dataset:       ./data/database/common
Effective Files selector:         files-development-common
Step 8 source baseline:           step8-20261002-143134
Frozen source inventory:          90 files / 100032776 bytes
Approved seed inventory:          89 files / 100032776 bytes
Excluded staging entries:         1
Temporary target hash comparison: exact match
Files copied:                     89
Bytes copied:                     100032776
.image-staging propagated:        no
Create/write/read/delete probe:   PASS
Final result:                     CANDIDATE ROOT READY
```

The source still matched the complete Step 8 SHA-256 baseline before the copy.
The only excluded entry was the Step 9-reviewed zero-byte
`.image-staging/catalogue.lock`. The four reviewed `Thumbs.db` files remained in
the approved non-staging seed and were copied unchanged.

## ACL review

The captured ACL evidence is retained as:

```text
runtime/20261002-155755/SOURCE-ACL.txt
runtime/20261002-155755/TARGET-ACL.txt
```

Both captures report the same owner, access-rule protection state, SDDL and
`Everyone` access rule. The target therefore did not become unexpectedly more
broadly writable than the old shared root. See [`ACL-REVIEW.md`](ACL-REVIEW.md).

The existing source ACL is itself broad; Step 10 intentionally preserves that
policy rather than treating this migration as an unrelated NAS-permission
hardening exercise.

## Completion decision

Step 10 is complete because:

- the effective non-production database topology was respected: the shared
  local `common` dataset received exactly one Files root;
- the frozen `files` source matched the Step 8 full SHA-256 baseline before
  seeding;
- the new candidate was created via a temporary sibling rather than by merging
  into an existing tree;
- the complete approved-seed and temporary-target SHA-256 inventories matched;
- the reviewed `.image-staging/catalogue.lock` was deliberately excluded;
- the candidate contains 89 files totalling 100032776 bytes;
- the target passed the create/write/read/delete permission probe without
  leaving probe residue;
- the source and target ACL captures are equivalent, so the target is not more
  broadly writable than the old shared root; and
- neither the production/shared `files` source nor the Step 8 rollback snapshot
  was deleted or overwritten by the Step 10 operation.

## Operational hand-off

Keep both responder write paths frozen. Do not begin Image lifecycle mutation
against the new root yet.

**Next implementation step:** Step 11 — repoint local modes and verify resolved
runtime paths after overrides.
