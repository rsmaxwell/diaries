# 0040-FEAT — Step 12 post-acceptance legacy-code retirement implementation

**Prepared:** 2026-11-08. **Status:** SOURCE PREPARED / REGRESSION VERIFIED / NOT DEPLOYED / REMOVAL NOT AUTHORISED.  
**Source bundle:** `playbook-sources-20261107-125132.zip` and `diaries-sources-20261107-125137.zip`; deployed repository revisions must be confirmed at application time.  
**Accepted earlier Playbooks revision:** `6553ace`; Diaries evidence revision: `61fd3a4`. Source ZIPs are not Git repository checkouts, and the ZIP preparation itself cannot establish the current live Git revisions.

## Objective and scope

Retire the superseded native-push/receiver executables and dormant intermediate
agreed-parent modules from `mars` and `backup` **after accepting the first
unattended receiver prune**. Preserve the current simplified sender at
`/usr/local/bin/btrfs-simplified-replication`, `btrfs-native-push.service` /
`.timer` names, 03:30 UTC sender schedule, 04:15 UTC receiver-prune timer,
retention policy and maximum 10 deletions, snapshots, protected state records,
checkpoint holds, historical receipts, data and unrelated system utilities.

## Permanent Playbooks changes

1. `btrfs-simplified-replication.py` now exposes a read-only `sender status`.
   It checks root-owned local parent and prior records against Btrfs identities,
   calls receiver `status` and `status --snapshot <receiver parent>`, and checks
   receiver identity and state consistency. It reports the next newest eligible
   source snapshot, or an explicit receiver-ahead reconciliation requirement,
   without starting a cycle, sending, saving, promoting, deleting, or creating
   a missing manager lock. Ambiguity, unreachable receiver and busy locks fail
   closed.
2. `diaries-backup-status.py` uses only `sender status` to populate its
   existing `replicationPreflight` and `offsite` sections. It preserves snapshot
   health, backup history and last verified pull reporting. Historic receipt
   listing and legacy `btrfs-native-push --latest --preflight` are eliminated.
   `sudo -n /usr/local/sbin/diaries-backup-status --json` is the operator check.
3. `tasks/native.yaml` installs the changed status script on the simplified
   source; skips copying the old source push, legacy receiver helper, Stage B
   gateway and old fixed endpoint for active simplified endpoints; stops
   installing the old observer and runtime when simplified code is installed;
   and ensures the obsolete source endpoint sudoers rule is absent.
   A legacy-mode deployment with simplified activation disabled retains its
   former default behaviour. There is no task deleting an old executable from
   deployed hosts. The legacy source lock and protected state are preserved.

This does **not** rewrite the active systemd service/timer names or source
schedule. Existing intermediate Python source remains in Git as historical
reference in this increment; its already-deployed executable copies are
handled only by the feature-local tool.

## Feature-local instruments and evidence

- `tools/verify-0040-step12-first-unattended-prune.py`: read-only SSH capture
  of 8 November's actual systemd service result, journal, delete receipt,
  receiver plan, old-prune-unit definition, timer status and two agreed-parent
  records. Writes raw log and JSON diagnostic to `evidence/Step 12/raw-logs`.
  A diagnostic PASS alone is **not** formal acceptance.
- `tools/legacy-code-candidate-paths.json`: explicit paths observed on the
  7 November audit: 39 candidate files on `mars`, 33 on `backup`, plus two
  specifically named legacy receiver-prune unit files. These are *candidates*,
  not evidence of unused status on their own. Python caches and snapshot
  manager editor backup files are intentionally excluded.
- `tools/retire-0040-obsolete-code.py`: `--capture` is read-only, records
  root ownership, regular-file mode, size and SHA-256 for each exact path.
  `--apply` is separately guarded by a reviewed 8 November acceptance report,
  exact confirmation token and a matching live manifest. It confirms the
  simplified sender/status/receiver/timers, disabled legacy receiver timer and
  removed legacy source sudoers; creates per-host verified local tar rollback
  archives under `evidence/Step 12/rollback`; only then unlinks exact checked
  paths and reloads systemd on `backup`. No globbing, recursive deletion,
  snapshot/parent-state action or remote temporary scripts.

**Important:** The one-off cleanup intentionally refuses a changed/missing
candidate, unexpected ownership, symlink, altered checksum, unaccepted prune
report or a changed active service. The two legacy unit files must actually
reside at `/etc/systemd/system/btrfs-legacy-prune.{service,timer}`; check their
paths using the recorded `systemctl cat` result first. If the unit locations
are different, stop and revise the explicit manifest rather than broadening
path deletion. A partial cross-host retirement requires review of the saved
host-specific rollback tar, not automatic rerun or improvised commands.

## Execution and evidence order

All commands must be run from the named host. **Do not put `set -e` in an
interactive shell**; any fail-fast commands belong in isolated subshells.

### A. First unattended receiver-prune acceptance — before deploying any changes

On Windows Cygwin, apply the **Diaries** ZIP to the authoritative Windows
Diaries repository using Beyond Compare. Review and commit/push only the
feature-owned scripts and report (not Playbooks files). Synchronise the
execution copy of Diaries to `mango` by a verified fast-forward. Do not assume
Windows changes are present on `mango` until that sync has succeeded.

**SSH terminal on `mango`:**

```bash
cd /home/richard/diaries
python3 'change-control/in-progress/0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage/tools/verify-0040-step12-first-unattended-prune.py'
```

Review the saved report and raw evidence, especially the `backup` journal
since 04:00 UTC on 8 November, `Result=success`, `ExecMainStatus=0`, actual
8 November start timestamp, exactly one completion receipt, delete count in
0..10, protected parent/prior identities and retention plan/holds. A zero
count can be valid. Missing/unexpected output means STOP, not acceptance.

### B. Deploy permanent Playbooks source only after acceptance

Apply the separate **Playbooks** ZIP through the `mango` Playbooks Beyond
Compare tab. On `mango`, inspect branch/HEAD/status and all eight changed
role/source/doc/test files before testing. Validate changes against the
accepted `6553ace` baseline; don't overwrite unrelated local work.

**SSH terminal on `mango`:**

```bash
cd /home/richard/playbooks
python3 roles/btrfs-replication/tests/verify-0040-simplified-replication.py
python3 roles/btrfs-replication/tests/verify-0040-simplified-protection.py
python3 roles/btrfs-replication/tests/verify-0040-simplified-cutover-readiness.py
python3 roles/btrfs-replication/tests/verify-0040-step12-3-shared-retention.py
python3 roles/btrfs-replication/tests/verify-0040-step12-parent-boundary.py
python3 roles/snapshots/tests/verify-diaries-backup-status.py
python3 roles/snapshots/tests/verify-0040-simplified-receiver-retention.py
python3 roles/btrfs-replication/tests/verify-0040-legacy-retirement-source.py
ansible-playbook btrfs-replication.yaml --syntax-check --vault-password-file ~/.vault_pass.txt
ansible-playbook btrfs-replication.yaml --limit 'mars,backup' --check --diff --vault-password-file ~/.vault_pass.txt
git diff --check
```

Inspect proposed drift (expect updated simplified script/status and obsolete
sudoers absence, no altered snapshot sources/retention policy/timers). Then
run the same Ansible playbook against `mars,backup` without `--check`, using
`--vault-password-file ~/.vault_pass.txt`, **only after accepted gate and
review**. This does not start a transfer or prune directly, but it can change
systemd/config files; record the actual recap. Validate:

```bash
ssh mars 'systemctl cat btrfs-native-push.service; sudo -n /usr/local/bin/btrfs-simplified-replication sender status; sudo -n /usr/local/sbin/diaries-backup-status --json'
ssh backup 'sudo -n /usr/local/bin/btrfs-simplified-replication receiver status'
```

A status operation may fail closed while the manager lock is busy; never
substitute `sender cycle` or a pruning command for a read-only check.

### C. Exact-code retirement — separately approved after deployment

**SSH terminal on `mango`, from the synced Diaries repository:**

```bash
cd /home/richard/diaries
python3 'change-control/in-progress/0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage/tools/retire-0040-obsolete-code.py' --capture
```

Inspect and preserve the generated `evidence/Step 12/manifests` file, recorded
file modes/hashes, exact units and actual status references; compare with the
read-only host inventory. Do not use the `--apply` mode before explicit
operator approval of the pruning gate and executable retirement. Apply mode
requires a matching manifest, the reviewed prune receipt with
`formal_acceptance: ACCEPTED`, and a specific confirmation token; consult
script `--help` for the required arguments. The operator approves the content
of the JSON acceptance summary; the raw journal log remains unchanged.

If executed after acceptance, verify no obsolete files were reinstalled by a
subsequent Ansible `--check` run, verify simplified sender/receiver status,
confirm the obsolete timer is absent while active timers persist, and transfer
manifests, rollback tar archives, logs and receipt to the **Windows Diaries**
feature directory for permanent versioned evidence. Do not leave these as
untracked permanent evidence only on `mango`.

### Exact-file rollback, only if explicitly authorised

The verified rollback tar archives are local to `mango` under the feature's
`evidence/Step 12/rollback/` directory, with a recorded SHA-256. To restore
specific obsolete code **without changing any snapshot or agreed-parent
record**, verify the intended archive, then pass it over SSH as stdin. Only
use this if a confirmed dependency requires reinstallation, and record
commands and results as feature evidence.

**SSH terminal on `mango`:**

```bash
cd /home/richard/diaries
FEATURE='change-control/in-progress/0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage'
# Substitute the actual inspected archive timestamp, not a guessed filename.
# tar -tf "$FEATURE/evidence/Step 12/rollback/legacy-code-mars-<UTC>.tar"
# ssh -T mars 'sudo -n tar -xf - -C /' < "$FEATURE/evidence/Step 12/rollback/legacy-code-mars-<UTC>.tar"
# ssh -T backup 'sudo -n tar -xf - -C / && sudo -n systemctl daemon-reload' < "$FEATURE/evidence/Step 12/rollback/legacy-code-backup-<UTC>.tar"
```

The commented examples intentionally require the operator to inspect and
replace the actual filename and consciously enable the command. Restoring an
old program is **not** authorisation to run the old replication protocol or
change the running sender command. If receiver/source state might be affected,
stop for separate rollback acceptance rather than starting old binaries.

## Local source-level verification at preparation

- 24 simplified replication tests PASSED (includes three new status tests and
  one no-lock-creation check).
- 3 protection tests PASSED; 5 cutover-readiness tests PASSED.
- Shared retention policy and source parent/pruning boundary checks PASSED.
- 17 simplified receiver retention tests PASSED.
- Operational status report synthetic regression PASSED.
- New legacy-installer source-gating regression PASSED.
- YAML parsed successfully. **Ansible live syntax check/check mode and
  deployment were not run in the source-preparation environment.**

## Closure boundary

Step 12 and 0040-FEAT remain OPEN until the 8 November unattended retention
result is reviewed and formally accepted; the source change, source deployment
and eventual exact-file retirement each require their own results/evidence.
The 0041-FEAT dedicated replication-user security work remains separate.
