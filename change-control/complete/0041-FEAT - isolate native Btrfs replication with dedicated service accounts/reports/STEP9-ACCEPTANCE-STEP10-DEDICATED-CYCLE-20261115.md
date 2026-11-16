# 0041-FEAT — Step 9 accepted evidence and Step 10 supervised dedicated transfer

Date: 2026-11-15. Feature status: IN PROGRESS. Do not close 0041 on this evidence alone.

## Step 9 — Technically passed

Evidence: `evidence/Step 9/disposable-native-transfer-20261115-144655Z.txt`.

- Full native Btrfs transfer: received UUID matched.
- Incremental send/receive: received UUID and payload checksum matched.
- Deliberately truncated stream: rejected.
- Exact interrupted fixture: successfully resent with correct UUID.
- Source and receiver production agreed-parent files: unchanged.
- All disposable test subvolumes: deleted successfully, without a general prune.

This test used the existing `richard` SSH transport for disposable fixtures; it did not exercise dedicated production `receive`.

## Step 10 — One supervised dedicated-identity production cycle

The single-command Cygwin launcher supports `--preflight` (read-only) and `--execute` (one production incremental replication). It sends a standalone Bash script to mango; every nested SSH call uses `-n` so none can consume the script. Evidence is written to `evidence/Step 10/` in the Windows Diaries checkout.

### Controls and scope

- Require reviewed source hashes on mango and installed hashes on both endpoints.
- Require the legacy root service and 03:30 timer to remain installed and active; refuse if sender or receiver-prune service is already running.
- Require verified, equal sender/receiver agreed-parent state, with a newer eligible incremental candidate.
- Inspect receiver candidate read-only; **refuse if it already exists** (prevents the tested cycle from invoking incomplete-candidate deletion).
- Verify source snapshot-manager lock contention is refused.
- Reconfirm stable state and selected candidate immediately before the one permitted run.
- Use the fixed `sudo` entrypoint as `btrfs-send`; its SSH subprocess uses `btrfs-receive` and pinned host key; never manually invoke `btrfs send` via `richard`.
- Verify post-run common parent advancement and independent receiver Btrfs Received UUID, read-only flag and protected state permissions.
- Do not cut over, disable timers, delete production snapshots, manually rewrite JSON records, or retry after failure.

The runtime can still create an **incomplete new receiver snapshot** if a transfer fails mid-stream. The script does not remove it or retry: review recovery/receiver-ahead state before any next action. If another process alters snapshots between preflight and sender lock acquisition, the existing transaction engine will re-check the authoritative state. Successful transfer intentionally updates both production agreed-parent records.

### Invoke from Windows Cygwin (Diaries repository root)

```bash
bash 'change-control/in-progress/0041-FEAT - isolate native Btrfs replication with dedicated service accounts/tools/run-0041-step10-dedicated-from-cygwin.sh' --preflight
```

After examining the preflight log, the user may explicitly authorise one real incremental transfer with:

```bash
bash 'change-control/in-progress/0041-FEAT - isolate native Btrfs replication with dedicated service accounts/tools/run-0041-step10-dedicated-from-cygwin.sh' --execute
```

**Execute mode is not a dry run**. It writes a received production snapshot and advances both protected agreed-parent records, if successful. Do not use near the regular 03:30 sender or 04:15 receiver prune schedule. A valid Step 10 execution log, including pre/post UUID evidence, is required before the scheduler cutover is considered.
