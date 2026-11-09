# 0040 Step 12 — controlled cutover from Windows Cygwin

**6 November 2026 consolidated operator path.** This package includes the previous revised receiver journal auditor plus a new guarded operator script, `tools/step12-controlled-cutover.sh`. It supersedes the piecemeal command sequence below as the preferred operating path, without changing Playbooks or permanent runtime code. Neither the receiver journal retirement nor the new replication cutover has been performed by preparation of this ZIP.


## 6 November 2026 — cutover policy after second preflight

Second production preflight (15:34 UTC) stopped safely on `Completed candidate receipt source_filesystem_uuid mismatch`. **This is not a verified legacy receipt.** The legacy receiver's original acceptance checks correctly reject a receipt with that field, and those operational checks remain unchanged.

For 0040 migration, the historical receipt and its claims are **not inputs** to the new bootstrap. We only preserve that receipt's file bytes unchanged, pin its SHA-256 in the audit and locked archive path, and independently verify the actual journal parent/candidate Btrfs read-only received UUIDs. The independent new common snapshot `20261101-140039Z` is verified on both hosts, including its exact source UUID. The obsolete journal alone is moved to a root-only rollback directory. Historical receipts and Btrfs subvolumes are not altered or promoted as trusted new state.

A malformed legacy receipt can therefore remain historical evidence, not a cutover blocker. This does **not** mean it has been repaired or accepted. The journal, candidate, snapshot identities, file types, permissions, no-stage rules, digest pins, timer/transport checks, and initial-parent checks must still pass. No production state change was observed in either failed preflight.

This section supersedes receipt-acceptance language in the earlier historical notes below. Use the **guarded** `bash "$RUNBOOK" preflight` then `bash "$RUNBOOK" execute` steps, not the older manual command sequence.

## 6 November 2026 — first preflight mismatch and corrected validation

Windows/main `220672e` and mango/main `220672e` were confirmed. Mango retains five **untracked** Step 12 raw logs; do not overwrite or discard them. The first preflight exited before mutations with `Completed candidate receipt does not match journal lineage and Btrfs transport`. The source-parent read-only audit passed. No journal retirement, bootstrap, transfer or timer changes occurred.

The prior migration-only auditor imposed conditions **stricter than the actual legacy receiver**: it allowed only incremental receipts and required a previously published receipt's parent to equal the **abandoned journal's** parent. In the legacy receiver's `receipt()` acceptance contract, receipts are validated for Btrfs transport (full or incremental), source/receiver filesystem and candidate identity, successful transfer status, destination, and read-only received UUID. The parent recorded for an earlier successful transfer need not equal the parent of a later interrupted journal. The first correction attempted to validate this legacy acceptance contract, but the second preflight identified a source filesystem metadata mismatch. The final cutover utility no longer treats historical receipt fields as authoritative. It pins the entire receipt file unchanged and verifies Btrfs subvolume identities independently. See the newer section above.

This historical correction did **not** establish receipt validity. The current migration explicitly preserves the receipt as untrusted history; only a successful full preflight authorises `execute`.

## Operational prerequisites

Apply this ZIP to the **Windows Diaries parent checkout** with Beyond Compare 4. The script is invoked from that checkout and streams the included audit utility over SSH. The Windows copy need not be synchronised to `mango` for this feature-specific operation. It verifies local Git branch/commit/status and submodule pointers, but does not modify Git. Check any local changes before executing.

**Windows Cygwin terminal**, from the Windows Diaries root:

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
FEATURE='change-control/in-progress/0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage'
RUNBOOK="$FEATURE/tools/step12-controlled-cutover.sh"
bash -n "$RUNBOOK"
bash "$RUNBOOK" preflight
```

The preflight rechecks the exact B source/receiver identity, the legacy journal SHA, historical candidate receipt file identity and SHA (not its provenance claims), absent staging markers, installed simplified executable hashes, expected legacy unit/timer status, noninteractive SSH and receiver pruning disabled. It also identifies the first newer source snapshot and refuses if a legacy receipt **or receiver object** already exists for it, so the controlled cycle must exercise an actual new send/receive rather than merely advancing a pre-existing received object. It writes a timestamped raw log inside the feature evidence directory, and **makes no state changes**.

If the preflight exits 0 with `PASS: guarded cutover preflight completed`, the same Cygwin terminal can perform the guarded transition:

```bash
bash "$RUNBOOK" execute
```

`execute` **reruns every preflight gate**, then stops the legacy mars timer/service, archives **only** the exact obsolete journal into a root-only rollback directory on backup, bootstraps the source/receiver `.simple-agreed-parent.json` records to `20261101-140039Z`, checks their equality, runs **one** simplified sender cycle, then reads and compares the advanced state. It prints `PASS: first simplified cycle completed` only if the records agree and retain B as `prior`. It never deletes or renames historical snapshots or receipts, and it never automatically restores the legacy timer. An unexpected state leaves the old timer **stopped** and is logged for diagnosis; do not blindly rerun `execute` after any partial state change.

**The script does not activate the unattended schedule.** After the manual cycle passes, inspect the source and Playbooks checkout on **mango** and review the Ansible preview:

```bash
cd /home/richard/playbooks
printf 'Branch: '; git branch --show-current
git rev-parse --short HEAD
git status --short
ansible-playbook btrfs-replication.yaml --limit 'mars,backup' --check --diff \
  --vault-password-file ~/.vault_pass.txt \
  -e '{"btrfs_native_push_schedule_enabled":true,"btrfs_simplified_replication_install_enabled":true,"btrfs_simplified_replication_active_enabled":true}'
```

Review the resulting service `ExecStart`, changes and failures before executing the identical Ansible command **without** `--check --diff`. Ansible should reenable the existing 03:30 UTC timer, not create a second schedule. Then verify `systemctl show -p ExecStart` and `systemctl is-enabled/is-active` on mars, and confirm receiver pruning remains disabled. Preserve the evidence log, Playbooks result and new state readbacks under 0040-FEAT; do not close Step 12 merely because the script succeeds.

**Rollback:** Keep both new state files and the archived legacy journal available for forensic examination after a partial cutover. Do not restore the old journal and restart the legacy sender automatically; it was already refusing that transaction. No snapshot deletion, receiver pruning or new schedule is approved by this runbook.

---

# 0040 Step 12 — completed legacy candidate and obsolete journal

**Revised 6 November 2026 after the first production read-only audits.** No live cutover has been performed. This version supersedes the earlier nine-test tool and README; apply to the Windows Diaries repository root through Beyond Compare 4.

## Evidence from the initial audits

- Both audits exited 0; source/receiver identity of B `20261101-140039Z` matched and B is read-only on both endpoints.
- Backup journal SHA-256 `e11483fe05c482894c2db6fc15ffa63164f6b9c3da831508e0a2990123b9f3f2`, mtime `2026-11-01T19:39:39.159265+00:00`, old parent `20261030-030033Z`, candidate `20261030-170009Z`.
- Old candidate `20261030-170009Z` is a **published, read-only received Btrfs snapshot** (received UUID `a9b78fb9-4da6-cf4f-b242-13909f574193`) and its legacy receipt is present.
- No nonce-bound private stage/sidecar; other transaction markers absent. Neither simplified state exists.
- **Unverified:** receipt *contents*, integrity, and historical transport/parent fields. The initial audit only reported its presence. Its contents subsequently failed the legacy acceptance contract; the transition therefore does not rely on those contents.

## 1 — Windows Cygwin: revised receiver audit (read-only)

The current audit verifies the historic candidate and journal parent from the actual Btrfs read-only `Received UUID` values, independently of the historical receipt. It verifies the receipt file is an ordinary private regular file, pins its bytes by SHA-256 and preserves it without treating its metadata as proof. It never modifies either host.

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
FEATURE='change-control/in-progress/0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage'
SCRIPT="$FEATURE/tools/step12-legacy-journal-transition.py"
LOGDIR="$FEATURE/evidence/Step 12/raw-logs"
mkdir -p "$LOGDIR"

ssh backup 'sudo -n python3 - audit receiver' < "$SCRIPT" > "$LOGDIR/step12-completed-candidate-audit.txt" 2>&1
rc=$?
cat "$LOGDIR/step12-completed-candidate-audit.txt"
printf 'Completed candidate audit exit: %s\n' "$rc"
```

**Gate:** require `rc=0`, `Candidate Btrfs identity: VERIFIED (readonly; independent of receipt claims)`, a new `Candidate receipt sha256`, the original unchanged journal SHA above, candidate stamp `20261030-170009Z`, and all staged objects/other markers absent. If any check fails, do not archive or bootstrap. Keep the original source audit as accepted evidence; rerun it only if B's source identity has changed.

## 2 — Windows Cygwin: transport, install and pruning configuration (read-only)

```bash
ssh mars 'sudo -n sha256sum /usr/local/bin/btrfs-simplified-replication; systemctl is-enabled btrfs-native-push.timer; systemctl is-active btrfs-native-push.timer; systemctl show -p ExecStart btrfs-native-push.service'
ssh backup 'sudo -n sha256sum /usr/local/bin/btrfs-simplified-replication'
ssh mars 'sudo -n -u richard ssh -o BatchMode=yes -o ConnectTimeout=15 -p 39263 richard@10.254.22.1 "sudo -n true" && echo "PASS: mars to backup noninteractive sudo transport"'
ssh backup "sudo -n python3 -c 'import json; p="/etc/btrfs-snapshot-manager.json"; c=json.load(open(p)); print("receiver_prune_enabled:",c.get("receiver_prune_enabled")); assert c.get("receiver_prune_enabled") is False'"
```

Installed executable hashes should both equal `9be64295a6b6807df0fcd33d924b7a6549959f2a03dcab2953dcf0ac77fa6297` (already supported by installation acceptance). If receiver pruning config differs, transport fails, or systemd command surprises us, stop and review rather than bootstrapping.

## 3 — Controlled journal retirement (only after gates 1–2 pass)

**Terminal: Windows Cygwin, in the same Diaries directory**. Stop the *source timer and service*, preserve the schedule definition, and verify stopped. The script locks both receiver-side historical locks and rechecks the journal SHA, candidate identity, receipt SHA and its provenance under those locks. It moves only the journal to an `0700` rollback directory, without deleting/changing snapshots, receipts or legacy parent state.

```bash
ssh mars 'sudo -n systemctl stop btrfs-native-push.timer && sudo -n systemctl stop btrfs-native-push.service && ! systemctl is-active --quiet btrfs-native-push.timer && ! systemctl is-active --quiet btrfs-native-push.service && echo "PASS: source service and timer stopped"'
stop_rc=$?
printf 'Stop exit: %s\n' "$stop_rc"
# DO NOT continue on nonzero stop_rc or if another transfer is active.

# Copy the exact Candidate receipt sha256 from the *new* audit output:
RECEIPT_SHA='<paste 64-character candidate receipt sha256 from audit>'
JOURNAL_SHA='e11483fe05c482894c2db6fc15ffa63164f6b9c3da831508e0a2990123b9f3f2'
CANDIDATE='20261030-170009Z'

# Run only after stop_rc=0 and receipt SHA has been verified:
ssh backup "sudo -n python3 - archive --expected-sha256 $JOURNAL_SHA --expected-candidate $CANDIDATE --allow-completed-candidate --expected-receipt-sha256 $RECEIPT_SHA" \
  < "$SCRIPT" > "$LOGDIR/step12-completed-candidate-journal-archive.txt" 2>&1
archive_rc=$?
cat "$LOGDIR/step12-completed-candidate-journal-archive.txt"
printf 'Archive exit: %s\n' "$archive_rc"
```

**Gate:** `archive_rc=0` and `PASS: obsolete receiver journal archived`. Retain the journal in the root-only rollback directory on backup and its checksum in the feature evidence. Do not run the archive again if it succeeds.

## 4 — Initial simplified agreed parent, controlled transfer, and service cutover

**Windows Cygwin, source service/timer stopped, only after successful archive and transport checks:**

```bash
ssh mars 'sudo -n /usr/local/bin/btrfs-simplified-replication sender bootstrap --snapshot 20261101-140039Z'
ssh mars 'sudo -n cat /media/usb/@snapshots/.simple-agreed-parent.json'
ssh backup 'sudo -n cat /@data/mars-received/.replication-state/.simple-agreed-parent.json'
```

Check both parent records for the same `(timestamp, uuid)` and null `prior`. **Only after readback equality**, run one manual `ssh mars 'sudo -n /usr/local/bin/btrfs-simplified-replication sender cycle'`. Inspect the new parent/prior and Btrfs identities on both hosts, including the last selected candidate, before enabling unattended operation. The executable deliberately chooses the next eligible snapshot; do not guess a timestamp.

To activate service cutover, use the Playbooks repo on mango (not the Windows Diaries repo) once manual acceptance is complete:

```bash
cd /home/richard/playbooks
ansible-playbook btrfs-replication.yaml --limit 'mars,backup' --check --diff \
  --vault-password-file ~/.vault_pass.txt \
  -e '{"btrfs_native_push_schedule_enabled":true,"btrfs_simplified_replication_install_enabled":true,"btrfs_simplified_replication_active_enabled":true}'
```

Review planned changes; then run the same command without `--check --diff` only after acceptance. Confirm source `ExecStart` points to simplified sender and the existing 03:30 UTC timer remains unchanged. **Receiver pruning remains disabled.** Preserve historical snapshots and receipts; no full restore or destructive tests required.

## Rollback

Stop the source service and timer. The archived journal and historical source/receiver states remain untouched and available for examination; do not restart the old replication cycle blindly because its journal was stale. The established Playbooks active-opt-in can be disabled to restore the old service template, but restoring a template does not reconcile the old protocol. After any partial bootstrap, preserve the new agreed-parent files for analysis rather than deleting them ad hoc.
