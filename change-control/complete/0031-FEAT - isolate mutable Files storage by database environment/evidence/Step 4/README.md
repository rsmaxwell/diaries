# 0031-FEAT — Step 4 evidence

## Step

**Step 4 — Update direct Windows development configuration and operating scripts**

## Implementation result

**CLOSED — 2026-10-02**

Direct Windows development now consumes the same effective database/Files selection as the `development-infrastructure` environment. The implementation deliberately leaves `%USERPROFILE%\.diaries\responder.json` developer-owned and unchanged. Instead, one shared helper loads `development-infrastructure.env` and then `local.env`, validates both dataset selectors, and generates an ignored effective copy at:

```text
build/development-infrastructure/responder.effective.json
```

Only `diaries.files` is replaced in the generated JSON. The developer's `diaries.root`, diary source directory, credentials, MQTT settings, database connection settings and other responder options remain the values from the base configuration.

## Shared direct-development configuration path

Both:

```text
diaries-responder/scripts/windows/run-responder.bat
diaries-responder/scripts/windows/migration0024ImageCatalogue.bat
```

call:

```text
scripts/windows/development-infrastructure/prepare-responder-config.bat
```

The helper applies the required precedence:

```text
development-infrastructure.env
local.env
```

and therefore makes this common local pair move together:

```text
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

The generated JSON is beneath the already ignored top-level `build/` directory and is not packaged as source evidence. `REDACTED-GENERATED-RESPONDER.json` records the safe expected shape instead.

## Non-secret diagnostics

The helper reports the effective database data directory, physical Files root and generated responder-config path. It does not print credentials or the responder secret. See `EFFECTIVE-PATH-DIAGNOSTICS.txt`.

`start.bat` and `status.bat` also validate that both `DIARIES_DB_DATA_DIR` and `DIARIES_FILES_DIR` are defined and display the selected database directory plus Files leaf.

## Stable public Files URL

`UploadFile` no longer derives its response URL from `config.getFiles()`. It uses the stable public context `/files`, matching the static server and `ListFiles`.

A focused regression test uses the non-default physical directory `files-development-common` and proves the intended separation:

```text
physical directory  = files-development-common
public URL           = /files/image.txt
Image.relativePath   = image.txt
```

See `URL-REGRESSION-TEST.md`.

## Verification

Step 4 is closed with both static and Windows runtime evidence.

`verification-output.txt` records the passing 23-check static verification of the source wiring and guards.

The first Windows workstation run on 2026-10-01 reached the expected effective database and Files paths but exposed a verifier-only quoting error: the inline PowerShell pipeline was written as `^|` inside the quoted `-Command` argument, causing the caret to reach PowerShell literally. That run is retained unchanged as:

```text
runtime-verification-failure-20261001-184521.txt
```

The verifier was corrected to use `|`, and the static verifier was strengthened to reject the erroneous `^|` form.

The corrected verifier was rerun successfully on the Windows development workstation on 2026-10-02. The successful run records:

```text
Database data: ...\data\database\common
Files root:    ...\files-development-common
PASS: generated diaries.files = files-development-common
BUILD SUCCESSFUL
PASS: 0031 Step 4 runtime verification completed.
```

The full successful workstation output is retained as:

```text
runtime-verification-success-20261002-070435.txt
```

`runtime-verification-output.txt` is the closure summary for the runtime evidence. With the generated Files selector, stable `/files/...` URL regression, static verifier, and successful Windows runtime rerun all passing, the Step 4 completion criteria are satisfied.

## Scope

Step 4 does not create, copy, rename or delete NAS Files roots and does not mutate PostgreSQL data. Production/Ansible Files selection remains Step 5.
