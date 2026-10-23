# 0040-FEAT Step 3 — Full-duplex sender/receiver loopback integration

Status: **source-only integration validated locally; production execution NOT authorised**.

## Inputs

The sender and receiver sources combine the accepted 0040-FEAT source patches through the manager-bound adapter stage. The regression loads those files by operator-supplied paths. No production host, SSH, sudo, Btrfs subvolume or privileged endpoint is contacted.

## Results

Four local regression tests passed: successful two-round full-duplex exchange and manager callback completion; failure in manager callback yields no success; changed source pin on second challenge prevents manager invocation; no publicly exposed delete switch. Temporary manager/receiver locks and stream sockets are used.

## Lifecycle finding

An initial abort-path test left the receiver awaiting the second challenge response until timeout. The loopback harness now explicitly half-closes the sender-to-receiver stream on abort, permitting receiver EOF detection and lock release. A production SSH/subprocess owner MUST implement deterministic close/kill/wait cleanup on sender failure and preserve the durable source pruning pin and any pending receiver journal. This is **not yet implemented/verified end-to-end**.

## Outstanding gates

- Production-capable caller not connected (and must stay disabled).
- Authenticated SSH lifecycle, privilege restrictions and abort cleanup not yet demonstrated.
- Real journal-based Btrfs delete and interrupted reconciliation only on disposable snapshots still required.
- Production inventory remains protected; receiver pruning remains false.

## Regression invocation

From the Windows Cygwin terminal at the Diaries repo root, pipe the script to `ssh mango 'python3 /dev/stdin /home/richard/playbooks/roles/btrfs-replication/files/btrfs-native-push.py /home/richard/playbooks/roles/btrfs-replication/files/btrfs-native-push-receiver.py'`.
