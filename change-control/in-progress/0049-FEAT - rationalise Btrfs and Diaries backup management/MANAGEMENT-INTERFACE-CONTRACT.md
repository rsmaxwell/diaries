# 0049 — Management command and output contract

**Status:** Proposed target for implementation; not a record of installed host state.

## A. Clear separation of concerns

### `diaries-backup-status` (`mars`)

Scope is the **Diaries application backup dataset** as discovered by `diaries-backup-history`, not the backup plumbing:

- Latest retained logical dataset and backup ID; label the evidence accurately (valid manifest identity / retained occurrence / fully content-verified, which are **not** automatically equivalent).
- Number of distinct retained backup IDs and occurrences, first/last retained snapshot, manifest identity conflicts and application-specific warnings.
- Recent backups as a titled, aligned table. Existing `--limit N` (default 5, range 0–100) is retained; support `--json` and optionally `--verbose` where useful.
- No qgroups, Btrfs filesystem status, last pull, accepted collection marker, snapshot-engine readiness, replication/push, receiver state, agreed parent, preflight or service schedules.
- Do not drop source verification checks from snapshot **creation eligibility** merely because the status output no longer prints them.

### `diaries-backup-history` (`mars`)

Retain its existing `list`, `list --all`, `show`, `path`, `verify` and associated selection options. Normalise `list`, `list --all` and multi-occurrence `show` to titled header tables; right-align numerical columns; ensure filenames/UUIDs/paths are not silently truncated. `path` must still return a **single unadorned path** for scriptability; do not place a table around it. Full `verify` must remain the explicit expensive content-validation operation. Preserve its warnings/conflict detection and current semantics unless explicitly required by a tested contract change.

### `btrfs-backup-status` (both hosts)

New concise, strictly **read-only** infrastructure summary. Display only appropriate sections:

| Section | `mars` | `backup` |
| --- | --- | --- |
| Backup collection | Latest completed/verified pull, latest accepted marker, service state/timer (if safely available) | Not applicable |
| Local snapshots | Filesystem, snapshot count/range, retention policy and creation/pruning health | Received snapshot inventory, retention policy and prune health |
| Replication | Sender/receiver relationship, agreed parent/prior, last verified received snapshot, next candidate/preflight, last completed cycle when verifiable | Receiver accepted parent/prior, source identity, received snapshot range, last completed receive when verifiable |
| Filesystem health | Qgroups, stale/under-deletion counts and prerequisite errors | Same, on receiver filesystem |
| Scheduled operations | Relevant service/timer last and next runs when discoverable, with clear labels | Receiver-prune and maintenance operations |

Do not conflate:

1. **Last verified pull** — time of source collection and validation.
2. **Last accepted dataset** — publication marker currently eligible for snapshots.
3. **Latest received snapshot** — actual receiver inventory.
4. **Agreed parent/prior** — verified incremental transfer identities shared by endpoints.
5. **Last successful push cycle** — systemd/operational execution, possibly with **no transfer**.
6. **Last verified transfer** — evidence of a completed specific received snapshot.

Avoid inventing these values from a parent timestamp or claiming they are equal. If evidence is missing, report `unknown`, `unavailable` or `not checked` with a reason; do not manufacture a time.

`btrfs-backup-status` options:

| Option | Meaning |
| --- | --- |
| (none) | Concise, human-readable infrastructure summary |
| `--json` | Pretty-printed, stable JSON with explicit host/role, check states and source timestamps |
| `--verbose` | Optional expanded tables: retention categories, holds, protected parents, detailed service results |
| `--local-only` | Absolutely no SSH/remote invocation; explicit `not checked` remote-state fields, without incorrectly degrading status solely because probing was deliberately disabled |
| `--config PATH` | Specialist configuration override; validate and never mutate the selected configuration |

Other existing command-specific options remain where relevant. Remove stale `--push`/`--history` implementation overrides from **Diaries** status when no longer relevant; allow dependency overrides only in correctly scoped utilities for tests and specialist diagnostics.

## B. Naming and command consolidation

| Current name (2026-11-12 source) | Target operator-facing name / disposition |
| --- | --- |
| `btrfs-simplified-replication` | `btrfs-replication` (same sender/receiver protocol, carefully preserve 0041 wrapper and privileges) |
| `btrfs-native-push.service` / `.timer` | `btrfs-push.service` / `.timer` |
| `btrfs-receiver-simple-prune.service` / `.timer` | `btrfs-receiver-prune.service` / `.timer` |
| `btrfs-snapshot-manager receiver-simple-plan` | `btrfs-snapshot-manager prune --dry-run` on receiver |
| `btrfs-snapshot-manager receiver-simple-prune --max-delete N` | `btrfs-snapshot-manager prune --max-delete N` on receiver |
| `btrfs-snapshot-manager receiver-prune --approval-file PATH` | Old, different receiver operation: prove unused and retire before `prune` unification; do not silently redirect it |
| `receiver-inventory`, `receiver-plan`, `receiver-coordination-check`, `receiver-recovery-plan` | Audit callers; retire obsolete operator entry points or keep necessary incident-recovery functionality with explicit internal/documented status |
| `btrfs_simplified_replication_*`, `btrfs_simplified_receiver_*` | Neutral `btrfs_replication_*`, `btrfs_receiver_*` variable families (enumerate exact used names and inventory overrides before changing) |
| `NEXT SIMPLIFIED PUSH PREFLIGHT`, `RECEIVER-SIMPLE-*`, active role headings and descriptions | Neutral, precise Btrfs replication/retention terminology |
| `.simple-agreed-parent.json`, `.simple-prune-pending.json` | Treat as **persistent state**, not cosmetic labels; see migration rule below |

Replace active use of *simple/simplified* with *Btrfs replication*, *push*, *receive*, *agreed parent* or *receiver prune*. Preserve historically accurate feature evidence, older tests archived in feature directories and Git history. Do not reintroduce permanent aliases for retired commands unless an identified external consumer needs one and the exception is documented.

### Snapshot manager contract

- Keep root and existing caller-authorisation checks; receiver **must not** gain snapshot creation, ad hoc holds, unlimited deletion or new privilege by virtue of sharing subcommand syntax.
- `prune --dry-run` is **purely read-only** on both hosts and must show the same candidate sets as the corresponding guarded prune would select at that point. Receiver read-only planning must not create/remove journals or state records.
- `prune --max-delete N` is bounded and destructive, permitted only with the endpoint's existing `receiver_prune_enabled` (on `backup`) and all existing lock, UUID, read-only, parent/prior, hold, journal and source-tree guards. Preserve endpoint-specific upper limits (source 32; receiver 20, with scheduled receiver limit 10 unless inventory says otherwise).
- Never let `prune` without a limit become an accidental unbounded receiver deletion; prefer requiring an explicit cap for manual operations. Scheduled source and receiver invocations retain their approved bounds.
- Investigate and retire/deprecate `run` (create then unlimited prune) only after checking callers; do not change a systemd invocation behind its back.
- Remove only the *application-specific displayed output* from generic `status`; preserve verification needed to permit snapshot creation.
- Source-only checkpoint hold commands stay source-only unless separate approval expands them.

### Persistent state migration rule

Enumerate all references in source, templates, inventory, wrappers, unit files, sudoers/forced command dispatch, documentation, regression tests and live installed copies before deciding any rename. Record actual SHA256/ownership/mode and protected parent/prior identities on **both** hosts. If renaming `.simple-*` is safely justified, use a guarded, atomic and reversible migration with a single coordination/maintenance window, locked operation, positive post-rename read-back of identities and rollback; never bootstrap or reset parents as a cosmetic fix. Where this introduces undue risk, explicitly document unchanged internal file paths as a narrow exception; remove *simple* from all visible operator interfaces nonetheless.

### systemd / 0041 compatibility

Change the unit names **and all** referenced service files, timers, start/restart instructions, monitoring, Ansible enable/disable/removal tasks and tests together. Preserve the accepted 0041 `btrfs-send`/`btrfs-receive` identities, dispatcher, fixed command allowlists, sender wrapper, sudo restrictions and transport secrets. Retire/disable old timers only as the new ones are activated: precisely one enabled push timer on `mars` and one receiver-prune timer on `backup`, with the **same scheduled calendar and configured max delete** as before. No duplicate invocation or unplanned downtime.

## C. Human-readable output standard

- A descriptive **title above every list**, followed by **column-header row** and separator or visually distinct header; fixed-width aligned columns, numbers right-aligned, dates aligned and explicitly UTC.
- No key=value runs pretending to be a table; no malformed columns under long values. Dynamically determine widths or use an equivalent robust formatter. Do not silently truncate UUIDs, hashes, IDs or paths.
- Long optional descriptions may be on following lines; preserve a compact width for common data but correctness wins over 80-column wrapping.
- Show `No retained backups` / `No eligible snapshots` / `Not checked (--local-only)` explicitly instead of an empty unlabeled area.
- Use accurate status labels such as `MANIFEST-OK`, `CONFLICT`, `FULLY-VERIFIED`, `NOT-CHECKED` only when supported by evidence. Existing `verified` list values may mean schema/identity validation, **not** a just-executed full file verification.
- Consistent UTC timestamp presentation: `YYYY-MM-DD HH:MM:SS UTC` (or `YYYYMMDD-HHmmssZ` for unmodified snapshot IDs, clearly labelled).

Illustrative, invented data (format only):

```text
RECENT DIARIES BACKUPS

Logical Dataset  Backup ID             First Retained (UTC)   Last Retained (UTC)    Snapshots  Evidence
---------------  --------------------  ---------------------  ---------------------  ---------  -----------
diaries          20261116-014500Z      2026-11-16 02:00:00    2026-11-16 09:00:00            8  MANIFEST-OK
diaries          20261115-014500Z      2026-11-15 02:00:00    2026-11-16 01:00:00           24  MANIFEST-OK
```

The actual backup ID and fields must be populated from the source report; the example above is **not** a verified production result.

## D. JSON and errors

- On an **operator-facing** command that emits JSON (e.g. `btrfs-replication sender status`, `diaries-backup-history --json list`, `diaries-backup-status --json`, `btrfs-backup-status --json`), use deterministic JSON with 2-space indentation and a final newline. Python should emit `json.dumps(payload, indent=2, sort_keys=True)` or equivalent directly; do not require `jq` to make it readable.
- Output **only** the JSON document to stdout. Diagnostics/warnings go to stderr. Empty collections are `[]`, not absent or text pasted into JSON. Machine consumers can still use `jq` freely.
- Preserve existing key names and types where consumers depend on them; additions/renames to report schemas must be documented and regression-tested. For internal sender/receiver RPC, lines on stdout may be protocol records: do **not** change framing, progress prefixes, stream bytes or what the remote dispatcher expects solely to beautify JSON.
- Keep `path`'s single-path stdout contract and program exit codes of low-level transport/verification commands unless a migration is proven safe.
- For top-level **status** commands, aim for consistent `0` (all required checks healthy), `1` (completed with degraded health), `2` (required check could not complete / malformed data/config). Decide and document the mapping of network failure, absent source data, missing timers, intentionally omitted remote checks and warning thresholds. Never show a required check as `UNAVAILABLE` while returning `0` unnoticed.

## E. Testable non-functional requirements

- All status and `--dry-run` forms are read-only; no side effects on snapshots, parent records, receipts, journals, holds, enabled services or timer state.
- Tests work in development with isolated fixtures without requiring live production datasets; use actual host smoke checks only for the final integrated read-back.
- Failure conditions must be clearly identified and security decisions must fail closed.
- No APT `jq` dependency is necessary for the tools themselves; `python3 -m json.tool` is an acceptable verification alternative.
