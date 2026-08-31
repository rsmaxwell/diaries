# Development steps — externalise local responder configuration

## Purpose

Ensure that removing the two explicitly named Mosquitto credential files does not leave a separate plaintext MQTT password in the tracked Docker-mode responder configurations.

## Current behaviour

`compose.local-docker-build.yaml` and `compose.local-published-smoke.yaml` mount tracked mode-specific responder JSON files. Both tracked files contain an MQTT password and additional runtime credential values. The development-infrastructure responder already uses a developer-owned file under `%USERPROFILE%\.diaries`.

## Required behaviour

Both containerised local modes must mount one developer-owned `%USERPROFILE%\.diaries\responder.docker.json` file through `DIARIES_RESPONDER_DOCKER_CONFIG_FILE`. The repository copies must be deleted without changing responder code or production configuration.

## Implementation steps

1. Securely create `%USERPROFILE%\.diaries\responder.docker.json` from the current required local settings without recording its content in logs or change control.
2. Keep the MQTT username `diaries-responder`; make its password match the same entry in `%USERPROFILE%\.diaries\pwfile.source.txt`.
3. Add `DIARIES_RESPONDER_DOCKER_CONFIG_FILE=C:/Users/<username>/.diaries/responder.docker.json` to ignored `config/environments/local.env` and document that this value must be an absolute path because Compose does not recursively expand variables from an `--env-file`.
4. Replace the short responder JSON mounts in both containerised Compose modes with long-syntax read-only bind mounts using the new variable.
5. Delete the two tracked responder JSON files only after `docker compose config` resolves the external source correctly.
6. Extend the local Mosquitto documentation with the responder credential consistency requirement.

## Files to add, change, or delete

Change:

- `compose.local-docker-build.yaml`
- `compose.local-published-smoke.yaml`
- `config/environments/local.env.example`
- `config/mosquitto/README.md`

Delete:

- `config/responder/local-docker-build/responder.json`
- `config/responder/local-published-smoke/responder.json`

## Migration and setup requirements

The external file must be created before either Compose mode is started. Preserve the existing non-MQTT settings and do not invent or rotate any credential as part of this change. The Docker-mode MQTT host remains `diaries-mqtt` and port remains `1883`.

The direct Windows responder used with development-infrastructure continues to use its existing developer-owned `%USERPROFILE%\.diaries\responder.json`; it is not copied into the repository.

## Tests and verification

1. With `DIARIES_RESPONDER_DOCKER_CONFIG_FILE` unset, verify each affected Compose invocation fails clearly rather than silently using a tracked fallback.
2. Set the variable in ignored `local.env` and run `docker compose config` for both modes; confirm the resolved bind source is external and the target is `/config/responder.json` read-only.
3. Start `local-docker-build`, confirm the responder becomes healthy, connects as `diaries-responder`, and completes client/responder MQTT traffic.
4. Repeat for `local-published-smoke` and confirm the published responder image reads the same external configuration.
5. Search tracked files for the former MQTT password only in a redaction-safe way; record filenames/counts, not matching lines or values.
6. Run the relevant configuration and smoke checks; no responder code build is required because this feature changes only bind-mounted configuration.

## Expected state after completion

All three local modes use developer-owned responder configuration where credentials are required, and no tracked responder JSON contains an MQTT password. The local Mosquitto source cleanup in `0013` can then remove the last tracked local password artifacts.
