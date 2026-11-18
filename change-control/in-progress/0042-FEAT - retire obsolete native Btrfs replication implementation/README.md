# 0042-FEAT — Retire obsolete native Btrfs replication implementation

**Prepared:** 10 November 2026. **Status:** Implementation package prepared, not applied to live Git worktrees, not deployed; OPEN.

## Purpose

Remove the legacy `btrfs-native-push`, old endpoint, Stage B receiver gateway and superseded 0040 intermediate agreed-parent code from the **Playbooks repository**, without changing the accepted simplified sender/receiver, protected parent/prior, checkpoint holds, snapshot manager, receiver pruning or 0039 qgroup maintenance.

The old systemd *unit names* `btrfs-native-push.service` and `.timer` stay in place because they currently invoke the simplified sender. The 03:30 UTC sender, 04:15 UTC receiver pruning and 05:30 UTC qgroup maintenance remain unchanged.

The **host executable retirement was already accepted under 0040 Step 12**; this feature does not re-delete host files. The bundled read-only audit checks the prior **39 mars and 35 backup** candidate paths for continued absence and confirms simplified sender/receiver status. Stop if a legacy executable has reappeared.

## Packages and source basis

- Playbooks ZIP: modified operational tasks/defaults/service template/readmes and current regressions. `native.yaml` and `defaults/main.yaml` incorporate the **already applied uncommitted 0039 changes** from the 9 November packages; compare before replacing and retain any newer local work.
- Diaries ZIP: feature-local guarded retirement utility and exact SHA-256 manifest for 215 obsolete tracked files from `playbook-sources-20261109-122355.zip`. Includes inactive prototype modules, obsolete tests/guides and unused `roles/remote-backup` duplicate role. It does **not** remove active simplified files, 0039 files, shared manager or production state.
- Source bundle is a copy, not a Git checkout. Playbooks live Git baseline in the 10 November user log was `e0da797310ab452ddc61e7368c50a444fe881e41` with 0039 uncommitted modifications. Recheck before application; hash mismatch means STOP and reconcile local changes.

## Execution and acceptance

See `IMPLEMENTATION-STEPS.md`. Apply source changes with Beyond Compare 4 first; deletion is **not** implied by applying a ZIP. Run the standalone feature tool `--plan` then `--apply` on mango after explicitly synchronising the Windows Diaries feature to `/home/richard/diaries`. Its archive and receipt are temporary in the mango execution copy; preserve them by synchronising into the authoritative Windows Diaries repository before closure. After that run a consolidated regression, Ansible syntax/check preview, deploy once and verify active hosts. Keep implementation evidence under this feature; formal closure requires reviewed acceptance.

No snapshot deletion, quota rescan, native transfer, parent reset, data-set removal or changes to backup recovery capability are in scope.
