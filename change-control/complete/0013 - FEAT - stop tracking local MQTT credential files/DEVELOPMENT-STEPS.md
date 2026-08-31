# Development steps — stop tracking local MQTT credential files

## Purpose

Complete the local repository cleanup after the external generation path is working.

## Current behaviour

Both `config/mosquitto/pwfile.source.txt` and `config/mosquitto/pwfile.txt` are tracked. The first is plaintext and the second is generated credential material. The Compose modes require the second path at runtime, but they do not require it to be tracked.

## Required behaviour

Neither file may remain in Git. The plaintext repository source must be removed. The generated file must remain creatable and usable locally while ignored by Git.

## Implementation steps

1. Confirm `0011` is complete and the external source exists.
2. Add explicit root-relative ignore rules for both old repository paths.
3. Remove `config/mosquitto/pwfile.source.txt` from the repository and working tree.
4. Remove `config/mosquitto/pwfile.txt` from the Git index without relying on its current contents as source; it may remain locally as ignored generated output.
5. Regenerate `pwfile.txt` with `config\mosquitto\mosquitto-passwd.bat` and confirm it stays ignored.
6. Leave all three Compose mounts unchanged.

## Files to add, change, or delete

Change:

- `.gitignore`

Delete from Git:

- `config/mosquitto/pwfile.source.txt`
- `config/mosquitto/pwfile.txt`

The second path continues to exist locally after generation but is no longer a repository file.

## Migration and setup requirements

Before removal, create `%USERPROFILE%\.diaries\pwfile.source.txt` with the existing four usernames and the developer's current matching passwords. Do not paste or archive the old source in change control. Ensure ignored `local.env` health credentials remain consistent.

Because the plaintext credential was previously tracked, repository history still contains it. Credential rotation and any history-rewrite decision are separate security operations requiring explicit coordination; deleting the current file does not erase history.

## Tests and verification

1. Run `git ls-files -- config/mosquitto/pwfile.source.txt config/mosquitto/pwfile.txt` and expect no output.
2. Run `git check-ignore -v config/mosquitto/pwfile.source.txt config/mosquitto/pwfile.txt` using safe empty/generated test paths; verify both rules match.
3. Regenerate `pwfile.txt` and confirm `git status --short` does not list it.
4. Verify `docker compose config` for development-infrastructure, local-docker-build, and local-published-smoke still resolves `/mosquitto/config/pwfile.txt` as a read-only mount.
5. Start each mode separately and confirm MQTT health, responder connection, and client/responder communication.
6. Search the active tracked tree for MQTT credential material by filename and key name, recording only redacted filenames and counts.

## Expected state after completion

The active Diaries repository contains neither the plaintext source nor generated Mosquitto password database. The developer can regenerate the ignored runtime file at the path already consumed by every local mode.

