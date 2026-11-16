# 0041-FEAT — Implemented least-privilege replication design

**Status:** Implemented and technically verified on 16 November 2026. This supersedes the original October draft; it does not imply production rollback was exercised.

## Trust boundaries

| Location | Identity / operation | Observed or accepted boundary |
| --- | --- | --- |
| `mars` | `btrfs-send` systemd identity | `User=btrfs-send`, `Group=btrfs-send`, fixed `sudo -n /usr/local/libexec/btrfs-replication-sender-cycle-0041` |
| `mars` | Privileged transaction engine | Existing root-owned `btrfs-simplified-replication sender cycle`, with original source manager lock and protected parent semantics; dedicated SSH subprocess deliberately runs as `btrfs-send` |
| SSH transport | Service Ed25519 credential | Private key held only on `mars` in service-owned protected `.ssh`; pinned root-owned receiver host key; strict batch/identity/host-key checking; port 39263 |
| `backup` | `btrfs-receive` forced-command identity | Root-managed `authorized_keys`, fixed SSH dispatcher, no permitted arbitrary commands/interactive use through dedicated key |
| `backup` | Privileged receive gate | No-argument root-owned `/usr/local/libexec/btrfs-replication-receiver-gate-0041`, bounded/validated request header; only `status`, `receive`, `advance`; binary stream is passed intact to trusted Btrfs engine |
| Both | General management | Snapshot creation/pruning, qgroup maintenance and retention remain separately root-managed. `richard` personal administration unchanged. |

The sender and receiver are **not** arbitrary command runners. Their sudoers rules enumerate fixed no-argument executables, not `/usr/bin/btrfs`, arbitrary Python, shells or `NOPASSWD:ALL`. Root-protected agreed-parent files remain mode `0600`. The receiver state directory and writer lock retained their pre-existing permissions, while the trusted root engine enforces state updates. No general `CAP_SYS_ADMIN` capability was assigned to a service executable.

## Verified behaviour

- Step 8 negative checks: unapproved sudo operations, shell request, arbitrary `id`, bootstrap, operator injection and path traversal were all rejected; read-only dedicated receiver status succeeded. `evidence/Step 8/security-idempotence-20261115-143643Z.txt`.
- Step 9 validated native Btrfs full/incremental send/receive, UUID/checksum, deliberate truncated stream rejection, retry and deletion of only disposable fixture subvolumes. The **existing `richard` transport** was used for this isolated fixture; do not call it an end-to-end dedicated-account fixture. `evidence/Step 9/disposable-native-transfer-20261115-144655Z.txt`.
- Step 10 used the actual dedicated transport for one incremental production transfer and verified sender/receiver state reconciliation. `evidence/Step 10/step10-execute-20261115-145938Z.txt`.
- Step 12 proved unattended systemd execution and successful accepted-parent advancement, with healthy snapshot report. `evidence/Step 12/scheduled-replication-20261116-092125Z.txt`.

## Preserved invariants

1. One canonical `btrfs-native-push.timer`, 03:30 UTC; systemd oneshot service remains inactive between successful cycles. Staged candidate unit remains inactive.
2. The trusted sender maintains the transaction-wide manager lock across transfer/reconciliation. Shared snapshot-manager and writer lock, lineage/UUID checks, agreed-parent pins and receiver holds remain in use.
3. Both agreed-parent files remain root-owned and mode `0600`; the accepted parent is advanced only after verified successful receive/reconciliation.
4. No changes to `richard`'s personal SSH and sudo permissions. No changes to receiver retention/prune controls, no unapproved deletion or re-seeding.
5. No fallback from dedicated transport to `richard` on failed dedicated SSH authentication.

## Rollback and residual limitations

Rollback tooling is retained in `tools/run-0041-step11-service-cutover-from-cygwin.sh --rollback` and its mango companion, with Ansible managing the canonical service identity. It must be used only after checking deployed source revision, timer/job state, snapshot pins and current parent equality; see Step 11 report. **No executed live rollback test was captured.** A scheduled successful run is documented, not a repeated multi-day observation period. These limitations are disclosed for formal closure; they do not negate the accepted transfer and scheduled-run evidence.

Historic decisions in the original draft about disabled receiver pruning and postponed 0040-FEAT work are superseded by the 13 November baseline showing receiver pruning already enabled at 04:15 UTC, managed separately from 0041.
