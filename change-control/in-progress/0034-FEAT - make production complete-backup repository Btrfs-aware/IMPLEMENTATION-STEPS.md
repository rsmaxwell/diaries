# 0034-FEAT — IMPLEMENTATION-STEPS (native Btrfs replication revision, 2026-10-11)

> **ACTIVE DESIGN DECISION — 2026-10-12: MARS-INITIATED NATIVE BTRFS PUSH**
>
> The previously documented `backup`-initiated native pull is **superseded for future replication** by `mars`-initiated Btrfs send/SSH/receive to `backup`. Historical pull experiments, signed-off steps, existing scripts and acceptance receipts remain evidence; this documentation update changes **no executable code, live SSH settings, systemd timers or transfers**. The currently running full pull of `20261012-100003Z` must complete and be verified as the common baseline before push migration. See `evidence/Step 10/PUSH-ARCHITECTURE-DECISION-20261012.md`.
>

**Current status:** Steps 1–9 were completed/closed under the previous documented contract. Preserve those source and runtime evidence records exactly. Step 10 is **OPEN** and redesigned; Step 11 is **OPEN**. Source `pluto` publication, schema-2 backup and restore behavior are unchanged. The former rsync pull implementation and its tests are historical transition evidence, **not** proof of the new Btrfs transfer path.

## Preserved completed work (no repeat required)

1. **CLOSED** — Freeze 0033 schema-2 production backup and restore contract.
2. **CLOSED** — Explicit production repository/storage configuration and Btrfs-awareness baseline.
3. **SUPERSEDED** — Original `pluto`-side reflink proposal; retain historical test artifacts, do not claim deployment.
4. **CLOSED (design)** — Fixed-directory publication and atomic generation contract.
5. **IMPLEMENTED/TESTED** — Isolated publication implementation; subsequent production proof captured in Step 9.
6. **CLOSED for existing `pluto` → `mars` contract** — Verified publication/pull from `pluto` to `mars`. This is **not** the newly selected `mars` → `backup` transport.
7. **CLOSED** — Historical restore/source compatibility.
8. **CLOSED** — Playbooks configuration, regression and operator guidance for publisher.
9. **CLOSED** — `pluto` controlled production deployment/publication. Do not disturb this path.

## Step 10 — Replace `mars` → `backup` rsync with native send/receive — OPEN

### 10.1 Freeze and inventory the source/receiver baseline

- Capture `btrfs filesystem show`, `findmnt`, `btrfs subvolume list/show`, filesystem/mount boundaries, snapshot UUIDs/received UUIDs, size and snapshot read-only flags on both machines. Record the *full* content of the `mars` sendable `@data` snapshot, not merely `/backup`.
- Reconcile `/media/usb/@data/backup`, `/media/usb/@snapshots/@data/<timestamp>`, `/@data/backup`, `/@data/diaries-mars-replica`, root and `@data` source management, legacy Snapper/timers, active rsync process, and available storage.
- Treat the currently running rsync copy as a separate, non-seeding dataset. **Do not interrupt it automatically**, delete it, or reuse it as a native incremental parent. Schedule a controlled retirement only after new baseline acceptance.
- Inventory mounted nested subvolumes, scope and rough full-send volume. **Gate:** explicit capacity and source scope acceptance; no inadvertent whole-disk transfer.

### 10.2 Ratify full-send path and privilege/locking design

- Confirm `mars` keeps its existing whole-backup and 0035 timestamp snapshot layout. Select read-only full-send source and dedicated empty destination Btrfs receiving root on `backup` distinct from `/@data/backup` and the old rsync replica.
- Define an SSH workflow using `richard@backup` → `mars` alias, with limited root helper(s) for Btrfs operations. Validate `btrfs send` source access, `btrfs receive` receiver permissions and no root SSH dependency.
- Define provenance/acceptance record stored outside immutable subvolumes; define receive transaction lock(s), temporary/unaccepted cleanup and incomplete-transfer failure handling. Shared rsync `.btrfs-snapshot-writer.lock` is a **legacy transfer lock**, not proof of receive validity.
- Agree incremental parent retention and rollback across both hosts; cross-feature contract owned jointly with 0035. **Gate:** checked design/safety and unchanged Snapper state.

### 10.3 Implement full native receive in Playbooks (default OFF)

- Create opt-in `btrfs-send-receive` helper and role/template/config, with `--preflight`, explicit `--snapshot`, `--full`, `--dry-run` (where safe), fail-closed path/subvolume checks and no automatic service activation.
- Transfer immutable snapshot using a reliable streamed SSH pipeline, capture exit status of each stage, verify read-only destination and received identity. If a stream fails, retain accepted snapshots and mark/clean the partial receive safely.
- Refuse overlapping destinations, symlinks and unexpected existing subvolume IDs; never operate on `/@data/backup` or the old rsync mirror. Add source regressions and syntax tests.

### 10.4 Establish and verify the new full native baseline

- Deploy *install only* on `mars` and `backup`; confirm prepared receiver is on the intended Btrfs filesystem, source snapshot is read-only, and source capacity/network checks pass.
- Manually execute one full `btrfs send`/`btrfs receive` into an isolated receive repository. Record `send` and `receive` exit codes, source UUID and destination `Received UUID`, logical size, transferred bytes, Btrfs usage and read-only state.
- Independently verify the whole source tree and find a Diaries backup dataset for disposable restore testing, without coupling transfer to Diaries. **Gate:** accepted baseline and unchanged old backup repositories.

### 10.5 Implement and verify incremental receive

- Produce a new verified read-only `mars` timestamp snapshot; keep prior source and destination parent unchanged. Implement `btrfs send -p <parent> <new snapshot>` and matching `btrfs receive` with exact common-parent validation.
- Rehearse no-data and changed-data cases; verify transfer bytes, final contents, UUID lineage and extent sharing, as applicable. Reject missing/unmatched parent, duplicate snapshot, modified read-only flag, interrupted stream, insufficient space and partial destination.
- Demonstrate parent pinning during transfer and across retention on **both** machines. **Gate:** repeatable accepted incremental lineage.

### 10.6 Integrate operator tools and acceptance with 0035

- Make **Diaries backup-history** available on `mars` and `pluto`, displaying IDs and actual containing snapshot paths (or the live published path on non-Btrfs `pluto`); optionally install on `backup` to validate received content. It is read-only and must not trigger restoration.
- Make native timestamp-named snapshot retention/prune utility available on `mars` and `pluto`. On a non-Btrfs `pluto`, preflight must refuse/skip safely. Preserve 0035 receiver-side retention on `backup` separately, with parent pinning.
- Demonstrate failed receive isolation, writer contention, source snapshot deletion prevention during send, disk pressure and rollback; confirm no host's legacy Snapper snapshots/timers were altered.

### 10.7 Controlled cutover, then close Step 10

- Record final accepted native baseline + incremental restore and evidence. Identify and disable legacy push and rsync pull schedules only after inventory; ensure *exactly one* newly selected transfer path is active.
- Keep prior rsync data available for a defined rollback window. Enable native receive scheduling only after independent acceptance and operator authorization; do not automatically enable 0035 native snapshot timers or retire Snapper.
- Record idempotent Playbooks deployment, regression suite results, source commit IDs, transfer logs and rollback. Close Step 10 only when these gates have actually passed.

## Step 11 — End-to-end production rehearsal and feature closure — OPEN

- Run two successive whole backups on `pluto`; demonstrate `mars` data publication/snapshot, one native full baseline and at least one correct incremental `backup` receive, history lookup and schema-2 disposable restore.
- Demonstrate snapshot retention safety, a failed/incomplete transfer and recovery without corruption of previously accepted recovery points, and distinct host identities/permissions.
- Verify schedules, restoration documentation, rollback and audit trail. Do not conflate a successful source-level test with production acceptance; close 0034 only on evidenced live results.

## Step 11.1 — Freeze final production baseline — EVIDENCE CAPTURE PREPARED (2026-10-13)

The accepted push, receipt, parent, independent pre-cleanup hold, pruning and source commit references have been assembled in `evidence/Step 11/STEP-11.1-PRODUCTION-BASELINE-20261013.md`. Run the provided read-only capture helper on `mango`, `pluto`, `mars` and `backup`; reconcile actual source revisions, current schema-2 generations, snapshot UUIDs, host mounts and schedules before marking Step 11.1 CLOSED. This substep changes no production data or services.

## Never change without explicit migration gate

- 0033 schema-2 format and existing restore semantics.
- Production `pluto` backup publishing, or whole-backup source layout on `mars`.
- Historical `/@data/backup`, old rsync `/@data/diaries-mars-replica`, and preexisting Snapper snapshots.
- Any native creation/prune timer, until host-specific 0035 sign-off.


## Step 10 continuation — source-initiated push migration (design approved 2026-10-12; NOT IMPLEMENTED)

The previously described `backup`-initiated native pull substeps and examples remain historical evidence; **the following supersedes unfinished implementation and acceptance work**. Do not reopen Steps 1–9.

1. **10.P1 — Freeze in-flight baseline.** Let the currently running `backup`-initiated full receive of `20261012-100003Z` finish; confirm full receipt `btrfs-full`, source `7ad1f171-d1c7-0545-82a1-52e84adac979`, matching receiver `Received UUID`, read-only status, proper receipt and source protection. Retain existing historical received `20261009-170001Z`. No network/SSH/timer change until this gate closes.
2. **10.P2 — Freeze push security and networking.** Use tested `mars` → `backup` outbound SSH `richard@10.254.22.1:39263`; configure a dedicated non-global SSH target with pinned host key, bounded connection timeouts and no implicit Tailscale fallback. Verify receiver's fixed-path restricted privileged endpoint and allowed destination; maintain 0033 schema-2 unchanged. Design receipt-fetch/verification permissions with no receiver receipt spoofing by sender.
3. **10.P3 — Implement source-side operator.** Introduce opt-in `btrfs-native-push` on `mars` with `--snapshot`, `--preflight` and explicit recovery/full-reseed options; check immutable local source snapshot UUID, source filesystem UUID, free space on receiver, destination exclusion and locks. Use `btrfs send [-p accepted-parent]` over SSH to validated `btrfs receive` on `backup`. The real implementation must not be a bare remote shell capable of arbitrary root commands.
4. **10.P4 — Retain receiver-controlled acceptance.** Receiver verifies subvolume readonly, `Received UUID`, filesystem boundary, expected parent and stream/receive exit outcomes, and atomically writes receipt outside readonly received subvolumes. On `mars`, consume an authenticated receipt and independently validate it before changing source protection state. A timeout after receive-but-before-ack must reconcile the existing receiver snapshot/receipt idempotently without deleting a valid accepted snapshot.
5. **10.P5 — Parent/candidate pin lifecycle.** Before send, atomically pin candidate and current parent in root-owned 0035 protection registry while holding agreed stable lock. Before incremental, validate matching accepted parent on both ends. On accepted child, promote new parent and release only superseded parent; on failure, no orphan/unprotected send candidate and no premature parent deletion. Handle concurrent prune and two push invocations safely.
6. **10.P6 — Regress and deploy disabled.** Add static/unit tests (full, incremental, missing parent, malicious inputs, protected prune, corrupt/missing receipt, interrupted send, duplicate request, network outage, capacity limits and SSH endpoint denial), then `mango` Ansible syntax/regressions, then `mars`/`backup` operator preflight. Keep old pull installed but unscheduled as temporary rollback; do not start another full send or schedule jobs in this documentation step.
7. **10.P7 — Live incremental acceptance.** Only after 10.P1, run a source-initiated incremental push from a newer `mars` snapshot; verify both ends, receiver-controlled acceptance, protected-source parent promotion, history and no changes to `/@data/backup`. Exercise pruning dry-run and controlled prune against eligible old snapshots, with parent immutability verified.
8. **10.P8 — Controlled cutover/close-out.** Inventory cron/timers and legacy scripts on both hosts; ensure only one active transport, enable scheduling only by explicit operator approval, prove failure/rollback and backup restore usability, document evidence and close Step 10/feature only after acceptance.

**Current state (12 Oct):** Source protection before the active full reseed and dry-run exclusion passed; the full transfer and push implementation/acceptance are still pending. `btrfs-snapshot-prune.timer` on `mars` is disabled. Documentation revision alone must not mark Step 10 CLOSED.

## 2026-10-13 — Step 10.P9 acceptance (CLOSED)

The narrow `roles/remote-backup/` pull-retirement cleanup passed source regressions, Ansible deploy on `mars`/`backup`, on-host legacy-helper absence and a post-deployment incremental preflight. The pre-cleanup checkpoint `20261013-171228Z` was received on `backup` and remains held independently of replication parent `20261013-180016Z` on `mars`. Evidence: `evidence/Step 10/STEP-10.P9-FINAL-CLEANUP-ACCEPTANCE-20261013.md`. Commit `5d3b2b3` was pushed but includes other ongoing work due to `git add -A`; see the evidence for the precise scope qualification. This **does not** by itself close the whole feature.

## 2026-10-14 — Step 11.3 disposable off-site recovery rehearsal: CLOSED

Gates A–D passed against published schema-2 generation `20261009-154847Z` held in off-site Btrfs snapshot `20261013-171228Z`. Recovery on `mars` used an isolated PostgreSQL 18 container and scratch Files, verified 89 Files and Image catalogue hashes, and removed each disposable container. The `mars` history CLI remains blocked by `verification.required=false`; configuration review is deferred to 0035-FEAT and not misrepresented as a successful history lookup. See `evidence/Step 11/STEP-11.3-OFFSITE-DISPOSABLE-RESTORE-CLOSEOUT-20261014.md`. Step 11 and 0034-FEAT remain OPEN; next Step 11.4 is unattended operating arrangements.
