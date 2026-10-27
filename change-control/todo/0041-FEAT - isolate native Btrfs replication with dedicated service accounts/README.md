# 0041-FEAT — Isolate native Btrfs replication with dedicated service accounts

**Type:** Feature  
**Status:** TODO — registered 27 October 2026; implementation NOT started  
**Priority:** Security hardening; schedule after 0040-FEAT receiver coordination stabilises, subject to operator approval.

## Objective

Run native Btrfs replication between `mars` (sender) and `backup` (receiver) using dedicated, least-privilege service identities rather than `richard`. Preserve `richard`'s independent administrative SSH and sudo access for inspection, incident response and recovery. Provision and maintain the identities, SSH credentials, file ownership, constrained privileged operations, systemd execution context, and rollback through Playbooks.

## Current verified baseline (27 October 2026)

- On `mars`, `btrfs-native-push.service` is a oneshot unit using `User=richard`, `Group=richard`, and `ExecStart=/usr/local/bin/btrfs-native-push --latest`.
- The sender's SSH transport targets `richard@10.254.22.1` on port `39263`; the unprivileged remote program is `/usr/local/bin/btrfs-native-push-receiver`.
- On `backup`, `/home/richard/.ssh/authorized_keys` contains keys labelled `richard@mango`, `richard@mars`, and `richard@pc`, without per-key forced-command restrictions in the inspected lines. These key labels are descriptive, not cryptographic proof of possession.
- `richard` on `backup` belongs to `sudo` and has both `(ALL : ALL) ALL` and a separate `(ALL) NOPASSWD: ALL` grant from `/etc/sudoers.d/sudoers`. Preserve these administrative privileges unless the operator separately approves changes.
- The dedicated Btrfs sudoers file on `backup` no longer grants a default `delete-receiver` endpoint permission; its Ansible opt-in remains false. Installed receiver manager configuration reports `mode=receiver`, `receiver_prune_enabled=false`.
- 0040-FEAT Step 12 is still working through source-held, approved receiver-side pruning. The planned dedicated-account migration must not assume this interface is complete.

## Desired final contract

1. Use distinct dedicated non-login service users on `mars` and `backup` (final names to be approved). Neither account belongs to `sudo` or another unrestricted administrative group.
2. Sender runs on `mars` under the dedicated sender identity. Receiver SSH authentication uses a dedicated key bound to the receiver identity and a tightly validated command allowlist or forced dispatcher; no interactive shell, PTY, forwarding or arbitrary remote commands for this key.
3. Privileged Btrfs functions use reviewed fixed-path endpoints and narrowly scoped sudoers/capability boundaries; no `NOPASSWD: ALL`, general root shell or arbitrary user-specified paths for either service identity. Pin filesystem ancestry, validate snapshot names/UUIDs, and enforce locks, durable source pin, receipts, holds, approval and journal recovery.
4. Keep existing snapshot trees, receipts, retention rules, schedules, checkpoint holds and verified incremental parent unchanged unless a separate approved change requires otherwise.
5. Preserve `richard`'s ordinary administrative login, sudo rights, and break-glass capability independently of the replication key. Do not re-purpose or restrict `richard@mars`'s existing administrative key in this feature by default.
6. Playbooks manage users, directories, permission modes, SSH keys/public-key installation, service definitions, sudoers (validated with `visudo`), and safe retirement of obsolete service access only after acceptance. No private keys in Git, logs or evidence archives.
7. Fail closed if the dedicated receiver identity, key, forced command, approval contract or lock topology is invalid. Do not fall back silently to `richard` or a root login.

## Scope and exclusions

**In scope:** `mars` and `backup` Playbooks/Ansible configuration; relevant native sender/receiver scripts and endpoint wrappers; user and SSH-key lifecycle; privilege and ownership adjustments; unit/scheduler cutover; source regressions and controlled read-only, disposable and live acceptance; rollback and documentation.

**Out of scope:** Modifying `richard`'s administrative permissions or existing personal SSH keys; production snapshot pruning activation; snapshot deletion or reseeding; changes to `pluto`, NAS, other backup schedules, Diaries client/responder, or MQTT; unrelated host security policy. Any necessary exception requires its own explicit gate.

## Dependencies and risk controls

- Coordinate with 0040-FEAT, especially Step 12's unfinished privileged deletion protocol. Define the service-account privilege set from the *accepted* protocol rather than granting speculative permissions.
- The current `richard` service and connection are the rollback path until the new identities pass acceptance. No early removal or credential revocation.
- Do not assume that a successful transfer alone proves least privilege. Include negative tests for shell, forwarding, unknown commands, excessive sudo, path injection and unexpected fallback.
- One controlled cutover at a time. Protect the current source-held parent, receiver holds, receipts, and schedules through cutover and rollback.

## Acceptance criteria

- [ ] Freeze exact service identities, key usage, service units, sudo privileges, paths/ownership, SSH policy and production replication baseline on both hosts.
- [ ] Approve a written least-privilege design, including a clear source/receiver command matrix and `richard` recovery path.
- [ ] Implement Playbooks provisioning with secrets handled outside Git and source-level regressions for permissions, dispatch, filesystem validation, access denial and rollback.
- [ ] Show no successful interactive shell, arbitrary command, forwarding, PTY, unrestricted sudo or unexpected `richard` fallback with the dedicated credentials.
- [ ] Demonstrate disposable Btrfs transfer, receipts, parent/hold protection, interruption handling and any approved pruning protocol, without using production data for destructive tests.
- [ ] Review host-scoped Ansible `--check --diff` on `mars` and `backup`; explicitly approve and perform additive deployment, not scheduler cutover.
- [ ] Prove an authenticated manual end-to-end `mars` → `backup` replication with the service accounts and verify received UUIDs, read-only state, receipts and common parent.
- [ ] Cut over one scheduler using a controlled window; ensure exactly one active transport; verify following unattended run(s), failure handling and idempotency.
- [ ] Verify `richard` administrative SSH/sudo still works; verify restricted service identities cannot access broader administrative operations.
- [ ] Document rollback to the pre-cutover service, credential retirement decisions, source revisions, logs and final permissions; close only on reviewed evidence.

## Workflow and artefacts

See `DESIGN.md` and `IMPLEMENTATION-STEPS.md`. Use the existing Diaries change-control state transitions: `todo` → `in-progress` → `complete` only when approved and evidenced. Maintain `evidence/Step NN/` when work begins. Source changes belong in the Playbooks repository on `mango`; change-control and evidence belong in the Diaries repository. Review regressions and Ansible `--check --diff` before controlled deployment, then runtime checks and idempotency.

**Next action:** Leave 0041-FEAT in TODO. Continue 0040-FEAT Step 12 without modifying account or SSH setup; revisit 0041 only when its dependencies and implementation window are approved.
