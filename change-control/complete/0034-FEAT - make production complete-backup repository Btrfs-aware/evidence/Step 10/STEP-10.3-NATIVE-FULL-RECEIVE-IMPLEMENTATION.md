# 0034-FEAT — Step 10.3 Native full receive implementation

**2026-10-11 — IMPLEMENTED IN SOURCE / NOT DEPLOYED / NO LIVE TRANSFER**

The Step 10.2 contract remains the authority. This patch installs an **opt-in** two-endpoint full-send implementation, without scheduling it or replacing the existing rsync machinery.

## Files / architecture

- `playbooks/native-btrfs.yaml`: separate `mars` sender and `backup` receiver installation; no transfer.
- `roles/remote-backup/files/btrfs-native-endpoint.py`: root-only fixed-UUID/path sender/receiver and constrained snapshot inspection.
- `roles/remote-backup/files/btrfs-native-pull.py`: unprivileged `richard` controller on `backup`; takes exclusive local lock, verifies source and destination, pipes distinct SSH/send/receive subprocesses, checks both exit codes and received UUID, writes atomic receipt.
- `roles/remote-backup/tasks/native.yaml`: opt-in installed binaries, narrow sudoers rule and isolated directories.
- `roles/remote-backup/tests/verify-native-btrfs-static.py`: offline source assertions.

## Frozen paths

Source: `/media/usb/@snapshots/@data/20261009-170001Z`, filesystem UUID `72d1d8ea-900e-4fca-837f-1b1febec036c`. Destination: `/@data/mars-received/@data/20261009-170001Z`, filesystem UUID `b915f967-7cb4-4c14-b11b-f52209637a22`. State: `/@data/mars-received/.replication-state`. The pre-existing `/@data/backup`, `/@data/diaries-mars-replica`, and Snapper snapshots are never transfer destinations.

## Operator workflow (not yet executed)

On `mango`, review changes, then deliberately install:

```sh
ansible-playbook -i <your-inventory> native-btrfs.yaml --ask-vault-pass
```

If the inventory is configured through `ansible.cfg`, omit `-i`. There is no `btrfs receive` during installation. On `backup`, as **richard** (no outer sudo):

```sh
btrfs-native-pull --snapshot 20261009-170001Z --preflight
```

A live first baseline requires explicit approval at Step 10.4:

```sh
btrfs-native-pull --snapshot 20261009-170001Z
```

## Safety / known deferrals

- Pre-existing destination always fails closed; interrupted receive leaves **unaccepted** subvolume to inspect, not automatically remove.
- Snapshot name is a strict UTC timestamp; source parent lineage and UUID are pinned; received UUID/read-only checks precede atomic receipt.
- The sender/receiver helpers are root-owned; `sudo -n` is limited to the named helper modes. Operator SSH still uses `richard`'s alias `mars`.
- `--preflight` tests endpoint snapshot identity and receiver filesystem path. It does not test bandwidth, receive write capacity, end-to-end content, or the full baseline stream.
- Root-owned receiver directory and user-owned receipt state prevent uncontrolled overwrite; receipt and transaction lock are separate from old rsync lock.
- **Not yet implemented:** retention leases/source-side prune coordination (must precede production scheduling), hardened failure/quarantine cleanup, deeper restore validation, additional filesystem capacity margin enforcement, incremental `-p` send, and automation. No 0035 timers may be enabled as a consequence of this step.
- Inspect the installed sudoers rules and target permissions before running a first baseline. The CLI is purpose-constrained but privileged; never expose it to untrusted accounts.

## Evidence

Executed locally: `python roles/remote-backup/tests/verify-native-btrfs-static.py` — PASS. Python source parsed and compiled. No Ansible execution or target-host runtime verification has been performed. **Step 10.3 can be treated as source implementation complete but runtime acceptance pending**, not Step 10.4 completion.
