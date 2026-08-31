# Files to delete or stop tracking

- Delete `config/mosquitto/pwfile.source.txt` from the repository and local working tree after the external source is verified.
- Remove `config/mosquitto/pwfile.txt` from Git. Do not copy its generated hashes into this proposal; the ignored file is recreated locally by `mosquitto-passwd.bat`.

Neither credential-bearing file is intentionally reproduced beneath `changed-files`.

