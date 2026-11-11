# 0045-FEAT — Implementation plan and acceptance gates

**Step 1 CLOSED (11 November 2026)** following accepted definitive v2 installed manifests and Playbooks source/inventory freeze. **Steps 2–4 OPEN.** 0039-DEF and 0043-FEAT are CLOSED. Prefer one substantial refactor plus one consolidated verification rather than numerous implementation increments.

## Step 1 — Freeze accepted source, effective inventory and installed baseline (CLOSED — 11 November 2026)

**Prerequisites:** 0039 and 0043 formally closed. On the **Windows Cygwin terminal**, verify the Diaries parent working tree and submodule revisions; on **`mango` SSH terminal**, verify `/home/richard/playbooks` branch, HEAD, status, remotes, and current 0044-named regression suite. Confirm actual roles and entry points against the latest Playbooks tree rather than relying on the 9 November archive.

**Required evidence (`evidence/Step 1/`):**

- Read-only audit of callers/references to `local-backup.yaml`, `remote-backup.yaml`, their wrappers, direct role inclusion, tags and any automated entry points, including `snapshots.yaml` and the `/etc/ansible` inventory.
- Generated source-to-installed-path manifest, inventory-effective non-secret settings, managed installation manifest on **`mars` and `backup`**, service/timer/cron/mount/ACL/sudoers readback and SHA-256/mode/owner snapshots. Capture source/service revision and time.
- Explicit acceptance of the equivalent-operation scope and no-destructive-change contract. Never stage secrets or raw Vault output.

**Gate: ACCEPTED.** Definitive schema-v2 baseline `evidence/Step 1/baseline-20261111-111819Z/` records Playbooks Git, inventory topology, installed files/units/packages/ACL/cron/mount and read-only runtime state for both hosts. Source-to-installed mapping and known launcher references are reconciled in `reports/STEP1-FINAL-ACCEPTANCE-20261111.md`; temporary artifacts are excluded. No installed-system changes occurred. Actual external callers (including unattended invocations outside tracked Playbooks) must be checked immediately before retiring `remote-backup.yaml` or launcher in Step 2, because Step 1 source/audit evidence alone cannot prove the absence of those callers.

## Step 2 — Implement one coherent Ledger-style refactor (OPEN)

**Target:** `/home/richard/playbooks` on `mango`, after confirming clean baseline. Prepare the coherent change package for Beyond Compare 4; **no** edits to Playbooks inventory copies or permanent one-off scripts.

- Preserve roles `local-backup`, `snapshots`, `btrfs-replication`, `btrfs` and endpoint roles `source|receiver`; keep source/receiver gate, safety assertions, package dependencies, mount logic and snapshot/replication state handling unchanged.
- Organise `snapshots` and `btrfs-replication` deployment around readable phases: validation/prerequisites; scoped directories; static installed files (loop/manifest or narrow synchronize); rendered templates; privileged/security controls; service unit validation; activation. Refactor `local-backup` only where it reduces duplication, since it already follows Ledger's pattern.
- Keep all manifest entries explicit, with destination, owner/group/mode and endpoint guards. Avoid copying unneeded test/cache/legacy files and never introduce broad deletion. Preserve task ordering where state/lock/handler/activation gates depend on it.
- Before deleting old playbooks or launchers, audit current tracked callers and external `/etc/ansible`, cron, systemd, Jenkins and operator entry points; do not retire a required invocation without updating its caller. Historical documentation is retained unchanged.
- Change only the **operator interface** as approved: propose `local-backup.yaml` → `backup-collection.yaml`, `scripts/local-backup.sh` → `scripts/backup-collection.sh`; retire `remote-backup.yaml` and its wrapper only after proving replacement coverage and no required callers. Keep `btrfs-replication.yaml` and `snapshots.yaml` semantics. Update current operator docs and source tests without rewriting historical completed features.
- If the default `btrfs-replication/tasks/main.yaml` currently dispatches differently from `native.yaml`, explicitly resolve that interface to avoid invoking generic source snapshot configuration on receiver. Do not hide a changed runtime installation behind renamed tasks.

**Gate:** Playbooks diff is complete, readable, limited in scope and reviewable as one package; every old installed asset and condition has a source mapping; risk-sensitive operations and rollback are identified. No deployment during code editing.

## Step 3 — Consolidated regressions, controlled apply, and installed-state equivalence (OPEN)

**Offline checks on `mango`:** full relevant Ansible syntax and host/tag selection checks, no obsolete executable entry-point references, permanent Btrfs replication tests (`verify-replication.py`, `verify-protection.py`, `verify-shared-retention.py`), maintained snapshot/backup tests, guards for source/receiver mismatch, role/task install-map tests, templated-unit comparisons and `--check --diff` where meaningful.

**Operational check:** use default `/etc/ansible` and `--vault-password-file ~/.vault_pass.txt` as required. Execute normal controlled apply on the intended targets, with no ad hoc send/receive, pruning, restore or retention modifications. Capture installed artifacts and enabled states **after** apply using exactly the Step 1 manifest collector; compare normalized manifests including expected-absent legacy files. Confirm intended jobs, source/receiver timers, local backup pull/cron, security modes, protected state and existing root/user boundaries. Reapply to verify no unexpected changes; check read-only source/receiver health and intact parent/checkpoint holds. Preserve old 0039/0043 correctness evidence; do not repeat costly full restores.

**Evidence (`evidence/Step 3/`, reports in `reports/`):** offline regression outputs, Ansible results, before/after manifest comparison, service and unit readbacks, natural scheduler state, any deviations with corrections and affected retests only.

**Gate:** *identical installation* accepted according to `INSTALLATION-EQUIVALENCE-CONTRACT.md`, maintained regressions all pass, no unapproved changed state, no failure concealed by summary output. If differences appear, keep 0045 open and fix/refactor/retest affected scope.

## Step 4 — Final evidence reconciliation, source-control publication and formal closure (OPEN)

- Review complete evidence/rollback and the final map of renamed/retired operator interfaces. Record live deployment/version, measured equality and residual risks.
- Commit and publish the Playbooks change from `/home/richard/playbooks` on `mango`; record SHA, branch and clean status. Stage feature-local one-off tools, raw logs, receipts, source manifest, plan and reports only under the **Diaries parent repo**. Do not assume the Windows checkout and `/home/richard/diaries` match.
- Mark each step CLOSED only after accepted criteria; move this feature **only after** formal closure from `in-progress` to `complete` on Windows using Beyond Compare or a safe filesystem move. Commit and publish the Diaries parent; verify both Git remotes and clean worktrees.

**Gate:** equivalent installation confirmed, operational behaviour unchanged, complete evidence and rollback record accepted, Playbooks and Diaries commits published. Otherwise feature remains IN PROGRESS.

## Operator command conventions for future execution

- Every command must identify **Windows Cygwin**, **`mango` SSH**, **`mars`**, or **`backup`** and use the correct checkout/location; no assumption that Windows and `mango` Diaries trees are synchronized.
- Never run `set -e`, `set -u`, or `set -euo pipefail` directly in an interactive shell. If fail-fast is needed, isolate it in a subshell and print explicit PASS/FAIL. This constraint does not prohibit those options inside standalone scripts.
- Run Ansible on `mango` using default `/etc/ansible` inventory (no redundant `-i`), with `--vault-password-file ~/.vault_pass.txt` when needed. Do not store plaintext secrets in evidence.
- Apply repository-relative ZIPs using Beyond Compare 4: Playbooks ZIP to `/home/richard/playbooks` on `mango`; Diaries ZIP to authoritative Windows Diaries checkout. One-off scripts and raw evidence belong to this feature's `tools/`, `tests/`, `evidence/`, `reports/` directories, not permanently in Playbooks or `/home/richard`.
