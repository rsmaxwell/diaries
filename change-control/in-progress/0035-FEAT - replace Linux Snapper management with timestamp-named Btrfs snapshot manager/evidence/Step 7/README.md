# 0035-FEAT Step 7 — Staged three-host deployment — CLOSED

**Status: CLOSED — 15 October 2026.** Scope: staged installation parity, passive receiver and read-only safety checks. No new full/incremental transfer, destructive prune, interrupted-transfer injection or restore performed in Step 7.

## Evidence and resolution

1. The Step 7 source-contract regression passed on `mango`: `PASS: three-host staged parity, read-only guards, receiver passive and legacy safety`.
2. Initial read-only checksum comparison incorrectly reported four `mars` differences because Ansible `lookup('ansible.builtin.file', ...)` stripped trailing whitespace. Comparison was corrected to set `rstrip=False, lstrip=False`; regression passed. The corrected comparison found three matches and **one real drift**: the older `diaries-backup-history` on `mars` lacked the Step 4 published-root extension.
3. Operator reviewed `ansible mars -b --ask-vault-pass -m copy ... --check --diff`, then copied **only** `roles/snapshots/files/diaries-backup-history.py` to `/usr/local/sbin/diaries-backup-history` (root:root, `0755`). The live copy returned `changed=true`; no other executable or configuration redeployed.
4. The final `verification/0035-step7/verify-staged.yaml` passed all three hosts: **`mars ok=6 changed=0 failed=0`, `pluto ok=6 changed=0 failed=0`, `backup ok=6 changed=0 failed=0`**. All four expected scripts matched on `mars`, two on `pluto`, and two on `backup`.
5. `mars` dry-run: `CHECKPOINT-HELD: ['20261013-171228Z']`; `REPLICATION-PROTECTED: ['20261015-030004Z']`; `RETENTION sets: total=52 keep=52 sources=2`; `Would delete 0 complete timestamp sets`. The snapshot create/prune and sender timers remained enabled.
6. `pluto` reported verified production publication `20261015-003023Z` and `UNSUPPORTED: pluto filesystem=ext4 — no native snapshot pruning configured; no-op`.
7. `backup` receiver and endpoint matched Playbooks source. Local Btrfs snapshot create/prune timers remained disabled. Historical `/@data/backup`, native `/@data/mars-received/@data`, and `.replication-state` remained present.
8. The separate read-only joint capture completed `mars ok=2 changed=0 failed=0`, `backup ok=2 changed=0 failed=0`, eight accepted snapshots and eight receipts with matching source/received UUIDs, read-only flags and no unreceipted or missing received entries. The current source replication pin `20261015-030004Z` UUID `6f44e0e0-1968-6e4d-a3bd-9f77d71e9a47` matched the accepted receiver snapshot.

## Attached operator transcripts

- `staged-final-20261015-094608.txt`: reviewed targeted history-only deployment and successful final three-host read-only staged verification.
- `joint-20261015-094050.txt`: separate joint-state capture (following the initial unsuccessful checksum-gate check); use its joint-state portion only. Its earlier failed staged comparison is superseded by the fixed and final verification.
- `staged-fixed-drift-20261015-094400.txt`: corrected comparison showing the real single-file history-tool drift.

## Acceptance limits / retained follow-ups

- The final staged check was **read-only**, and `changed=0` there does not mean no targeted history-tool deployment occurred immediately beforehand.
- No new Btrfs send/receive, real pruning, interruption simulation, restore or measured transfer/space test occurred during Step 7. These remain relevant to **Step 8 acceptance**.
- Receiver-side legacy snapshot-manager verification path mismatch (from Step 1) is unchanged, and receiver-local timers remain deliberately disabled. Do not enable them, alter schedules, remove Snapper snapshots, remove historical `/@data/backup`, or remove replication/checkpoint pins as a consequence of this closure.
- Git commit IDs for the final Step 7 documents/source were not evidenced by these logs; record them after committing. **Feature 0035 stays IN PROGRESS.**
