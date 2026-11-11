# Step 03 — Receiver receipts and historical incremental-parent reconciliation

**Date:** 2026-10-21. **Result:** observational identity/lineage checks passed; Step 03 still IN PROGRESS. **No qgroup deletion authorised.**

## Contract

Playbooks `roles/remote-backup/README.md` and native source/receiver programs describe **mars-initiated @data-only** replication into `/@data/mars-received/@data/`, with receiver receipts under `/@data/mars-received/.replication-state/`. Receiving `root` snapshots is not required by this contract.

## Accepted live evidence

A read-only capture at 2026-10-21 13:15:05 UTC recorded 15 receiver receipt JSON filenames and `writer.lock` (`protection/backup/receiver-receipt-inspection.txt`, already present in operator's checkout). For the three protected checkpoints, receipts record `transport=btrfs-incremental`, `source_uuid=received_uuid` matching the source and received snapshots, the independently observed filesystem UUIDs, `read_only_verified=true`, and zero sender/receiver exit statuses. The receipt directory owner is `richard`, mode `0700`.

| Accepted checkpoint | Receipt source UUID | Historical parent | Parent source UUID |
| --- | --- | --- | --- |
| `20261013-171228Z` | `340674cc-d02c-244e-b7ec-e3ea5a6b151f` | `20261013-140006Z` | `c0b81383-bdfc-224e-97b1-90ceee4d54f0` |
| `20261018-165453Z` | `087c906a-0518-e34a-88f7-40a5b693c41a` | `20261018-030006Z` | `f91b322a-4aa7-ad45-a766-d7a1e2eb15b9` |
| `20261021-030006Z` | `c0ad8538-dc61-bc48-8922-6c37eaf1a902` | `20261020-030026Z` | `2239b0bd-b483-884e-8a14-30dcbb8d8392` |

`mars` no longer lists the historical `20261013-140006Z` and `20261018-030006Z` parents; it still lists `20261020-030026Z` as ID 20954, UUID `2239b0bd-b483-884e-8a14-30dcbb8d8392`. This is not by itself a replication defect: the older received children have been accepted. `backup` still lists **all three** historical parents, with `received_uuid` equal to the receipt's parent source UUID:

| Parent | `backup` subvolume ID | Received UUID check |
| --- | ---: | --- |
| `20261013-140006Z` | 55708 | MATCH |
| `20261018-030006Z` | 55789 | MATCH |
| `20261020-030026Z` | 55792 | MATCH |

The currently pinned snapshot `20261021-030006Z` is present and read-only on both hosts (received as @data), and has an accepted receiver receipt. Historical receipt parent references do **not** automatically require permanent protection of every earlier source snapshot, nor do these observations guarantee future incremental sends.

## Original operator logs

- `protection/backup/note(20261021-131622).txt` — receipt directory, three receipt bodies and checksum.
- `protection/mars/note(20261021-131715).txt` — historical source parent presence/absence.
- `protection/backup/note(20261021-131807).txt` — historical receiver parents and received UUIDs.

SHA256 of original bytes:

- `note(20261021-131622).txt`: `41798b667f1f43e1fdbc4b0fd78ce9de17c06391d3094f5e6d979eefb9afd7aa`
- `note(20261021-131715).txt`: `a9173768191641fd474967985003cb004962d0c8c33897d47e6203f96c7bde6f`
- `note(20261021-131807).txt`: `8d3462e53b35e0a430e6da635d85a16bdf0d1d72bfb67eddb82e9b351fb948f5`

## Next decision gate

Implement a **separate, offline, fail-closed qgroup safety assessment** using already validated manifests, without any removal commands or deletion authorisation. Exclude active/pending/higher-level/related/limited/ambiguous qgroups, explicitly report unmatched observational candidates and all known protected snapshot IDs, retain evidence fingerprints, and require a fresh independent live check and explicit approval before any future remediation. Do not equate zero use or missing source parents with removal safety. Review mechanism/recurrence and recovery limitations independently.
