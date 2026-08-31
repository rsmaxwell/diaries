# 0013-FEAT - Stop tracking local MQTT credential files

## Type

Feature

## Status

Complete

## Priority

High

## Opened

2026-08-31

## Summary

Remove the local plaintext Mosquitto source and generated Mosquitto password database from Git, while keeping the generated output available as an ignored local runtime file.

## Expected Behaviour

- `config/mosquitto/pwfile.source.txt` no longer exists in the repository.
- `config/mosquitto/pwfile.txt` is no longer tracked and is ignored.
- Running the externalized generator recreates or updates the ignored local `pwfile.txt` used by all three Compose modes.
- Git cannot accidentally stage either old repository path through a normal `git add`.

## Acceptance Criteria

- [ ] Both credential files are absent from `git ls-files` after this uncommitted deletion is committed.
- [x] `.gitignore` covers both the obsolete plaintext path and generated password database path.
- [x] The external source and generated output are not copied into change control.
- [x] All three Compose files retain their existing read-only runtime mount.

## Implementation and validation record

Implemented in the working tree on 2026-08-31. Both tracked credential files are deleted, both paths match explicit ignore rules, generation from the external source succeeds, and the generated hashes were used by a healthy Mosquitto container. Git will stop listing the deleted paths only after the user commits this change.

## Deployment and Rollback Notes

This feature depends on `0011`. Do not remove the tracked source until the developer-owned source has been created and generation has succeeded. A rollback must not recommit either credential file.
