# Step 10 — Independent receiver reconciliation (2026-10-20)

**Assessment: receiver evidence supports proceeding to explicit operator review; Step 10 OPEN; no deletion authorised.**

## Evidence source

`diaries-sources-20261020-080242.zip`, `evidence/Step 10/receiver-preflight/` (backup capture 2026-10-20T07:01:43Z) compared with `evidence/Step 10/fresh-preflight/` (mars capture 2026-10-20T06:44:37Z). Both are point-in-time read-only captures.

## Verified receiver facts

- `backup` Btrfs `/dev/sda2` mounted at `/`, subvolid=5.
- Actual receiver: `/@data/mars-received/@data`, with `.replication-state/` restricted to `richard` (0700).
- 14 received read-only Btrfs subvolumes, dated `20261009-170001Z` through `20261020-030026Z`.
- Latest received: `20261020-030026Z`, receiver subvolume ID 55792, UUID `09b30932-a08a-894b-8728-6ba6ec72a7f1`, Received UUID `2239b0bd-b483-884e-8a14-30dcbb8d8392`, `ro=true`; receive time 2026-10-20 04:31:28 BST (03:31:28 UTC).
- Matching receipt metadata file `20261020-030026Z.json` exists, modified 2026-10-20 04:31:46 BST (03:31:46 UTC). Contents were deliberately not captured or independently validated.
- `mars` native dry run records `REPLICATION-PROTECTED: ['20261020-030026Z']`, matching the latest receiver *name*. Source UUID and receipt contents have not been independently compared.
- Filesystem estimated free space approximately 319 GB; btrfs device counters report zero read/write/flush/corruption/generation errors. This is not a data-integrity or recovery verification.
- No matching replication process reported at capture time; point-in-time only.

## Items requiring disposition before approval

1. `backup` reports **failed `backup.service` (unit not found)** and failed `user@0.service`. Determine whether these are stale/unrelated failures or affect current off-site operations. Do not dismiss them solely because a new snapshot was received.
2. The receiver capture confirms a recent read-only received snapshot and metadata *presence*, not contents/receipt reconciliation, full parent lineage, or a tested restoration path. The previous obsolete diagnostic dataset-parent configuration remains a separate known limitation.
3. The exact legacy `@data` snapshot `19605` on `mars` remains `WOULD-DELETE`, creation `2026-09-28T00:00:38Z`, ID 20165, UUID `489332dc-3b48-eb40-b59a-d9bd86cc9915`, `ro=true`; it is **not** shown on the receiver, nor should the receiver's native recovery copy be construed as an identical legacy Snapper snapshot.
4. 58 complete native sets (0 incomplete); 25 legacy entries (16 KEEP / 9 WOULD-DELETE); 2 checkpoint holds and 1 replication pin. Recompute these immediately before any separately approved deletion.

## Decision

**Technical receiver inspection: PASS (limited scope). Operator pilot approval: PENDING. Step 10: OPEN.** No approval token/file generated, `legacy-delete` not executed, and no Snapper snapshot removed. Only `@data` snapshot ID `19605` may be considered for one explicitly approved Step 11 pilot, after resolving relevant service status and accepting the remaining recovery evidence/limitations. This record is not an approval.
