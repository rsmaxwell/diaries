# Prepared Step 4 change summary

## Removed from the live Windows script tree

Seven completed-feature directories:

```text
scripts/windows/0031-step8/
scripts/windows/0031-step9/
scripts/windows/0031-step10/
scripts/windows/0031-step11/
scripts/windows/0031-step12/
scripts/windows/0031-step13/
scripts/windows/0031-step16/
```

Eight historical validation files classified `ARCHIVE` by Step 2 are also absent from the prepared live validation tree. Their archived copies were verified through the Step 3 manifest.

## Promoted

Fourteen permanent validation/helper files are present at the exact feature-neutral destinations frozen by Step 2. `smoke-imagefragment-reader.cjs` imports the promoted helper names.

The original mixed `verify-0031-step11.py` was not merely renamed: its historical Step 11 capture/runbook assertions were removed from the live successor. `verify-effective-dataset-diagnostics.py` keeps only current diagnostics, local mode, Compose and stable `/files` assertions.

## Unchanged operational areas

Byte-for-byte comparison against the Step 3 baseline confirms these directories are unchanged:

```text
scripts/windows/common/
scripts/windows/development-infrastructure/
scripts/windows/local-docker-build/
scripts/windows/local-published-smoke/
```

Only their parent Windows README was updated to stop advertising completed-feature live tooling.
