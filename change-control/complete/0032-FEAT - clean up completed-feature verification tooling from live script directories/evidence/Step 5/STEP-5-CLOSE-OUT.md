# 0032 Step 5 close-out — Clean the Playbooks source and permanent production tooling model

## Status

**COMPLETE — 2026-10-03**

## Scope completed

Step 5 applied the frozen Step 2 disposition to the authoritative Playbooks checkout at:

```text
/home/richard/playbooks
```

The Playbooks role now models only supported permanent production tooling. Completed migration/deployment helpers are no longer present in role source, retained regression coverage uses behaviour-oriented names, and deployment contains an explicit narrowly-scoped stale-file removal list for the later production cleanup.

No Diaries playbook deployment to `pluto` was performed by Step 5. Deployed production cleanup remains Step 6.

## Source changes accepted

The authoritative Playbooks source now:

- retains the supported production backup/restore scripts plus `dataset-backup-manifest.py`;
- removes the eight approved completed-feature helpers from `roles/diaries/files/sync/scripts/`;
- removes `migration0024ImageCatalogue.sh` from the supported live production tooling model;
- replaces live `verify-0031-*` coverage with three behaviour-oriented production regressions;
- updates current role/operator documentation;
- adds an explicit Ansible `state: absent` removal list for the exact eight obsolete deployed filenames;
- continues to avoid unrestricted `rsync --delete`.

The approved stale deployed filenames are:

```text
migration0024ImageCatalogue.sh
step8-freeze-writes.sh
step8-capture-production-database-backup.sh
step9-reconcile-production.sh
step12-compare-reconciliation.py
step12-reconcile-production.sh
step13-capture-production-control.sh
step14-production-deployment.sh
```

## Authoritative application result

`apply-step5-playbooks-source.sh /home/richard/playbooks` successfully applied the Step 5 patch. Git emitted file-mode warnings because the patch snapshot represented some executable files as `100644` while the authoritative checkout held them as `100755`; these warnings did not prevent application.

The wrapper then stopped before validation because `mango` provides `python3` rather than a `python` command:

```text
Applied Step 5 Playbooks source patch.
./apply-step5-playbooks-source.sh: line 30: python: command not found
```

This launcher issue did not affect the applied source. The three validators were then run directly using `python3` against the authoritative checkout.

## Authoritative validation result

All three permanent validators passed:

```text
python3 roles/diaries/tests/verify-production-backup-restore-semantics.py
python3 roles/diaries/tests/verify-production-storage-isolation.py
python3 roles/diaries/tests/verify-production-deployment-contract.py
```

Their results prove, among other things:

- production backup/restore remains explicitly database-only and paired with Files identity metadata;
- production storage isolation remains explicit;
- role source contains only the approved supported production script set;
- all eight completed-feature helpers are absent from role source;
- Ansible explicitly removes each of the eight obsolete deployed filenames;
- production synchronization does not use unrestricted `rsync --delete`.

A repository-wide `git diff --check` also exposed existing CRLF/trailing-whitespace warnings in other modified configuration/template files. To distinguish that working-tree state from Step 5, the Step 5 source areas were checked separately:

```text
git diff --check -- \
  roles/diaries/files/sync/scripts \
  roles/diaries/tests \
  roles/diaries/tasks/copy.yaml \
  roles/diaries/README.md
```

That command produced no output, so the Step 5-specific changes are whitespace-clean.

## Completion criteria

Step 5 required:

1. Playbooks source to contain only supported live production tooling;
2. permanent regression coverage to be behaviour-oriented rather than feature-step-oriented;
3. stale deployed-file removal to be explicit and narrowly scoped;
4. unrestricted `rsync --delete` to remain prohibited;
5. source validations to pass in the authoritative Playbooks checkout.

All five conditions are satisfied.

## Safety statement

Step 5 changed Playbooks source only. It did **not**:

```text
run the Diaries playbook
remove scripts from pluto
restart production services
restore or modify the database
modify mutable Files contents
alter the PostgreSQL schema
clear retained MQTT state
```

Those production-side effects remain outside Step 5.

## Evidence

Prepared/source-package evidence:

- `PLAYBOOKS-SCRIPTS-AFTER.txt`
- `PLAYBOOKS-TESTS-AFTER.txt`
- `ANSIBLE-REMOVAL-LIST.txt`
- `VALIDATION-OUTPUT.txt`
- `scripts/playbooks-0032-step5.patch`
- `scripts/apply-step5-playbooks-source.sh`
- `scripts/apply-step5-playbooks-source.ps1`

Authoritative checkout evidence:

- `AUTHORITATIVE-APPLICATION-OUTPUT.txt`
- `AUTHORITATIVE-VALIDATION-OUTPUT.txt`
- `AUTHORITATIVE-SCOPED-DIFF-CHECK.txt`

## Handoff to Step 6

Step 6 may now deploy the cleanup through the normal controlled Diaries Playbooks path. Before deployment it should capture a fresh `pluto` scripts inventory, then prove after deployment that the exact eight retired helpers are absent while all permanent operational scripts remain present and production health/configuration is unchanged.
