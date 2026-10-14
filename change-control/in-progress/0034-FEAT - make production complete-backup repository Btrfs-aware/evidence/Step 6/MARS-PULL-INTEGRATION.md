# 0034 Step 6 — Opt-in mars-initiated pull (2026-10-09)

Status: **implemented in source; not activated, not live-verified; Step 6 remains OPEN**.

## Verified live topology (operator inventories)

- `mars`: `/media/usb` is a Btrfs mount; existing 02:00 user and 02:15 root backup cron jobs.
- `mars`: 02:15 root job presently pushes data to `backup` with `--delete --delete-excluded`. **Not modified.**
- `backup`: Btrfs root mount; no current user/root crontab. Migration to backup-initiated pull belongs to 0035.
- `pluto`: legacy timestamped complete-backup directory exists; new fixed `diaries-backup/` publisher has not been shown deployed.

## Source integration

Playbooks `roles/local-backup/files/backup-machine/diaries-pull.py` performs a mars-initiated SSH rsync pull from the stable published path. Remote `rsync --rsync-path` holds a **shared flock on pluto** at `.diaries-backup.lock` while rsync reads, blocking publisher writes. The receiving side uses an isolated temporary directory, checks schema-2 with the permanent manifest tool and invokes the permanent publisher to atomically select the received generation on mars. A failure never publishes an incomplete candidate; previously published generations remain available.

Installation by Ansible is **off by default** (`diaries_pull_install: false`); there is no new cron job, daemon, automatic pull or snapshot invocation. Activation requires separate explicit operator command. The success output contains `backupId`, `state=verified-published`, `destination`, `snapshotEligible=false`; a complete, verified whole-backup snapshot still belongs to 0035.

## Deployment and manual pilot prerequisites

1. Confirm that the Step 5 publisher and schema-2 manifest helper have been installed on **pluto**, and that the fixed published symlink exists and verifies. Current production capture may still only produce legacy timestamp-ID directories: do not pull until the fixed publisher has a valid generation.
2. Confirm SSH from `mars` to `pluto` without interactive password prompts, remote `rsync`, `flock`, read access to the published generation and permission to acquire the shared lock. Confirm the actual SSH alias and user; do not assume credentials.
3. Confirm receiving directory `/media/usb/@data/backup/pluto` exists as an ordinary directory on Btrfs and is not managed destructively by an unrelated rsync `--delete` job. Confirm appropriate space and permissions. The receiver publisher and manifest verifier must be accessible on `mars` (use a reviewed deployment path).
4. Opt into the helper installation by setting `diaries_pull_install: true` **only for mars** in Playbooks. Deploy that opt-in with the normal Ansible checks; it creates no schedule.
5. First run local `--preflight` and then an explicitly authorised manual pull. Verify backup ID, received schema-2 contents, absence of partially published generation, and the previous generation retained. Deliberately test a failed transfer and publisher-lock contention in a controlled environment.
6. Record results before any scheduling or 0035 snapshot-eligibility integration. Do not enable legacy/new competing push/pull schedules.

Example (adjust confirmed paths to match deployment):

```bash
sudo python3 /root/scripts/backup/diaries-pull.py \
  --host richard@pluto \
  --source-parent /home/richard/projects/diaries/data/dataset-backups/production \
  --destination-parent /media/usb/@data/backup/pluto \
  --publisher /path/to/complete-dataset-publisher.py \
  --manifest-tool /path/to/complete-dataset-manifest.py \
  --preflight
```

Remove `--preflight` only when the source is published and the destination has been confirmed not to conflict with existing backup jobs. The helper is not a substitute for whole-backup transaction coordination on mars.

## Regression evidence

Source-level `python3 roles/local-backup/tests/verify-diaries-pull.py`: passed locally, including non-mutating preflight. Python compilation and YAML parsing passed. Actual SSH transfer, network interruption and production contention are **not yet tested**; those remain acceptance gates.
