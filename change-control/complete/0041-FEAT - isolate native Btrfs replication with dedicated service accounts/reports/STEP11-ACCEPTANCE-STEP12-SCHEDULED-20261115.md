# 0041-FEAT — Step 11 acceptance and Step 12 scheduled-run verification

Date: 15 November 2026. Feature **remains in progress**. No feature closure is authorised by this report.

## Accepted live Step 11 technical result

Evidence already saved in the Windows Diaries repository at `evidence/Step 11/service-execute-20261115-151925Z.txt`.

* After the correction to the controller locale (`LANG=C.UTF-8`, `LC_ALL=C.UTF-8`), the scheduling-only Ansible preview predicted exactly one service-file change on `mars`, and none on `backup`.
* The deployment made exactly one change on `mars` and none on `backup`. Loaded `btrfs-native-push.service` is now `User=btrfs-send`, `Group=btrfs-send`, `ExecStart=/usr/bin/sudo -n /usr/local/libexec/btrfs-replication-sender-cycle-0041`.
* The original 03:30 UTC `btrfs-native-push.timer` stayed unchanged. Both root-protected agreed-parent records remained unchanged during cutover.
* No Btrfs transfer was launched by the service-unit cutover. The earlier Step 10 supervised transfer already proved the dedicated-account end-to-end transaction.
* `richard`'s personal SSH/sudo access is unchanged by the 0041 packages.

This **passes Step 11 technical cutover verification**. Formal closure of Step 11 and feature closure still follow the established change-control acceptance procedure.

## Step 12 — First timer-triggered cycle

Expected scheduled run: **Monday 16 November 2026 at 03:30 UTC** (the first regular run following the cutover).

Run the supplied Cygwin launcher **after the scheduled run has finished**, preferably after 05:00 UTC. This step is read-only: it must never invoke a new replication, delete snapshots, change Btrfs state, run Ansible, restart systemd or trigger another scheduler cycle. A failed/incomplete run must be investigated; do not retry replication automatically.

The verifier captures:

1. Controller and Playbooks Git identity and persistent `dedicated` role default.
2. Loaded canonical service and active 03:30 timer definition.
3. Actual timer last-trigger time on or after 16 Nov 03:30, service start/exit timestamps, `Result=success` and `ExecMainStatus=0`.
4. Sender service journal entries and any diagnostics.
5. Identical root-protected agreed-parent records on `mars` and `backup`, verified via dedicated transport, including advance beyond the Step 10 accepted parent `20261115-140017Z`.
6. Backup health output and no active duplicate candidate service.

If no newer snapshot was eligible, the new-parent advancement assertion will correctly keep the gate open for investigation rather than treating service-exit success as a verified replication. This does not automatically imply that the backup system failed.

## Next acceptance actions

Review the Step 12 output, reconcile any journal warnings, review final Playbooks source and commit its changes plus parent Ansible-controller submodule pin, and record the verified rollback method. Do not move 0041 from `in-progress` to `complete` without formal feature closure.
