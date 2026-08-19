# 0010 - FEAT - support standalone and shared production frontends

## Type

Feature

## Status

To do

## Opened

2026-08-18

## Summary

Make the Diaries Ansible production deployment installable in either of two frontend topologies:

- **standalone** — the Diaries Compose stack owns its own Nginx service and public host ports;
- **shared** — the Diaries Compose stack omits Nginx, joins an existing external Docker network, and is exposed through an already-installed infrastructure Nginx service.

The default remains `standalone` so a clean target such as `acorn` can receive a complete Diaries deployment without first installing the shared web infrastructure. A multi-application host such as `pluto` can select `shared` so Diaries can coexist with Jenkins, Archiva and, later, Ledger without competing for ports 80, 443 and 9418.

## Background

The current Diaries production Compose template always creates an `nginx` service and publishes:

```text
80:80
443:443
9418:9418
```

That is suitable for a dedicated target, but it cannot coexist on `pluto`, where `infra-nginx` already owns those host ports and provides the shared entry point for other applications.

Removing the Diaries Nginx service alone is not sufficient. In shared mode the browser-facing Diaries containers must be reachable from `infra-nginx`, the shared Nginx route must be installed safely, and startup/reboot ordering must not make Nginx dependent on Diaries containers already being resolvable.

## Current limitation

The current production deployment has one fixed topology:

```text
browser
  |
diaries-nginx :80/:443/:9418
  |
  +-- diaries-client
  +-- diaries-responder
  +-- diaries-mqtt
```

On a shared target the existing infrastructure stack already has:

```text
browser
  |
infra-nginx :80/:443/:9418
  |
  +-- Jenkins
  +-- Archiva
```

Starting the current Diaries stack on that host would fail when `diaries-nginx` attempts to bind the same public ports.

## Required behaviour

### Standalone mode

With:

```yaml
diaries_frontend_mode: standalone
```

Diaries shall:

- create the existing Diaries Nginx service;
- publish ports 80, 443 and 9418 as before;
- use the existing standalone Diaries Nginx configuration;
- optionally create the Diaries Cloudflare tunnel when `diaries_cloudflare_tunnel_enabled` is true;
- have no dependency on an infrastructure Compose stack or external shared network.

This is the default mode.

### Shared mode

With:

```yaml
diaries_frontend_mode: shared
```

Diaries shall:

- omit the Diaries Nginx service;
- not bind ports 80, 443 or 9418;
- omit the application-specific Cloudflare container;
- attach `diaries-client`, `diaries-responder` and `diaries-mqtt` to the existing external shared Docker network as well as the normal Diaries Compose network;
- leave `diaries-db` only on the private/default Diaries network;
- install a Diaries route into the existing infrastructure Nginx configuration;
- validate and reload the existing Nginx container when that route changes;
- fail early with a useful message if the shared Docker network or shared Nginx installation is missing;
- order the Diaries systemd service after, and require, the infrastructure systemd service on reboot.

## Configuration

The role adds these defaults:

```yaml
diaries_frontend_mode: standalone

diaries_shared_network_name: "{{ shared_network_name | default('infrastructure_shared') }}"
diaries_shared_frontend_project_dir: "{{ projects_dir }}/infrastructure"
diaries_shared_frontend_nginx_container_name: infra-nginx
diaries_shared_frontend_systemd_unit: infrastructure-compose.service
diaries_shared_frontend_location_dir: "{{ diaries_shared_frontend_project_dir }}/nginx/config/conf.d/locations"
diaries_shared_frontend_location_file: "{{ diaries_shared_frontend_location_dir }}/diaries.conf"

diaries_cloudflare_tunnel_enabled: "{{ enable_cloudflare_tunnel | default(false) }}"
```

A dedicated target requires no new host variable because `standalone` is the default.

For `pluto`, add:

```yaml
diaries_frontend_mode: shared
```

to the host variables used by the controller.

## Design details

### Shared Docker network

In shared mode only services that must be reached by the shared reverse proxy join the external network:

```text
infra-nginx
    |
    | infrastructure_shared
    |
    +-- diaries-client
    +-- diaries-responder
    +-- diaries-mqtt

Diaries private/default network
    |
    +-- diaries-db
    +-- diaries-mqtt
    +-- diaries-responder
    +-- diaries-client
```

The database is deliberately not exposed to the shared application network.

### Shared Nginx DNS behaviour

The shared Nginx route uses Docker's embedded DNS resolver (`127.0.0.11`) and variable-based `proxy_pass` targets.

This is important for reboot behaviour. `infra-nginx` must be able to start or reload even when the Diaries containers are temporarily absent. A static `proxy_pass http://diaries-client:8080` can cause Nginx configuration loading to fail if the name is not resolvable at that instant. Request-time resolution avoids that startup coupling.

### Cloudflare

The Diaries-specific Cloudflare container is only rendered when both conditions are true:

```text
diaries_frontend_mode == standalone
diaries_cloudflare_tunnel_enabled == true
```

In shared mode the existing infrastructure Cloudflare service, if enabled, remains responsible for the target's external entry point.

### Transition between modes

When shared mode is selected, the role installs `diaries.conf` in the infrastructure Nginx location directory.

When standalone mode is selected, the role removes a stale shared `diaries.conf` if one exists and reloads a running shared Nginx instance. This prevents an old shared route remaining active after a target is changed back to standalone deployment.

## Scope

### Diaries client

No application source change is required. The existing same-origin responder URL and `/mosquitto/` proxy configuration are retained.

### Diaries responder

No Java responder source change is required. The responder continues to use internal Compose service names for PostgreSQL and MQTT.

### PostgreSQL

No database schema change is required.

### Mosquitto

No broker configuration change is required. In shared mode the Mosquitto container gains membership of the shared Docker network so `infra-nginx` can reach its WebSocket listener.

### Ansible / deployment

This feature changes the Diaries Ansible role only, plus this change-management record.

## Complete changed source-file set

The implementation supplied with this feature contains complete versions of:

```text
playbooks/roles/diaries/defaults/main.yaml
playbooks/roles/diaries/tasks/main.yaml
playbooks/roles/diaries/tasks/copy.yaml
playbooks/roles/diaries/tasks/shared-frontend.yaml                 (new)
playbooks/roles/diaries/tasks/standalone-frontend.yaml             (new)
playbooks/roles/diaries/templates/compose.yaml.j2
playbooks/roles/diaries/templates/.env.j2
playbooks/roles/diaries/templates/config/nginx/shared/diaries.conf.j2 (new)
playbooks/roles/diaries/templates/etc/systemd/system/diaries-compose.service.j2
playbooks/roles/diaries/templates/scripts/start.sh.j2
playbooks/roles/diaries/templates/scripts/status.sh.j2
playbooks/roles/diaries/templates/scripts/shell-prompt-nginx.sh.j2
```

## Implementation steps

See `DEVELOPMENT-STEPS.md` in this feature package for the detailed implementation and verification sequence.

## Acceptance criteria

- [ ] `diaries_frontend_mode` accepts only `standalone` or `shared`.
- [ ] `standalone` is the default and preserves the existing dedicated-host topology.
- [ ] Standalone Compose contains `nginx` and publishes ports 80, 443 and 9418.
- [ ] Shared Compose contains no Diaries `nginx` service and publishes none of those frontend ports.
- [ ] Shared Compose joins client, responder and MQTT to the configured external shared network.
- [ ] The database remains off the shared network.
- [ ] Shared deployment fails clearly if the required external network does not exist.
- [ ] Shared deployment fails clearly if the infrastructure Nginx container/configuration is missing.
- [ ] The shared Nginx route can be loaded while Diaries containers are stopped.
- [ ] `/diaries/` reaches `diaries-client` through `infra-nginx`.
- [ ] `/diaries-responder/` reaches the responder through `infra-nginx`.
- [ ] `/mosquitto` supports MQTT WebSocket upgrade through `infra-nginx`.
- [ ] Shared mode does not start `diaries-cloudflared`.
- [ ] Standalone mode can still optionally start `diaries-cloudflared`.
- [ ] The standalone Nginx shell helper enters `diaries-nginx`.
- [ ] The shared Nginx shell helper enters `infra-nginx`.
- [ ] Rebooting a standalone target restores the complete Diaries stack.
- [ ] Rebooting a shared target restores infrastructure first and then Diaries without breaking shared Nginx startup.
- [ ] Jenkins and Archiva remain reachable on `pluto` after Diaries is installed in shared mode.
- [ ] Existing Diaries database and NAS content survive redeployment.

## Test evidence

### Template validation

```text
Standalone rendered services:
Shared rendered services:
Result:
```

### Standalone target

```text
Target:
Frontend mode: standalone
Ansible command:
docker compose ps:
Browser URL:
MQTT WebSocket result:
Result:
```

### Shared target

```text
Target: pluto
Frontend mode: shared
Shared network:
Shared Nginx container:
Ansible command:
docker compose ps:
infra-nginx nginx -t:
Browser URL:
Jenkins regression check:
Archiva regression check:
Result:
```

### Reboot validation

```text
Target:
Reboot time:
systemctl status infrastructure-compose.service:
systemctl status diaries-compose.service:
docker ps:
Browser result:
Result:
```

## Rollback

Before committing the feature, rollback is simply to restore the previous Diaries role files and redeploy.

For a target already deployed in shared mode:

1. stop the Diaries stack;
2. remove the shared Nginx `diaries.conf` route;
3. reload `infra-nginx`;
4. restore the previous playbook source;
5. choose a dedicated host, or otherwise free ports 80/443/9418, before redeploying the old standalone-only Compose topology.

Do not roll back to the old standalone-only Compose template on `pluto` while `infra-nginx` still owns those ports.

## Follow-on work

Apply the same frontend-topology pattern to the Ledger production role so Ledger can also run either standalone or behind the shared Pluto infrastructure Nginx.
