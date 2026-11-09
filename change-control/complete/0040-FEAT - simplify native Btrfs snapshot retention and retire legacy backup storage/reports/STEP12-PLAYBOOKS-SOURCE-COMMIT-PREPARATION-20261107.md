# Step 12 — Playbooks source commit and operating-doc reconciliation (7 November 2026)

Status: PREPARED, pending integration verification and Playbooks commit.

## Basis

The historical verification-test archive was committed as Diaries `2f1c860`;
the corresponding 146 Playbooks historical-file removals were committed as
Playbooks `a1f359c`; the `mango` Diaries checkout was reconciled to `2f1c860`.
The remaining Playbooks working-tree changes comprise eight modified source,
test and documentation files and five untracked receiver-retention files.

Accepted deployed source identities:

- `/usr/local/bin/btrfs-simplified-replication`:
  `cfa8a696b36eb49935d518cfd2c99d38e28fe3fbbfaa7a0faa6618a485e2fd36`
- `/usr/local/sbin/btrfs-snapshot-manager`:
  `26ba24e711558a358069775ef042c01765355dd5dc80f9eb5521f42a2673dfc0`

The 7 November Playbooks source bundle contains matching executable hashes.
The 03:30 replication service is already active on `mars`, with its first
unattended execution accepted on 7 November. The 04:15 receiver retention
service was explicitly authorised and activated on `backup` with a ten-delete
bound; first unattended execution is scheduled 8 November and remains pending.

## This package

Updates **only operating documentation and comments**, not Btrfs runtime,
Ansible task logic, inventory configuration or systemd templates. Replaces
out-of-date descriptions of "install-only", pending sender cutover and
disabled receiver pruning with the accepted active state. Role defaults
remain default-off and host inventory remains authoritative.

## Next acceptance

Apply the Playbooks documentation ZIP using Beyond Compare, preserving local
changes. Verify accepted executable hashes, inventory gate values and
expected Git status; run consolidated retained regressions, Ansible syntax
and tagged check-mode preview. If acceptable, stage only the 13 enumerated
implementation/documentation files and commit to Playbooks. Do not claim
unattended receiver pruning executed before reviewing 8 November logs.
