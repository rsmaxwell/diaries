# 0028-FEAT — Step 3: retained recovery contents and writer-isolation gate

**Prepared:** 24 November 2026. **Status:** read-only verification package; live contents inspection, writer isolation, fresh recovery point, owner approval and production application **remain OPEN**.

## Accepted observations; do not repeat expensive work

- 71 reviewed conversions, 1 deferred Fragment 1564; 30 preserved original image hyperlinks; 22 preserved Marquees. Step 1 technical review passed; **formal owner acceptance remains open**.
- Step 2 isolated PostgreSQL migration, controlled date rollback, resume, idempotence, 71+71 journal rows, MQTT replay, Reader original scans, Editor GUI and representative original image-link click passed. 0053-DEF records separate undo-to-original lock-release behaviour.
- At `2026-11-24T09:53:20Z`, fresh production source preflight was `PASS_SOURCE_FRESHNESS`, NAS Files `70/70`, locks `0`. This is a point-in-time check and is **not** the final writer-stopped preflight.
- `sudo -n /usr/local/sbin/diaries-backup-status --limit 5` succeeded on **both `mars` and `backup`**; each reported `HEALTHY`, `0` manifest conflicts, and latest logical dataset `production/20261124-003112Z`. Local `mars` last retained occurrence was `10:00:09Z`; receiver `backup` last retained occurrence was `03:00:20Z`. The different occurrence timestamps are *not* backup ID differences.
- Running the same status/history commands as the unprivileged SSH user fails because `/etc/btrfs-snapshot-manager.json` is intentionally restricted. Do **not** weaken its permissions. The earlier audit interpreted empty stdout as invalid JSON. This package fixes the feature-specific probe to use `sudo -n`, and requires a successful host-local status exit before interpreting healthy results.

## New verification script

From **Windows PC — Cygwin**, after applying the package in the Diaries parent repository:

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/verify-0028-step3-retained-components.sh'
```

It runs two `sudo -n` *read-only* queries per host under existing SSH privileges and stores receipts at `evidence/Step 3/private/<timestamp>-retained-components/`:

1. `diaries-backup-status --json` on each host; require zero exit, healthy status, same latest logical dataset and backup ID, zero reported conflicts.
2. `diaries-backup-history --json show <backup-id> --logical-dataset production` on each host to select one existing retained occurrence. Verify every occurrence for that backup reports the same manifest SHA-256.
3. Verify the selected retained `dataset-manifest.json` SHA-256, schema version, backup ID, database custom and SQL dump **presence and declared file sizes**, database hash list, Files directory, inventory, Files SHA-256 list and three bounded sample Files paths/sizes. Verify small metadata hash lists against the manifest and inventory. All reads stay within the retained snapshot: reject symlinks and unsafe relative paths.
4. Compare retained **manifest SHA-256, two database dump metadata descriptors, Files count/bytes and metadata hashes** across both hosts; fail closed if they differ. Print no passwords or media contents. A success receipt is `MATCHING_RETAINED_COMPONENT_METADATA`, **not** a restored-backup acceptance.

**Limitations by design:** This bounded inspection does not hash all file payload bytes, extract PostgreSQL dumps, restore a database, verify every Files payload byte, prove a pre-migration fresh recovery point or stop any writer. Full dataset schema-2 verification, where required, is provided by the existing `diaries-backup-history verify` command and `restore-dataset.sh preflight`; these may be expensive and must be scheduled deliberately rather than repeated at each audit. A prior accepted restore rehearsal may be used where its method and source are demonstrably equivalent.

## Production writer-isolation plan — design only, not executed

Before any separate production authorisation, review the *live* `pluto` inventory captured in `20261124T100044Z-recovery-writer-inventory/pluto-runtime-and-backup-metadata.log` (or rerun the corrected read-only collection if needed). The Playbooks source is only a design input; use live Compose services/ports and actual container digests for execution.

- **User-facing ingress:** A shared Nginx route serves Editor and Reader. The route must be in maintenance mode before the writer stop; simply stopping the responder can leave requests failing rather than cleanly blocked. Do not use the general `stop.sh` unreviewed: it removes the entire Compose stack including the PostgreSQL database needed by the migration.
- **Application channels:** Stop/drain `diaries-responder` and prevent MQTT RPC writers from restarting or publishing while work is underway; the editor uses browser WebSockets via MQTT. Reader has a read-only projection but is not a writer-isolation guarantee. Confirm current service roles and restart policies, including systemd/Compose supervision.
- **Direct SQL writers:** The production Compose template publishes PostgreSQL to a host port (default 5433). The observed absence of active Fragment locks **does not rule out SQL writers**. Determine all database clients and direct network access, and choose an effective reversible database-write exclusion mechanism before approving execution. Confirm PostgreSQL remains running for the migration CLI and that only its authorised session can write. Do not assume broker isolation alone covers this channel.
- **Backup collision:** Check `diaries-complete-backup-publish.timer/service` and any scheduled maintenance before the release. Its capture procedure may restart the responder; a production run must coordinate a maintenance window and a fresh complete database+Files recovery point. No timer or backup process is stopped by this package.
- **Final freshness:** Once all writers are verifiably isolated and a fresh complete recovery point is recorded, rerun the Step 3 source comparator, validate 70 Files SHA-256 values, 71 intended conversions and the deferred Fragment, and bind the precise manifest/plan identity to the execution authorisation.
- **Recovery procedure:** Identify the exact pinned immutable backup ID and matching DB/Files data, record a proven restoration method and stop conditions, and explicitly decide how date-level journal/replay rollback and the latest full-data restore interact. A rollback to a pre-migration backup is destructive to intervening writes, so keep the maintenance window closed and obtain explicit authorisation for any restore. Do not run `restore-dataset.sh prepare`, `apply` or `rollback` in a read-only gate.
- **Execution approval:** Separate owner approval is still required for the exact production command, software revision, backup identity, downtime and rollback terms. The migration must apply only against that plan. Postflight and MQTT retained replay must finish before reopening client writers.

## Current gates

| Gate | Status |
|---|---|
| Offline migration and integrated rehearsal | Passed; accepted evidence retained |
| Manifest and NAS source freshness, 24 November 09:53 UTC | Passed at capture time; needs final maintenance-window refresh |
| Both retained hosts healthy with common backup ID | Passed from user terminal log |
| Matching retained DB+Files component metadata | **Pending new script execution** |
| Verified fresh complete recovery point / approved rollback | **Open** |
| All production writers isolated | **Open** |
| Formal Step 1/Step 2 owner acceptance | **Open** |
| Explicit production `apply` approval | **Not authorised** |

Feature-specific tools and evidence remain under the **Diaries parent** `change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/`. There are no Playbooks changes in this package and no production writes.
