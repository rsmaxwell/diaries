# 0028-FEAT — Read-only writer access assessment before a maintenance window

Prepared 24 November 2026. This is a **read-only discovery** increment after the committed 0028 change-control handoff, not permission to stop services or apply a migration.

## Existing accepted evidence

The 71-conversion isolated migration and GUI rehearsal passed. The matching retained backup `production/20261124-003112Z` was verified on `mars` and `backup`; its custom-format PostgreSQL dump was restored into a network-disabled PostgreSQL 18 container, with 2,331 Fragments, 2,270 Marquees, 85 Images and 683 Pages. Three Files payloads were hashed. Java 25 compatibility, pinned temporary migration JAR, and parent/submodule identity were separately checked. The change-control source commit is `7e51b62` and the responder source revision is `7aa6296`. No production apply has been authorised.

## Why a new targeted probe is necessary

The older writer survey showed a published PostgreSQL host port and two connections. It did **not** prove that new clients can be excluded, nor did it identify the maintenance actions needed for backup service, container restart policy and Files NAS writers. This tool captures the presently active service/container state, published port bindings, *SELECT-only* PostgreSQL connection inventory and redacted mount targets, without reading secrets or changing production.

From **Windows 11 Cygwin**, in the Diaries parent repository:

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
python3 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tests/test_0028_step3_writer_access_window.py'
python3 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/inspect-0028-step3-writer-access-window.py'
```

The probe reads `pluto` over existing SSH, uses Docker inspect *only for selected safe fields*, `systemctl show` for three known units, and a single SQL `SELECT` from `pg_stat_activity` inside `diaries-postgres`. It writes full connection data only to feature-local ignored `evidence/Step 3/private/…-writer-access-window/`. It does not print passwords, runtime environment variables, live SQL statements, production configs, host mount sources or user-provided diary content. The output includes `WRITER-ACCESS.json` and `READOUT.md`. Send the terminal log and, if further diagnosis requires it, a suitably redacted `READOUT.md`, **not** the full JSON containing client IPs or names.

## Production controls still requiring owner authorisation

- Control authoring / MQTT RPC ingress and safely stop the responder without invoking `diaries-compose.service`'s broad stop (which removes shared routing and brings down all Compose services).
- Inspect current direct SQL sessions and port binding, select a reversible method to prevent new non-maintenance SQL clients and *test denial*. Zero current sessions alone is not proof.
- Coordinate `diaries-complete-backup-publish.timer` and active `.service` to avoid a surprise responder restart.
- Confirm no independent NAS/Files writers remain. The responder's `/data/files` mount is RW in the source Compose contract.
- After genuine writer isolation and explicit maintenance approval, generate a fresh consistent DB+Files backup, verify it, transfer and protect immutable Btrfs snapshots on `mars` and `backup`.
- Recheck the 72 legacy occurrences, generate a new production dry-run plan and request formal separate approval before installing journal or applying.

**Do not run service-stop, firewall, backup-creation, snapshot, SQL journal, migration apply or restore commands during this read-only discovery.** A Git push of parent commit `7e51b62` is a separate source-publication action; its success is not assumed from earlier logs.
