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

The ACL grants `diaries-health` only the permissions needed by the two health checks:

- read `$SYS/broker/version` for Mosquitto health;
- write `diaries/rpc/request` for responder readiness; and
- read `diaries/rpc/<mqtt-client-id>/response` only when the topic's client ID matches the health-check client's own ID.

It does not grant the health user access to retained Diaries business-data topics.

## Responder configuration

The responder run directly with development-infrastructure uses the existing developer-owned `%USERPROFILE%\.diaries\responder.json`.

For `local-docker-build` and `local-published-smoke`, create `%USERPROFILE%\.diaries\responder.docker.json` and set this in ignored `config/environments/local.env`:

```text
DIARIES_RESPONDER_DOCKER_CONFIG_FILE=C:/Users/<username>/.diaries/responder.docker.json
```

Use the real absolute path rather than embedding `${USERPROFILE}` in this value: Docker Compose does not recursively expand variables read from an `--env-file`.

Keep the Docker MQTT host as `diaries-mqtt`, the port as `1883`, and the username as `diaries-responder`. Its password must match the `diaries-responder` entry in the external password source. Never copy the responder configuration into Git or change-control evidence.
