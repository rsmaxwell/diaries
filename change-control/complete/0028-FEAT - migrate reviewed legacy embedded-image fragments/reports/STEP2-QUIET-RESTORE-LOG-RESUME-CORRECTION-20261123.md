# Step 2 isolated rehearsal — zero-byte `pg-restore.log` resume fix (23 November 2026)

## Observed failure

The `--resume-restored` run stopped before any image staging or database write with
`FAIL: missing original restore evidence: pg-restore.log`. The original 15:57
runner redirected `pg_restore` stdout/stderr into this file, and successful
`pg_restore` with default (quiet) output may leave the log **empty**. The new
resume guard used `-s` (non-empty), which incorrectly treats an empty, existing
success log as missing.

## Narrow correction

Require `-s` for the dump, its SHA-256 receipt, the fragment-count receipt and
Docker identity receipt, but require only `-f` for `pg-restore.log`. A missing
restore log still blocks resume. All other protections remain in place: the
production-dump SHA-256 verification, isolated Docker container/volume/image/
localhost-port checks, PostgreSQL 18 and fragment count 2331, and no preexisting
migration journal. No file is forged, removed or overwritten.

The runner includes a new non-mutating test for the resume evidence predicate.
It is intended to reuse the preserved `20261123T155735Z-isolated-db-rehearsal`
restore; no new production dump or restore is required if all identity checks
succeed. On any guard failure, STOP; do not bypass it or run production apply.

## Scope

One existing feature-local Bash runner, one new feature-local regression test,
and this diagnostic report. No changes to Java, databases, MQTT, application
code, existing private evidence or the Playbooks repository.
