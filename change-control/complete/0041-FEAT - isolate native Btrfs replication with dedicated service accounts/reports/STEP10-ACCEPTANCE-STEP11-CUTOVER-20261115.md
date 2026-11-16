# 0041-FEAT — Step 10 acceptance and Step 11 canonical service cutover

Date: 15 November 2026. Feature remains **in progress**.

## Accepted technical evidence — Step 10

Source evidence: `evidence/Step 10/step10-execute-20261115-145938Z.txt` (existing Windows repository file).

* PASS: verified installed sender/receiver program hashes and independent dedicated-identity transport preflight.
* PASS: one incremental production replication via `sudo -n -u btrfs-send sudo -n /usr/local/libexec/btrfs-replication-sender-cycle-0041`.
* PASS: agreed parent advanced from `20261115-030001Z` to `20261115-140017Z`, and sender and receiver agreed-parent records reconciled.
* PASS: receiver's Btrfs received UUID and read-only snapshot confirmed.
* PASS: original 03:30 service/timer unchanged; no automatic retry or JSON rollback.

This validates the transport and privilege pathway but **not** a timer-triggered systemd execution of the canonical unit.

## Step 11 source change

The Playbooks ZIP changes exactly the source role's canonical systemd service template, adds a persistent `btrfs_native_sender_service_identity: dedicated` default, and adds Ansible checks for the fixed gate and locked-down key/host-key files. The same Ansible scheduling role continues to manage the existing `btrfs-native-push.service` and 03:30 timer. No service is activated merely by applying the ZIP to the Git working copy.

* The canonical service's `User`/`Group` are `btrfs-send`, and `ExecStart` invokes `sudo -n /usr/local/libexec/btrfs-replication-sender-cycle-0041`.
* That gate runs the original root-owned transaction, preserving its existing manager lock, consistency rules, stream and receiver-reconciliation logic.
* `richard`'s personal SSH access, authorized keys and sudoers are not changed; snapshot create/prune and receiver maintenance remain independent root services.
* The legacy template branch remains available for rollback. Only the sender service identity is changed, not the timer time or schedule state.

## Execution and rollback

Apply **Playbooks** ZIP to `/home/richard/ansible-controller/playbooks/` using Beyond Compare, and **Diaries** ZIP to the Windows Diaries repository. Review the three Playbooks diffs before running.

In the Windows Cygwin terminal (from the Diaries repo), run the Step 11 launcher with `--preflight` for an Ansible read-only preview, then `--execute` to deploy the service identity change. Execution mode includes its own preview; separate preflight is optional.

`--rollback` restores the original root service using an Ansible extra-variable and rewrites **only the exact dedicated-default line** in the Playbooks working copy to `legacy`, preserving other uncommitted work. It does not delete the dedicated accounts or keys and does not roll back any Btrfs state. Review and commit the resulting source changes if rollback is exercised.

Failure and interrupted cutover require reading both the systemd loaded-unit state and the Playbooks source before further action. Neither execution mode runs a transfer or edits an agreed-parent record. The first scheduled 03:30 run must subsequently be inspected before feature closure.

## Acceptance remaining

* Confirm Step 11 `--execute` succeeded and retained the exact active 03:30 timer and protected state metadata.
* Observe one 03:30 timer-triggered run, journal exit status, and matching sender/receiver agreed-parent state.
* Run backup-health status and appropriate Ansible regression checks; record rollback readiness.
* Commit the final Playbooks and parent Ansible-controller submodule revisions only after accepted results, followed by formal 0041 closure.
