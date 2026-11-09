# 0040-FEAT — Post-acceptance retirement of legacy Btrfs executables

**Prepared:** 2026-11-07  
**Status:** PLAN ONLY — no executable or inventory removal authorised by this document  
**Owner:** 0040-FEAT feature change control in the Diaries parent repository  
**Evidence basis:** user-supplied `mars:/usr/local/bin` listing at 2026-11-07 15:23 UTC; latest supplied Playbooks source bundle `playbook-sources-20261107-125132.zip` (subsequent documentation updates accepted and committed in Playbooks `6553ace`); source and receiver inventory audit and Step 12 accepted logs.

## Findings

| Observed `mars` path | Classification | Supporting source evidence |
|---|---|---|
| `/usr/local/bin/btrfs-simplified-replication` | **KEEP / ACTIVE** | `btrfs-native-push.service.j2` executes `sender cycle` when `btrfs_simplified_replication_active_enabled=true`, as on `mars`. Do not rename or change the existing service/timer unit names. |
| `/usr/local/bin/btrfs-agreed-parent-sender` | **RETIRE CANDIDATE** | Legacy opt-in installer: `roles/btrfs-replication/tasks/agreed-parent-runtime.yaml`, task `Install manual source transaction command`. The associated runtime install gate defaults to `false`; no active systemd reference has been established. |
| `/usr/local/bin/btrfs-native-push` | **RETIRE AFTER DEPENDENCY MIGRATION** | `roles/btrfs-replication/tasks/native.yaml` still always installs it on the source. The active source service now selects the simplified executable, but `roles/snapshots/files/diaries-backup-status.py` still invokes legacy `--latest --preflight`. |
| `docker-compose`, `dotenv`, `normalizer`, `wsdump.py` | **OUT OF SCOPE** | Not related to Btrfs replication. |
| `/usr/local/bin/__pycache__` | **OUT OF SCOPE** | Inspect provenance first; do not broadly delete directories from the bin path. |

These are Python executables, not compiled binaries. Presence alone is not proof that a file is inactive.

### Other potential cleanup on `backup`

The old receiver helper `/usr/local/bin/btrfs-native-push-receiver` is still installed by `roles/btrfs-replication/tasks/native.yaml` and consumed by the current `diaries-backup-status.py`. There may also be dormant `btrfs-agreed-parent-*` modules under `/usr/local/libexec` and legacy prune components under `/usr/local/sbin`. Audit them separately by **exact path**. Do not infer their presence from the source tree and do not delete them via broad globbing.

### Important CLI contract

`btrfs-simplified-replication` supports `receiver status`; it **does not implement `sender status`**. The executable requires root, and `sender cycle` is **not read-only**. Therefore, do not replace the legacy preflight with `sender cycle`. A new read-only operator report should inspect the root-owned source `.simple-agreed-parent.json`, validate the protected parent and eligible source snapshots, query the receiver read-only state, and preserve the existing backup-history/snapshot/pull sections. It must never advance an agreed-parent record or start an incremental send.

## Retirement sequence

1. **Wait for operational acceptance.** Verify the first unattended `btrfs-receiver-simple-prune.service` run on `backup`, scheduled 2026-11-08 04:15 UTC. Confirm successful exit, delete count at most 10, appropriate retention inventory, protected `parent` and `prior` on both endpoints, and existing holds. Do not alter active code, schedule, checkpoint holds or snapshots to conduct this housekeeping.
2. **Capture read-only dependency evidence.** On `mars`, record `systemctl cat btrfs-native-push.service`, `systemctl show ... -p ExecStart`, `stat`/SHA-256 of the three observed scripts and `diaries-backup-status`, and references in `/etc/systemd/system`, cron, operational shell scripts and Ansible source. Check for manual operators or rollback instructions. On `backup`, inspect the legacy receiver executable and any observer/privileged helper registrations separately. Preserve logs in `evidence/Step 12/raw-logs` in this feature directory.
3. **Migrate the status command.** Change the permanent `diaries-backup-status.py` source and relevant tests/docs so that its off-site and next-transfer reporting reflect the simplified agreed-parent implementation, not legacy `--latest --preflight` and legacy receiver receipts. Use a genuinely read-only interface and define failure behaviour for unreachable `backup`, ambiguous state, held snapshots and missing/unsafe parent. Verify no status invocation sends data or changes state.
4. **Stop installing retired executables.** Remove/retire the unconditional legacy source operator installation task in `roles/btrfs-replication/tasks/native.yaml`; remove the dormant agreed-parent runtime installation path only after all users/rollback needs are reconciled. Assess the old receiver helper's installation in the same change. Do **not** remove the active `btrfs-simplified-replication` installation, source timer/service, shared snapshot-manager or active receiver-pruning units.
5. **Consolidated source regression and deployment check.** Test the updated status report, active simplified replication/protection and shared receiver retention, then run Ansible syntax and targeted `--check --diff` against `mars,backup`. A preview that shows legacy files absent is not sufficient: Ansible does not automatically remove files that a `copy` task no longer installs.
6. **Retire exact installed paths once.** Use a feature-specific, guarded playbook/tool under `0040-FEAT/tools/` executed from `/home/richard/diaries` on `mango`: validate `stat`, checksum, correct host and absence of live references; remove only a reviewed explicit allowlist of legacy executable files. Keep a manifest with original SHA-256, owner/mode, host, commands, and rollback copies/reconstruction method. Do not put one-off cleanup tasks into permanent Playbooks roles. No Btrfs subvolumes, backup datasets or checkpoints are to be deleted.
7. **Post-removal acceptance.** Confirm active systemd `ExecStart` still names `/usr/local/bin/btrfs-simplified-replication sender cycle`; `diaries-backup-status` succeeds without legacy helpers; Playbooks idempotence does not recreate retired scripts; receiver status and retention planning remain operational; source and receiver agreed-parent records stay unchanged by read-only checks. Commit Playbooks permanent changes separately from feature-local Diaries evidence.

## Preliminary read-only host commands

**SSH terminal on `mars`:**

```bash
cd /usr/local/bin
systemctl cat btrfs-native-push.service
systemctl show btrfs-native-push.service -p ExecStart -p FragmentPath -p Result -p ExecMainStatus --no-pager
stat -c '%n %F %U:%G %a %s bytes' btrfs-simplified-replication btrfs-agreed-parent-sender btrfs-native-push
sha256sum btrfs-simplified-replication btrfs-agreed-parent-sender btrfs-native-push
command -v diaries-backup-status || true
```

**SSH terminal on `mango`, Playbooks working copy:**

```bash
cd /home/richard/playbooks
git branch --show-current
git rev-parse HEAD
git status --short
rg -n 'btrfs-agreed-parent-sender|btrfs-native-push|diaries-backup-status' roles --glob '!**/__pycache__/**' || true
```

If `rg` is absent on `mango`, use `grep -RInE` over the explicit `roles/btrfs-replication` and `roles/snapshots` directories, excluding `.pyc` files. Inspect the findings before approving removal. Host commands above are diagnostics, not evidence of acceptance until actually run and captured.

## Rollback and release boundary

Preserve the established snapshot and agreed-parent state; do not use a legacy executable as an automatic rollback. Its receipt/journal expectations may no longer agree with the simplified protocol. Restoring a retired executable only restores a file, not protocol compatibility. Retain exact original binaries/code in Git history and record path hashes before removal. If a dependency unexpectedly breaks, restore the specific helper and its original permissions while leaving the simplified sender and receiver-pruning timers unchanged; obtain explicit authorisation before any rollback affecting snapshot state.

**Acceptance status:** This document authorises **planning and read-only evidence collection only**. Execute retirement after the first unattended receiver-pruning run is accepted and the dependency/status-tool replacement is verified. Do not mark Step 12 or 0040-FEAT closed based solely on this plan.
