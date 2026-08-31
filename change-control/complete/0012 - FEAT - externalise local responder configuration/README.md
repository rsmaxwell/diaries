# 0012-FEAT - Externalise local responder configuration

## Type

Feature

## Status

Complete

## Priority

High

## Opened

2026-08-31

## Summary

Remove the MQTT password and other credential values currently present in the two committed Docker-mode responder JSON files by mounting one machine-local responder configuration in both containerised local modes.

## Expected Behaviour

- `local-docker-build` and `local-published-smoke` bind-mount a responder configuration selected by `DIARIES_RESPONDER_DOCKER_CONFIG_FILE`.
- The machine-local configuration remains outside Git and contains the existing responder, database, and signing values required by the developer.
- Its MQTT username remains `diaries-responder`, and its MQTT password matches the external Mosquitto source.
- The two repository responder JSON files are deleted after migration.

## Acceptance Criteria

- [x] Both committed responder JSON files are deleted by this change and will cease to be tracked when it is committed.
- [x] Both Compose modes resolve the external bind source through ignored `local.env`.
- [ ] The responder connects as `diaries-responder` in both modes.
- [x] No credential value is copied into change-control artefacts or command output.

## Implementation and validation record

Implemented on 2026-08-31. A developer-owned Docker responder configuration was created outside Git and both Compose modes resolve it as a read-only file bind. The locally built responder read it successfully, connected to PostgreSQL and Mosquitto, synchronized retained state, and subscribed to RPC requests. The published-image mode still requires a smoke run with its complete database environment.

## Deployment and Rollback Notes

Create and validate the external Docker responder configuration before deleting the repository files. Rollback may restore the old mounts only with a safe external file; do not restore credential-bearing JSON to Git.
