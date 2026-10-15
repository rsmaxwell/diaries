# 0034-FEAT — Step 11.3 off-site disposable restore acceptance (Gates A–D)

**Status: CLOSED — 2026-10-14 (UTC).** This closes **Step 11.3 only**, not Step 11 or 0034-FEAT. Evidence reflects operator-provided terminal transcripts; the detailed Gate C/D JSON evidence was not supplied for independent inspection. Preserve those on `mars` and attach a redacted copy for final archival if required.

## Source lineage and frozen identity

| Item | Accepted evidence |
|---|---|
| Production generation | `20261009-154847Z`, schema 2, `production`, `complete-dataset`, status `complete` |
| Production published pointer | `/home/richard/projects/diaries/data/diaries-backup` → `.diaries-backup-generations/20261009-154847Z` (Step 11.2) |
| Held source/received snapshot | `20261013-171228Z`; source/receipt `Received UUID` `340674cc-d02c-244e-b7ec-e3ea5a6b151f` |
| Receiver Btrfs snapshot | `/@data/mars-received/@data/20261013-171228Z`, read-only |
| Acceptance receipt | `/@data/mars-received/.replication-state/20261013-171228Z.json`: `btrfs-incremental`, both transfer exit statuses 0, `read_only_verified=true` |
| Off-site generation | `/@data/mars-received/@data/20261013-171228Z/backup/pluto/.diaries-backup-generations/20261009-154847Z` |
| Disposable staged generation on `mars` | `/var/tmp/0034-step11-3/20261009-154847Z` |

## Gate A — Accepted off-site discovery: PASS (2026-10-13)

`capture-step-11-3.sh 20261013-171228Z` on `backup` confirmed the read-only received subvolume, matching source UUID and accepted receipt, discovered the exact requested schema-2 generation, and reported the `mango` Playbooks checkpoint readable. It also found an earlier `20261007-145013Z` generation manifest; that earlier generation was **not** the chosen restore candidate. Evidence directory on `backup`: `/home/richard/0034-step11-3-backup-20261013-171228Z`. No data modified.

## Gate B — Off-site schema-2 verification: PASS (2026-10-13)

Manifest on `backup`: `backupId=20261009-154847Z`, `schemaVersion=2`, logical dataset `production`, database custom dump `database/diaries.dump`, SQL dump `database/diaries.sql`, 85 Image catalogue rows, 89 durable Files, 100,032,776 Files bytes. `schema2-manifest-validator.py verify --backup-dir <off-site-generation>` returned **exit 0** and `Valid complete Diaries dataset backup manifest` with 89 Files. Initial failed commands were tool filename/CLI syntax errors and did not validate backup data; corrected invocation passed.

## Gate C — Disposable restore: PASS (2026-10-14)

The receiver `backup` has no Docker; a non-destructive copy was therefore pulled from its read-only snapshot to `mars` using SSH `richard@10.254.22.1:39263`, remote `sudo -n /usr/bin/rsync` **for read access only**. Initial non-privileged read failed on restrictive snapshot directories; no permission or ownership changes were made. Rsync completed and transferred approximately 101 MB. After relocating staging under its exact backup-ID basename, schema-2 verification passed again.

On `mars`, `postgres:18-alpine` ran in a disposable container with `--network none`, without publishing ports or mounting production volumes. `pg_restore --exit-on-error --no-owner --no-privileges` completed; all 89 restored scratch Files matched exact paths, sizes and SHA-256 hashes (100,032,776 bytes), and transient `.image-staging` content was absent. Script reported `PASS: disposable database restored and scratch Files inventory verified`; the container `d0034-rehearsal-1f236c6eee89` was removed. Evidence directory: `/var/tmp/0034-step11-3-rz1y8eof`.

## Gate D — Application-level reconciliation: PASS (2026-10-14)

An initial rehearsal stopped during PostgreSQL startup (`database system is starting up`); the temporary container was removed. The readiness check was corrected to use successful `SELECT 1` before database creation, then rerun with `set -o pipefail`. The subsequent run reported:

```
PASS: restored tables, image catalogue hashes, and 89 staged Files reconciled
Gate D exit code: 0
```

It used a fresh disposable PostgreSQL 18 container, read-only restoration source, staged Files verification, and application table/Image catalogue reconciliation. The container `d0034-gated-f03903853ff4` was removed. Evidence directory: `/var/tmp/0034-step11-3-gate-d-e68fjzur`; console log `~/0034-step11-3-gate-d.log` on `mars`. **Exact per-table row counts and the itemized catalogue JSON results were not included in the supplied terminal transcript**, and should not be invented; retain `table-counts.json`, `catalogue-reconciliation.json`, and `gate-d.json` as supporting machine-readable evidence.

## Deferred 0035-FEAT finding — history CLI configuration

On `mars`, both `sudo diaries-backup-history list --all` and `show 20261009-154847Z --logical-dataset production` returned:

```
ERROR: Diaries verification is not enabled in snapshot-manager configuration
```

The observed `/etc/btrfs-snapshot-manager.json` has `verification.required=false`, `dataset_relative_path=""`, `marker_relative_path=""`, `source_name="@data"`, and `manifest_tool=/usr/local/lib/diaries-backup/complete-dataset-manifest.py`. **History-tool integration was not demonstrated.** Direct off-site Btrfs subvolume/receipt inspection and schema-2 verification provided an independent recovery path, but do not constitute a history-CLI pass. Record configuration contract, safe dataset-relative path, and whether to enable required verification under **0035-FEAT**; do not toggle verification blindly because it can affect snapshot manager behavior.

## Safety, limitations and next steps

- Production `pluto` PostgreSQL and NAS Files were not restored into; `backup` received snapshot remained read-only. No production restart, new Diaries Docker image or production Ansible deployment required.
- The independent hold on `20261013-171228Z` must remain until explicit full-feature release. Replication parent `20261013-180016Z` remains separately protected per the earlier Step 11.1 evidence.
- Gate A–D success supports **Step 11.3 CLOSED**. Step 11 overall and feature **remain OPEN** for scheduling/operating ownership review (11.4), final regression/rollback and feature sign-off.
- Retain Gate C and D machine-readable evidence directories; do not prematurely delete the scratch copy or held snapshot.
