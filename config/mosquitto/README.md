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

## Editing-client Image projection

The `diaries-client` identity can read the canonical retained Image metadata
lookup topic:

```text
diaries/images/+
```

This permission is required by the first-class ImageFragment editor so a
selected IMAGE Fragment can resolve its `imageId` to retained Image metadata.
It is read-only and metadata-only; Image bytes continue to use HTTP/static
Files routes. The existing RPC, Fragment, Marquee and date-index permissions
remain unchanged. Restart/reload Mosquitto after ACL changes before live client
verification.

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
non-retained QoS-1 retained-snapshot drain barriers. The retained snapshot uses QoS 1 with MQTT 5 Receive Maximum 20. The separate barrier
namespace prevents overlapping subscriptions. Step 13 also requires the local broker
to use `max_queued_messages 0` so an already-large retained replay cannot be silently
truncated at an arbitrary fixed message-count limit. Client, web and health identities
have no synchronization barrier permission.

The production Ansible-managed Diaries ACL must carry the same narrow
`diaries-web` Image read permission. Do not replace it with `diaries/images/#`
or a broad `diaries/#` web permission.

The responder run directly with development-infrastructure uses the developer-owned `%USERPROFILE%\.diaries\responder.json` as its base. `scripts/windows/development-infrastructure/prepare-responder-config.bat` generates an ignored effective copy whose `diaries.files` value comes from `development-infrastructure.env` followed by `local.env`, so the direct responder follows the same database/Files dataset selection as the local environment.

For `local-docker-build` and `local-published-smoke`, create `%USERPROFILE%\.diaries\responder.docker.json` and set this in ignored `config/environments/local.env`:

```text
DIARIES_RESPONDER_DOCKER_CONFIG_FILE=C:/Users/<username>/.diaries/responder.docker.json
```

Use the real absolute path rather than embedding `${USERPROFILE}` in this value: Docker Compose does not recursively expand variables read from an `--env-file`.

Keep the Docker MQTT host as `diaries-mqtt`, the port as `1883`, and the username as `diaries-responder`. Its password must match the `diaries-responder` entry in the external password source. Never copy the responder configuration into Git or change-control evidence.

## Step 13 retained-snapshot queue safeguard (interim)

`0031-FEAT` Step 13 exposed two different MQTT backlog risks: publishing a large database snapshot into an empty broker, and a newly attached responder snapshot client receiving an already-large retained tree. The first path can be paced by the application; the second path is broker-driven once a subscription is accepted.

For the second path the local Diaries broker now uses:

```text
max_inflight_messages 20
max_queued_messages 0
```

`max_inflight_messages 20` retains bounded QoS 1/2 flow on the wire. `max_queued_messages 0` removes the message-count queue ceiling so an already-populated retained tree cannot be truncated merely because the replay contains more than an arbitrary fixed number of messages. The responder also keeps the Step 13 branch-by-branch retained snapshot (`diaries/diaries/#`, `diaries/pages/#`, and so on) because smaller replay units remain useful for progress, diagnostics and peak backlog reduction.

This is an **interim correctness safeguard**, not the final MQTT snapshot architecture. After the current TODO features are complete, revisit this design and consider a bounded protocol that segments the subscription space more finely and paces successive subscriptions (or otherwise makes complete retained-tree recovery explicit) before reintroducing a finite queue limit. Do not reduce `max_queued_messages` from `0` until the replacement design proves that a complete retained snapshot cannot be silently truncated.

