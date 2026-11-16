# 0041-FEAT — Step 7 restart after malformed interactive paste (2026-11-15)

## Evidence disposition

The Windows Cygwin log from `note(20261115-141822).txt` showed only the
receiver-host-key heading and a malformed pasted shell line, followed by an
unsupported `PASS: 0041 additive provisioning`. It did **not** show the
fingerprints, Ansible run, account creation, or dedicated transport status.
The PASS is **invalid**, and Step 7 remains **OPEN** until a complete live log
is obtained. Do not delete or overwrite that failed-attempt evidence.

## Failure mechanism addressed

The previous shell heredoc was too large and visibly corrupted in the pasted
terminal transcript. More importantly, nested `ssh` calls inside a remote
`bash -s` stream can consume the rest of the script from standard input. The
replacement uses `ssh -n` for every nested SSH invocation, explicitly redirects
Ansible stdin from `/dev/null`, and requires a final acceptance marker as well
as a successful remote exit code.

## Candidate boundary

The deployment script pins the exact SHA-256 hashes of all eleven previously
verified Playbooks candidate files, and the controller, inventory and Playbooks
Git revisions in the successful 2026-11-15 14:06 source-check log.
The additive role remains gated by `--tags btrfs-0041-provision` plus
`-e btrfs_0041_additive_enabled=true`.

The preflight compares the remote `backup` ED25519 SSH host-key fingerprint with
the key actually offered on `10.254.22.1:39263` as scanned from `mars`. A
mismatch prevents any provisioning. The deployment does not activate a new
service, touch the production timer, or invoke any Btrfs send/receive.

The postdeployment read-only status is a **transport/identity validation**, not
a binary-transfer or security-acceptance test. Adversarial forced-command and
sudo tests, idempotence, isolated binary transfer, interruptions, and explicit
cutover authorisation remain outstanding. `richard`'s personal SSH and sudo
access is deliberately unchanged.

## Execution

Apply the accompanying ZIP to the **Windows Diaries repository only** using
Beyond Compare 4. In the Windows Cygwin terminal, from the Diaries repo root:

```bash
bash 'change-control/in-progress/0041-FEAT - isolate native Btrfs replication with dedicated service accounts/tools/run-0041-step7-additive-from-cygwin.sh'
```

The launcher saves the full output under the feature's `evidence/Step 7/`
directory and will report FAIL if the remote script terminates prematurely.
If the Ansible run has already begun, a failure does not imply that its
additive changes have been rolled back; examine the log before attempting
another run. The existing production 03:30 timer is not intentionally switched.
