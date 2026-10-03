# 0031-FEAT — Step 7 evidence

## Result

**COMPLETE — 2026-10-02.**

Step 7 now defines and enforces matched database + Files backup/restore semantics
for the local Windows tooling and the production Playbooks helpers.

Local backup identity is derived from the effective database dataset after the
mode environment and `local.env` have been applied. This means the normal
`./data/database/common` + `files-development-common` override produces one
`data/database-backups/common` namespace regardless of which local launch mode
invokes the database backup.

All database backup/restore helpers now clearly label themselves
`DATABASE-ONLY`, report the matching Files selector/root, and do not claim to
back up or restore mutable Files bytes.

New database backups write a `.dataset.json` sidecar. Sidecar-backed restores
reject a database backup whose recorded durable dataset/Files identity differs
from the current effective pair. Legacy dumps without a sidecar remain usable
with an explicit manual-Files verification warning.

Production applies the same contract through the deployed
`dataset-backup-manifest.py` helper. Its regression test writes a real temporary
manifest, verifies the matching pair, then changes the Files selector and proves
that verification rejects the mismatch.

The actual pre-migration Files snapshot is intentionally **not** taken in Step 7.
That is Step 8 work, where writes are frozen and the real database + Files
recovery artifacts are captured together.

## Verification

Portable Diaries verification:

```text
python scripts/windows/validation/verify-0031-step7.py
```

Result: PASS. See `verification-output.txt`.

Portable Playbooks verification:

```text
python roles/diaries/tests/verify-0031-backup-semantics.py
```

Result: PASS. See `playbooks-verification-output.txt`.

All changed production shell helpers also pass `bash -n`; see
`playbooks-shell-syntax.txt`.

The packaging environment cannot execute Windows `.bat`/PowerShell against the
real Docker/PostgreSQL/NAS setup. Step 8 will exercise the backup path against
the real frozen dataset while creating the required pre-migration backups.

## Data safety

No PostgreSQL database, NAS Files tree, Docker volume, retained MQTT state or
production inventory was modified while implementing or verifying Step 7.

## Completion decision

Step 7 is complete because:

- database-only backup and restore operations are explicitly labelled and cannot be mistaken for a complete dataset backup;
- backup identity is derived from the **effective** database dataset after local overrides, so intentionally shared local modes use one durable backup namespace;
- every new database backup records the matching Files selector/root in a sidecar;
- sidecar-backed restores reject a database/Files mismatch before destructive restore work;
- legacy backups require an explicit manual-Files verification warning;
- equivalent semantics are implemented for the production Playbooks helpers; and
- the portable Diaries and Playbooks regression checks pass, with the production shell helpers also passing syntax validation.

The Step 7 completion criterion is therefore satisfied. The absence of an actual Files snapshot is **not** a Step 7 gap: freezing writes and capturing the real matched database + Files recovery artifacts is explicitly Step 8.
