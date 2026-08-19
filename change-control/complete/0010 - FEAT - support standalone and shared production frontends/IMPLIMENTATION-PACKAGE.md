# Diaries FEAT-0010 implementation package

This package contains a proposed implementation for making the Diaries production Ansible role usable in either a standalone or shared frontend environment.

## Source basis

The files were prepared from the supplied source bundles dated 2026-08-18:

```text
playbook-sources-20260818-171927.zip
diaries-sources-20260818-171935.zip
```

## Package contents

```text
README-FIRST.md
DEVELOPMENT-STEPS.md
change-management/README.md
changed-source-files/
  playbooks/roles/diaries/...
changes.patch
```

`changed-source-files` contains the **complete contents** of every playbook file proposed to be added or changed. Copy/review these against the corresponding files under `~/playbooks` on the controller.

`changes.patch` is a convenience unified diff against the supplied playbook source bundle.

## Intended deployment modes

```yaml
# Dedicated/empty target such as acorn
diaries_frontend_mode: standalone
```

```yaml
# Shared multi-application target such as pluto
diaries_frontend_mode: shared
```

The default is `standalone`.

## Important

The shared mode assumes that the infrastructure stack already owns the external Docker network (default `infrastructure_shared`) and the Nginx container (`infra-nginx`). It intentionally does not create those resources itself.

The supplied files have been structurally checked by rendering the Compose Jinja template in both modes and parsing the resulting YAML. They have not been executed against your live `pluto` or `acorn` hosts, so follow the staged tests in `DEVELOPMENT-STEPS.md` before treating the feature as complete.
