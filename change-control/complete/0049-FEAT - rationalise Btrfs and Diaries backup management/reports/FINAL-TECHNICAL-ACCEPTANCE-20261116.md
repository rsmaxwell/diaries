# 0049 — Final technical acceptance review (16 November 2026)

**Result: TECHNICAL ACCEPTANCE PASSED. Formal feature closure is NOT yet authorised or recorded.**

## Evidence used

- `evidence/Step 4/BACKUP-FINAL-READBACK-20261116.txt` — direct receiver read-back on `backup` following the post-0049 live sender push.
- `evidence/Step 4/MANGO-FINAL-IDEMPOTENCE-20261116.txt` — production Ansible reapply to both endpoints from `mango`.
- Earlier 0049 feature evidence: source regressions; Ansible check-mode; receiver-first deployment; sender deployment/read-back; first complete push on `mars` (journal and after-state); prior receiver retention evidence.

## Acceptance summary

| Gate | Result | Evidence |
| --- | --- | --- |
| `backup` infrastructure status | PASS — `HEALTHY`; 41 retained received sets | Final receiver read-back |
| Newly replicated Btrfs snapshot | PASS — `20261116-150008Z`; received UUID `818b8956-76de-564f-8351-37cc89037d14`; `Flags=readonly` | `btrfs-replication receiver status --snapshot ...` |
| Agreed parent on receiver | PASS — `20261116-150008Z` | Receiver state JSON |
| Prior agreed parent protected | PASS — `20261116-030016Z` | Receiver state JSON and retention preview |
| Receiver retention safety | PASS — 41 retained, 0 proposed deletions, 2 independent holds, 27 historical receipts preserved | `prune --dry-run --max-delete 10` |
| Receiver qgroups | PASS — 44 total, 0 stale, 0 under deletion, manager status `ok` | `btrfs-backup-status --local-only` |
| Receiver prune schedule | PASS — timer active, next 17 November 2026 04:15 GMT | systemd status embedded in receiver report |
| Ansible repeatability: `backup` | PASS — `ok=34 changed=0 unreachable=0 failed=0` | Final Ansible recap |
| Ansible repeatability: `mars` | PASS — `ok=26 changed=0 unreachable=0 failed=0` | Final Ansible recap |
| Replication over 0041 service identities | PASS in preceding push acceptance log — `btrfs-send` transport and receiver verified | Earlier `MARS-FIRST-PUSH-ACCEPTANCE-20261116.txt` |
| Old/new timer exclusivity | PASS in preceding sender/receiver read-back logs | Earlier 0049 deployment evidence |

**Cross-host lineage:** initial agreed parent `20261116-030016Z` advanced to `20261116-150008Z`; the latter is confirmed locally and on the receiver, with matching expected received UUID and immutable read-only status. The sender's after-cycle check reported `relation=equal`, `receiver_parent_verified=true`, and `preflight.action=up-to-date`. The receiver independently confirmed the resulting on-disk snapshot.

**No destructive test:** these final commands reported status and planned retention only. No live prune, rebootstrap, dataset deletion, or restore was run for 0049. A real live snapshot transfer was run once via the newly named service earlier in the feature.

## Explicit limits and follow-ups

1. `lastVerifiedTransfer` is presented as unknown without a separate independent transfer receipt. This is a deliberate distinction from the positively verified agreed-parent lineage and service completion, not a failed transfer.
2. `mars` had 2 stale qgroups with `qgroups_status=ok` in the earlier sender read-back. This is managed under 0039-DEF and did not prevent 0049 acceptance. The final receiver has no stale qgroups.
3. Earlier repo inspection recorded `main` at Playbooks commit `0904bc7ebe801e391a3aa4dc59bbc9ccc7dfa532` with 0049 changes uncommitted. Do **not** treat this as a final implementation commit. Neither final Playbooks commit nor the final Windows Diaries parent commit/submodule revisions are established by the uploaded terminal logs.
4. The persistent internal `.simple-agreed-parent.json` and related state filenames remain intentionally unchanged to avoid altering recovery state as part of a user-facing naming cleanup. Historical labels in archived feature evidence are not rewritten.
5. The implementation report and step checklist prepared before live deployment have status text reflecting that earlier point in time. Update the feature's summary/step-status documents when formal acceptance is recorded; preserve the original dated evidence.

## Recommendation

Accept the **technical result** of Steps 2–4, subject to normal operator review. Proceed to one repository finalisation pass: review/commit the 0049 Playbooks changes, verify the Ansible-controller parent submodule pins and private inventory are consistent, record Windows Diaries branch/commit/submodules and feature evidence, and then request formal approval to move the feature directory from `in-progress/` to `complete/`. Do not mark CLOSED or move the feature solely on the basis of this report.
