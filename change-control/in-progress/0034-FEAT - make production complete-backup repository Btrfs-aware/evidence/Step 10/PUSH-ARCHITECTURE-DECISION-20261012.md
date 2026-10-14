# 0034 Step 10 — Native Btrfs push architecture decision (2026-10-12)

**Decision:** replace *future* `backup`-initiated native pull transactions with `mars`-initiated native **push**. Scope is whole-backup replication from `mars` to `backup`; `pluto` → `mars` Diaries backup consumption remains pull-based. The existing full pull is allowed to finish. **Design/documentation only; no runtime change.**

## Why

`mars` is behind the home UniFi NAT/firewall at `192.168.5.219`; `backup` is a data-centre host reachable from `mars` at `10.254.22.1` over SSH port `39263` (successful `hostname` returned `backup`). Conversely `backup` → `192.168.5.219` ping and SSH timed out. Tailscale `backup` → `mars` was relayed over `lhr`, with observed `mars` ping to Tailscale `backup` ~220 ms versus ~9.8 ms to `10.254.22.1`. **Latency does not establish achievable throughput**; benchmark a later push. No inbound UniFi firewall hole, reverse tunnel, or change to global DNS is required.

## Baseline and compatibility

- Existing in-flight native **pull** of `20261012-100003Z`, source UUID `7ad1f171-d1c7-0545-82a1-52e84adac979`, may become the first push incremental parent after independently verified successful receive and acceptance receipt. No assumption of completion; no restart, retransfer, or network re-route mid-stream.
- Older `20261009-170001Z` was fully received on `backup`, but its matching source on `mars` was pruned at 03:15 UTC on 12 Oct, so cannot be used as a common incremental parent. Do not delete its historical received copy as part of this migration.
- Preserve unchanged schema-2 backup, separate destination `/@data/mars-received/@data/TIMESTAMP`, receiver receipt directory `/@data/mars-received/.replication-state/`, historical `/@data/backup`, and 0033/0034 Steps 1–9 evidence.

## Target transaction

1. Operator invokes opt-in source-side `btrfs-native-push` on `mars`, selecting a validated read-only `@data` timestamp snapshot; a preflight does not mutate state.
2. Establish source-side exclusive replication lock and register candidate + required accepted parent in the root-owned 0035 protection registry **before** initiating stream. Reject concurrent prune or transfer races. Verify both source and receiver filesystem UUID/paths and enough receiver space.
3. Connect outbound as normal SSH user to the authenticated dedicated `backup` endpoint (`10.254.22.1:39263`, configured via Playbooks after approval). Restrict remote privileged Btrfs receive/inspect/finalisation to fixed allowed operations, destinations and filesystem UUID; no general root SSH or arbitrary remote shell execution.
4. For a common matching, immutable accepted parent, stream `btrfs send -p P CHILD`; for an expressly requested initial full/reseed, stream full. Fail closed, never silently downgrade an incremental to full. Only accepted receiver snapshots may be chosen as parents.
5. Stage and verify receive on `backup`, confirm both process exits, `readonly`, matching source UUID with `Received UUID`, correct parent provenance and correct receiver filesystem. Publish **receiver-controlled** receipt atomically outside received snapshot; preserve accepted snapshots through failed attempts.
6. Have `mars` independently retrieve and verify authenticated receiver receipt. Promote new snapshot in 0035 protected registry, **then** release old pin; failures/timeouts retain current parent protection and reconcile any accepted-but-unacknowledged receive without accidental overwrite/deletion.
7. Receiver-side retention independently protects its current accepted parent and does not let `mars` unilaterally delete received snapshots. Any pruning schedule and parent advancement must be tested under controlled concurrency and outages.

## Cutover and acceptance gates

- Complete and verify `20261012-100003Z` via the existing running pull. Record immutable received subvolume UUID and receipt.
- Freeze a push-specific security contract, integrate Playbooks for source orchestration and receiver helper, and add tests for idempotence, error recovery, duplicate/partial receive, malicious snapshot/path, broken SSH, missing parent, disk pressure and retention races.
- Deploy push disabled, preflight the direct network, then run **one** verified incremental against the accepted baseline, check protection before/during/after, receipt, history and restore usability.
- Only then propose timer activation and retire/disable automated native pull, without deleting historical pull implementation. Explicit approval required for any production schedule changes.

**Current acceptance:** 0034/0035 pre-send source protection and prune dry-run were demonstrated on the in-flight `20261012-100003Z` pull; full receive and future push acceptance not yet demonstrated. `mars` prune timer disabled. No code or deployment changes included in this doc revision.
