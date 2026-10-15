# 0034-FEAT — Step 11 final evidence reconciliation and closure gate

**Prepared:** 2026-10-15 UTC. **Status:** RECONCILED / PENDING FINAL SIGN-OFF. **Step 11 and 0034-FEAT are NOT CLOSED.**

This record separates successful operational gates from outstanding formal acceptance obligations. It introduces no operational changes and authorises no deletion or checkpoint release.

## Acceptance traceability

| Requirement | Evidence / observed result | Finding |
|---|---|---|
| Preserve 0033 schema-2 backup/restore | Historical Step 1 and Step 7 closeouts; live schema-2 manifest validator accepted production backup `20261015-003023Z` (89 Files) | PASS |
| Two successive production generations | Previous `20261009-154847Z` validated in Step 11.3; later `20261015-003023Z` published and independently received on 15 Oct | PASS for distinct generations; not consecutive calendar days |
| Native full baseline + incrementals | Accepted historical full `20261012-100003Z` recorded in Step 11.1; 14 Oct incremental `20261014-100031Z` accepted; 15 Oct incremental `20261015-030004Z` accepted | PASS for full baseline and repeated incremental lineage |
| On-prem receive / snapshot verification | 15 Oct 01:30 UTC `mars` `PUBLISHED`, `VERIFIED`, `VERIFIED_RECEIVE`; 03:00 timestamp set `20261015-030004Z`, 2 snapshots | PASS |
| Unattended end-to-end schedule | `pluto` 00:30, `mars` pull 01:30, snapshot 03:00, push 03:30, `backup` read-only receipt 03:31:38 UTC; final Ansible acceptance `pluto ok=3`, `mars ok=6`, `backup ok=3`, all changed=0 failed=0 | PASS (Step 11.4 CLOSED) |
| Off-site recovery | Step 11.3 Gates A–D: disposable PostgreSQL 18 restore, 89 Files SHA256 matches and Image catalogue reconciliation; cleaned disposable containers | PASS (Step 11.3 CLOSED) |
| Receipt, identity and integrity | `20261015-030004Z` receipt `btrfs-incremental`; source and received UUID `6f44e0e0-1968-6e4d-a3bd-9f77d71e9a47`, both exits 0; receiver `Flags: readonly` | PASS |
| Retention/rollback protection | Held `20261013-171228Z`; replication parent advanced to `20261015-030004Z` only after acceptance; pruning logs kept holds/pins; old rsync off-site disabled, receiver pull helpers absent | PASS for observed safeguards |
| Failure handling | 02:00 snapshot refused writer-lock conflict without unsafe capture; 03:00 automatic successful retry, then off-site acceptance. Other negative tests in Step 10 source regression evidence; do not substitute for specific live interrupted transfer unless documented | PASS for observed lock failure; broader interruption evidence is source/test-level |
| History lookup | `diaries-backup-history` originally refused because manager `verification.required=false`; Step 11.3 used direct receipt/subvolume discovery | EXPLICIT DEFERRAL to 0035; not a history CLI pass |
| Full four-host final baseline and source SHA | Step 11.1 lists required capture on `mango`, `pluto`, `mars`, `backup`, Diaries SHA/cleanliness, mounts/UUID, configuration and operator approval; captured complete outputs are not present in consulted source evidence | **OPEN — FINAL BLOCKER** |
| Post-correction cron unattended execution | `richard` backup moved from 02:00 to 01:45 UTC by isolated Ansible, repeat deployment `changed=0`, installed crontab confirmed; next overnight execution not observed in current evidence | FOLLOW-UP; not misrepresented as passed |

## Repository / configuration identities

- Diaries documentation close-out commit confirmed by operator: `89d113ea25a4fef207fa5f2ef5452b32d1838fd2`, `main` and `origin/main` (15 Oct).
- Playbooks Step 11.4 baseline commit reported earlier: `974c1b8bb6dc4d697f740301d3202b674234e6c1`. Later Playbooks cron and Snapper tasks were deployed; **the current final Playbooks commit/working-tree state has not been independently supplied** and must be captured in Step 11.1.
- Source-initiated receiver: `richard@10.254.22.1:39263`; `backup` accepted receipts under `/@data/mars-received/.replication-state/`.
- Old storage, numbered Snapper snapshots and `@data/backup` must not be removed through this feature closure. Snapshot housekeeping belongs to a separately authorised review after 0034/0035.

## Outstanding closure checklist

- [ ] Run the existing `evidence/Step 11/capture-step-11-1.sh` on **each** of `mango`, `pluto`, `mars`, `backup`; check per-host `ERRORS.txt`, redact sensitive captures, record evidence checksums (raw secrets stay private).
- [ ] Reconcile real mounts/filesystem UUIDs, current source/receiver UUIDs and received receipts; record currently deployed timer owners and 0033 backup paths.
- [ ] Record **current** Diaries and Playbooks Git SHAs and working-tree status, including any change since `89d113e` and `974c1b8`.
- [ ] Sign off Step 11.1 explicitly, or record an authorised acceptance waiver for any unavailable capture field; do not silently deem it complete.
- [ ] Review failed transfer coverage and retained rollback media against acceptance contract; document any approved remaining deferral.
- [ ] Obtain operator approval for feature close-out, move 0034 directory from `in-progress` to `complete` using repository convention, update feature statuses and commit.

## Guardrails and deferrals

Continue protecting held recovery checkpoint `20261013-171228Z` until explicit separate release. No permission to delete old Snapper snapshots, legacy backup repositories or received native snapshots is implied. The history-tool configuration limitation belongs to 0035-FEAT; the rolling backup/reflink improvement belongs to 0036-FEAT. A successful `--preflight` after the 03:30 push selected the next incremental snapshot, not a full reseed.

**Decision:** All major operational gates passed, but the explicit Step 11.1 formal baseline gate has not been evidenced as complete. Feature close-out is **READY AFTER BASELINE/SIGN-OFF**, not claimed complete.

## Addendum — 15 October 2026 final evidence resolution and disposition

The earlier **OPEN — FINAL BLOCKER** entry above is historical and was resolved following creation of this document. The operator subsequently supplied `0034-step11-3-backup-2.zip` with four independently named 15 October Step 11.1 host directories and SHA256 manifests for `mango` 06:58:50Z, `pluto` 07:00:22Z, `mars` 07:01:07Z and `backup` 07:01:56Z. These were verified in the close-out review. Step 11.1 is **ACCEPTED**. The earlier statement that the latest Playbooks source revision was unavailable is also superseded: `mango` `main` and `origin/main` were clean at `2fb96e60ea75f55882b91a230d271e9e7fdbc635` (15 October). Diaries Step 11.4 close-out had previously been clean and synchronized at `89d113ea25a4fef207fa5f2ef5452b32d1838fd2`.

Operator approval for formal feature closure was given in the request to close 0034-FEAT. **Step 11: CLOSED. 0034-FEAT: CLOSED**, subject to preserving the previously documented deferred follow-ups and held checkpoint. This addendum intentionally preserves the preceding contemporaneous pre-sign-off assessment for traceability; it must not be read as the current status.
