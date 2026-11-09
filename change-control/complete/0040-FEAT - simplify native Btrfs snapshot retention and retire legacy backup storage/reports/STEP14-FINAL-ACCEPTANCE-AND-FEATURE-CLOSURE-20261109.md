# 0040-FEAT — Step 14 final acceptance and conditional overall feature closure

**Prepared:** 9 November 2026 (UTC). **Decision:** Operational and documentation evidence is sufficient for *conditional* Step 14 acceptance. **Formal Step 14 and overall 0040-FEAT closure are NOT yet effective**: they require explicit operator acceptance of the material legacy-storage scope exception below, followed by a verified Git move/commit/push of the complete feature directory into `change-control/complete/`.

## Baseline and provenance

- Authoritative Diaries Windows checkout: `main`, commit `815eb25` (`0040-FEAT: Formally close Step 13`), pushed. The `mango` Diaries clone remained at older `4f166ac` and had untracked Step 13/14 artifacts; it is **not** the source of final feature documentation. The five Step 14 audit logs were copied in a validated archive from `mango` into Windows; the 9 November 10:53 Cygwin output verified their presence and reported only an untracked `evidence/Step 14/` directory.
- Playbooks on `mango`: `main`, commit `e0da797` (unreferenced task-backup removal, pushed and clean). The feature's source-prune runtime was added at `6ccbf73`; follow-up receiver manager deployment brought the installed manager into parity with source.
- Step 12 was formally closed on 8 November 2026; Step 13 formally closed at Diaries `815eb25` on 9 November. The earlier accepted retirement and replication test/restore evidence is intentionally reused, not rerun.

## Step 14 acceptance matrix

| Criterion | Verified result | Primary raw evidence (`evidence/Step 14/`) |
| --- | --- | --- |
| No regenerated `mars` root snapshots | Privileged `find` found no entries; native Btrfs listing no `@snapshots/root` subvolumes | `step14-final-discrepancy-investigation-20261109-094938.txt` |
| Source snapshot integrity and capacity | `147` complete/managed and `0` incomplete at 09:45 audit, verified Diaries marker; `mars` `/media/usb` 3.4 TB available | `step14-final-readonly-audit-20261109-094544.txt` |
| Bounded unattended prune | 09:45:39–09:45:53 UTC source pruning, `eligible=78 selected=10 max_delete=10`; deleted 10 sets; exit 0 | `step14-final-discrepancy-investigation-20261109-094938.txt` |
| Receiver retained snapshots and receipt protections | 32 received snapshots, 0 prune candidates, 27 historical receipts preserved, 0 orphaned; two checkpoint holds and both parents maintained | `step14-receiver-manager-reconciliation-20261109-100229.txt` |
| Shared manager source/install identity | Playbooks, `mars`, `backup` SHA-256 `89602f0aac07900b367a82728e42339ee9c9d3ed40e55010af87576dadc7a2b7` | `step14-receiver-manager-reconciliation-20261109-100229.txt` |
| Simplified sender/receiver identity | Both host executables SHA-256 `7eba4a04aca1f9b04333cd82952744ab1559cc7736092d7d1dcc11a25be67363` | `step14-final-readonly-audit-20261109-094544.txt` |
| Receiver Ansible deployment and idempotency | One intended manager installation `changed=1 failed=0`; subsequent check/diff `changed=0 failed=0` | `step14-receiver-manager-reconciliation-20261109-100229.txt`; `step14-receiver-final-verification-20261109-103348.txt` |
| Native agreed-parent safety | Sender/receiver equal, `receiver_parent_verified=true`; parent `20261109-030030Z`, prior `20261108-030011Z` | `step14-receiver-final-verification-20261109-103348.txt` |
| Scheduling and receiver status | Source create :00, prune :45, sender 03:30 UTC; receiver prune 04:15 UTC, enabled/active with last result success | Step 13 logs; `step14-final-readonly-audit-20261109-094544.txt`; `step14-receiver-manager-reconciliation-20261109-100229.txt` |
| Receiver capacity | `backup` root Btrfs 856 GB available at audit | `step14-final-readonly-audit-20261109-094544.txt` |
| Evidence custody | Five Step 14 files imported to Windows repository, ZIP validated and essential files checked; this package adds import transcript as sixth | `step14-windows-evidence-import-20261109-105319.txt` |

A sender `status` attempt immediately after deployment returned `DEFERRED: local snapshot-manager lock busy`. The subsequent Python JSON parse failed because the command returned a deferral instead of JSON. Both are preserved, not counted as successful checks. Later sender status passed normally with unchanged parent agreement. This supports the intended non-blocking safety behaviour without a restart or reset.

## Material historical-storage exception requiring operator approval

The original 0040-FEAT planned to retire `/@data/backup` on the `backup` host. **That deletion has NOT occurred and MUST NOT be claimed.** Final inspection found that `/@data/backup` is a populated ordinary directory containing historical copies for `nas`, `richard-laptop`, `richard-pc`, `mars`, `bob`, `mango`, `pluto`, plus a backup writer lock and Diaries marker. The top-level directory's recorded modification was 10 October 2026; its content is not proven redundant or safe to delete. Existing Playbooks `roles/remote-backup/README.md` and 0035 acceptance/verification documentation explicitly protect this historical mirror.

**Proposed amended closure boundary:** Retain `/@data/backup` exactly as found, without deletion, rename or data mutation. Treat it as a separately preserved historical recovery dataset, not as a current native received-snapshot target. This is an explicit, material exception to the original retirement plan; it requires operator acceptance rather than being silently represented as completed cleanup. The empty ordinary directories `/@snapshots/@data` and `/@snapshots/root` likewise remain, but hold no Btrfs subvolumes or content. Keep them without cleanup merely for cosmetic absence. Snapper root `/.snapshots` and legacy `/@data/.snapshots` are absent. No root snapshot population was regenerated on `mars`.

The accepted architecture uses native received snapshots under `/@data/mars-received/@data/<timestamp>` with receiver state under `/@data/mars-received/.replication-state/`. Historical `/@data/backup` does not participate in native incremental send/receive or receiver pruning and is not newly authorised for destruction. No further deletion is necessary to accept the working replication architecture.

## Outstanding work deliberately deferred

- **0039-DEF:** recurring stale `mars` Btrfs qgroups (606 at the 9 November acceptance audit; 0 under deletion, warning active). This feature neither resolves nor authorises destructive qgroup operations.
- **0041-FEAT:** dedicated sender/receiver service identities and restricted SSH privileges.
- Historical empty containers and historical `/@data/backup`: preservation is intentional under the proposed amended scope; any future removal requires its own explicit data inventory, recovery assurance and destructive approval.

## Formal decision and Git closure gate

**Prepared decision:** Accept all operational Step 14 gates, subject to express operator acceptance of the historical-storage exception above. To finish, the operator must approve that exception and move the *complete* `0040-FEAT` directory from `change-control/in-progress/` to `change-control/complete/` in the Windows Diaries `main` checkout, retaining all historical evidence and reports. Verify the move and limited staged scope, then commit and push. The successful Git revision/remote update and clean feature worktree are the formal closure receipt.

**Effect:** On such acceptance and successful promotion only, mark **Step 14 CLOSED** and **0040-FEAT CLOSED**. If approval or Git promotion does not occur, both remain **OPEN**, with this report recording a closure proposal, not a completed status. No new server operation, full restore, manual replication or deletion is required.
