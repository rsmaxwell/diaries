# Development steps — generate production MQTT password file from vaulted variables

## Purpose

Remove the production controller-side plaintext rendering step and derive both the temporary target source and idempotence fingerprint from existing Vault-backed Ansible variables.

## Current behaviour

The authoritative `/home/richard/playbooks` role already uses the four required username/password variables, but renders `roles/diaries/templates/config/mosquitto/pwfile.source.txt.j2` into a controller temporary file, checksums it, copies it to another target temporary file, and runs `mosquitto_passwd -U` there.

The current Playbooks worktree contains unrelated user changes; implementation must preserve them. The current Diaries `pwfile.yaml` itself is unmodified. Inspection of `/etc/ansible/host_vars/pluto.yaml` and `/etc/ansible/host_vars/acorn.yaml` found the required usernames. The client, responder, and health passwords are Vault-tagged; the admin password is currently a literal non-Vault value on both hosts. No value was read into this proposal.

The feature description's older `misc/config/mosquitto/pwfile.source.txt` path is not present in the authoritative tracked Playbooks source, so there is no current file at that path to delete.

## Required behaviour

Use the existing variables without renaming them. Calculate a stable hash over an ordered JSON representation of all eight username/password values. When regeneration is required, create one target temporary file, write its content directly from variables under `no_log`, hash it in place with `mosquitto_passwd -U`, install it with the existing ownership/mode, write only the fingerprint marker, and always delete the temporary file.

## Implementation steps

1. On every production target, use `ansible-vault edit /etc/ansible/host_vars/<host>` to Vault-protect all four existing password variables without changing their values.
2. Verify usernames remain `admin`, `diaries-client`, `diaries-responder`, and `diaries-health` through their existing variable names.
3. Replace controller tempfile/template/stat tasks in `roles/diaries/tasks/pwfile.yaml` with an in-memory deterministic fingerprint task.
4. Retain installed `pwfile.txt` and `pwfile.source.sha256` checks and existing regeneration conditions.
5. Populate the target temporary source directly with `ansible.builtin.copy: content` under `no_log: true`.
6. Retain `mosquitto_passwd -U`, installed owner/group `1883`, mode `0600`, and the target `always` cleanup.
7. Delete `roles/diaries/templates/config/mosquitto/pwfile.source.txt.j2`.
8. Leave the production Compose template, ACL, responder/client templates, variable names, and health-check identity unchanged.

## Files to add, change, or delete

In the Playbooks repository, change:

- `roles/diaries/tasks/pwfile.yaml`

Delete:

- `roles/diaries/templates/config/mosquitto/pwfile.source.txt.j2`

Manual external migration, not a repository file proposal:

- `/etc/ansible/host_vars/pluto.yaml`
- `/etc/ansible/host_vars/acorn.yaml`
- every other target host file defining these passwords

No host-variable contents are included beneath `changed-files` because they contain secrets and live outside the Git repository.

## Migration and setup requirements

Every target must provide non-empty values for:

- `mosquitto_admin_password`
- `mosquitto_client_password`
- `mosquitto_responder_password`
- `mosquitto_health_password`

Each must be protected with Ansible Vault. Use `ansible-vault edit` so the plaintext is not placed on the command line or in shell history. Do not rotate or invent values as part of this implementation. Confirm the production health password matches the `diaries-health` entry that will be generated.

## Tests and verification

1. Review the final Playbooks diff without displaying Vault data or generated source content.
2. Run `ansible-playbook diaries.yaml --syntax-check` with the normal inventory/Vault setup.
3. On a safe target, remove neither persistent data nor unrelated files. Run the role with missing `pwfile.txt` and verify generation succeeds.
4. Verify `stat` reports owner/group `1883` and mode `0600` for installed `pwfile.txt` and that no plaintext `.pwfile.source` temporary file remains.
5. Run the playbook unchanged a second time and verify the password-file task is idempotent.
6. Through `ansible-vault edit` on a safe test target, change one MQTT credential, rerun, and verify regeneration without printing either old or new value; then restore the intended value securely.
7. Independently test a missing checksum marker and confirm regeneration.
8. Confirm normal Ansible output contains no secret values, including with the project's normal verbosity and diff settings.
9. Run `docker compose config`, start the production stack, and verify Mosquitto becomes healthy with `diaries-health`, the responder connects, and client/responder MQTT traffic works.
10. Verify both standalone and shared frontend production modes retain their current MQTT behavior.

## Expected state after completion

Production derives the installed Mosquitto password database from Vault-protected host variables without any controller-side plaintext source template. The installed hash database and marker remain restrictive and idempotent, and runtime Compose/ACL behavior is unchanged.

