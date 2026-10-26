# 0040 Step 11 — Raw evidence archive checklist

This checklist does not assert that the listed records are already in Git.

- [ ] Source `mars` retirement receipt copied unmodified to this directory; SHA-256: `e75e5c57f5a99524d37dccca2c8c9982a1e22b32e011b9bd95f132901cc8c955`.
- [ ] Frozen 63-root retirement manifest and tested utility/regression revisions preserved (currently Playbooks `roles/snapshots/tests/0040-step11/`).
- [ ] Operator-approved irreversible-deletion decision and execution log preserved.
- [ ] Receipt reconciliation and native-root absence, holds, verification and receiver status logs preserved.
- [ ] Original replication unit restore and subsequent Ansible source/replication idempotency evidence preserved.
- [ ] One-time Snapper APT-hook cleanup check/deployment/idempotency, APT health and rollback-copy checksum logs preserved.
- [ ] Check revision identifiers; review the Git staging list for secrets, obsolete generated files and intentionally untracked documents.
- [ ] Integrate closure into current local `IMPLEMENTATION-STEPS.md` and change-control status only after the evidence is reconciled.

The Step 10 archive has a separate accepted evidence transfer and should not be duplicated here. Preserve receipt and rollback originals on `mars` until documentation is accepted.
