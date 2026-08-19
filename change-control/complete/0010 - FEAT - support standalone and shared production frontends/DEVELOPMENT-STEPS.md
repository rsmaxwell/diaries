# Development steps — Diaries standalone/shared production frontend

These steps implement change-management feature **0010 - FEAT - support standalone and shared production frontends**.

The implementation is based on the supplied source bundles:

```text
playbook-sources-20260818-171927.zip
diaries-sources-20260818-171935.zip
```

## 1. Create the change-management item

Create:

```text
diaries/change-control/todo/0010 - FEAT - support standalone and shared production frontends/README.md
```

Use the supplied feature `README.md` as its initial content.

## 2. Add frontend-mode defaults

Edit:

```text
playbooks/roles/diaries/defaults/main.yaml
```

Add `diaries_frontend_mode`, defaulting to `standalone`, plus the shared-network, infrastructure-Nginx and systemd integration defaults.

Keep the default standalone so existing dedicated-host deployments do not require a new variable.

## 3. Validate the mode early

Edit:

```text
playbooks/roles/diaries/tasks/main.yaml
```

Add an `assert` accepting only:

```text
standalone
shared
```

Tag the validation `always` so invalid configuration is rejected even when running a tagged subset of the role.

## 4. Make the Compose Nginx service conditional

Edit:

```text
playbooks/roles/diaries/templates/compose.yaml.j2
```

Wrap the Diaries `nginx` service so it is rendered only in standalone mode.

Also make the Diaries Cloudflare service conditional on both standalone mode and `diaries_cloudflare_tunnel_enabled`.

## 5. Add shared-network membership

In the same Compose template, when frontend mode is shared:

- connect `diaries-client` to `default` and `shared`;
- connect `diaries-responder` to `default` and `shared`;
- connect `diaries-mqtt` to `default` and `shared`;
- leave `diaries-db` on the default/private network only;
- define `shared` as an external network whose name is `diaries_shared_network_name`.

Do not publish Nginx host ports in shared mode because there is no Diaries Nginx service.

## 6. Make the Cloudflare environment consistent

Edit:

```text
playbooks/roles/diaries/templates/.env.j2
```

Only render `CLOUDFLARE_TUNNEL_TOKEN` when the Diaries stack is standalone and its own tunnel is enabled.

This prevents a generic infrastructure `enable_cloudflare_tunnel` setting on `pluto` from accidentally creating a second application-specific tunnel.

## 7. Add a shared Nginx route

Add:

```text
playbooks/roles/diaries/templates/config/nginx/shared/diaries.conf.j2
```

The route should provide:

```text
/diaries/            -> diaries-client:8080
/diaries-responder/  -> diaries-responder:8081
/mosquitto            -> diaries-mqtt:9001
```

Use Docker embedded DNS (`127.0.0.11`) and variable-based `proxy_pass` values so Nginx can load the configuration even when the Diaries containers are absent during startup or maintenance.

Preserve the existing responder prefix-removal behaviour with an explicit rewrite before proxying.

## 8. Add shared-frontend Ansible tasks

Add:

```text
playbooks/roles/diaries/tasks/shared-frontend.yaml
```

The tasks should:

1. verify the external shared Docker network exists;
2. verify the shared Nginx container exists;
3. verify the shared Nginx location directory exists;
4. install the shared `diaries.conf`;
5. run `nginx -t` inside `infra-nginx` when the route changes;
6. reload Nginx after successful validation.

Import the task file from `tasks/main.yaml` only when `diaries_frontend_mode == 'shared'`.

## 9. Clean up a stale shared route in standalone mode

Add:

```text
playbooks/roles/diaries/tasks/standalone-frontend.yaml
```

When deploying standalone mode, remove a previously installed shared `diaries.conf` if it exists. If the shared Nginx container is running, validate and reload it after removing the route.

This makes switching modes explicit and idempotent.

## 10. Update systemd ordering

Edit:

```text
playbooks/roles/diaries/templates/etc/systemd/system/diaries-compose.service.j2
```

Standalone mode should retain its Docker dependency.

Shared mode should additionally be ordered after and require:

```text
infrastructure-compose.service
```

or the configured `diaries_shared_frontend_systemd_unit`.

This makes reboot ordering deterministic on `pluto`.

## 11. Update operational scripts

Edit:

```text
playbooks/roles/diaries/templates/scripts/start.sh.j2
playbooks/roles/diaries/templates/scripts/status.sh.j2
playbooks/roles/diaries/templates/scripts/shell-prompt-nginx.sh.j2
```

Required behaviour:

- `start.sh` checks the shared network/Nginx preconditions in shared mode before running Compose;
- `status.sh` reports the selected frontend mode and shared Nginx status;
- `shell-prompt-nginx.sh` enters `diaries-nginx` in standalone mode and `infra-nginx` in shared mode.

## 12. Ensure configuration changes restart the Diaries stack

Edit:

```text
playbooks/roles/diaries/tasks/copy.yaml
```

Notify the existing `Restart diaries stack` handler when synchronized/template deployment files change. This ensures a changed Compose topology is applied rather than merely copied to disk.

## 13. Configure `pluto`

In the controller inventory/host variables actually used by Ansible, add:

```yaml
diaries_frontend_mode: shared
```

Ensure `pluto` also has all existing Diaries credentials, NAS settings, image tags and container-name variables required by the role.

Do not set shared mode on a clean host unless the infrastructure stack has already created the shared network and Nginx service.

## 14. Leave a clean standalone target unchanged

For a dedicated host such as `acorn`, either omit the new variable or set:

```yaml
diaries_frontend_mode: standalone
```

No infrastructure stack should be required for this mode.

## 15. Static validation before deployment

On `mango`, check the Ansible syntax and render path before touching `pluto`.

Suggested checks:

```bash
cd ~/playbooks
ansible-playbook diaries.yaml --syntax-check
```

If you have a test inventory/host, render/copy only first and inspect the result:

```bash
./scripts/diaries.sh   # or the equivalent command with --tags copy
```

On the target inspect:

```bash
cd ~/projects/diaries
docker compose config
```

For shared mode verify the resolved Compose output contains no `nginx:` service and contains the external shared network.

## 16. Deploy and test shared mode on `pluto`

Before deployment:

```bash
docker ps
docker compose ls
docker network inspect infrastructure_shared
```

Confirm `infra-nginx`, Jenkins and Archiva are healthy.

Run the Diaries playbook.

Then verify:

```bash
cd ~/projects/diaries
./scripts/status.sh

docker compose config --services
docker network inspect infrastructure_shared
docker exec infra-nginx nginx -t
docker exec infra-nginx nginx -T | grep -A20 -B2 'location /diaries/'
```

Expected Compose services in shared mode:

```text
diaries-db
diaries-mqtt
diaries-responder
diaries-client
```

There must be no Diaries `nginx` or `cloudflared` service.

## 17. Verify application routing

From `pluto` and from a browser, test:

```bash
curl -I http://localhost/diaries/
curl -I http://localhost/diaries-responder/
```

Then sign in through the Diaries GUI and verify:

- diary list loads;
- retained MQTT state is received;
- diary page images load from NAS-backed content;
- responder requests work;
- browser MQTT WebSocket connection works.

Inspect browser console, responder logs, Mosquitto logs and Nginx logs together if anything fails.

## 18. Regression-test existing shared applications

After installing Diaries on `pluto`, verify that the existing shared routes still work:

- Jenkins;
- Archiva;
- any existing static-file route.

The Diaries deployment must not restart or replace `infra-nginx`; it should only install/reload its location file.

## 19. Reboot-test shared mode

Reboot `pluto` and verify:

```bash
systemctl status infrastructure-compose.service
systemctl status diaries-compose.service
docker ps
kubectl get pods
```

Then test Jenkins, Archiva and Diaries again.

This is important because the shared Nginx route has deliberately been designed so `infra-nginx` can start even before Diaries service names are available.

## 20. Validate standalone mode on a clean target

On `acorn` or another disposable/dedicated host:

```yaml
diaries_frontend_mode: standalone
```

Deploy and verify:

```bash
cd ~/projects/diaries
docker compose config --services
docker compose ps
```

Expected services include `nginx`. If the Diaries-specific Cloudflare tunnel is disabled, `cloudflared` should be absent.

Confirm ports 80/443/9418 are owned by the Diaries Nginx service and the application works without an infrastructure installation.

## 21. Record evidence and complete the feature

When both topologies have passed:

- record playbook output;
- record `docker compose config --services` for both modes;
- record shared network membership;
- record Nginx validation output;
- record browser smoke-test results;
- record reboot results;
- record Git commit IDs;
- move the change-control directory from `todo` through `in-progress` to `complete` according to the project's normal process.
