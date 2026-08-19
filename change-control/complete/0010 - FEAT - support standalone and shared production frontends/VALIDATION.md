# Validation performed while preparing this package

The proposed files were checked locally without connecting to the user's target machines.

Completed checks:

- YAML parsing of all changed/new Ansible task files.
- Jinja rendering of `compose.yaml.j2` in both `standalone` and `shared` modes.
- YAML parsing of both rendered Compose documents.
- Verified rendered standalone services are:
  - `nginx`
  - `diaries-db`
  - `diaries-mqtt`
  - `diaries-responder`
  - `diaries-client`
- Verified rendered shared services are:
  - `diaries-db`
  - `diaries-mqtt`
  - `diaries-responder`
  - `diaries-client`
- Verified shared rendered Compose declares external network `infrastructure_shared` in the test rendering.
- Jinja rendering of the changed operational scripts in both modes.
- `bash -n` syntax checking of the rendered `start.sh`, `status.sh` and `shell-prompt-nginx.sh` scripts in both modes.

Not performed here:

- `ansible-playbook --syntax-check` against the user's actual controller inventory and Vault variables.
- live `docker compose config` on `pluto` or `acorn`;
- live Nginx reload;
- browser/MQTT smoke tests;
- reboot testing.

Those tests are included in `DEVELOPMENT-STEPS.md` and should be completed before moving the change-management item to `complete`.
