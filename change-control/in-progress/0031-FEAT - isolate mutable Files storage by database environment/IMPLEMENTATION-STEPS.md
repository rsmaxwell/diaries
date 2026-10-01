# 0031-FEAT - Implementation Steps

Prepared 2026-10-01 from the current Diaries and Playbooks source bundles and the existing 0031 feature definition. Revised to reflect the existing `local.env` override model used by all three local modes.

## Objective

Isolate the mutable Diaries `Files` storage by **effective durable database dataset** so that Image/File lifecycle operations against one dataset cannot change the physical bytes expected by another dataset.

The implementation must establish and preserve this invariant:

```text
one effective database dataset <-> one effective mutable Files root
```

A local execution mode is not itself the dataset identity. The committed mode files provide defaults, but `config/environments/local.env` is loaded afterwards and can deliberately make `development-infrastructure`, `local-docker-build`, and `local-published-smoke` use the same effective database dataset. When it does, the same override mechanism must make those modes use the same effective mutable Files root as well.

The original diary-page source tree remains shared and read-only. Docker responders continue to see the stable logical Files path `/data/files`, and browser URLs remain under the stable `/files/...` route. Persisted `Image.relativePath` values remain relative to the selected Files root and therefore environment-neutral.

This feature is primarily configuration, deployment, operating-script and data-migration work. A small responder correction may be required to ensure that the public `/files/...` URL is not derived from the physical Files directory name, but no environment names should be introduced into responder domain logic or persisted Image data.

## Current source baseline

At the start of this feature, the checked source has these important properties:

- `config/environments/development-infrastructure.env` defaults to `DIARIES_DB_DATA_DIR=./data/database/development-infrastructure`;
- `config/environments/local-docker-build.env` defaults to `DIARIES_DB_DATA_DIR=./data/database/local-docker-build`;
- `config/environments/local-published-smoke.env` defaults to `DIARIES_DB_DATA_DIR=./data/database/local-published-smoke`;
- `config/environments/local.env.example` deliberately documents `DIARIES_DB_DATA_DIR=./data/database/common` so all three local modes can use one common local database dataset;
- the Windows scripts load the mode-specific environment first and `local.env` second, so values in `local.env` take precedence;
- therefore the **effective** local database layout can be one shared local dataset even though the three committed mode files contain separate defaults;
- `compose.local-docker-build.yaml` mounts `${DIARIES_NAS_CONTENT_PATH}/files` at `/data/files`;
- `compose.local-published-smoke.yaml` does the same;
- both Docker local modes use the same NAS content root and therefore currently address the same physical mutable Files tree;
- the direct Windows development responder obtains its physical Files directory from developer-owned `%USERPROFILE%\.diaries\responder.json`, independently of the `local.env` database override;
- `diaries-responder/scripts/windows/run-responder.bat` currently uses `%USERPROFILE%\.diaries\responder.json` directly and does not apply the mode/local environment pairing to `diaries.files`;
- `ListFiles` and the static HTTP server already use the stable public route `/files`, but `UploadFile` currently constructs its returned URL from `config.getFiles()`, coupling the public URL to the physical directory name;
- the production Playbooks `.env.j2` emits `DIARIES_NAS_CONTENT_PATH` but no separate mutable Files selector;
- the production `compose.yaml.j2` mounts `${DIARIES_NAS_CONTENT_PATH}/files` at `/data/files`;
- the Diaries Ansible role already has an `assert`-based validation pattern in `roles/diaries/tasks/main.yaml`, which is a suitable place for fail-fast validation.

The main gap is therefore not simply that local mode defaults are insufficiently isolated. It is that the **effective database selection and effective Files selection are not controlled as one pair**.

## Configuration model to implement

Use one explicit Files-directory selector that can be overridden by `local.env` in the same way as `DIARIES_DB_DATA_DIR`.

Recommended local/runtime name:

```text
DIARIES_FILES_DIR
```

Its value is the mutable Files directory name beneath the configured Diaries content root, for example:

```text
files
files-development-infrastructure
files-local-docker-build
files-local-published-smoke
files-development-common
```

This leaf-directory form is preferable to a Docker-only full NAS subpath because the same value can be consumed by:

- Docker Compose as `${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}`; and
- the direct Windows responder as the effective `diaries.files` value beneath the root already configured in `%USERPROFILE%\.diaries\responder.json`.

For production Playbooks use the corresponding role variable:

```text
diaries_files_dir
```

The exact names may be adjusted during implementation if an existing naming convention makes another name clearly better, but there must be a **single paired override concept** rather than separate manually synchronised local settings.

## Working rules

The following rules apply to every step:

1. Treat the PostgreSQL database and mutable Files root as a matched durable dataset.
2. Determine dataset identity from the **effective configuration after overrides**, not from the mode name or committed default file alone.
3. If `local.env` overrides `DIARIES_DB_DATA_DIR`, it should normally override `DIARIES_FILES_DIR` at the same time.
4. Sharing is valid when both sides are shared deliberately: several modes may use the same database and the same Files root.
5. Sharing only one side is invalid: two different databases must not silently mutate one Files root, and one database must not silently switch between unrelated Files roots.
6. Do not add environment names to persisted `Image.relativePath` values.
7. Keep the browser/static-file contract at `/files/...` regardless of the physical Files directory name.
8. Keep the original diary scans under the shared `diaries` tree read-only.
9. Do not silently default a missing mutable Files selector back to the production Files directory.
10. Preserve the existing production Files path where practical; isolate non-production by creating new roots rather than moving production.
11. Do not perform destructive Image/File lifecycle testing against a database/Files pair until reconciliation for that pair is understood.
12. Record implementation evidence under `evidence/Step N/` so each step can be reviewed and closed independently.
13. Do not treat retained MQTT state as durable authoritative storage. It must be environment-specific at runtime, but it can be rebuilt from the database.
14. A rollback must never merge independently changed Files roots back together silently.

---

## Step 1 — Freeze the effective dataset/storage invariant and capture the current mapping

Before changing configuration, record exactly which database and physical Files tree each mode **actually** uses after all overrides have been applied.

Inventory at least:

```text
development-infrastructure
local-docker-build
local-published-smoke
production
```

For each mode record:

```text
mode name
committed DIARIES_DB_DATA_DIR default
effective DIARIES_DB_DATA_DIR after local.env
database host/container
database name
configured/effective Files selector
physical NAS Files path
MQTT broker/topic namespace
whether the mode intentionally shares a database with another mode
whether it intentionally shares Files with that same mode/current source identity
```

Explicitly capture the current local override behaviour:

```text
mode-specific .env
        then
local.env
        => local.env wins
```

If the current ignored `local.env` sets:

```text
DIARIES_DB_DATA_DIR=./data/database/common
```

record all three local modes as one logical database dataset even though their committed defaults are different.

Also record the current source lines showing the implicit mutable Files mount in both local Compose files, the direct responder configuration path, and the production Playbooks template.

Do not mutate Files or database content in this step. Do not copy secrets from `local.env` into evidence; record only relevant non-secret path selections.

**Likely files:** no application-source change is required; evidence only, plus clarification to feature documentation if the inventory reveals another incorrect assumption.

**Evidence:** source identities, redacted effective configuration extracts, path map, and a table identifying every intentional or accidental shared dataset/root.

**Complete when:** every active mode is mapped to an **effective logical dataset**, and no conclusion is based solely on the committed mode default.

---

## Step 2 — Decide and document the final effective dataset-to-Files-root map

Choose the final mutable root for each **independent effective database dataset** before editing Compose, responder launch tooling or Ansible.

The committed defaults may remain independently usable:

```text
production
  DB dataset: production
  Files root: .../diaries-content/files

development-infrastructure default
  DB dataset: ./data/database/development-infrastructure
  Files root: .../diaries-content/files-development-infrastructure

local-docker-build default
  DB dataset: ./data/database/local-docker-build
  Files root: .../diaries-content/files-local-docker-build

local-published-smoke default
  DB dataset: ./data/database/local-published-smoke
  Files root: .../diaries-content/files-local-published-smoke
```

However, if the normal developer `local.env` deliberately selects the common local database:

```text
DIARIES_DB_DATA_DIR=./data/database/common
```

then the intended effective local mapping should instead be one matched local dataset, for example:

```text
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

and all three local modes should resolve to:

```text
DB dataset: ./data/database/common
Files root: .../diaries-content/files-development-common
```

That is not a violation of 0031. It is the intended paired-sharing case.

Keep:

```text
.../diaries-content/diaries
```

shared and read-only.

Freeze the public configuration contract now:

```text
DIARIES_FILES_DIR
```

for local/runtime selection and:

```text
diaries_files_dir
```

for the Playbooks role, unless implementation review identifies a compelling naming conflict.

**Evidence:** approved path map showing both committed defaults and the normal effective `local.env` mapping, rationale for intentional local sharing, and rollback mapping to the pre-feature configuration.

**Complete when:** every independent effective database dataset has exactly one explicit mutable Files root, including the intentionally shared common local dataset if that override is in use.

---

## Step 3 — Add one paired database/Files override contract to all three local modes

Extend the existing environment precedence model rather than creating a separate Files-selection mechanism.

Update at least:

```text
config/environments/development-infrastructure.env
config/environments/local-docker-build.env
config/environments/local-published-smoke.env
config/environments/local.env.example
compose.local-docker-build.yaml
compose.local-published-smoke.yaml
```

Give each committed mode file an isolated Files default, for example:

```text
development-infrastructure.env
  DIARIES_DB_DATA_DIR=./data/database/development-infrastructure
  DIARIES_FILES_DIR=files-development-infrastructure

local-docker-build.env
  DIARIES_DB_DATA_DIR=./data/database/local-docker-build
  DIARIES_FILES_DIR=files-local-docker-build

local-published-smoke.env
  DIARIES_DB_DATA_DIR=./data/database/local-published-smoke
  DIARIES_FILES_DIR=files-local-published-smoke
```

Update `local.env.example` so its existing common database example also demonstrates the matching Files override:

```text
# All three local modes deliberately share one durable development dataset.
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

The real ignored `local.env` on a developer machine should be updated in the same paired manner when the common database is used.

For the two Docker responder modes, change the mutable Files volume from:

```text
${DIARIES_NAS_CONTENT_PATH}/files
```

to conceptually:

```text
${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}
```

while the read-only diary scan mount remains:

```text
${DIARIES_NAS_CONTENT_PATH}/diaries
```

Do not provide a fallback such as:

```text
${DIARIES_FILES_DIR:-files}
```

for non-production local modes, because that could silently send an isolated database back to the production/shared Files directory.

Add configuration checks proving:

- every local mode has a committed `DIARIES_FILES_DIR` default;
- `local.env` is loaded second and can override both `DIARIES_DB_DATA_DIR` and `DIARIES_FILES_DIR`;
- the two Docker mutable mounts use `${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}`;
- the diary scan mount still uses `${DIARIES_NAS_CONTENT_PATH}/diaries`;
- omission of `DIARIES_FILES_DIR` fails clearly;
- a test `local.env` containing the common pair makes both Docker modes resolve the same database and same Files root.

**Complete when:** the local environment mechanism can select either isolated mode defaults or one intentionally shared local database/Files pair without editing Compose files.

---

## Step 4 — Make direct Windows development consume the same effective Files override

`development-infrastructure` runs PostgreSQL/MQTT in Compose but runs the Java responder directly. It therefore needs an explicit bridge from the same environment precedence model into the responder's effective `diaries.files` value.

Do **not** rely on manually editing `%USERPROFILE%\.diaries\responder.json` every time `local.env` changes. That would recreate the mismatch 0031 is intended to prevent.

Implement a reusable direct-development configuration preparation path with these properties:

1. load `config/environments/development-infrastructure.env`;
2. load `config/environments/local.env` second;
3. validate that `DIARIES_FILES_DIR` is defined;
4. take the developer-owned `%USERPROFILE%\.diaries\responder.json` as the base configuration;
5. produce an ignored/generated effective responder configuration whose `diaries.files` value is the effective `DIARIES_FILES_DIR`;
6. leave all credentials and unrelated developer-owned settings unchanged;
7. run the responder with the generated effective configuration;
8. display the effective database directory and Files directory at startup without displaying secrets.

A committed helper script may be used to generate the effective JSON; the generated file itself must not be committed. Reuse that helper for direct-development tools that must address the same physical Files tree, especially Image reconciliation/migration tooling, rather than allowing each script to interpret the base responder JSON independently.

Review at least:

```text
diaries-responder/scripts/windows/run-responder.bat
diaries-responder/scripts/windows/migration0024ImageCatalogue.bat
scripts/windows/development-infrastructure/*
```

and any other direct-development maintenance script that consumes `%USERPROFILE%\.diaries\responder.json` for Files access.

### Preserve the stable `/files/...` public URL

Changing the physical `diaries.files` directory from `files` to a name such as `files-development-common` must **not** change browser/RPC URLs.

The current source already serves the HTTP context at hard-coded `/files`, and `ListFiles` builds URLs under `/files`, but `UploadFile` currently constructs its response URL using:

```text
"/" + config.getFiles() + "/..."
```

Correct that coupling so uploaded-file URLs remain:

```text
/files/...
```

regardless of the physical Files directory name.

Add a responder regression test that runs with a non-default physical directory name and proves:

```text
physical directory: files-development-common
public URL:         /files/...
```

No environment name should appear in persisted `Image.relativePath` values.

Update `diaries-responder/README.md` where it currently states that the three local modes address the same physical NAS Files tree without explaining the paired effective override.

**Evidence:** redacted generated direct-development config, effective path diagnostics, responder URL regression test, and proof that direct reconciliation uses the same effective Files selection.

**Complete when:** changing the common pair in `local.env` changes both the development database and direct responder Files root together, with `/files/...` URLs unchanged.

---

## Step 5 — Add explicit production Files-root configuration to the Ansible role

Update the production Diaries role so the mutable Files directory is explicit and required.

Expected Playbooks files:

```text
roles/diaries/templates/.env.j2
roles/diaries/templates/compose.yaml.j2
roles/diaries/tasks/main.yaml
roles/diaries/defaults/main.yaml          # only if a non-dangerous declaration is useful
host/group variables that own production NAS paths
```

Render:

```text
DIARIES_FILES_DIR={{ diaries_files_dir }}
```

and change the responder Files volume subpath to:

```text
${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}
```

Keep the diary scan mount using:

```text
${DIARIES_NAS_CONTENT_PATH}/diaries
```

Add an Ansible preflight assertion before templating/deployment. It should reject an undefined, empty or obviously invalid `diaries_files_dir` rather than relying on an implicit production-path fallback.

The production inventory/host/group configuration should explicitly set:

```text
diaries_files_dir: files
```

if production is to retain its existing physical path.

Do not add a role default that silently resolves an unspecified environment to production `files`; that would defeat the guard this feature is adding.

Add template/render validation proving the generated `.env` and Compose mount use the explicit selector.

**Complete when:** production deployment cannot render a Diaries Compose configuration without an explicitly supplied mutable Files directory selector.

---

## Step 6 — Add regression guards for override pairing and accidental storage re-sharing

Add automated checks at the most appropriate repository levels.

At minimum prove:

```text
local-docker-build Files mount    -> DIARIES_NAS_CONTENT_PATH/DIARIES_FILES_DIR
local-published-smoke Files mount -> DIARIES_NAS_CONTENT_PATH/DIARIES_FILES_DIR
production template Files mount   -> DIARIES_NAS_CONTENT_PATH/DIARIES_FILES_DIR
shared diary scans                -> DIARIES_NAS_CONTENT_PATH/diaries
public file URL                   -> /files/...
```

Test both configuration modes:

### Isolated defaults

With no overriding common pair, each committed local environment resolves a distinct database directory and distinct Files directory.

### Deliberately shared local dataset

With a test `local.env` containing:

```text
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

prove that all three local modes resolve the same database dataset and the same Files dataset.

Also add a guard for obvious mismatched overrides. If tooling can reliably detect that a user has overridden `DIARIES_DB_DATA_DIR` in `local.env` but omitted `DIARIES_FILES_DIR`, fail with a clear message rather than silently combining the common database with a mode-specific or production Files root.

Do not attempt to infer database identity from the mode name inside responder Java. The validation belongs in configuration/launch/deployment tooling.

A future durable dataset marker stored inside a Files root is optional for 0031; do not expand scope unless path-based validation proves insufficient during implementation.

**Evidence:** test source, commands and passing reports for both isolated-default and shared-common configurations.

**Complete when:** the exact mismatch that motivated 0031 is covered by a repeatable regression check.

---

## Step 7 — Define matched database + Files backup/restore semantics using effective configuration

Review the existing database backup/restore scripts and production backup helpers in light of the new invariant.

The goal is not to remove useful database-only operations. It is to distinguish clearly between:

```text
database-only backup/reset
```

and:

```text
complete recoverable Diaries dataset backup
  = effective PostgreSQL dataset
  + matching effective mutable Files root
  + configuration/path identity
```

Local backup tooling must report the **effective** selections after loading the mode file and `local.env`; it must not label a backup according to the mode default if `local.env` has redirected that mode to the common dataset.

Where practical, add a small manifest for complete-dataset backups containing at least:

```text
logical dataset name/effective database directory
database backup filename and timestamp
effective DIARIES_FILES_DIR
resolved physical Files root
application/source identity
Image row count
catalogued-file count
optional reconciliation/checksum inventory reference
```

Review relevant locations, including:

```text
scripts/windows/development-infrastructure/backup-*
scripts/windows/development-infrastructure/restore-*
scripts/windows/local-docker-build/backup-*
scripts/windows/local-docker-build/restore-*
scripts/windows/local-published-smoke/backup-*
scripts/windows/local-published-smoke/restore-*
production role backup/restore helpers and documentation
```

If all three local modes resolve to `./data/database/common` plus `files-development-common`, treat them as one durable dataset for full backup purposes; do not create three misleading full-dataset backups merely because three launch modes exist.

Do not claim a database-only restore is a complete dataset restore.

**Complete when:** an operator can tell which effective Files root belongs with a database backup and can identify intentional cross-mode sharing.

---

## Step 8 — Freeze mutable writes and take pre-migration backups

Before splitting the currently shared physical Files tree, prevent Image/File upload, replacement and deletion in all environments that can reach it.

Then capture and verify:

```text
production database backup
one backup for each independent effective non-production database dataset
full snapshot/copy of the currently shared Files root
current effective database/Files mappings
application/source identities
```

If the three local modes currently resolve through `local.env` to one common database, capture one common-local database backup and record all three modes as consumers of that same dataset.

Inspect the current staging area before copying. In particular, identify active or abandoned content under locations such as:

```text
.image-staging
```

Do not blindly replicate unexplained transient/recovery content into every new dataset root.

Generate checksums or another reproducible inventory for the shared source tree so later copies can be compared.

**Evidence:** backup filenames/locations, verification results, effective source-tree mapping, staging review, and write-freeze procedure.

**Complete when:** rollback can restore each independent database/Files pair to a known pre-split point.

---

## Step 9 — Reconcile each independent effective database against the existing shared Files tree

Before making copies, run the existing Image catalogue reconciliation/inventory tooling separately for every **independent effective database dataset** while all of them still reference the current shared Files tree.

For each dataset record at least:

```text
catalogued Image row count
matching physical files
missing physical files
untracked physical files
metadata/checksum conflicts
staging/recovery anomalies
```

If `development-infrastructure`, `local-docker-build` and `local-published-smoke` all resolve to `./data/database/common`, they are one dataset for this purpose. Run reconciliation once against the effective common database/Files pair, not three times against the same data.

Use dry-run/read-only reconciliation first.

The direct-development reconciliation tool must use the Step 4 generated/effective responder configuration so that it cannot inspect a different Files root from the database selected by `local.env`.

Do not repair one independent database based on assumptions derived from another database. The purpose of this step is to determine whether the shared tree is already inconsistent with any dataset before duplication freezes those differences into separate roots.

If unexplained mismatches exist, stop the migration for that dataset and resolve/review them explicitly.

**Evidence:** one reconciliation report per independent effective database dataset, with database identity and Files-root identity captured together.

**Complete when:** the state of every independent database relative to the shared tree is understood and any exception has an explicit disposition.

---

## Step 10 — Create one Files root per independent non-production database dataset

Prefer to leave the current production mutable tree at:

```text
.../diaries-content/files
```

Create a separate physical root for each **independent non-production database dataset** according to the Step 2 mapping.

For the normal shared-local configuration this may mean creating only:

```text
.../diaries-content/files-development-common
```

because the three local execution modes intentionally share one database dataset.

If the common overrides are removed and the modes use their isolated committed defaults, create/use their separate corresponding Files roots instead.

Seed each new root from the verified pre-migration source tree using a copy mechanism that preserves the attributes needed by the responder and NAS deployment.

After copying:

- compare file counts and size totals;
- verify a checksum/inventory sample or complete inventory as appropriate;
- confirm permissions allow only the intended server processes to mutate the tree;
- preserve or deliberately exclude staging/recovery content according to the Step 8 review;
- do not delete the original shared tree or backup.

Do not create three physical copies merely because three launch modes exist if all three consume the same effective database dataset.

**Evidence:** copy commands, source/destination identities, before/after inventories, permission check and exceptions.

**Complete when:** every independent non-production database dataset has exactly one candidate Files root ready for configuration cut-over.

---

## Step 11 — Repoint local modes and verify resolved runtime paths after overrides

Reconfigure one **effective dataset** at a time, then test every mode that consumes it.

For Docker modes, prove that the responder still sees:

```text
/data/files
```

while the underlying NAS subpath resolves to:

```text
${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}
```

For direct Windows development, prove that the generated effective responder configuration resolves `root + files` to the same physical Files root selected for that database dataset.

If `local.env` selects:

```text
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

then verify all three modes resolve to that same database/Files pair, even though they reach it through different runtime mechanisms.

Also verify:

- the original diary scans still resolve to the shared read-only tree;
- the static HTTP route remains `/files/...`;
- startup/status diagnostics display the effective database and Files selections;
- no mode silently falls back to production `files`.

At this stage, perform only non-destructive startup and read/list checks. Do not yet use upload/delete as the primary validation.

Capture responder startup logs, rendered Compose configuration, mount inspection, generated direct-responder configuration with secrets redacted, and Files-list/static-file checks.

**Complete when:** every local mode resolves the same matched pair when common overrides are active, or its own matched pair when isolated defaults are active.

---

## Step 12 — Reconcile every new effective database + Files-root pair

Run the same Image catalogue reconciliation/inventory process again, now against each newly selected pair.

For each independent pair compare the result with its Step 9 pre-split baseline.

Expected result:

```text
same database semantics
same catalogued/missing/untracked disposition
new intended physical Files-root identity
```

If all three local modes share the common pair, one reconciliation report is authoritative for that durable dataset, although startup/read validation should still cover each mode.

Any difference caused solely by the copy/split must be investigated before destructive Image lifecycle testing begins.

Where a pre-existing mismatch was deliberately resolved during migration, document the exact repair and why it belongs to that dataset only.

Do not copy missing content from production to development, or vice versa, merely to make reconciliation green unless that movement is explicitly reviewed as a data correction.

**Evidence:** post-split reconciliation report per independent dataset and comparison to Step 9.

**Complete when:** every new database/Files pair is clean or has explicitly reviewed exceptions and is safe for lifecycle testing.

---

## Step 13 — Prove cross-dataset isolation with controlled Image lifecycle tests

Use a disposable, uniquely named Image in the non-production dataset selected by the normal local override configuration.

Before mutation, capture a production control baseline covering:

```text
production Image row/catalogue state
production Files-tree inventory/checksum for the relevant path
production retained state or read-only catalogue snapshot as useful
```

Then in one local mode:

1. upload a new disposable Image;
2. confirm its database row exists only in the local effective database dataset;
3. confirm its retained Image topic appears only in the intended local broker/namespace;
4. confirm its physical file appears only in the local effective Files root;
5. confirm its returned/static URL remains `/files/...`;
6. confirm the production database and Files root are unchanged.

If the three local modes deliberately share the common dataset, start a second local mode separately and prove that it sees the same database row and same physical file because it is intentionally consuming the same durable pair. Do not run two PostgreSQL containers concurrently against the same host data directory.

Then delete the disposable Image through the supported deletion path and confirm:

1. the row disappears from the shared local database dataset;
2. the retained topic is removed/rebuilt correctly for the active local broker;
3. the physical file is removed from `files-development-common` (or the selected effective local root);
4. production remains unchanged.

Also verify replacement/overwrite behaviour if the current supported Image workflow permits it safely.

The strongest isolation proof is a before/after inventory or checksum of the production Files tree relevant to the test, not merely absence of a production UI change.

**Evidence:** request/result evidence, DB queries, retained-topic evidence, physical path checks, stable `/files/...` URL evidence, and production before/after comparison.

**Complete when:** a real local upload/delete cycle proves that intentional sharing occurs only among modes using the same database dataset and that no physical mutation crosses into production.

---

## Step 14 — Deploy the explicit production configuration non-destructively

Apply the Playbooks changes with production still using its existing physical Files root.

Before deployment:

- verify the production database backup and Files backup/snapshot from Step 8 remain available;
- verify `diaries_files_dir` is explicitly set to `files` or the intended production directory;
- render/review the generated `.env` and Compose configuration;
- confirm `/data/files` will still map to the existing production physical path;
- confirm no local override file participates in production deployment.

Deploy and verify:

```text
services healthy
responder startup successful
/files route serves existing content
Image catalogue remains consistent
read-only reconciliation has no new differences
non-production Files roots are untouched
```

Do not introduce a production Image mutation merely to prove configuration if existing non-destructive evidence is sufficient. If a controlled production lifecycle test is later considered necessary, treat it as a separately backed-up operational verification.

**Evidence:** Ansible command/result, generated path configuration with secrets redacted, deployed service status, read-only Files/Image checks and reconciliation result.

**Complete when:** production is explicitly configured and healthy while retaining the same intended production database/Files pairing.

---

## Step 15 — Update architecture and operating documentation

Update documentation so the effective dataset pairing is a normal operating rule, not knowledge confined to 0031.

Expected locations include:

```text
README.md
ARCHITECTURE.md
diaries-responder/README.md
config/environments/local.env.example
relevant Windows script/readme documentation
Playbooks Diaries role documentation
backup/restore operating notes
```

Document:

- the one-effective-database-dataset/one-Files-root invariant;
- that mode defaults are overridden by `local.env`, which is loaded second;
- that the normal developer configuration may intentionally make all three local modes share `./data/database/common`;
- that the common database override must be paired with the common `DIARIES_FILES_DIR` override;
- the separation between shared read-only `diaries` and mutable Files storage;
- the `DIARIES_FILES_DIR` variable and its leaf-directory semantics;
- the production `diaries_files_dir` variable;
- how direct Windows responder configuration is generated/applied from the same effective selector;
- how isolated committed defaults can be restored by removing/changing the common overrides;
- the fact that `/files/...` URLs and `Image.relativePath` remain environment-neutral;
- how to create a complete dataset backup;
- how to restore a matched database + Files pair;
- how to identify the effective Files root before running destructive tests;
- why switching only the database override or only the Files override is invalid;
- the danger of temporarily reverting independently changed datasets to one shared Files root.

**Complete when:** a future operator can understand both the isolated defaults and the intentionally shared local override without consulting the 0031 implementation conversation.

---

## Step 16 — Full regression, rollback rehearsal and feature close-out

Run the final cross-repository regression gate against the exact release candidate.

At minimum verify:

### Configuration precedence

- all three local mode files define independent database and Files defaults;
- `local.env` is loaded second;
- one test common override makes all three local modes resolve `./data/database/common` and `files-development-common`;
- removing that override returns each mode to its own committed database/Files pair;
- overriding the common database without the matching Files selector is rejected clearly.

### Docker and production mounts

- both local Docker Compose files use `${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}` for mutable Files;
- production generated Compose uses the same explicit selector pattern;
- shared diary scans still use `${DIARIES_NAS_CONTENT_PATH}/diaries`;
- no committed runtime configuration reintroduces an implicit `${DIARIES_NAS_CONTENT_PATH}/files` mutable mount for non-production.

### Direct-development behaviour

- `run-responder.bat` and direct maintenance/reconciliation tooling consume the effective `development-infrastructure.env` + `local.env` selection;
- the generated direct responder configuration contains the intended effective `diaries.files` value;
- physical Files directory names do not change the public `/files/...` URL;
- `UploadFile` and `ListFiles` agree on the `/files/...` contract.

### Application behaviour

- client/responder/web Image behaviour remains unchanged apart from storage isolation;
- existing `/files/...` URLs still work;
- `Image.relativePath` values are unchanged and contain no environment prefix;
- upload/delete in the local common dataset affects that common database and Files root only;
- another local mode intentionally using the same pair sees the same durable data;
- production database and physical Files bytes remain unchanged;
- retained MQTT state remains mode/broker-specific and rebuildable from the matching database.

### Backup/restore

- complete-dataset documentation/tooling identifies both durable sides from effective configuration;
- one non-production restore/reconciliation rehearsal proves that the common/local database is restored with its intended Files root;
- a database-only reset is clearly labelled as potentially requiring Files reconciliation.

### Rollback

Rehearse or document a concrete rollback using the Step 8 backups:

1. stop the affected responder/mode;
2. restore the previous matched configuration or database/Files pair as required;
3. preserve isolated copies until reconciliation is complete;
4. if temporarily reverting two independently changed datasets to the old shared tree, disable destructive Image/File lifecycle operations;
5. never merge divergent roots automatically;
6. if restoring the shared common-local model, restore both `DIARIES_DB_DATA_DIR` and `DIARIES_FILES_DIR` together.

Create a final acceptance mapping from the 0031 README acceptance criteria to evidence produced by Steps 1–16.

Move the feature to `change-control/complete` only after that mapping has no unexplained gaps.

**Evidence:** complete test/regression logs, final source identities, final effective path map, acceptance matrix, rollback instructions and close-out summary.

**Complete when:** all 0031 acceptance criteria are evidenced and an operator cannot accidentally combine the common local database with the wrong mutable Files root without a validation failure.

---

## Expected implementation scope

The exact changed-file set should be determined during the steps above, but the current source indicates the following likely scope.

### Diaries repository

```text
compose.local-docker-build.yaml
compose.local-published-smoke.yaml
config/environments/development-infrastructure.env
config/environments/local-docker-build.env
config/environments/local-published-smoke.env
config/environments/local.env.example
README.md
ARCHITECTURE.md
diaries-responder/README.md
diaries-responder/scripts/windows/run-responder.bat
diaries-responder/scripts/windows/migration0024ImageCatalogue.bat
shared/direct-development helper for effective responder JSON generation
scripts/windows/development-infrastructure/*     # only files needing dataset/path awareness
scripts/windows/local-docker-build/*             # only files needing dataset/path awareness
scripts/windows/local-published-smoke/*           # only files needing dataset/path awareness
diaries-responder/src/main/java/.../UploadFile.java   # likely stable /files URL correction
responder regression test for non-default physical Files directory
validation/tests for environment precedence and Compose/config isolation
```

The developer-owned file below remains operational input and must not be committed:

```text
%USERPROFILE%\.diaries\responder.json
```

The generated effective responder configuration derived from it must also remain ignored/uncommitted.

### Playbooks repository

```text
roles/diaries/templates/.env.j2
roles/diaries/templates/compose.yaml.j2
roles/diaries/tasks/main.yaml                    # likely fail-fast assertion location
roles/diaries/defaults/main.yaml                 # only if useful without unsafe fallback
production host/group configuration that supplies diaries_files_dir
relevant role backup/restore documentation/helpers
validation/tests for rendered production configuration
```

### Not expected to change

Unless implementation uncovers another defect, 0031 should not require semantic changes to:

```text
diaries-client Image RPC/UI behaviour
diaries-web browser URL contracts
persisted Image.relativePath values
Image catalogue database schema
read-only diary scan storage layout
MQTT RPC request/response shapes other than correcting an already-derived file URL if necessary
```

## Acceptance summary

0031 is ready to close only when all of the following are true:

- storage pairing is based on the **effective database configuration after overrides**, not the mode name;
- production and non-production do not share a mutable physical Files root unless they intentionally share the same database dataset;
- `local.env` can deliberately make all three local modes use the same database data **and the same Files data**;
- the common database and common Files selectors are overridden as one pair;
- removing/changing the common overrides restores the independently configured local defaults;
- every independently persisted database dataset has one explicit matching Files root;
- `/data/files` remains the stable Docker runtime path;
- `/files/...` remains the stable public URL even when the physical directory is named `files-development-common` or another environment-specific name;
- the original diary scans remain shareable/read-only;
- missing/mismatched Files configuration fails rather than falling back to production storage;
- direct Windows development consumes the same effective Files override as its database environment;
- local Compose and production Ansible both render the intended explicit Files root;
- Image catalogue reconciliation is clean or explicitly reviewed for each independent database/Files pair;
- a controlled local upload/delete proves production database and physical Files bytes do not change;
- backup/restore guidance treats the database and mutable Files as a matched durable dataset;
- persisted `Image.relativePath` values remain environment-neutral;
- final documentation records default mappings, effective common-local mappings, validation evidence and rollback procedure.
