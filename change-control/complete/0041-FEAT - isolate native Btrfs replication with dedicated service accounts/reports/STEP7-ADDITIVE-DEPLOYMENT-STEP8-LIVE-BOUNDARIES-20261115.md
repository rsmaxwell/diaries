# 0041-FEAT — Step 7 verified; Step 8 live security and idempotence verification

Date: 2026-11-15 (UTC).

## Step 7 — observed deployment evidence

Source: user terminal log `note(20261115-142738).txt`, including Windows evidence file
`evidence/Step 7/additive-provision-20261115-142639Z.txt`.

- Exact reviewed Playbooks candidate source hashes: all passed.
- Receiver ED25519 host-key fingerprint matched on the receiver and the live SSH port:
  `SHA256:xUMdQvKNOUGmOAvO0MuEX71NQINUMBaLkPRysW6cgO0`.
- Additive Ansible provisioning completed with no failures/unreachable hosts:
  `mars ok=15 changed=10`; `backup ok=12 changed=7`.
- `mars`: system account `btrfs-send` (`/usr/sbin/nologin`) and owned private key (0600) installed.
- `backup`: system account `btrfs-receive` (`/bin/sh`), root-owned restricted authorized key (0644), root-owned dispatcher and receiver gate installed.
- Dedicated SSH `sender status` succeeded, including verified identical receiver and sender parent identity.
- The existing root sender service, enabled 03:30 timer, candidate inactive staging and protected-state permissions were explicitly checked unchanged.
- Nonfatal warning: Ansible auto-created `/var/lib/btrfs-send/.ansible/tmp` with mode 0700. Review cleanup only as part of durable role maintenance; no operational failure demonstrated.

**Assessment:** Step 7 additive provisioning technically passed. Keep acceptance evidence separate from implementation and retain formal feature closure gates. No full production replication through the new identities has occurred.

## Step 8 — restricted-key, sudo and convergence tests

Run `tools/run-0041-step8-security-from-cygwin.sh` from Windows Cygwin.
The launcher streams a standalone script to `mango` and saves terminal evidence under `evidence/Step 8`.
All nested SSH operations use `-n` to prevent consuming remaining script input.

The script:

1. Verifies the original sender service and live 03:30 timer and confirms the candidate unit remains staged.
2. Validates dedicated users' group/shell boundaries, root-controlled receiver `authorized_keys` and key count.
3. Checks that both dedicated identities are refused arbitrary sudo commands and rejects root-helper arguments.
4. Performs one successful read-only dedicated SSH status query.
5. Tests forced SSH-command rejection for arbitrary command, shell, bootstrap, injection and path traversal.
6. Reapplies the previously authorised additive provisioning and **requires `changed=0` on both hosts**.
7. Rechecks that the original service/timer is unchanged and the candidate is not active.

The only requested live mutation is an idempotent repeat of the authorised additive Ansible role; a non-idempotent result stops the test. It does not start a Btrfs transfer, delete snapshots, change replication parent records, adjust SSH for `richard`, or switch systemd timers.

## Open integration / cutover items

- Prove *actual binary transfer* end-to-end with disposable Btrfs test subvolumes and safe interruption/recovery, without touching the protected live parent or replication destination. Do not test by invoking `sender cycle` against the live snapshots.
- Review the sender's root transaction boundary and the receiver shared lock inode when designing that fixture.
- After the integration evidence is accepted, perform a separately authorised service cutover, preserving a tested rollback and avoiding a second concurrent schedule.
- Reconcile the live Ansible inventory and formal 0041 plan/step acceptance before closure.

**Status:** Step 8 verification not yet run. 0041 remains IN PROGRESS.
