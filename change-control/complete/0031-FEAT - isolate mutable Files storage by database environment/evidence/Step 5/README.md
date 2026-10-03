# 0031-FEAT — Step 5 evidence

## Step

**Step 5 — Add explicit production Files-root configuration to the Ansible role**

## Implementation result

**SOURCE IMPLEMENTATION COMPLETE — 2026-10-02**

The Playbooks `diaries` role now treats the mutable Files leaf as an explicit deployment input rather than silently assuming the production `files` directory.

The approved production selector remains:

```yaml
diaries_files_dir: files
```

but there is deliberately **no role default** for `diaries_files_dir`.

## Fail-fast preflight

`roles/diaries/tasks/main.yaml` now validates `diaries_files_dir` before the role performs deployment work. The selector must be defined, be a string, be non-empty, and be one leaf-directory name containing only letters, digits, `.`, `_` or `-`, beginning with an alphanumeric character.

This rejects missing values, blank values, absolute paths, path separators, whitespace and traversal-style values. A missing production inventory value therefore stops safely instead of reverting to the old production Files root.

## Generated production configuration

`roles/diaries/templates/.env.j2` now renders:

```text
DIARIES_FILES_DIR={{ diaries_files_dir }}
```

and the responder mutable volume in `roles/diaries/templates/compose.yaml.j2` now uses:

```yaml
subpath: ${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}
```

The original diary-page source mount remains unchanged and read-only:

```yaml
subpath: ${DIARIES_NAS_CONTENT_PATH}/diaries
```

## Render validation

Immediately after the role templates the deployment files, `roles/diaries/tasks/copy.yaml` verifies that:

```text
.env contains exactly DIARIES_FILES_DIR=<effective diaries_files_dir>
compose.yaml contains subpath: ${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}
```

Those checks are read-only and report no secret values.

The packaging-time source/render verification also confirms that:

- the edited Ansible YAML files parse successfully;
- `.env.j2` renders `DIARIES_FILES_DIR=files` when the production selector is supplied;
- `.env.j2` fails under strict rendering when `diaries_files_dir` is absent;
- the Compose template renders the selector-based mutable mount;
- the read-only diary mount remains `${DIARIES_NAS_CONTENT_PATH}/diaries`;
- the old hard-coded `${DIARIES_NAS_CONTENT_PATH}/files` mutable mount is absent; and
- `roles/diaries/defaults/main.yaml` contains no `diaries_files_dir` assignment.

The captured checks are in `verification-output.txt`.

## Production inventory action still required

The uploaded Playbooks source bundle contains the reusable Git repository but not the external Ansible inventory commonly held under `/etc/ansible/group_vars/` or `/etc/ansible/host_vars/`. Therefore that live production configuration was not edited here.

Before the next Diaries production deployment, add this to the existing inventory file that already owns the production Diaries NAS/database settings:

```yaml
diaries_files_dir: files
```

Do **not** add this as a role default. If the inventory update is omitted, the updated role is expected to fail at its preflight assertion before templating/deployment.

After adding the inventory value, run the normal production playbook and retain the successful preflight/render output as runtime closure evidence. No database row, NAS file, Docker volume or retained MQTT state is changed by this source implementation itself.

## Changed Playbooks files

```text
roles/diaries/defaults/main.yaml
roles/diaries/tasks/main.yaml
roles/diaries/tasks/copy.yaml
roles/diaries/templates/.env.j2
roles/diaries/templates/compose.yaml.j2
```

Feature documentation is also updated to record the Step 5 implementation and the external inventory action.
