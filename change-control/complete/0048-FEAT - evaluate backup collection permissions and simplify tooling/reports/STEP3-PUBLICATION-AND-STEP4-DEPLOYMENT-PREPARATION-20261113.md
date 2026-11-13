# 0048-FEAT — Review of source normalisation and deployment publication plan

**Date:** 13 November 2026 (UTC)
**Status:** Publication and live deployment **NOT YET EXECUTED**. Do not mark CLOSED on proposed commands.

## Evidence already observed

The operator log `source-preview-20261113-081531Z.txt` records the `mango`
controller `f6ba7fec7752f4bbfa1535958500bde9dea3ea84`, Playbooks
`df68a0e3bc57bae29a76f46a58c30835126d7f20` and inventory
`ebcce026723db37b9b53b76ba21903a351d48466`. Before the preview,
the five synchronized source directories had mode `0775` and the nine filters
`0664`. They were normalised locally to `0755` and `0644`, respectively,
with source contents unchanged. The preflight, Ansible syntax test and
`--check --limit mars --tags user,machine` succeeded. Preview recap:
`ok=14`, `changed=2`, `failed=0`, `unreachable=0`.
The two changes were solely the normal-user and root-machine archive rsync
copy operations; templated launchers and cron jobs reported `ok`.

Earlier Step 3 disposable tests demonstrated second-run convergence
(`FRESH_RUN2_CHANGED=0`, `EXISTING-0750_RUN2_CHANGED=0`) and allowed-reader /
denied-unauthorised-reader ancestry checks on `mars`. No production
permissions were changed by those steps. The installed `mars` parent
paths `/home/richard` (0750) and `/root` (0700) are to remain unchanged.

## Explicit design decision for review

**Proposed retirement: YES.** Remove the *active* Playbooks
`roles/backup-collection/source-modes.json` and historical restoration
instructions; retain a much smaller pre-deployment metadata/task-policy
regression which relies on ordinary checkout modes. Its nine filter content
hashes remain captured in the accepted 0047 and 0048 evidence; the live
post-deployment verifier compares the deployed bytes to the actual Playbooks
source, not to a permanent, manually maintained historical hash manifest.
Retain all 0047 completed feature evidence and one-off restoration tools.

This simplifies the permanent Playbooks implementation while preserving
`archive: true` and `--omit-dir-times`, separately restricted user cron/log
`0750`, launcher templates `0744`, and existing root parent boundaries.
The intended installation changes are limited to the five synchronized
directory modes (`0750` → `0755`) and nine filters (`0664` → `0644`);
no changes to backup data, Btrfs snapshots, cron schedule, transport,
credentials or sudoers are authorised.

## Publication, verification, rollback and stop conditions

1. Apply the Playbooks ZIP in the `mango` Playbooks Git checkout. The ZIP
   updates three files; the publication tool explicitly removes the old
   `source-modes.json` from the active Playbooks tree.
2. From Windows Cygwin, execute `tools/publish-0048-playbooks.sh` on `mango`
   through SSH and save its output under `evidence/Step 3/`. This verifies
   base revisions, exact candidate hashes and stage scope before committing
   Playbooks and the controller's `playbooks` Git-submodule pin.
3. Once publication passes, execute `tools/deploy-and-verify-0048-mars.sh`
   through SSH from Windows and save output in `evidence/Step 4/`. It runs
   one predeployment preview, the selected real Ansible tasks on `mars`,
   a second idempotence run, installed-mode/byte-hash checks and read-only
   backup scheduling checks.
4. The fallback Playbooks commit is
   `df68a0e3bc57bae29a76f46a58c30835126d7f20`; re-establishing the
   old `0750`/`0664` installed state would also require the historically
   preserved 0047 mode restoration procedure. **Do not automatically
   roll back or delete backup datasets/snapshots if verification fails.**
   Diagnose using the captured output before changing production again.
5. Review the resulting live operation, record formal acceptance and
   published Diaries change-control receipts before closing 0048.

The publication script stops if base Git revisions, existing user edits,
upstream main or expected staged files differ. A failure *after* a Playbooks
push may leave its commit published but the controller pin unpublished;
recover from the log instead of rerunning blindly. Live deployment is a
separate, explicit command and cannot occur during the publication script.
