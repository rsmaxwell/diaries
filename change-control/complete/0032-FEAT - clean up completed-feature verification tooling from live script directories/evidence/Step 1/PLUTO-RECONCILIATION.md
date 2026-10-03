# 0032 Step 1 - `pluto` production inventory reconciliation

## Result

**PASS — the deployed production script inventory is fully explained. Step 1 may be closed.**

The runtime capture was taken on `pluto` at `2026-10-03T12:39:30+01:00` from:

```text
/home/richard/projects/diaries/scripts
```

It contains **23 files**.

## Reconciliation against Playbooks

The frozen Playbooks `roles/diaries/files/sync/scripts/` inventory contains **14 files**. All 14 filenames are present on `pluto`.

Of those 14 synchronized files:

- **13 are byte-for-byte identical** by size and SHA-256;
- **1 differs:** `README.md`.

The differing documentation file is:

| File | Playbooks source | `pluto` deployed |
| --- | --- | --- |
| `README.md` size | 9917 bytes | 8298 bytes |
| `README.md` SHA-256 | `b5c5b133be19a18da512ef32aaa5deb92fc0a31ae2c0ce52ae907808450203dc` | `3c86b04cf95dc71143cd0e70085e75e37563b6db08a4eb2e707a9f5b79e7ca82` |

This is known source/deployment documentation drift, not an unexplained executable or cleanup candidate. It does not block the Step 1 inventory/reference freeze. A later deployment/cleanup step may naturally bring the deployed README back into line with source.

## Expected deployed-only files

The remaining **9 files** are not in `files/sync/scripts/` because `roles/diaries/tasks/copy.yaml` renders them from templates directly into the production `scripts/` directory:

```text
logs.sh
shell-prompt-client.sh
shell-prompt-database.sh
shell-prompt-mosquitto.sh
shell-prompt-nginx.sh
shell-prompt-responder.sh
start.sh
status.sh
stop.sh
```

These are therefore expected permanent operational files, not stale deployed leftovers.

## 0031 production cleanup candidates confirmed deployed

The runtime capture confirms that every 0031 production helper identified by Step 1 is currently deployed and is byte-identical to the frozen Playbooks source:

```text
step8-capture-production-database-backup.sh
step8-freeze-writes.sh
step9-reconcile-production.sh
step12-compare-reconciliation.py
step12-reconcile-production.sh
step13-capture-production-control.sh
step14-production-deployment.sh
```

`migration0024ImageCatalogue.sh` is also deployed and byte-identical to source. Its Step 2 disposition remains intentionally `PENDING` until the feature makes the explicit supported-vs-historical decision required by the implementation plan.

## Stale-file check

There are **no unexplained deployed-only files** in the captured production `scripts/` directory.

The deployed filename set is exactly:

```text
14 files from roles/diaries/files/sync/scripts/
+
9 operational scripts rendered from roles/diaries/templates/scripts/*.j2
=
23 deployed files
```

The Playbooks synchronization intentionally does not use unrestricted `--delete`, but the Step 1 runtime capture shows no residual script outside the currently explained deployment model.

## Step 1 closure decision

The production evidence gate is satisfied because:

1. the exact deployed inventory has been captured;
2. every deployed filename has an identified source/deployment mechanism;
3. every 0031 production cleanup candidate has been confirmed present and fingerprinted;
4. there are no unexplained active/deployed files;
5. the only checksum drift is the non-executable production scripts README and is explicitly documented;
6. no live file has been moved, renamed or deleted.

**Step 1 — Freeze the live tooling inventory and find every reference: COMPLETE.**
