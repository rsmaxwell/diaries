# 0043-FEAT — Effective inventory reconciliation (10 November 2026)

Recorded from operator terminal logs, not from a new host deployment.

- 11:50 UTC: `/etc/ansible/group_vars/all/btrfs-maintenance-schedule.yaml`
  exists, is root-owned and loaded by Ansible.
- First effective `mars` inventory showed `*-*-* *:45:00`, while `backup`
  inherited `04:15 UTC`. A targeted inventory search located the obsolete
  hourly source-prune override in
  `/etc/ansible/host_vars/mars/local-backup.yaml`.
- The first exact-match override-removal command failed its precheck without
  editing inventory. A later idempotent readback reported **override already
  absent**; no deletion was performed by that command.
- Final verified effective inventory: `mars` source prune `04:15 UTC`, cap
  `32`; `backup` receiver prune `04:15 UTC`, cap `10`. Both checks PASS.
- The earlier installer regression failed due to hard-coded old filename,
  not an error in Ansible's standard discovery. Decision: remove installer
  and dedicated tests, retain renamed standard-inventory YAML plus ordinary
  Ansible roles.
- The earlier Ansible preview runs are **not** deployment evidence. Final
  04:15 timer installation and activation still require verification.

No change to 0039 Step 11 timer schedule, parent pins or snapshot retention.
