# 0040-FEAT Step 12.3 — source reconciliation and receiver architecture review

Date: 2026-10-31. Status: **SOURCE REVIEW COMPLETE; LIVE RECONCILIATION AND ARCHITECTURE ACCEPTANCE OPEN**. This report is a proposed technical decision, not transfer/deployment authorisation.

## Baseline

Latest supplied source archives: `diaries-sources-20261031-113345.zip` and `playbook-sources-20261031-113339.zip`. Read-only `mango` terminal evidence `note(20261031-113438).txt` reports Playbooks branch `main`, HEAD `f1512870cd6ce24ba6fdd68357006bfc069a7c26`, multiple modified tracked files and numerous untracked agreed-parent modules and tests. Preserve them; do not reset/overwrite. Source archives supersede older 08:50 archives and include 04P–04U source. Live installed-file parity, timers, and both endpoint states have not been rechecked in this baseline.

Governing decision: `STEP-12-3-UNATTENDED-DESIGN-DECISION.md` (six formal acceptance gates). Agreed-parent redesign: `reports/STEP12-3-AGREED-PARENT-REDESIGN-20261030.md`. Historical 04A–04U filenames remain unchanged. No new lettered increment; assign the next linear number only after checking the full step index.

## Code findings

1. Existing `roles/btrfs-replication/files/btrfs-native-push-receiver.py` `--accept` acquires a receiver writer lock, executes `btrfs-native-endpoint --role receiver`, inspects B and writes a success receipt under that lock. It **does not** demonstrate the agreed-parent manager lock plus exact prepared A/B preflight held across the receive.
2. Its receipt presently sets `source_send_exit: 0` on receiver-side success even though the receiver cannot observe the sender process's final exit status at that instant. Existing receipt consumers depend on this schema; migration needs explicit compatibility and fail-closed handling.
3. The dormant 04F `btrfs-agreed-parent-transfer-execution-adapter.py` uses direct `ssh`, unlike the verified 04P `runuser -u richard -- ssh` identity. It suppresses both subprocess stderr streams and waits without a bounded transfer deadline. **Do not enable it as written.**
4. The 04S endpoint performs the exact prepared-state and absence check under actual receiver manager and writer locks; live read-only success was previously observed. 04T/04U local peer/socket tests do not bind remote SSH authentication to a shared receiver process.
5. The latest source contains many independent validators, which must be integrated rather than treated as individually sufficient live transfer evidence.

## Gate B recommendation: prefer one authenticated SSH data session and journaled completion

**Proposed, not yet accepted:** Reuse the established `richard` SSH authentication and a constrained receiver entrypoint rather than implement the two-channel root socket architecture. The sender supervises a single bounded Btrfs send→SSH receiver pipeline and obtains **both local process statuses**. Receiver holds manager then writer lock, rechecks A/B, destination, receipt and journal, receives once, verifies B independently, and writes a **durable provisional transaction record** (not a final success receipt). Only after *both* sender and SSH receiver processes return successfully does sender initiate a constrained, authenticated finalisation request identifying the same exact A/B and transaction. Finaliser reacquires both locks, verifies the same provisional journal, B UUID/readonly/incremental lineage, current state and source outcome, and commits a final receipt atomically; failure leaves A pinned, B pending and forensic evidence intact. Do not infer sender success from receiver EOF.

**Critical trade-off:** Between the first SSH receive and the finalisation request the manager/writer locks are released. Safety therefore depends on a durable, uniquely identified provisional journal that *every* receiver operation capable of deleting, receiving or committing B must recognise and refuse to conflict with. If current entrypoints cannot be made to share that guard, reject this proposal and design a truly continuous-lock supervisor with a trustworthy sender-completion channel. Also require a clear threat-model decision: the authenticated `richard` sender can report its own exit result; this is not independent cryptographic remote process attestation. It is acceptable only under the pre-existing trusted sender/SSH operational model and only after end-to-end verification.

Avoid an unrestricted root socket, new broad sudo privileges, auto-delete, automatic retry, and premature modification of legacy receipt semantics.

## Required acceptance before any real B receive

- Freeze and inventory active legacy entrypoints, handlers, receipt schema readers and prune authorities; confirm the provisional journal is enforced by **all** relevant code paths.
- Review process supervision (bounded overall deadline, captured diagnostics, signal/EOF and shutdown handling), precise root-vs-richard execution identity, exact A/B identity checks, and transaction ID binding.
- Test on disposable Btrfs: successful receive/finalisation, sender fail after receiver success, SSH fail after B exists, termination at each commit point, concurrent prune, stale journal, replay/retry, idempotent reconciliation and A pin preservation.
- Repeat runtime source/receiver A/B observations and deployment/check-diff before any controlled live operation. No destructive snapshot operation is authorised by this report.

## State and operations

Last accepted live snapshot identities: A=`20261030-030033Z` (`d901ddd2-66c7-0b42-b26c-ab6886273b7a`), B=`20261030-170009Z` (`a9b78fb9-4da6-cf4f-b242-13909f574193`), established A and pending B on both endpoints. These observations are historical. Keep native push and prune inactive on mars; leave hourly snapshot creation running.

**Next read-only gate:** Obtain host runtime state, current locks/timers/receipts, installed endpoint checksums and current observers, then accept/reject the recommended Gate B architecture before implementing code. Formal Step 12.3 acceptance gates 1–6 remain OPEN.
