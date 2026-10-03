# 0031-FEAT Step 9 Windows tooling

`reconcile-local-shared-files.bat` performs the local half of Step 9 against the
frozen pre-split `files` tree. It is deliberately dry-run/read-only.

The normal local configuration now points at the future dataset-specific Files
root (normally `files-development-common`). Step 9 must not change `local.env`
back to `files`. Instead the wrapper:

1. proves the Step 8 local responder write freeze is still in force;
2. requires exactly one local Diaries database container to be running;
3. validates the normal effective database/Files target pair;
4. invokes the Step 4 `prepare-responder-config.bat` path;
5. derives a temporary config from that generated config with only
   `diaries.files` changed to the frozen pre-split selector `files`;
6. runs the existing 0024 Image reconciliation in dry-run mode only;
7. separately inventories and SHA-256 hashes `.image-staging`; and
8. writes `STEP9-REPORT.json` and `STEP9-REPORT.md` with the required counts.

No 0024 apply is performed. No Image row or Files byte is changed.

Run from the Diaries project root after Step 8 is complete and while both
responder write paths remain frozen:

```bat
scripts\windows\0031-step9\reconcile-local-shared-files.bat
```

The default evidence location is:

```text
change-control/in-progress/0031-FEAT - isolate mutable Files storage by database environment/evidence/Step 9/runtime/local-<dataset>-<timestamp>/
```

If `local.env` selects `./data/database/common`, this one run represents all
three intentionally shared local launch modes. Do not repeat it for
`local-docker-build` and `local-published-smoke` against the same database.

A successful script exit means the read-only reconciliation ran and evidence was
captured. It does not mean Step 10 is automatically safe. Inspect
`requiresExplicitDisposition` / `step10Ready` in `STEP9-REPORT.json`.
