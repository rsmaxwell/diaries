# 0042-FEAT — Retire obsolete native Btrfs replication implementation

**Prepared:** 10 November 2026. **Execution updated:** 10 November 2026. **Status:** Steps 1–2 verified; Step 3 core host checks passed but final backup-status readback remains; formal acceptance and source-control receipts remain OPEN.

## Purpose

Remove the legacy `btrfs-native-push`, old endpoint, Stage B receiver gateway and superseded 0040 intermediate agreed-parent code from the **Playbooks repository**, without changing the accepted simplified sender/receiver, protected parent/prior, checkpoint holds, snapshot manager, receiver pruning or 0039 qgroup maintenance.

The old systemd *unit names* `btrfs-native-push.service` and `.timer` stay in place because they currently invoke the simplified sender. The 03:30 UTC sender, 04:15 UTC receiver pruning and 05:30 UTC qgroup maintenance remain unchanged.

The **host executable retirement was already accepted under 0040 Step 12**; this feature does not re-delete host files. The bundled read-only audit checks the prior **39 mars and 35 backup** candidate paths for continued absence and confirms simplified sender/receiver status. Stop if a legacy executable has reappeared.

## Packages and source basis

- Playbooks ZIP: modified operational tasks/defaults/service template/readmes and current regressions. `native.yaml` and `defaults/main.yaml` incorporate the **already applied uncommitted 0039 changes** from the 9 November packages; compare before replacing and retain any newer local work.
- Diaries ZIP: feature-local guarded retirement utility and exact SHA-256 manifest for 215 obsolete tracked files from `playbook-sources-20261109-122355.zip`. Includes inactive prototype modules, obsolete tests/guides and unused `roles/remote-backup` duplicate role. It does **not** remove active simplified files, 0039 files, shared manager or production state.
- Source bundle is a copy, not a Git checkout. Playbooks live Git baseline in the 10 November user log was `e0da797310ab452ddc61e7368c50a444fe881e41` with 0039 uncommitted modifications. Recheck before application; hash mismatch means STOP and reconcile local changes.

## Actual execution and evidence (10 November 2026)

The Playbooks removal utility verified, archived and staged exactly 215 tracked files (Git baseline `e0da797310ab452ddc61e7368c50a444fe881e41`). Its archive and JSON receipt were transferred back to the Windows Diaries feature directory. The corrected regression suites all passed, including 22 tests of the separately uncommitted 0039 maintenance feature. Ansible syntax and `--check --diff` passed on both hosts. The actual deployment used `--skip-tags qgroup-maintenance` and reported **0 changed, 0 failed** on `mars` and `backup`. The read-only host audit found all 39 retired `mars` paths and all 35 retired `backup` paths absent. The simplified service and receiver status agreed on parent `20261110-030004Z`; protected checkpoints were validated, and all relevant timers were enabled/active. Snapshot status: `mars` 70 complete/0 incomplete with valid production backup, `backup` 33 complete/0 incomplete. See `reports/ACCEPTANCE-RECONCILIATION-20261110.md` and original raw evidence in `evidence/Step 1` through `Step 3`.

No new data deletion, off-site transfer, restore, quota rescan or qgroup cleanup occurred during 0042 deployment or its read-only acceptance audit. The source deletions remain **staged but uncommitted** at the end of the supplied log. Existing 0039 work remains uncommitted and must not be mixed accidentally into a 0042 source commit. An explicit read-only backup-status check and source-control commit receipts are the remaining closure reconciliation items; no repeat of completed deployment or regression suites is needed.

## Execution and acceptance

See `IMPLEMENTATION-STEPS.md`. Apply source changes with Beyond Compare 4 first; deletion is **not** implied by applying a ZIP. Run the standalone feature tool `--plan` then `--apply` on mango after explicitly synchronising the Windows Diaries feature to `/home/richard/diaries`. Its archive and receipt are temporary in the mango execution copy; preserve them by synchronising into the authoritative Windows Diaries repository before closure. After that run a consolidated regression, Ansible syntax/check preview, deploy once and verify active hosts. Keep implementation evidence under this feature; formal closure requires reviewed acceptance.

No snapshot deletion, quota rescan, native transfer, parent reset, data-set removal or changes to backup recovery capability are in scope.
