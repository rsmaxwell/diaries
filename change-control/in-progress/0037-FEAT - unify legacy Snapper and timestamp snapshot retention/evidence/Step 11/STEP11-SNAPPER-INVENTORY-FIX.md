# Step 11 — Snapper inventory performance fix (2026-10-20)

**Status:** Source patch prepared; regression/deployment not yet executed; pilot deletion remains NO-GO.

## Source and rationale

The `mars` Snapper 0.10.6 inventory hangs while calculating snapshot used space; the verified read-only command `snapper --no-dbus --csvout --iso -c @data list --disable-used-space` returns all expected records. The manager uses named CSV headers and its retention algorithm uses timestamps, type and cleanup, not used space. Its common `legacy_snapper_inventory()` function services both `legacy-plan` and `legacy-delete` preflights.

Patch adds `--disable-used-space` **after `list`**, as required by the installed CLI. It makes no changes to scheduler, policy or deletion authorization.

## Apply and test

1. Apply the **Playbooks ZIP to `/home/richard/playbooks` on `mango`**. The ZIP is rooted at `roles/`, not a Windows `playbooks/` copy. Back up/inspect changes with `git diff -- roles/snapshots/files/btrfs-snapshot-manager.py`.
2. Apply the **Diaries ZIP to the Windows Diaries repository**, preserving `change-control/...` paths.
3. In **Cygwin** run `bash "change-control/in-progress/0037-FEAT - unify legacy Snapper and timestamp snapshot retention/tests/step11-run-manager-fix-regressions-from-cygwin.sh"`.
4. Check all regression results; stop if any fail. The existing Step 7 runner records evidence in `evidence/Step 07/results.txt` as well.
5. Only then deploy the snapshots role to `mars` using the existing documented targeted Ansible workflow from `mango`; first inspect the playbook and `--check --diff`. Do not deploy to backup or change timers.
6. Verify SHA-256 of Playbooks source and `/usr/local/sbin/btrfs-snapshot-manager` on `mars` match (new digest below). Perform read-only `legacy-plan` and full safeguards/receiver checks again; record execution GO separately.

**Expected patched manager SHA-256:** `200998f4bdf129637025fd94730735d27919d48b1f47941b58846e408f2692c5`.

## Stale qgroup records

The uploaded listing showed ~16,000 stale `0/<id>` qgroups. Btrfs supports `btrfs qgroup clear-stale /media/usb` on versions implementing it, but this is a *write* operation and **must not run as part of the Step 11 snapshot pilot**. After Step 11 closure, establish `btrfs --version` and `btrfs qgroup --help` support, capture fresh qgroup counts, backup/receiver health and qgroup status; schedule separate controlled maintenance with a rollback/verification plan. Do not disable quotas, rescan or destroy individual qgroups casually.
