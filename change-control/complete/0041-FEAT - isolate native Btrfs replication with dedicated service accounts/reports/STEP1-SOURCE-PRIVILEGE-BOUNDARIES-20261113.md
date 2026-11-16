# 0041-FEAT — Step 1: Source-derived privilege and execution boundaries

**Recorded:** 13 November 2026 (UTC)
**Decision:** Source review recorded; **Step 1 OPEN**, pending live `mars`/`backup` evidence.
**No deployment or production changes authorised.**

## Provenance and scope

This review uses `playbook-sources-20261112-193409.zip`, whose `SOURCE-REVISIONS.txt` records controller `f6ba7fec`, Playbooks `df68a0e` and inventory `ebcce02` (the private inventory is intentionally absent from the shareable bundle). This source predates the unrelated 0048 change that published Playbooks `c510934` and controller `83cba34` on 13 November. Reconcile the live revisions and installed binaries with the accompanying collector before touching code. The 0041 directory has been moved from TODO to IN PROGRESS by the operator; this package does not overwrite the existing 0041 plans.

## Current implementation as documented by the source bundle

| Boundary | Existing code | Security implication / planned change |
| --- | --- | --- |
| Sender systemd | `templates/btrfs-native-push.service.j2`: `User=root`, `Group=root`; `sender cycle` | Dedicated unprivileged sender is a *design change*, not a unit-field-only adjustment |
| Runtime root gate | `files/btrfs-simplified-replication.py:478` checks `os.geteuid()==0` for **all** commands | Reads/status and SSH orchestration currently inherit root requirement |
| Network | `ssh_command()` (`:219–223`) runs `sudo -n -u richard ssh` to `richard@10.254.22.1:39263`; remote command is `sudo -n ... receiver OP` | Replace with a unique dedicated sender key and receiver forced command, never silently fall back to `richard` |
| Sender Btrfs stream | `stream_send()` (`:331–361`) invokes `btrfs send -p ...` and streams binary stdout to SSH stdin | Privileged stream generation must remain a *binary* stream; preserve complete-transfer lock/ack semantics |
| Receiver Btrfs / cleanup | `receive_receiver()` (`:257–278`) executes `btrfs receive` and, only for an identified incomplete candidate, `btrfs subvolume delete` | Root-only, path-pinned receiver operation; cannot expose arbitrary Btrfs or filesystem deletion |
| State | `load_state/save_state` (`:83–114`) demand root-owned `0600` state files, validate schema and replace atomically | Do not chown protected records to service accounts or relax ownership validation |
| Concurrency | `locked()` (`:116–143`) opens `/run/lock/btrfs-snapshot-manager.lock`, with sender holding it across remote calls, transfer, verification and state advancement | A sequence of independently locked privileged subprocesses is **not** equivalent; preserve transaction-wide protection |
| Agreement | `sender_main` (`:409–466`) verifies receiver, handles receiver-ahead, advances source only after readback | Preserve UUID/read-only verification and interruption/reconciliation behaviour |
| Receiver hold protections | `classify_candidate` (`:185–216`) checks agreed parents, independent holds, legacy receipts and candidate identity | Preserve before/after deletion checks; do not weaken receipt or held-snapshot protections |
| Receiver retention | `btrfs-receiver-simple-prune` remains a distinct root service; receiver retention was enabled during 0040 | Do not change deletion/snapshot timers, pruning limits or service users in 0041 |
| Extra lock boundary | Receiver `writer.lock` is installed by `tasks/receiver-config.yaml`, alongside the manager lock | Live permissions and lock interaction require verification before sharing any helpers |

## Proposed least-privilege architecture (subject to approved live baseline)

1. **Unprivileged sender identity on `mars`**, without membership in the `sudo` group. Owns the dedicated SSH key and a small non-sensitive runtime directory. Runs a dedicated orchestrator under systemd; its root interaction is only through fixed, owned and allowlisted privileged operations.
2. **Restricted receiver identity on `backup`** with its own public-key authentication. Its credential is bound by `authorized_keys` to a forced dispatcher, with no PTY or port/agent/X11 forwarding; no general-purpose shell or arbitrary command through the service key. Do not use `nologin` blindly: forced-command execution and binary stream input must be compatibility-tested with the account shell policy.
3. **Root-owned privileged endpoint(s)** on each host enforce exact accepted operations, canonical paths/filesystem IDs, locks, state invariants and receipt verification. No service account receives `NOPASSWD:ALL`, unrestricted Python, generic `btrfs` or shell access. Privileged sender process must hold transaction protection across streaming and acknowledgement; merely allowing isolated `sudo btrfs send/receive` commands would be unsafe.
4. **Retain** existing snapshot create/prune, receiver-prune and stale-qgroup services as root services within this feature. No change to `richard`'s personal login, sudoers, membership or SSH credentials. Preserve existing `btrfs-native-push.timer` as the sole replication scheduler, with an explicit cutover and rollback plan.

## Live audit information still required

- Actual `mars`/`backup` unit identity, status, timer schedule and rendered commands.
- Root file modes, parent traversal rules, shared writer/manager locks and protected parent records (metadata only; do not print records or secrets).
- Actual service accounts and SSH policy, key *metadata* and effective sudo rights; do not archive any private keys or Vault values.
- Executable hashes versus reviewed source and current Git/submodule revisions, including the post-0048 parent pin.
- Current parent/receiver state, latest successful replication and receiver-prune enablement from read-only commands.

## Execution and evidence handling

Run `tools/collect-0041-step1-privilege-baseline.sh` on `mango` from the **Windows** checkout, capturing stdout/stderr into `evidence/Step 1/`. The collector is read-only and does not dump protected state files, authorised-key contents or private key material. Inspect its report before amending the 0041 design decisions or beginning additive implementation. A successful collection is **not** authorisation for new identities, keys, sudoers or a scheduler cutover.
