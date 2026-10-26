# 0039-DEF Step 03 — production remediation and replication acceptance

**Evidence assessment date:** 2026-10-22. **Scope:** `backup` orphaned level-0 qgroups and post-remediation mars→backup incremental replication. **Decision:** production remediation and replication **PASSED**; full defect remains **OPEN**.

## Baseline and authorisation

Original `backup` filesystem UUID `b915f967-7cb4-4c14-b11b-f52209637a22`; **29,571 total qgroups**, 133 subvolumes, active root qgroup `0/5`, and **29,437 unmatched** (15,475 unlimited and 13,962 limited). The earlier no-mutation planning restriction was superseded by operator-approved staged remediation after disposable Btrfs deletion rehearsals, protection inventory, receipt/source lineage checks, candidate checks and deliberately bounded pilots. Qgroup destruction is not intrinsically reversible; historical backup/snapshot/receipt protections were retained. No OS upgrade, quota disable/enable, snapshot-retention change, reseed or full restore was part of this operation.

## Production deletion sequence and journal handling

- Unlimited and 1 TiB-limited pilot deletions: 2; first guarded batch: 20; subsequent successful journalled batch: 100.
- A 1,000-target run stopped after **675 successful deletions** on the overly strict `active set changed` guard. The original journal `stage-c-20261021-201036Z-598228.jsonl` remains **FAIL** and immutable. Its 675 `ATTEMPT`/`REMOVED` pairs were checked against live missing IDs; the checksum-bound acknowledgement `stage-c-20261021-201036Z-598228.jsonl.ack.json` records successful reconciliation, not an ex-post PASS. Journal SHA256 `8871c1f69f5dad6cbbc63bc406e590ec84fe28c6847cf5098191aab08074f2af`; acknowledgement SHA256 `0b6f9146908dcf1f27dbdf51f716be4407a43ed6218d38f5de69dac8459cfc3e`.
- Post-fix single 1,000 batch: PASS; second 1,000 batch: PASS; two sequences of ten 1,000 batches each: PASS; final six 1,000 batches plus 640: PASS. **Total 29,437 successful deletions.** Journals and dated checksum manifests are present under `reconciliation/backup/`. The helper was revised to ignore volatile `rfer`/`excl` for active-qgroup stability and to admit new legitimate snapshot IDs *between* runs, while retaining ID, limit and relationship checks during each run. Its acknowledgement and live-inventory gates were regression tested (18 tests accepted); source changes were reviewed/applied by operator.
- Representative operator terminal logs: `note(20261022-075447).txt`, `note(20261022-080347).txt`, `note(20261022-081306).txt`, `note(20261022-081738).txt`, `note(20261022-081903).txt`. Journals are the exact-ID primary evidence rather than terminal progress counters.

## Independent post-deletion invariant check

`note(20261022-082032).txt`: UUID match; 134 live subvolumes; **135 qgroups = 134 + root 0/5**; **zero unmatched**; four explicitly protected received snapshots with correct IDs, received UUIDs and `ro=true`; no pending subvolume deletions or active quota rescan. `note(20261022-082203).txt`: receiver-state history extended through the daily `20261022-030026Z` snapshot; writer lock available. This earlier daily receive was pre-cleanup and is not itself post-cleanup replication evidence.

## Manual post-remediation mars → backup replication

- `note(20261022-082856).txt`: `mars` snapshot-create service completed successfully and created root and `@data` set **`20261022-082824Z`**; a oneshot inactive status caused the combined shell to stop before its next command, not a snapshot failure.
- `note(20261022-083034).txt`: read-only sender preflight chose source UUID `0bf0a247-263f-ff4c-8368-48a91221cc9b`, parent `20261022-030026Z`, action **incremental**.
- `note(20261022-083202).txt`: actual `btrfs-native-push.service` `Result=success`, `ExecMainStatus=0`; receiver `ACCEPTED: 20261022-082824Z`.
- `note(20261022-083330).txt`: independent receiver observation. New subvolume **55816**, `ro=true`, `Received UUID: 0bf0a247-263f-ff4c-8368-48a91221cc9b`, incremental parent still present at ID **55815** with received UUID `571d59ec-5110-4944-b4e1-78b3372675d2`. Receipt `20261022-082824Z.json` records `transport=btrfs-incremental`, matching parent source UUID, `source_send_exit=0`, `receiver_receive_exit=0`, `read_only_verified=true`, completion `2026-10-22T08:31:42.048346+00:00`.
- **Post-replication filesystem:** 135 live subvolumes, 136 qgroups (including `0/5`), **zero orphaned qgroups**. This is an independent post-remediation send/receive acceptance gate.

## Boundaries, risks and remaining steps

This proves the identified orphan population was removed and incremental replication continued after remediation, not that recurrence has been permanently prevented. Historic Snapper deletion correlation and disposable reproduction support a causal hypothesis, but the kernel-level persistence mechanism and eventual recurrence on `mars` remain unresolved. Do not claim preventative remediation, stable future qgroup counts, OS upgrades, or all defect acceptance gates completed. Reconcile remaining Step 3 prevention/design decisions, standalone Steps 4–7 (source/Ansible/idempotency requirements, as applicable), Git revisions, and Step 8 closeout before moving the defect to `complete`.
