# 0031-FEAT Step 13 runtime runbook

This runbook performs the first deliberately destructive Image lifecycle test in 0031. The mutation is confined to the normal non-production common dataset. Keep the **production responder stopped throughout the entire Step 13 run**.

The normal ignored `config/environments/local.env` must select:

```text
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

Never run two local PostgreSQL modes concurrently against `./data/database/common`.

## Authoritative completed run — 2026-10-03

Step 13 has now been completed successfully. The authoritative evidence is:

```text
production BEFORE:
  /home/richard/projects/diaries/data/0031-step13/production-before-20261002-203216
local lifecycle:
  evidence/Step 13/runtime/local-20261003-080333-8f26d1bc
production AFTER:
  /home/richard/projects/diaries/data/0031-step13/production-after-20261003-083327
```

The sequence below is retained as the reproducible runbook. See `CLOSE-OUT.md` for the reviewed results and runtime corrections.

## 1. Install only the new production control helper on pluto

The production write freeze is already in force after Step 12. Do **not** rerun the whole Diaries playbook merely to install the Step 13 helper if that would restart the stack.

Copy this Playbooks source file to pluto's deployed scripts directory and make it executable:

```text
roles/diaries/files/sync/scripts/step13-capture-production-control.sh
    -> /home/richard/projects/diaries/scripts/step13-capture-production-control.sh
```

A later normal Step 14 playbook deployment will install the same role-managed file permanently.

## 2. Capture the production BEFORE control on pluto

On pluto:

```bash
cd /home/richard/projects/diaries
./scripts/step13-capture-production-control.sh before
```

Expected result:

```text
PASS: Step 13 production BEFORE control captured with responder writes frozen.
Evidence: /home/richard/projects/diaries/data/0031-step13/production-before-...
```

Record the exact BEFORE directory. Do not start the production responder.

## 3. Upload the disposable Image in the first local mode

Use `development-infrastructure` for the first mode because it exercises the direct Windows responder configuration.

Start its PostgreSQL/MQTT infrastructure. Because Step 13 changes the Mosquitto queue policy, stop/start the infrastructure after applying this implementation so the broker definitely reloads `max_queued_messages 0`:

```bat
scripts\windows\development-infrastructure\stop.bat
scripts\windows\development-infrastructure\start.bat
```

Verify the running broker sees the intended flow-control settings:

```bat
docker exec diaries-development-mqtt sh -c "grep -E '^(max_inflight_messages|max_queued_messages)' /mosquitto/config/mosquitto.conf"
```

Expected:

```text
max_inflight_messages 20
max_queued_messages 0
```

In a second Command Prompt start the direct responder and leave it running:

```bat
diaries-responder\scripts\windows\run-responder.bat
```

Then run:

```bat
scripts\windows\0031-step13\run-local-lifecycle.bat -Action upload
```

The script prompts for an active Diaries EDITOR/ADMIN application username and password. Credentials are passed only to the child process and are not written to evidence.

Expected result includes:

```text
PASS: uploaded disposable Image in development-infrastructure, proved DB row, retained topic, physical file and stable /files URL.
Evidence: ...\evidence\Step 13\runtime\local-...
```

Record that local run directory.

The upload phase also retries the same catalogued path with `overwrite=true` and requires HTTP/RPC conflict status 409. This is the current safe replacement/overwrite proof: the supported workflow does not permit in-place replacement of a catalogued Image.

## 4. Stop the first local mode completely

Stop the direct responder with `Ctrl+C`, then:

```bat
scripts\windows\development-infrastructure\stop.bat
```

Confirm no `diaries-development-db` container remains before starting the next mode.

## 5. Start a second local mode and prove intentional sharing

Start local Docker build normally:

```bat
scripts\windows\local-docker-build\start.bat
scripts\windows\local-docker-build\status.bat
```

It must report the same effective pair:

```text
./data/database/common
files-development-common
```

Then run:

```bat
scripts\windows\0031-step13\run-local-lifecycle.bat -Action observe -RunDirectory "<local-run-directory>"
```

Expected result:

```text
PASS: local-docker-build sees the same Image row, bytes, retained Image and /files URL created by development-infrastructure.
```

This is the intentional-sharing proof. The observer command refuses to pass if the active mode is the same one that performed the upload.

## 6. Delete through the supported Image lifecycle path

With `local-docker-build` still active, run:

```bat
scripts\windows\0031-step13\run-local-lifecycle.bat -Action delete -RunDirectory "<local-run-directory>"
```

The script again prompts for the Diaries application password. It refuses to run unless a successful `OBSERVE-*.json` file already exists.

Expected result:

```text
PASS: deleteImage removed the common-dataset row, retained topic and physical file in local-docker-build.
```

The evidence must show:

- one Image row immediately before deletion and zero afterward;
- matching physical bytes immediately before deletion and no file afterward;
- successful `deleteImage` RPC identity;
- an empty-payload MQTT tombstone observed live;
- no retained Image message when reconnecting after deletion; and
- the former `/files/...` URL no longer returning HTTP 200.

Stop local Docker build after the delete proof:

```bat
scripts\windows\local-docker-build\stop.bat
```

## 7. Capture and compare the production AFTER control

Back on pluto, with the production responder still stopped:

```bash
cd /home/richard/projects/diaries
./scripts/step13-capture-production-control.sh after \
  /home/richard/projects/diaries/data/0031-step13/production-before-<timestamp>
```

Expected result:

```text
PASS: Step 13 production controls are unchanged.
```

The helper fails if either:

```text
IMAGE-ROWS.tsv
FILES-INVENTORY.tsv
```

differs by even one byte from the BEFORE control. The Files inventory hashes every production mutable file, so this is stronger evidence than checking that the production UI did not change.

## 8. Preserve evidence for close-out

Preserve/copy these complete successful evidence sets:

```text
Windows:
  evidence/Step 13/runtime/local-.../

pluto:
  data/0031-step13/production-before-.../
  data/0031-step13/production-after-.../
```

For any future rerun, do not treat the run as authoritative until all three evidence sets are available for review. For the completed 2026-10-03 run, keep the production responder stopped until Step 14 explicitly reviews/deploys production operation.

### Local Docker CIFS volume recreation after the staging-permission correction

If the Step 13 package changes the `nas-photo` CIFS driver options, stop the active local Docker mode, remove only that mode's `nas-photo` Docker volume, and restart the mode before retrying `observe` or `delete`. Do not use `docker compose down -v`, because that would also remove unrelated persistent volumes. For `local-docker-build`, the volume is normally `diaries-local-docker-build_nas-photo`. The remote NAS contents are not deleted by removing this Docker volume definition.
