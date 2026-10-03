# 0032 Step 5 — Playbooks source and permanent production tooling cleanup

## Status

**COMPLETE — 2026-10-03**

The frozen Step 2 Playbooks disposition has been applied to the authoritative Playbooks checkout at `/home/richard/playbooks` and validated there.

The resulting role source:

- removes the eight archived production helpers from `roles/diaries/files/sync/scripts/`;
- keeps only the supported database backup/restore commands and `dataset-backup-manifest.py` as persistent production script source;
- removes `migration0024ImageCatalogue.sh` from live Playbooks source, in accordance with the Step 2 decision that it is completed 0024 migration tooling;
- replaces the live `verify-0031-*` tests with three permanent behaviour-oriented regressions;
- rewrites the production script README as current operator documentation rather than a completed-feature runbook;
- removes 0031 numbering from retained production documentation/comments;
- adds an exact eight-name Ansible `state: absent` allow-list so the later production deployment removes already-deployed obsolete scripts from `pluto`;
- deliberately does **not** add `rsync --delete`.

## Why the implementation was supplied as a patch

Step 5 contains deletions and renames in the Playbooks repository. A normal overlay ZIP would add the promoted files but leave obsolete files behind. `scripts/playbooks-0032-step5.patch` is therefore the authoritative source change and was applied atomically with Git.

The convenience scripts were intended to apply the patch and run the three permanent regressions without running Ansible or touching `pluto`:

```text
scripts/apply-step5-playbooks-source.sh
scripts/apply-step5-playbooks-source.ps1
```

On `mango`, the Linux wrapper successfully applied the patch but then stopped because it invoked `python` while that host provides `python3`. The source application remained valid; the same three validators were then run manually with `python3` and all passed. This sequence is retained verbatim in the authoritative evidence files.

## Final source after-state

The supported role-managed production script source is exactly:

```text
README.md
backup-db-to-binary.sh
backup-db-to-sql.sh
dataset-backup-manifest.py
restore-db-from-binary.sh
restore-db-from-sql.sh
```

The live Playbooks regression directory becomes exactly:

```text
verify-production-backup-restore-semantics.py
verify-production-deployment-contract.py
verify-production-storage-isolation.py
```

## Validation

Prepared validation against `playbook-sources-20261003-145048.zip` is retained in `VALIDATION-OUTPUT.txt`.

Authoritative checkout validation is retained in:

```text
AUTHORITATIVE-APPLICATION-OUTPUT.txt
AUTHORITATIVE-VALIDATION-OUTPUT.txt
AUTHORITATIVE-SCOPED-DIFF-CHECK.txt
```

The authoritative results prove:

- all three permanent regressions pass;
- the exact eight obsolete helpers are absent from role source;
- the exact eight filenames are present in the Ansible removal model;
- unrestricted `rsync --delete` is absent;
- the Step 5-specific source diff is whitespace-clean.

A repository-wide `git diff --check` exposed CRLF/trailing-whitespace warnings in other modified configuration/template files. The narrower Step 5 path check produced no output, so those warnings do not block this step.

## Deployment boundary

Step 5 changes Playbooks **source only**. It does not remove anything from `/home/richard/projects/diaries/scripts/` on `pluto`. The explicit Ansible removal list is now present so Step 6 can deploy the cleanup through the normal controlled production path and verify the deployed after-state.

See `STEP-5-CLOSE-OUT.md` for the closure decision and Step 6 handoff.
