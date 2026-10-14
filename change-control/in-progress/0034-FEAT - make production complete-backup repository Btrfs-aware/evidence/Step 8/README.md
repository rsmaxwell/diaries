# 0034-FEAT Step 8 — Update Playbooks configuration, source regression and operator guidance

**Status:** **CLOSED — 2026-10-09 (source/configuration and operator-guidance step).**  
**Date:** 2026-10-09.

## Implemented Playbooks contract

Step 8 converts the Step 4/6 design into permanent Playbooks configuration without executing a backup, transfer, snapshot or restore.

- Adds `diaries_complete_backup_published_root`, defaulting to `{{ diaries_project_dir }}/data/diaries-backup`, and renders it as `DIARIES_COMPLETE_BACKUP_PUBLISHED_ROOT`.
- Keeps the Step 2 legacy timestamp-ID repository, restore-state root and storage-mode inputs. The direct Step 3 reflink-on-`pluto` strategy is explicitly historical/superseded rather than silently deleted.
- Requires the legacy repository, restore-state root and stable publication path to be absolute, distinct and non-overlapping, and rejects a stable publication path that overlaps a locally-resolved mutable source Files root.
- Changes the `diaries-backup` restore selector to resolve through the explicit stable publication path. Historical `<backup-id>` restore continues to resolve beneath the legacy repository; explicit snapshot paths remain unchanged.
- The default stable publication path is deliberately outside `data/dataset-backups/production`, matching the Step 4 design. The Step 6 live pilot path beneath the repository remains valid evidence of the pilot only; Step 9 owns the non-destructive production migration to the final configured path.

## Permanent `local-backup` reconciliation

The Step 6 helper remains in the role source for compatibility, but the generic root machine-script synchronization now explicitly excludes `diaries-pull.py`; only the dedicated opt-in task may install it.

Permanent role integration now:

- defaults `diaries_pull_install: false`;
- installs `diaries-pull.py`, `complete-dataset-publisher.py`, `complete-dataset-manifest.py` and a configured `diaries-pull.sh` wrapper under the normal SSH user's `~/scripts/backup` only after explicit opt-in;
- owns the installed files as the normal Ansible/SSH user (`richard` on the accepted Step 6 topology);
- creates no cron job, timer, service, transfer or snapshot;
- makes old `/root/scripts/backup` Step 6 helper cleanup a separate `diaries_pull_cleanup_legacy_root: true` opt-in.

The permanent regression also records the delete-scope audit: the scheduled local user/root home jobs write below `/media/usb/@data/backup/mars`, so their `--delete --delete-excluded` cannot delete the sibling `/media/usb/@data/backup/pluto` Diaries receiver. The historical remote job reads the whole local backup root and deletes only on its **remote `backup` destination**. Runtime `--dry-run` evidence remains advisable before any future unattended activation because deployed scripts may differ from source.

## Source regression coverage

New permanent `verify-production-publication-contract.py` proves the stable publication variable, generated `.env`, runtime consumption and non-overlap guards. `verify-diaries-pull.py` is upgraded to enforce normal-user ownership, disabled-by-default installation, no scheduling, private incoming-tree delete scope, legacy-root cleanup opt-in, and the existing scheduled rsync destination boundaries.

The complete Step 8 regression set is listed in Playbooks `verification/0034-step8/README.md`. It deliberately includes the existing manifest, publisher/concurrency, receiver validation, backup/restore semantics, historical Step 3 compatibility, complete-tooling, restore-source compatibility, storage-isolation and deployment-contract suites. No historical test is silently removed.

## Operator guidance and failure/rollback rules

Playbooks documentation now covers:

- manual stable publication and verification;
- duplicate `backupId` refusal;
- abort/failure semantics and last-good pointer preservation;
- receiver validation and `snapshotEligible=false` boundary;
- generation cleanup and disk-pressure rules;
- source/deployed-script synchronization expectations;
- existing `mars` rsync deletion scope; and
- non-destructive configuration rollback.

An Ansible role deployment must install/configure only. It must not implicitly capture, publish, pull, snapshot or restore a dataset.

## Acceptance evidence and closure

On 2026-10-09, `mango` ran the complete eleven-command source-regression suite and every suite reported `PASS`. The subsequent four-file `python3 -m py_compile` check completed without an error. See `RUNTIME-MANGO-REGRESSIONS-20261009.md` for the evidence summary and `CLOSEOUT.md` for closure decision and outstanding Step 9 gates.

**Step 8 is CLOSED.** **Do not deploy the Step 8 production configuration to `pluto` yet**: the new default `DIARIES_COMPLETE_BACKUP_PUBLISHED_ROOT` differs from the transitional Step 6 live pilot path. Step 9 owns controlled migration/deployment and first production publication at the new path.
