# 0050 — Corrected receiver live verification acceptance

**Evidence date:** 17 November 2026  
**Feature status:** IN PROGRESS — functional verification accepted; remaining operational and publication checks pending.

## Deployment result (mango → backup)

- Executed normal `btrfs-replication.yaml --limit backup` on `mango` with vault password file.
- Five 0050 permanent deployment/compatibility contract tests: PASS.
- Ansible recap `backup: ok=37 changed=1 unreachable=0 failed=0 skipped=43`.
- Only reported changed item: `diaries-backup-history` within the shared receiver history installation loop; `diaries-backup-status` unchanged.
- Receiver configuration, retention, checkpoint holds, replication runtime, scheduled timer and verifier install tasks were `ok` (no reported change).

## Live read-only verification result (backup)

- Invoked `sudo -n diaries-backup-history verify 20261116-003112Z --snapshot 20261116-150008Z --logical-dataset production`.
- Actual schema-2 verifier: `Valid complete Diaries dataset backup manifest`.
- Backup ID `20261116-003112Z`, logical dataset `production`, completed backup workspace; **128 files**.
- Reader confirmed: `VERIFIED ... snapshot=20261116-150008Z path=/@data/mars-received/@data/20261116-150008Z/backup/pluto/diaries-backup`.
- `sudo -n diaries-backup-status`: **HEALTHY**, 30 distinct backup IDs, 42 retained occurrences, 0 conflicts; manifest identity only, not a claim of universal file-content verification.
- `sudo -n btrfs-backup-status --local-only`: **HEALTHY**, 42 retained sets, qgroups 45 total / 0 stale / 0 under deletion; receiver prior/agreed snapshot parent unchanged in observed report; receiver prune timer active.
- Script concluded `0050 LIVE CONTENT VERIFICATION: PASS`.

## Acceptance assessment and remaining work

The prior fixed-root schema-2 verification failure is resolved by using the existing `--allow-fixed-working-root` verifier option in the shared history reader. No snapshot contents, markers, receipts, pinned parents or retention settings were modified as part of this verification.

Receiver-only history detection, warning/conflict handling, and tampering rejection have passed disposable tests. This live log does not prove that a **naturally retained receiver-only ID** exists right now, nor that all 42 retained occurrences have undergone full file verification.

Pending: strict receiver Ansible reapply `changed=0`, independent read-only host-history comparison, final change manifest and Playbooks/controller/Diaries Git publication. Feature remains under `in-progress`; no step is marked CLOSED by this receipt.

## Raw evidence

- `evidence/Step 3/MANGO-CORRECTED-READER-DEPLOYMENT-20261117.txt`
- `evidence/Step 3/BACKUP-FULL-SCHEMA2-VERIFICATION-PASS-20261117.txt`
- `evidence/Step 3/CORRECTED-LIVE-VERIFICATION-LOG-SHA256-20261117.md`

This report is additive to earlier evidence including the initial failed live verification, correction analysis and tests. Do not overwrite those historical records.
