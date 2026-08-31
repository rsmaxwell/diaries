# 0011-FEAT - Externalise local MQTT password source

## Type

Feature

## Status

In progress

## Priority

High

## Opened

2026-08-31

## Summary

Generate the local Mosquitto password database from the developer-owned `%USERPROFILE%\.diaries\pwfile.source.txt` file instead of the repository copy.

## Expected Behaviour

- `config/mosquitto/mosquitto-passwd.bat` fails clearly when the external source is missing.
- The script does not fall back to the repository source or print credential contents.
- The existing Docker-based `mosquitto_passwd -U` mechanism still produces `config/mosquitto/pwfile.txt`.
- Local setup documentation identifies the four required MQTT users and the existing health-check configuration without including passwords.

## Scope

This feature changes only the local password-generation entry point, machine-local environment example, and Mosquitto setup documentation. Compose mounts, ACLs, usernames, and `generate-pwfile.sh` remain unchanged.

## Acceptance Criteria

- [x] The external source is checked before changing directory, copying files, or starting Docker.
- [x] Missing input returns a non-zero exit code and a useful path-specific message.
- [x] Failed conversion removes any plaintext working copy from `config/mosquitto/pwfile.txt`.
- [x] Successful conversion retains the generated password database at the existing Compose-mounted path.
- [x] Documentation contains no actual password.

## Implementation and validation record

Implemented on 2026-08-31. The existing credential values were copied to the external developer-owned source without printing them. Successful generation, missing-source failure, plaintext cleanup, all three Compose configurations, and an authenticated development-infrastructure Mosquitto health check were verified.

## Deployment and Rollback Notes

Create the external source before applying this feature. Rollback restores the previous script, but that would reintroduce dependency on repository-held plaintext and is not an acceptable long-term security state.
