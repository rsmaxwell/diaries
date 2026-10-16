# 0036-FEAT Step 8 — controlled cutover gates (2026-10-16)

**Current disposition (2026-10-16): Step 8 IN PROGRESS; Gates A, B and C CLOSED, Gates D and E OPEN.** The text below retains the original prospective gate procedure; actual Gate C production results and formal acceptance are recorded in `STEP-8-GATE-C-PRODUCTION-CUTOVER-CLOSURE-20261016.md`. This plan is not, by itself, evidence that Gate D unattended cycles or off-site replication have completed.

## Gate A — evidence and read-only inventory

Run `scripts/diaries-0036-step8-readonly-preflight.sh` *on each named host* and capture its output. Inspect the exact deployed paths (Playbooks defaults are not proof of live values), both systemd timer units, current `pluto` publication symlink and `mars` working dataset. Record current Git SHAs, resolved variable precedence including non-Git host vars, Btrfs history identifiers, latest accepted schema-2 snapshot and remote receipt. Run new source test on `mango`: `python3 roles/local-backup/tests/verify-0036-step8-cutover-configuration.py` and previous regressions only if a source change warrants them. **Do not enable fixed mode as part of a read-only inventory.**

## Gate B — approved rollback and preparation

Before changing paths, require operator approval based on Gate A and a verified known-good historical recovery point. Preserve the legacy `pluto` publication symlink target and generation tree under a clearly named rollback alias. Save old unit settings and Ansible host-variable values. Prepare a fixed **plain directory**, never have fixed capture or fixed receiver run against an existing symlink. Explicitly verify the same schema-2 dataset identity and existing snapshot marker/lock scope. Do not remove historical snapshots, ancestry, receipts or original generations.

## Gate C — explicitly authorised cutover

Disable conflicting schedules before switching either host. Check live capture's opt-in environment and host NAS mount/Files selector. Enable fixed capture on `pluto` only after path migration; run its preflight and one guarded verified capture. Then opt into `diaries_pull_fixed_destination_enabled: true` in host-specific Playbooks variables for `mars` (defaults remain false), verify guard path actually deployed on `pluto`, preserve the existing `@data` boundary, and run guarded receiver once. Independently validate manifest/marker, create an accepted read-only snapshot, then activate the new schedule. **These are operator procedures, not actions already performed.** A wrong mount/path, stale marker, concurrent writer or missing verified checkpoint is a STOP gate.

## Gate D — unattended acceptance and off-site receipt

Capture **at least two unattended complete cycles** of producer → guarded receiver → eligible native Btrfs snapshot, with timestamps, real logical dataset IDs, exit status, markers and snapshot history. Confirm no unexpected files retransferred if measurable, but no particular quantitative saving threshold is imposed. Preserve and verify incremental/full fallback ancestry, receipt on `backup` and protected send parents via the existing `mars`-initiated push. Record acceptance before decommissioning any legacy mechanism.

## Gate E — retirement and feature close-out

Retire legacy generation/publisher execution only after Gate D evidence and explicit approval; **delete old generations only with separate explicit deletion approval**, outside this package. Replace temporary feature-numbered (`0036`) operational names with stable names across code, Ansible, deployed scripts and configuration, while retaining 0036 IDs in historical documentation/tests. Remove superseded experiments only following dependency analysis so 0034/0035 rollback and historical restore remain intact. Capture actual deployed commits for both Playbooks and Diaries. Close 0036 only once every acceptance gate passes and evidence is attached.

## Rollback trigger and path

On a failed capture, failed receiver validation, missing eligibility, snapshot failure or receipt error: stop the new schedules, preserve the failed working copy for diagnosis, restore the original publication symlink and original services/settings from the captured inventory, and independently verify historical snapshot and recovery reference. Do not repair failures by synthesizing markers or receipts. Do not delete existing snapshots or off-site data.

## Known limitations

Gate A host inventory and Gates B–E require operator action on live hosts. Step 7 synthetic database artifacts do not replace the accepted Step 3 real PostgreSQL restore evidence; the Step 6 regression is not a fresh physical off-site transfer. No Docker application images are required by these Playbooks-only changes.
