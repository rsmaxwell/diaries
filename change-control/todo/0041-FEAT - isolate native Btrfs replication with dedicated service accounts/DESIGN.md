# 0041-FEAT — Design and security invariants

**Status: DRAFT / NOT APPROVED.** No production changes authorised.

## Identity architecture

- `mars`: dedicated sender service identity (placeholder: `btrfs-send`; exact account/group to be approved), running the existing push service and holding only its required source state/lock permissions.
- `backup`: dedicated receiver service identity (placeholder: `btrfs-receive`; exact account/group to be approved) with a unique SSH public key and a fixed, allowlisted receiver dispatcher. This account has no general-purpose interactive SSH shell through the replication credential.
- `richard`: separate human administrator on both hosts, with existing independent administrative access preserved. Explicitly avoid locking down the existing `richard@mars` personal/admin SSH key as a substitute for service isolation.

The names above are design placeholders, **not** proposed executable commands. Account shell, authorized_keys `command=`/`restrict`, and sshd `Match` design are subject to a compatibility test of the native streaming transfer and bidirectional challenge responses. A forced command must reject unexpected `SSH_ORIGINAL_COMMAND` values and must never evaluate them in a shell. Restrict forwarding, agent/X11 forwarding and PTY for the service credential.

## Privileged endpoint model

- Define the exact required operations by tracing current sender and receiver code (list/inspect/send/receive/lock/protect/recovery); pin arguments, filesystem and paths in the endpoint rather than granting arbitrary `btrfs`, `sudo`, shell or Python commands.
- Keep Btrfs kernel operations behind narrowly authorised root-owned executables, with validated config/locks/receipts and root-only approval material where required.
- Separate routine replication from retention deletion: receiver pruning remains disabled until independently accepted 0040 coordination and an explicit approval gate. Service users must not gain broader privileges just because `richard` historically had `NOPASSWD: ALL`.
- Prevent source lock or pin loss during an in-progress approved receiver action; ambiguous SSH disconnection requires journal reconciliation, not blind replay.
- Validate directory owner/group/mode and whether existing root-owned paths and writer/source locks must move or be accessed by constrained helpers. Avoid weakening directories to world-write.

## Deployment and cutover strategy

1. Baseline both hosts and store rollback copies of non-secret configs, unit definitions and privilege policy; identify key fingerprints without archiving private keys.
2. Provision users/keys/dispatcher/limited privileged endpoints additively. Preserve current `richard` path and timer.
3. Run source tests, negative auth/privilege tests and disposable Btrfs rehearsals. Validate backup receipts and parent ancestry; prove no unapproved prune.
4. Execute explicit `--check --diff` for both hosts and review any unrelated changes; deploy only controlled, approved tasks.
5. Test manual dedicated-identity send/receive while current scheduler remains unchanged, avoiding concurrent sessions and double sending.
6. During an approved window, switch the existing timer/service to the dedicated sender identity and receiver key/host, with one authoritative scheduler. Verify next run(s), monitor parent protection and rollback conditions.
7. Once stable, retire obsolete *replication-specific* `richard` usage if separately approved; do not remove `richard`'s administrative rights or keys.

## Security tests (must be adversarial)

- Reused/expired/wrong key rejected; interactive SSH/PTY, TCP/agent/X11 forwarding and arbitrary command rejected.
- Credential cannot run `sudo -l` as a general administrator, arbitrary commands, shell escapes, unrestricted endpoint roles or root shell.
- Malformed timestamp, UUID, path traversal, symlink/hardlink attacks and unknown role rejected.
- Receiver accepts only expected snapshot lineage and Btrfs receive stream; no race between replication lock and manager/prune lock.
- Interrupted transfer and interrupted approval transaction fail closed, preserve receipts/journal/pin appropriately and are operator-recoverable.
- Scheduler cannot silently fall back to `richard`; existing human administrative SSH/sudo still functions separately.

## Open design decisions

1. Final Linux account names and shells; decide distinct users per host versus identical account names.
2. SSH key location, lifecycle/rotation, provisioning with Ansible Vault and root/user file ownership; whether dedicated SSH client config is required.
3. Forced-command implementation and protocol transport for native binary streams and challenge sessions; account for remote command invocation currently embedded in sender source.
4. Minimal privileged roles and their invocation (sudoers/capabilities), including owner of receiver writer lock, source lock, pin, approvals and consumed records.
5. Whether 0040 Step 12 approved pruning is part of initial cutover or remains strictly disabled until a separate gate.
6. Timing of scheduling cutover, observation period, monitoring and credential rollback.

No decision above is implicitly authorised by registering this feature.
