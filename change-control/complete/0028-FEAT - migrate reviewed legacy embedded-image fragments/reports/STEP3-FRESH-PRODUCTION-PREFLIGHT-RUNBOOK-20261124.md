# 0028 — Step 3 fresh production source and media preflight

**Prepared 24 November 2026. Status: prepared, NOT executed; production APPLY NOT AUTHORISED.**

## Accepted work not to repeat

- Frozen review: 72 legacy embedded-image occurrences, 71 reviewed `CONVERT_TO_IMAGE`, one `DEFER` (Fragment 1564), 30 saved hyperlinks, 22 preserved Marquees.
- Restored PostgreSQL 18 rehearsal: 71 conversions, negative approval, date-level rollback, recovery, idempotence, original Fragment identities and unrelated-data fingerprint tests PASSED (23 Nov).
- Isolated MQTT replay, Reader HTTP and manuscript scans, Editor startup/sign-in/navigation and representative IMAGE visual tests PASSED.
- Fragment 1251's original hyperlink opens on **ordinary click** in Day reader. Extra Street View navigation is a pre-existing destination-content issue, not a migration failure; preserve its URL unchanged.
- Undo-to-original lock-release issue is recorded separately as 0053-DEF; navigation-away unlock is confirmed. Do not modify or re-test 0028 conversion logic for that Editor defect.

The preceding offline audit `evidence/Step 3/private/20261124T093333Z-offline-readiness` passed, but checked **only frozen manifest integrity and Windows Git status**, not production freshness.

## Execute fresh read-only preflight

On **Windows PC, Cygwin terminal**, from the authoritative local Diaries parent checkout:

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
export DIARIES_0028_SOURCE_FILES_ROOT='/cygdrive/p/nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content/files'
bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/verify-0028-step3-production-freshness.sh'
```

Read-only operations performed:

1. Run 15 synthetic comparator regression tests and check the accepted SHA-256 manifest receipt.
2. Capture Windows parent and three submodule branch/revision/working-tree identities without altering Git.
3. Capture `pluto`'s running Diaries Docker names/tags/container IDs and locally recorded image digests (not container environment variables or passwords).
4. Reuse `step1_inventory.py` to perform **one** fresh, statement-consistent PostgreSQL `COPY (SELECT ...)` on `pluto` with `PGOPTIONS=default_transaction_read_only=on`; raw source HTML stays in private evidence. It does not connect to production MQTT or modify Postgres.
5. Compare all reviewed Fragment IDs, versions, source HTML SHA-256, embedded image source SHA-256, Page, type, date, sequence and exact candidate coverage. All reviewed Fragments must be unlocked at snapshot time. New unreviewed legacy images block the plan.
6. Verify all reviewed catalogue Image IDs/relative paths/checksums and independently rehash the corresponding files under the NAS Files-root. This is **NAS Files-root** verification; matching this to the live `pluto` Files mount remains a separate operational check.
7. For preserved Marquees, **allow** moved/resized geometry and newer Marquee versions; **block** missing, added, replaced or reassigned Marquees, changed Page or version moving backwards. The production migration must preserve the current coordinates, dimensions and version.

A successful result is `PASS_SOURCE_FRESHNESS`; it is valid only for the recorded snapshot and does not certify the production writer-stop, current backup, live Files mount, or an apply approval. Any mismatch produces `BLOCKED_SOURCE_DRIFT` and a private list of issue codes/Fragment IDs, without source HTML or URL values in stdout.

**Evidence:** under `change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/evidence/Step 3/private/<UTC>-production-freshness/`. These include a private raw production inventory. Do not commit them to public Git or include them in source ZIPs.

## Recovery and production execution gates still OPEN

After the fresh source check, and before asking for a production apply:

- Review actual `pluto` image tags and confirm that deployed responder/client/reader versions can consume 0051 IMAGE links and same-Page Marquees. The migration CLI exists only in the **local** responder checkout until deliberately released; a read-only image inventory does not prove deployed support.
- Determine and document how to stop **all** Editor/MQTT RPC writers while keeping safe read-only access. Do **not** assume closing the browser or stopping one nginx container blocks every MQTT client.
- Confirm active sessions and lock clearance at the actual maintenance window. An unlocked snapshot does not prevent a new lock from appearing later.
- Inspect the current established backup chain without changing retention/snapshots. On **Windows PC Cygwin**, if installed/current commands are available, `ssh mars 'diaries-backup-status'` and `ssh backup 'diaries-backup-status'` are starting diagnostics; their outputs require interpretation. Verify the associated production `pg_dump` and NAS Files-root recovery source and ensure a **fresh, independent, restorable** recovery point exists **at the maintenance time**. No destructive Btrfs actions are authorised by this runbook.
- Document exact backup artefact location, SHA-256 checks, Files snapshot identity, restore authorities, rollback deadline and corresponding production software versions. A successful existing historical backup must not silently replace the required fresh pre-apply recovery point.
- Obtain explicit owner signoff for Step 1 reviewed scope and Step 2 technical acceptance. This document records the user's observed GUI tests but is **not** an approval on their behalf.
- Prepare and review a maintenance runbook including separate, explicit owner approval for the actual production apply. Bind the production plan to live DB, Files-root and approved manifests; do not copy the `RESTORED_REHEARSAL` approval file to production.

Step 3 remains **OPEN** until the production migration, DB and MQTT postflight, Editor/Reader checks and restoration evidence have been accepted. 0028 feature closure is an independent Step 4 decision.
