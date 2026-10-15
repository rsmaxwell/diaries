# 2026-10-11 — Change-control decision: native Btrfs replication

**Decision:** Replace the still-open `mars` → `backup` rsync receiver design with full-once, incremental thereafter `btrfs send`/`btrfs receive` of timestamp-named read-only snapshots of the existing whole-backup-containing Btrfs source on `mars`.

**User-required constraints:** (a) preserve the whole backup source unchanged, with Diaries included incidentally and no Diaries-specific replication logic; (b) make Diaries backup locator/history and native snapshot pruning utilities available on both `mars` and `pluto`; (c) treat the current rsync copy as non-seeding, requiring a new native baseline; (d) regenerate the 0034/0035 implementation steps.

**Scope consequence:** A snapshot of `@data` contains more than its `/backup` folder where applicable; native send does not filter a subdirectory. Confirm size/other source data and nested-subvolume boundaries before initial full send.

**Evidence:** Completed Steps 1–9 (0034) remain closed, immutable evidence. The rsync receiver Items 1–4 performed/deployed during 0034 Step 10 are historical interim work and do not constitute Btrfs send/receive acceptance. 0035 implementation already developed is to be adapted, not silently discarded.

**Cutover gates:** New isolated destination; read-only full Btrfs baseline; matching snapshot identities and received UUIDs; controlled incremental send with retained common parent; verified failure isolation and retention; generic transport without schema-2 knowledge; read-only app history and disposable restore test separately; explicit schedule migration/rollback. Historical `/@data/backup` and old rsync directory must remain untouched until separately approved retirement.

**Open question resolved operationally:** The request names **`pluto`** (not `backup`) as the second host requiring history and pruning tools. The receiver `backup` still needs its *own* native received-snapshot retention and may optionally carry the history locator. If `pluto` is ext4, pruning utility must refuse/no-op instead of claiming Btrfs support.

**Status:** Documentation/design revision only. No source implementation, host deployment, interruption of live rsync or scheduler changes performed by this ZIP.
