# Development steps — externalise local MQTT password source

## Purpose

Make `%USERPROFILE%\.diaries\pwfile.source.txt` the only input used by the existing local Mosquitto password-generation script.

## Current behaviour

`config/mosquitto/mosquitto-passwd.bat` changes into `config/mosquitto`, copies the tracked `pwfile.source.txt` to `pwfile.txt`, and runs `generate-pwfile.sh` inside `eclipse-mosquitto:2`. The three local Compose modes mount the resulting `config/mosquitto/pwfile.txt` read-only.

## Required behaviour

The script must read `%USERPROFILE%\.diaries\pwfile.source.txt`, reject a missing source before doing any work, avoid printing its contents, and continue using the existing Docker and `generate-pwfile.sh` conversion path. A failed copy or conversion must not leave a plaintext working copy behind.

## Implementation steps

1. Create `%USERPROFILE%\.diaries\pwfile.source.txt` before changing the script.
2. Update `config/mosquitto/mosquitto-passwd.bat` to define and validate the external path before `pushd`.
3. Copy the external source to the existing working output path, run the unchanged `eclipse-mosquitto:2` conversion, and delete the working output on failure.
4. Add `config/mosquitto/README.md` with safe setup, format, generation, and health-check guidance.
5. Add artificial health-check placeholders to `config/environments/local.env.example`; keep real values only in ignored `local.env`.
6. Do not alter `generate-pwfile.sh`, the three Compose files, `aclfile.txt`, or any username.

## Files to add, change, or delete

Add:

- `config/mosquitto/README.md`

Change:

- `config/mosquitto/mosquitto-passwd.bat`
- `config/environments/local.env.example`

Delete:

- None in this feature. Deletion of tracked credential files is deliberately deferred to `0013` so the external generation path can be prepared and verified first.

## Migration and setup requirements

Create the directory and source file outside Git. The file must contain exactly the required identities in `username:password` form:

```text
admin:<local-admin-password>
diaries-client:<local-client-password>
diaries-responder:<local-responder-password>
diaries-health:<local-health-password>
```

The angle-bracketed values above are placeholders, not passwords to copy literally. Set `DIARIES_MQTT_HEALTH_USERNAME=diaries-health` in ignored `config/environments/local.env`, and make its password match the `diaries-health` entry.

## Tests and verification

1. Temporarily move the external source aside, run `config\mosquitto\mosquitto-passwd.bat`, and verify a non-zero exit and the missing-file message without credential output.
2. Restore the source, run the script, and verify exit code zero.
3. Verify `config/mosquitto/pwfile.txt` contains Mosquitto password hashes rather than the source plaintext, without recording either file in test evidence.
4. Run `docker compose config` for all three local Compose files with the normal mode environment plus ignored `local.env`.
5. Start each local mode separately and verify Mosquitto becomes healthy and `diaries-health` can read `$SYS/broker/version`.
6. Verify the existing responder and client communication still works; record only pass/fail and redacted logs.

## Expected state after completion

Local password generation uses only the external developer file, while the generated output path, ACL, Compose mounts, health-check identity, and conversion implementation remain compatible with later cleanup features.

