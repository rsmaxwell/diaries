# 0031-FEAT Step 14 runtime runbook

Step 13 handed production to this step with `diaries-responder` intentionally stopped. Keep that write freeze in force until the Step 14 preflight passes and the normal Ansible deployment deliberately restarts the stack.

Also keep local Diaries modes stopped or otherwise free of Image/File lifecycle activity during this deployment window. Step 14 brackets every `files-development-*` root and will fail if non-production Files bytes change between preflight and postflight.

## 1. Apply the Step 14 source package

Apply the supplied Diaries/Playbooks changed files. On the Playbooks source tree, run the portable checks before touching production:

```bash
cd ~/playbooks
python3 roles/diaries/tests/verify-0031-step14.py
python3 roles/diaries/tests/verify-0031-storage-isolation.py
python3 roles/diaries/tests/verify-0031-step13.py
bash -n roles/diaries/files/sync/scripts/step14-production-deployment.sh
```

All must pass.

## 2. Install only the Step 14 helper on `pluto`

The helper is needed before the full playbook run, while the production responder must remain stopped. Copy only this file first; do not run the playbook yet.

From `mango`:

```bash
scp ~/playbooks/roles/diaries/files/sync/scripts/step14-production-deployment.sh \
  pluto:/home/richard/projects/diaries/scripts/
ssh pluto chmod +x /home/richard/projects/diaries/scripts/step14-production-deployment.sh
```

## 3. Confirm the production inventory selector

On `mango`, verify the inventory file that owns the production Diaries settings still contains:

```yaml
diaries_files_dir: files
```

For the current installation this is expected in:

```text
/etc/ansible/host_vars/pluto/diaries.yaml
```

A simple non-secret check is:

```bash
grep -n '^[[:space:]]*diaries_files_dir:' /etc/ansible/host_vars/pluto/diaries.yaml
```

Do not continue if the effective production selector is not `files`.

## 4. Run the production preflight on `pluto`

```bash
cd /home/richard/projects/diaries
./scripts/step14-production-deployment.sh preflight
```

Expected final output:

```text
PASS: Step 14 production preflight is clean.
Production responder remains stopped for the normal Ansible deployment.
Evidence: /home/richard/projects/diaries/data/0031-step14/preflight-YYYYMMDD-HHMMSS
```

Record that exact preflight directory.

Review these files before deploying:

```text
REDACTED-CONFIG.txt
STEP8-DATABASE-BACKUP-CHECK.txt
STEP8-FILES-SNAPSHOT-CHECK.txt
STEP13-HANDOFF-CHECK.txt
PAIR.txt
```

The redacted configuration must show:

```text
DIARIES_FILES_DIR=files
compose dataFilesTarget=/data/files
compose dataFilesSubpath=${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}
containsMutableSelector=yes
containsHardCodedMutableFiles=no
mentionsLocalEnv=no
```

The Step 8 checks must both report `PASS`, and the Step 13 hand-off check must prove the production Image/File controls are still byte-for-byte unchanged from the authoritative Step 13 AFTER capture.

## 5. Deploy the production configuration from `mango`

Use the existing Diaries Playbooks deployment path. Capturing the command/result with `tee` provides the required controller-side deployment evidence without enabling Ansible `--diff` (which must not be used because the rendered `.env` contains secrets).

```bash
cd ~/playbooks
stamp=$(date +%Y%m%d-%H%M%S)
ansible-playbook diaries.yaml \
  --limit pluto \
  --vault-password-file ~/.vault_pass.txt \
  --tags copy \
  2>&1 | tee ~/0031-step14-ansible-${stamp}.txt
```

The `copy` tag is the same path used by the existing `scripts/diaries.sh`; it synchronises the role-managed configuration/templates and triggers the Diaries systemd restart handler. This deployment installs the permanent Step 14 helper and changes the production Diaries broker queue policy from the old `10000` ceiling to `0` while retaining `max_inflight_messages 20`. The role validates those installed broker lines before the restart handler is allowed to run.

Do not use `--diff`.

If Ansible fails, stop here. Do not run postflight as though the deployment succeeded.

## 6. Run postflight on `pluto`

Use the exact preflight directory from Step 4:

```bash
cd /home/richard/projects/diaries
./scripts/step14-production-deployment.sh postflight \
  /home/richard/projects/diaries/data/0031-step14/preflight-YYYYMMDD-HHMMSS
```

Postflight first verifies the restarted stack and current responder synchronisation. It then stops only `diaries-responder`, performs the deterministic comparisons and Step 12 dry-run reconciliation, and restarts the responder only if all checks pass.

Expected final output:

```text
PASS: Step 14 production deployment is healthy and non-destructive.
Evidence: /home/richard/projects/diaries/data/0031-step14/postflight-YYYYMMDD-HHMMSS
```

If the helper reports that it has intentionally left `diaries-responder` stopped, do not restart it manually until the reported mismatch/failure has been investigated.

## 7. Preserve the runtime evidence

Copy the complete successful preflight and postflight directories into:

```text
change-control/in-progress/0031-FEAT - isolate mutable Files storage by database environment/evidence/Step 14/runtime/
```

Also preserve the controller-side Ansible log from `mango`. It may be stored beside the runtime directories after checking that it contains no secret material.

Do not copy the production `.env` itself into Git. `REDACTED-CONFIG.txt` and `REDACTED-CONFIG-AFTER-DEPLOY.txt` are the intended long-term configuration evidence.

## 8. Completion decision

Step 14 can be closed only when the reviewed evidence proves all of the following:

```text
Step 8 database backup still available and hash-valid
Step 8 Files rollback snapshot still available
production inventory explicitly selects files
no local.env participation in production deployment
Ansible deployment successful
production broker loaded max_inflight_messages 20 / max_queued_messages 0
all services healthy
current responder startup logged synchronise: ok
existing /files object served unchanged bytes
production Image rows unchanged
production Files SHA-256 inventory unchanged
all files-development-* SHA-256 inventories unchanged
Step 12 read-only reconciliation still PASS
responder restarted and final stack healthy
```

No production Image upload/delete/replace is required or permitted by this Step 14 proof.
