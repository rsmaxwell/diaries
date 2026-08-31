# Local Mosquitto credentials

Local Mosquitto credentials are developer-specific and must not be stored in Git.

## Password source

Create:

```text
%USERPROFILE%\.diaries\pwfile.source.txt
```

Use `username:password` format with one entry for each required identity:

```text
admin:<local-admin-password>
diaries-client:<local-client-password>
diaries-responder:<local-responder-password>
diaries-health:<local-health-password>
```

Replace every angle-bracketed placeholder with a local password. Do not copy real passwords into documentation, committed environment files, or change-control evidence.

## Generate the password database

From the repository root, run:

```bat
config\mosquitto\mosquitto-passwd.bat
```

The script uses `eclipse-mosquitto:2` and `generate-pwfile.sh` to create the Compose-mounted `config/mosquitto/pwfile.txt`. The generated file is credential material and must not be committed.

## Health-check configuration

In ignored `config/environments/local.env`, set `DIARIES_MQTT_HEALTH_USERNAME` to `diaries-health` and set `DIARIES_MQTT_HEALTH_PASSWORD` to the password used by that entry in the external source. Do not use the `admin` account for health checks.

The ACL intentionally grants `diaries-health` read access only to `$SYS/broker/version`.

