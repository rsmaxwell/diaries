# 0038-FEAT — Reconcile off-site Btrfs snapshot manager and receiver configuration

**Status: CLOSED — all Steps 1–8 accepted 21 October 2026.**

## Problem

On `backup`, `sudo btrfs-snapshot-manager status` fails because `/etc/btrfs-snapshot-manager.json` still refers to the retired `diaries-mars-replica/pluto` working dataset. The native off-site receive tree is instead `/@data/mars-received/@data/`, with replication receipts under `/@data/mars-received/.replication-state/`. This is a separate post-0037 reconciliation; do not reopen 0037-FEAT.

## Goals

- Reconcile the installed snapshot-manager program/configuration with current Playbooks source and confirm `status` succeeds on `backup`.
- Ensure `backup` remains a **receive-only** host: no accidental local create/prune activation; no receiver snapshot or receipt mutation during manager reconciliation.
- Confirm native receiver integrity, history discovery, replication safety boundaries and repeat-run Ansible idempotency.
- Use source-controlled Ansible for permanent configuration, not host-local manual tweaks.
- Keep feature-specific captures, diagnostics, temporary scripts, regressions and reports **within this feature tree**, rather than production directories on `mango`, `mars`, `backup` or `pluto`.

## Scope / exclusions

In scope: `remote-backup.yaml`, `roles/remote-backup`, shared `roles/snapshots` install/configuration, installed `backup` manager/history/verifier, inventory overrides, systemd activation checks, native receiver read-only inspection.

Out of scope without new approval: deleting or reseeding received snapshots, changing receiver retention policy/receipts, changing `/@data/mars-received` layout, enabling local snapshot timers, changing production schedules, running a full backup transfer/restore, and changes to Diaries client/responder images.

## Directory index

- `DESIGN.md`: source-of-truth distinction between local snapshot manager and native receiver.
- `IMPLEMENTATION-STEPS.md`: gated sequence and acceptance criteria.
- `WORKSPACE-POLICY.md`: staging and production-tree hygiene.
- `PROMOTION-MANIFEST.md`: only final permanent source changes and their evidence.
- `tools/`: feature-only command wrappers and capture scripts.
- `tests/`: feature-only experiments, regression drivers and fixtures.
- `reports/`: interpreted inventories, dry-run reviews and findings.
- `evidence/Step NN/`: raw operator logs, pre/post verification, approvals and closure notes.
- `scratch/`: ignored/disposable extracted material and intermediate artifacts.

Use **mango SSH terminal** for Ansible, **backup SSH terminal** for read-only host tests, **Cygwin** for local source inspections and applying ZIPs with Beyond Compare 4. WinSCP is available for inspection, not needed for ordinary capture via SSH.

## Historical status — 20 October 2026 (superseded by updates below)

Steps 1–4 CLOSED. Step 4 final check/diff accepted (`note(20261020-203011).txt`, `ok=22 changed=5 failed=0`). **Step 5 IN PROGRESS:** controlled installation on `backup`, not yet executed. Steps 6–8 pending. See `evidence/Step 04/STEP04-ACCEPTANCE.md` and `evidence/Step 05/STEP05-CONTROLLED-DEPLOYMENT.md`.

**20 October 2026:** Step 5 formally CLOSED with successful real deployment (`changed=5`), post-install manager/receiver/timer checks and subsequent Ansible check-mode convergence (`changed=0`). Step 6 IN PROGRESS pending read-only receipt-content and installed-tool verification; Step 7 NOT STARTED. See evidence/Step 05 and Step 06.

**21 October 2026 update:** Step 6 formally **CLOSED**. Installed tools, receiver receipts and the 15-subvolume inventory were verified; the new overnight incremental `20261021-030006Z` has a receipt UUID matching Btrfs Received UUID and both transfer exit statuses `0`. See `evidence/Step 06/STEP06-ACCEPTANCE.md`. Step 7 **IN PROGRESS**; Step 8 NOT STARTED. The optional qgroup summary remains an explicitly deferred non-blocking diagnostic.

**21 October 2026 — Step 7 CLOSED:** source and installed negative regressions passed; repeated real remote-backup Ansible run `backup ok=26 changed=0 failed=0` proved actual convergence. Step 8 is **IN PROGRESS** for feature evidence reconciliation, Git/source provenance, rollback disposition and final close-out. Feature not yet CLOSED. See `evidence/Step 07/STEP07-ACCEPTANCE.md` and `evidence/Step 08/STEP08-CLOSEOUT-PLAN.md`.

**Final closure — 21 October 2026:** Step 8 and overall 0038-FEAT formally **CLOSED**. Git provenance is Diaries `e69e08b2ff100b7d2afcf8458e9cb9204bc6be5a` and Playbooks `fc8233da3464aa114d69a2e34bd8990f96daf281` (amended and pushed). Four rollback copies on `backup` are retained by explicit decision. Optional qgroup summary parsing remains a deferred, non-blocking diagnostic. The completed change-control tree is archived under `change-control/complete/`. See `evidence/Step 08/STEP08-ACCEPTANCE.md`.
