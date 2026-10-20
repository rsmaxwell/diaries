# 0037-FEAT — Step 13 production documentation and housekeeping

**State: CLOSED — PASSED WITH RECORDED DEFERRED HOUSEKEEPING (2026-10-20).** Formal acceptance and residuals: `STEP13-FORMAL-CLOSURE.md`. The original pending checklist below is preserved as the pre-closure operating plan, not a statement of present status. This Step 13 record does not authorize snapshot deletion, service restart, Btrfs mutations or removal of evidence.

## Scope and decisions

1. Permanent production implementation belongs under Playbooks `roles/snapshots/` and `roles/local-backup/`; `local-backup.yaml` remains the supported entry point. No standalone staging playbook is a permanent operational dependency.
2. Native timestamp pruning runs hourly (`*-*-* *:15:00`). Legacy pruning runs independently daily at `08:20 UTC`, configured via the `mars` inventory; `--max-delete 1` is **per service invocation**, not a strict per-calendar-day deletion cap.
3. Legacy source inventory uses `snapper ... list --disable-used-space`; old Snapper timeline/boot/cleanup timers remain retired. `btrfs-snapshot-manager status` reports bounded read-only qgroup counts.
4. Host holds, replication pins and independent `backup` receiver receipts are operational protections, not cleanup candidates.
5. Step 12 proved focused-tag installation and repeated idempotency. A full untagged local-backup dry run / deployment is **not yet evidenced**; prior snapshots-tag dry run proposed an unrelated `complete-dataset-manifest.py` upgrade. Treat it as an open reconciliation item, not a Step 13 completed assertion.

## Operator acceptance checklist — read-only first

On `mango`:

```bash
cd /home/richard/playbooks
 git status --short
 git rev-parse HEAD
 ansible-playbook local-backup.yaml --limit mars --check --diff --vault-password-file ~/.vault_pass.txt
```

Read the untagged dry-run diff carefully, especially the manifest verifier and any backup scheduling work. **Do not execute untagged deployment solely to satisfy Step 13.** Capture and investigate failure or proposed unrelated changes.

On `mars`:

```bash
sudo systemctl cat btrfs-legacy-prune.service btrfs-legacy-prune.timer btrfs-snapshot-prune.timer
sudo systemctl is-enabled btrfs-legacy-prune.timer btrfs-snapshot-prune.timer
sudo systemctl is-active btrfs-legacy-prune.timer btrfs-snapshot-prune.timer
sudo btrfs-snapshot-manager status
sudo btrfs-snapshot-manager hold-list
sudo btrfs-snapshot-manager legacy-prune --legacy-map root=root --legacy-map @data=@data --max-delete 1
sudo systemctl list-timers --all | grep -E 'snapper|btrfs|diaries' || true
```

For host-side temp hygiene, **inventory only** (`find`/`ls`), do not use `rm` until paths and owners are individually reviewed. A new daily natural timer run may already have changed eligible legacy counts; preserve current journal output as separate operational evidence.

In Diaries repository on Windows/Cygwin, record `git status --short` and `git rev-parse HEAD`; confirm change-control files have no secrets. Retain the original Step 11 and Step 12 raw logs and checksum files.

## Outstanding work for Step 13 closure

- Collect actual host inventory of 0037 temporary workspaces and approve each removal explicitly; no host cleanup is claimed in this package.
- Reconcile unrelated full-playbook check-mode differences and distinguish expected source drift from deployment blockers.
- Populate actual Git revisions after the user applies/commits the source/document updates.
- Only then mark Step 13 **CLOSED** and proceed to original Step 14 final feature closure.

## Final Step 13 disposition (2026-10-20)

The full live `./local-backup.sh` reported `ok=64 changed=0 failed=0` after correction of the backup directory rsync permission conflict. Host inventory found three residual root-owned helpers, retained with disposition deferred to Step 14. Source/Python and timer reconciliation accepted. See `STEP13-FORMAL-CLOSURE.md`; its final decision supersedes the pre-closure pending checklist above.
