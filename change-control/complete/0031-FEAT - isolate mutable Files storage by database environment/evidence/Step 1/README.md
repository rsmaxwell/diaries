# 0031 Step 1 — Frozen effective dataset/storage mapping

Completed 2026-10-01. Step 1 records the pre-0031 storage topology and freezes the invariant that subsequent implementation must preserve:

```text
one effective durable database dataset <-> one effective mutable Files root
```

No application code, database content, MQTT retained state, NAS file, deployment, or developer-owned configuration file was changed by this step.

## Result

**Step 1 complete.** The current topology contains two durable database datasets relevant to this feature:

1. one intentionally shared **local** dataset selected by the ignored `local.env` override (`DIARIES_DB_DATA_DIR=./data/database/common`) and used by `development-infrastructure`, `local-docker-build`, and `local-published-smoke`; and
2. the separate **production** database dataset backed by the production Compose volume `diaries-db-data`.

The three local modes intentionally share the same physical mutable Files tree as each other. The defect frozen by 0031 is that the production dataset currently resolves to that same physical NAS `.../diaries-content/files` tree as well. Therefore the current topology violates the invariant across the local/production dataset boundary even though the local-to-local sharing is valid.

The retained MQTT trees do not define durable dataset identity. Each mode has its own broker/runtime storage while using the same application topic namespace (`diaries/#` plus `diaries-sync/#` for responder synchronisation). This is compatible with the invariant because retained state can be rebuilt from the database.

## Effective local override precedence

The committed mode file is loaded first and the ignored `local.env` second:

```text
mode-specific .env
        then
local.env
        => local.env wins
```

The current local dataset selection recorded for this feature is:

```text
DIARIES_DB_DATA_DIR=./data/database/common
```

The actual ignored `local.env` was deliberately not copied into evidence because it can contain credentials. The selection above is the non-secret current override already established by the 0031 feature definition and is consistent with `config/environments/local.env.example` and the responder documentation. The evidence therefore records the effective selection without archiving secrets.

## Current topology conclusion

| Relationship | Database sharing | Files sharing | Classification |
| --- | --- | --- | --- |
| development-infrastructure ↔ local-docker-build | Yes — common local DB data directory | Yes — same NAS Files tree | intentional and valid |
| development-infrastructure ↔ local-published-smoke | Yes — common local DB data directory | Yes — same NAS Files tree | intentional and valid |
| local-docker-build ↔ local-published-smoke | Yes — common local DB data directory | Yes — same NAS Files tree | intentional and valid |
| any local mode ↔ production | **No** — separate durable database dataset | **Yes** — same NAS `.../files` tree | **accidental and invalid** |

This is the baseline that Step 2 must turn into an explicit final dataset-to-Files-root map. Step 1 does not choose the replacement directory names and does not move or copy any files.

## Evidence files

- `CURRENT-MAPPING.md` — per-mode mapping of committed defaults, effective dataset identity, Files selection, physical storage and MQTT runtime.
- `REDACTED-EFFECTIVE-CONFIG.md` — only the non-secret configuration selections needed to identify the datasets/roots.
- `SOURCE-EXTRACTS.md` — exact source anchors that establish override precedence, implicit Files mounts, direct responder configuration ownership, current local sharing, production mounts, and MQTT namespaces.
- `SOURCE-IDENTITIES.txt` — hashes of the uploaded Diaries and Playbooks source bundles and the included production database backup used only to confirm the logical production database name.
- `SOURCE-SHA256SUMS.txt` — hashes of the specific source files relied on by this evidence.
- `SHA256SUMS.txt` — hashes of this Step 1 evidence package, excluding the manifest itself.

## Scope limitations recorded rather than hidden

The developer-owned `%USERPROFILE%\.diaries\responder.json`, Docker responder JSON and ignored `local.env` are intentionally outside the source bundle. Their secrets are not reproduced here. The committed source nevertheless establishes that the direct Windows responder uses `%USERPROFILE%\.diaries\responder.json`, and the responder documentation explicitly records that, under the common local database override, all three local responder configurations address the same physical NAS Files tree.

Production host/group variables and vault values are also outside the supplied Playbooks bundle. The production templates are sufficient to identify the durable database volume (`diaries-db-data`), the responder database service (`diaries-db:5432`), and the implicit mutable mount `${DIARIES_NAS_CONTENT_PATH}/files -> /data/files`. The included production dump identifies the logical database as `diaries`; no production system was contacted.

These limitations do not prevent the required Step 1 conclusion: there is one effective common local database dataset and one separate production database dataset, while both currently resolve to the same mutable physical Files tree.
