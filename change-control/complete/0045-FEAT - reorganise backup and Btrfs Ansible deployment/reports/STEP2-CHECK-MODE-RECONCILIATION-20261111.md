# 0045-FEAT — Step 2 check-mode reconciliation and Step 3 deployment prerequisites

**Date:** 11 November 2026. **Status:** source/runner prepared; Step 3 not yet deployed or accepted.

## Accepted checks already performed

- Windows source-equivalence regression: 24 snapshot tasks and 36 native replication tasks preserve task order, guards, tags and parameters; native/generic role entry points unchanged in meaning.
- On `mango`: Ansible syntax checks for `backup-collection.yaml`, `btrfs-replication.yaml` and `snapshots.yaml` passed. All five permanent regression scripts passed, including the corrected snapshot static-import test.
- Four-host caller audit on `mango`, `mars`, `backup`, `pluto`: no old-playbook references in inspected files; running Jenkins pod inspected 27 job configurations with zero matches. Dynamically fetched Jenkinsfiles and external schedulers remain outside that audit. Existing launchers are **retained**, rather than removed without complete coverage.
- Ansible `--check` with unchanged inventory: `backup-collection.yaml --limit mars` ended with `ok=57 changed=1 failed=0`; `btrfs-replication.yaml --limit mars,backup` ended with `mars ok=15 changed=0 failed=0`, `backup ok=25 changed=0 failed=0`. No unreachable hosts.

## Predicted Docker key change and logging correction

The only `--check` change was `Docker | Install Docker apt signing key`, implemented by the existing Docker role's `ansible.builtin.get_url`. Check mode can predict a change without proving that an actual apply would change the file. Do not change the Docker role as part of 0045; fingerprint `/etc/apt/keyrings/docker.asc` on `mars` immediately before and after the controlled apply. That key is not part of the accepted v2 snapshot/backup installation manifest, so this explicit supplement is necessary.

The new `scripts/backup-collection.sh` operator launcher inherited a `--diff` default from the older launcher. For safer evidence handling, its normal modes now omit `--diff`; default remains `--check`, while explicit `--apply` performs deployment. The legacy launchers are unchanged. Raw Ansible logs can still contain returned configuration fields (including Base64-encoded receipts), so review before publishing and never stage Vault plaintext.

## Step 3 controlled deployment

The feature-specific `tools/apply-0045-step3-and-compare.sh` requires explicit `--apply` and runs from **Windows Cygwin**. It checks that the refactored Playbooks on `mango` have been committed and pushed (descended from baseline `7dfa93f`), invokes normal Ansible on `mango` without `--diff`, collects definitive v2 manifests from `mars` and `backup`, compares them to the accepted `baseline-20261111-111819Z`, checks the Docker signing key SHA-256 and captures read-only operational status. The script does **not** directly call backup, snapshot, prune or replication actions; normal Ansible roles may enforce configured service/timer state. It must be reviewed before operator execution. On any failure, do not assume automatic rollback or claim Step 3 complete; keep the captured evidence and diagnose the mismatch.

No full restore, manual native transfer or fresh Step 1 baseline is required. A subsequent accepted apply is still needed for practical idempotence under the installation-equivalence contract; this script intentionally performs the first apply only to allow review of installed-state findings before the second.
