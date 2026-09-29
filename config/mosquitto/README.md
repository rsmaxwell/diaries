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
diaries-web:<local-web-password>
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

## Read-only web projection

The `diaries-web` identity can receive only the five canonical lookup
families for diaries, pages, fragments, marquees and Image metadata:

```text
diaries/diaries/+
diaries/pages/+
diaries/fragments/+
diaries/marquees/+
diaries/images/+
```

It has no write permission and no RPC, date-index, people, role or
`diaries-sync/#` permission. The Image permission is metadata-only; image bytes
continue to be served over HTTP from the configured Files route. Set the web
password through `DIARIES_WEB_MQTT_PASSWORD`; do not put it in the web JSON
configuration.

The web identity also has an explicit `topic deny diaries/rpc/#` rule.
Mosquitto `pattern` rules apply to every user, so the existing client-ID reply
pattern otherwise permits the web reader to receive its own RPC response
topic. The user-scoped deny overrides that shared grant without changing the
client or health-check reply permissions. Apply the same deny in production.

All three local Compose modes mount this same `aclfile.txt`, so changing this
file updates the intended ACL source for development-infrastructure,
local-docker-build and local-published-smoke. Restart/reload the selected
Mosquitto broker after changing the file; a running broker can still be using
the previous ACL.

With Mosquitto's file ACL, a granted SUBACK does not prove read permission:
unauthorized retained and live messages can be silently withheld. Verify a
controlled canonical Image publication is received using the actual
`diaries-web` identity after deployment/reload. Reader readiness cannot
distinguish an empty catalogue from a silently filtered one. Explicit failed
SUBACK codes do keep the reader unready.

## Responder configuration

The responder has read/write permission on the canonical Image catalogue
`diaries/images/+` for startup replay and retained tombstones. It also has
read/write permission on the transient `diaries-sync/#` namespace used only for
non-retained QoS-1 retained-snapshot drain barriers. The bulk `diaries/#`
snapshot uses QoS 1 with MQTT 5 Receive Maximum 20. The separate barrier
namespace prevents overlapping subscriptions. Keep broker queue capacity
sufficient for the full retained tree (see `max_queued_messages` in
`mosquitto.conf`). Client, web and health identities have no synchronization
barrier permission.

The production Ansible-managed Diaries ACL must carry the same narrow
`diaries-web` Image read permission. Do not replace it with `diaries/images/#`
or a broad `diaries/#` web permission.

The responder run directly with development-infrastructure uses the existing developer-owned `%USERPROFILE%\.diaries\responder.json`.

For `local-docker-build` and `local-published-smoke`, create `%USERPROFILE%\.diaries\responder.docker.json` and set this in ignored `config/environments/local.env`:

```text
DIARIES_RESPONDER_DOCKER_CONFIG_FILE=C:/Users/<username>/.diaries/responder.docker.json
```

Use the real absolute path rather than embedding `${USERPROFILE}` in this value: Docker Compose does not recursively expand variables read from an `--env-file`.

Keep the Docker MQTT host as `diaries-mqtt`, the port as `1883`, and the username as `diaries-responder`. Its password must match the `diaries-responder` entry in the external password source. Never copy the responder configuration into Git or change-control evidence.
