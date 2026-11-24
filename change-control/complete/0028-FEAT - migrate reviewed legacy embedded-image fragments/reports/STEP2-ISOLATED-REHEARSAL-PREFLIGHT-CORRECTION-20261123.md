# 0028 Step 2 — isolated rehearsal preflight and resume correction (2026-11-23)

## Observed terminal evidence

The 15:57 UTC rehearsal (`20261123T155735Z-isolated-db-rehearsal`) ran eight helper tests and verified the prepared manifest hashes. Media staging incorrectly rejected **72** rows as though all rows were conversions; the approved Step 1 image-decisions contract deliberately includes **71 conversion rows and one `DEFER` (Fragment 1564)**. The original runner then incorrectly continued despite this failure, restored 2,331 Fragments into its new isolated PostgreSQL 18 container, and failed configuration creation because the staged Files-root had never been produced. Java subsequently reported the missing configuration path; it did not produce a plan or run `apply`.

The primary shell bug was the use of an outer `( ... ) && success || failure` expression. When the whole subshell is an AND/OR list test, Bash can ignore its internal `set -e`; an error therefore did not stop subsequent stages. The failure must never be treated as passed simply because the script advances.

## Corrections

- The media-staging helper validates exactly 72 rows, permits exactly 71 `REMOVE_AS_IMAGE` entries and one unmapped `DEFER` entry for Fragment 1564, and stages only the 71 reviewed conversion images (deduplicated by validated path/checksum). Unreviewed actions, duplicate Fragment IDs, mismatched checksums, or resolved media on `DEFER` fail closed.
- The standalone Bash runner now uses effective fail-fast and an EXIT failure report. No Docker creation, production dump, config, plan or migration operation follows a failed staging step.
- `--resume-restored <prior-evidence-folder>` reuses only an independently identified running `diaries-0028-rehearsal-db` from a **pre-migration restored** rehearsal: previous private pg_dump SHA-256 receipt and restore count are checked; exact label/image/mount/labelled volume/localhost port/PostgreSQL 18 are checked; and the journal must not yet exist. It creates new dated evidence, never alters or overwrites the old failed evidence, and **does not repeat pg_dump/pg_restore**.
- A resume with an existing migration journal is refused; there is no automatic cleanup, no deletion of the previous Docker volume, and no production approval.

## Execution (Windows PC, Cygwin)

Apply the ZIP at the Windows Diaries parent checkout root using Beyond Compare 4. The previous labelled database must still be running with its original volume and the earlier private evidence must exist.

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'

bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/rehearse-0028-step2-isolated.sh' \
  --resume-restored 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/evidence/Step 2/private/20261123T155735Z-isolated-db-rehearsal'
```

If the restored instance has been removed, the script will refuse this resume. Do not automatically delete backups or evidence. A separate clean rehearsal requires the existing reserved container/volume to be explicitly reviewed first.

## Validation evidence for the corrective ZIP

- Python rehearsal-fixture tests: 11 PASS, including new real-contract 72-row, unexpected-DEFER and mapped-DEFER negatives.
- Bash syntax: PASS.
- Mocked runner failed-media test: nonzero exit, failure logged, **no Docker run** and no advancement to DB creation.
- ZIP integrity and repository-relative package scope: PASS.

The corrected runner has **not** yet been executed against the user's real Docker database or images. The outstanding migration-engine PostgreSQL integration, rollback/idempotence, MQTT replay and Reader/Editor visual gates remain OPEN.
