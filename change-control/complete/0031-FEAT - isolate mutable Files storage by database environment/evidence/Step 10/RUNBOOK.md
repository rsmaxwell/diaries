# 0031-FEAT — Step 10 runbook

## Purpose

Create and verify the candidate mutable Files root for the current independent
non-production dataset while preserving the frozen production/shared source and
rollback snapshot.

With the normal local override, run Step 10 **once** for the shared local
`common` dataset. Do not create three copies for the three launch modes.

## Preconditions

Before running:

1. Step 8 is complete and its NAS snapshot still exists under
   `.0031-backups/step8-*`.
2. Step 9 is complete and the `Thumbs.db` / zero-byte `catalogue.lock`
   disposition remains valid.
3. The local responder write freeze is still in force.
4. The production responder write freeze on `pluto` is still in force.
5. `config/environments/local.env` still contains the intended paired common
   override:

```text
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

Do not restart either responder before Step 11.

## Run source verification first

From the Diaries project root:

```bat
python scripts\windows\validation\verify-0031-step10.py
```

Expected final line:

```text
PASS: 0031-FEAT Step 10 Files-root seeding tooling verified
```

## Create the common local candidate root

Run:

```bat
scripts\windows\0031-step10\seed-local-files-root.bat -ProductionWriteFreezeConfirmed
```

The switch is an explicit operator assertion that the production freeze remains
active; the Windows script cannot inspect the remote production responder.

The script should report a final result similar to:

```text
RESULT: CANDIDATE ROOT READY. Review SOURCE-ACL.txt and TARGET-ACL.txt before closing Step 10. Keep both responder write paths frozen.
```

## What the script is expected to do

It will resolve the effective pair, which should be:

```text
Database: ./data/database/common
Files:    files-development-common
```

It then:

- proves the current shared `files` tree still matches Step 8 exactly;
- excludes `.image-staging` according to the Step 9 disposition;
- copies all remaining bytes to a temporary sibling root using `robocopy`;
- verifies the complete SHA-256 inventory before promotion;
- renames the verified temporary root to `files-development-common`;
- performs a temporary create/write/read/delete permission probe;
- verifies the probe leaves the target inventory unchanged; and
- captures source and target ACL/SDDL evidence.

If `files-development-common` already exists, the script stops rather than
merging into it. Do not bypass that guard. Inspect why it exists first.

### Windows mapped-drive fallback used for the completed run

On the migration workstation the default `\\nas.localdomain\photo\...` UNC
path was not accessible even though the NAS content was available through the
mapped `P:` drive. The successful Step 10 run therefore used the supported
explicit path switches:

```bat
scripts\windows\0031-step10\seed-local-files-root.bat ^
  -ProductionWriteFreezeConfirmed ^
  -SharedFilesRoot "P:\nancy-and-ronald-maxwell\documents\sea-captains-chest\diaries-content\files" ^
  -TargetFilesRoot "P:\nancy-and-ronald-maxwell\documents\sea-captains-chest\diaries-content\files-development-common"
```

This changes only how the Windows migration tool reaches the same NAS content;
it does not change the configured dataset/Files selector contract.

## Review the result

Open the newly created Step 10 runtime evidence directory and check:

```text
STEP10-REPORT.md
STEP10-REPORT.json
SOURCE-ACL.txt
TARGET-ACL.txt
```

The report must show an exact approved-seed/target inventory match and a passing
permission probe.

Compare the source and target ACL evidence (and, if appropriate, the NAS share
permissions) to ensure the new candidate has not become unexpectedly more
broadly writable. The script proves practical create/write/read/delete access
for the migration account, but it cannot infer your intended NAS user/group
policy from ACL text alone.

## Stop point

Do **not** restart a responder yet. Keep both write paths frozen and retain:

```text
.../diaries-content/files
.../diaries-content/files-development-common
.../diaries-content/.0031-backups/step8-*/
```

unchanged.

Once the evidence and permission review are satisfactory, Step 10 can be closed
and Step 11 can repoint/verify the local runtime paths.
