# 0014-FEAT - Generate production MQTT password file from vaulted variables

## Type

Feature

## Status

In progress

## Priority

High

## Opened

2026-08-31

## Summary

Generate the production Mosquitto password database directly from the existing Ansible MQTT username/password variables, remove the controller-side plaintext template, and retain deterministic idempotence without exposing secrets.

## Expected Behaviour

- The role calculates a deterministic SHA-256 fingerprint from all four username/password pairs in memory.
- A target temporary file is populated directly with `copy: content`, converted with `mosquitto_passwd -U`, installed as owner/group `1883` and mode `0600`, and always removed.
- Unchanged credentials do not regenerate the installed file; changed credentials or missing outputs do.
- All four password variables are Vault-protected in `/etc/ansible/host_vars/<host>`.
- Production Compose health-check and password-file mounts remain unchanged.

## Acceptance Criteria

- [x] No controller or repository plaintext password-source file is required.
- [x] `roles/diaries/templates/config/mosquitto/pwfile.source.txt.j2` is deleted.
- [x] Secret-bearing tasks use `no_log: true`.
- [x] Normal playbook output and change-control files contain no password values.
- [ ] First, unchanged, changed-credential, missing-password-file, and missing-marker cases behave as specified.
- [ ] Mosquitto health and responder connectivity succeed after deployment.

## Implementation and validation record

Implemented in `/home/richard/playbooks` on 2026-08-31. The role now derives the fingerprint and target temporary source directly from the eight existing variables, validates inputs, installs restrictive files, and always cleans up plaintext. The admin password on both `pluto` and `acorn` was encrypted in place without changing its value; all eight host/password entries are now Vault-tagged. `ansible-playbook diaries.yaml --syntax-check --vault-password-file ~/.vault_pass.txt` passed. Target execution and runtime checks remain deliberately pending because production deployment was not authorized.

## Deployment and Rollback Notes

Vault migration is a precondition. The observed `pluto` and `acorn` host files currently have three Vault-tagged MQTT passwords but a literal non-Vault `mosquitto_admin_password`; encrypt that existing value in place without changing it before deployment. Rollback must preserve Vault protection and must not restore the deleted plaintext template.
