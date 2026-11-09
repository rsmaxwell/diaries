# 0040-FEAT Step 12.3 — Consolidated implementation baseline and remaining acceptance gates

Date: 2026-11-01  |  Status: SOURCE RECONCILIATION ONLY — NOT CLOSED

## Source baselines reported by operator

- Playbooks `/home/richard/playbooks`: `main` clean, HEAD `bdba058b0f3b634f94e7da4b7ab62eeadfa625b6` (`Pre-step 12.3`).
- Diaries parent Windows repository: `main` clean, HEAD `4ef46f44495eda940b6ba4502587f2107f673225` (`Pre-step 12.3`).
- Source archives inspected: `playbook-sources-20261101-075234.zip`, `diaries-sources-20261101-075239.zip`.
- The source ZIPs lack live Git metadata, so their exact byte-for-byte correspondence to the reported commits has **not** been independently proved; they were created shortly before the reported commits. Preserve this distinction.

## Confirmed source components

The Playbooks bundle contains `btrfs-agreed-parent-receive-core.py`, `btrfs-agreed-parent-receiver-entry.py`, `btrfs-agreed-parent-provisional-journal.py` and the direct deletion guard in `btrfs-native-endpoint.py`.

The receiver entry's `main()` accepts only `--review-only`, while the internal migrated receive adapter refuses production execution by default. In `btrfs-agreed-parent-receive-core.py`, the transaction reserves the provisional journal before the binary receive but does not persist a final receipt or transition the agreed parent. The bounded subprocess is launched through `sudo` to the existing constrained endpoint; this does not establish inherited lock ownership if the coordinator dies. The legacy source-side transport still targets `/usr/local/bin/btrfs-native-push-receiver`.

## Baseline offline regressions run against the source ZIP

- `verify-0040-step12-3-entry-core-link.py`: 7/7 pass.
- `verify-0040-step12-3-migrated-receive.py`: 9/9 pass.
- `verify-0040-step12-3-receiver-process-lifetime.py`: 6/6 pass.
- `verify-0040-step12-3-privileged-delete-transfer-guard.py`: 6/6 pass.
- Total: 28/28, offline only, on extracted source files; not a deployment or full integration acceptance.

## Remaining implementation work (single consolidated workstream)

1. Bind authenticated source SSH stream to a fixed privileged receiver entry, not arbitrary client-provided execution flags. Audit sudo, command restrictions, stdin, stderr and exit propagation.
2. Make receiver lock protection survive unexpected coordinator death. A surviving Btrfs filesystem writer must retain exclusion via lock ownership or a proven systemd/cgroup lifecycle. Do not presume systemd-run or process-group termination alone guarantees this. Test with disposable processes and Btrfs.
3. Integrate actual journal-first A-to-B receive with exact state identity and filesystem verification. Preserve journal on incomplete or ambiguous execution. No automatic retry or rollback deletion.
4. Implement sender-observed completion and receiver-side authenticated, idempotent finalisation; the receiver must not mistake local EOF/exit 0 for sender success. Define recoverable receipt/ack ordering under interruptions.
5. Implement durable common-parent reconciliation and advancement on *both* endpoints, including repeated operations, crash points, disagreement, and pin protection throughout. Retain A until B is converged and verified at both ends.
6. Unify sender/receiver unattended prune with retention (48 hourly/14 daily/12 weekly/24 monthly/5 yearly), minimum age, protected A/B, hold and journal rules. Include direct privileged boundary checks.
7. Replace legacy runtime wiring only after the new route passes disposable testing; maintain rollback. Update Ansible tasks, templates, service units/SSH invocation, reports and operator documentation. Do not install dormant historical proof-of-concept paths as production requirements.
8. Run full source regression, syntax and Ansible --check --diff, disposable real-Btrfs end-to-end and concurrency/kill/recovery checks; then separately approve and perform a controlled live transfer and unattended cycles. Record actual evidence and idempotency before closing original six acceptance gates.

## Operational safety hold

No live commands were executed for this report. Keep native push and snapshot pruning inactive on `mars`; hourly snapshot creation may remain active. Do not delete or modify historical A/B, snapshots, holds, receipts or recovery journals. The last observed A `20261030-030033Z` and B `20261030-170009Z` require fresh read-only reconfirmation before live tests.

This report is **not** a claim that the whole Step 12.3 has been implemented or accepted. Formal closure requires the six gates in `STEP-12-3-UNATTENDED-DESIGN-DECISION.md`.
