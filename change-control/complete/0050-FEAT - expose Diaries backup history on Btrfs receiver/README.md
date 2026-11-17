# 0050-FEAT — Expose Diaries backup history on Btrfs receiver

- **Type:** Feature
- **State:** FORMAL CLOSURE APPROVED; STEPS 1–4 CLOSED; archive publication pending execution of the guarded closure helper
- **Opened:** 2026-11-17
- **Predecessor:** 0049-FEAT (formally closed; published Diaries commit `19dcaba94616152738fda1f93c504d77da888f63`)
- **Permanent change-control owner:** Diaries parent repository, this feature directory
- **Operational code owner:** public Playbooks repository on `mango`, under `roles/btrfs-replication/` and `roles/snapshots/`
- **Hosts:** `mars` (source, existing Diaries history) and `backup` (receiver, new history)

## Problem

0049 installed `diaries-backup-status` only on `mars`; `diaries-backup-history` is installed by the source `snapshots` role and is not provisioned as part of the receiver's `btrfs-replication` role. The receiver's Btrfs manager deliberately has `verification.required=false`. Consequently the receiver cannot independently list or verify Diaries backups embedded in **its own retained received snapshots**. Independent retention can leave a backup present on `backup` after its final occurrence on `mars` has been pruned.

## Objective / agreed scope

1. Install `/usr/local/sbin/diaries-backup-status` and `/usr/local/sbin/diaries-backup-history` on `backup` using normal Ansible roles (and install their independent schema-2 verifier if absent), without changing existing `mars` functionality.
2. Make both receiver commands inspect the local received snapshot tree `/@data/mars-received/@data/<timestamp>/` and the embedded `backup/.diaries-snapshot-verified.json` marker and `backup/pluto/diaries-backup/dataset-manifest.json` manifest. Require verified marker state, snapshot eligibility, matching backup/dataset identities and SHA-256 manifest digest; reject unsafe paths.
3. Preserve the source command semantics: `list [--all]`, `show`, `path`, `verify`, optional `--snapshot` / `--logical-dataset`, JSON format, conflict detection, warnings, empty-history, error and exit behaviour. `verify` must execute the same complete schema-2 verifier against the selected **receiver-local** dataset, not just check a manifest hash.
4. Prove, with disposable fixtures and live read-only inspection, that a backup present **only on `backup`** is listed, can be selected, and can be verified without contacting or depending on `mars`.

## Design decisions to preserve

- **Do not enable the receiver snapshot manager's `verification.required` flag.** The deployed Btrfs manager specifically refuses Diaries *source* verification in receiver mode. Keep its receiver pruning and replication semantics unchanged; use a separate read-only history configuration namespace (see `DESIGN-AND-INTERFACE-CONTRACT.md`).
- Operate on received **read-only** Btrfs snapshots, not the live source or replication transport. The history commands are local readers, not a new cross-host merge service.
- Do not expand 0041 sender/receiver SSH privileges or sudoers. Existing operator `sudo -n` is the supported way to access protected backup files. No snapshot deletion, restore, retention-policy change or manual transfer is in scope.
- Preserve the existing `diaries-backup-status` JSON schema/health semantics. Do not treat manifest identity as full backup integrity; `verify` is the explicit content-integrity operation.

## Expected operator commands

Run in **mars SSH terminal** (existing):

```bash
sudo -n diaries-backup-status
sudo -n diaries-backup-history list
```

Run in **backup SSH terminal** (new after implementation):

```bash
sudo -n diaries-backup-status
sudo -n diaries-backup-history list
sudo -n diaries-backup-history list --all
sudo -n diaries-backup-history show BACKUP_ID --logical-dataset production
sudo -n diaries-backup-history path BACKUP_ID --logical-dataset production
sudo -n diaries-backup-history verify BACKUP_ID --logical-dataset production
```

`verify` may be I/O-intensive; run an explicit, suitably small retained test dataset during acceptance. No command above deletes or rewrites snapshots. `path` returns exactly one local path; use `--snapshot TIMESTAMP` when a specific occurrence matters.

## Workflow and acceptance

Implement a complete coherent Playbooks change set; run consolidated fixture/permanent regressions and Ansible checks; deploy to `backup` using the normal playbook after inventory/permission verification; then compare representative `mars` output for regressions. Record exact revisions, tests, installed hashes and read-only live checks under this feature's `evidence/` directory. Formal closure is separate from technical acceptance: mark a step CLOSED only with accepted evidence.

See `IMPLEMENTATION-STEPS.md`, `DESIGN-AND-INTERFACE-CONTRACT.md`, `tests/ACCEPTANCE-MATRIX.md`, and `reports/BASELINE-SOURCE-REVIEW-20261117.md`.

## 17 November 2026 — Implementation increment prepared

One coherent eight-file Playbooks change package implements receiver-local reader
configuration, installs the reader/status/verifier on `backup` through the
existing receiver-manager/retention install gates, and extends the shared
reader without changing its source-side interface. Source tests were executed
against the supplied 0049 Playbooks baseline: all ten test groups passed,
including the nine-case receiver-only acceptance fixture and a real schema-2
integrity test. See `reports/IMPLEMENTATION-AND-SOURCE-TEST-20261117.md`.

**Not yet done:** validation of the actual receiver's marker/dataset layout,
Ansible syntax/check mode on mango, deployment, installed read-back, live
full verification, strict idempotence, committed revisions, and formal closure.
No implementation or acceptance step is yet CLOSED.

## 17 November 2026 — Initial deployment and verification correction

Deployment to `backup` succeeded (`ok=37 changed=2 failed=0`); the new
reader/status discovered 30 distinct backup IDs in 42 received snapshot
occurrences with zero conflicts. Full `verify` exposed a fixed-directory
invocation error, not confirmed data damage. See
`reports/FIRST-LIVE-VERIFICATION-CORRECTION-20261117.md` for the minimal
reader correction and passing local regressions. Re-deployment and **live**
content-verification acceptance remain pending; no step is CLOSED.

## 17 November 2026 — Final operational acceptance

The receiver-side correction was deployed successfully. A live schema-2 verification of 128 files passed for `production/20261116-003112Z` from received snapshot `20261116-150008Z`. Receiver history reports 30 distinct backups in 42 retained occurrences, with zero manifest conflicts and healthy infrastructure. A strict Ansible reapply yielded `changed=0 failed=0`. Read-only comparison against `mars` found **11 naturally retained backup identities existing only on `backup`**, while `mars` retains 3 source-only identities.

This supersedes the earlier stage-specific statements that live verification, deployment and idempotence were pending; those sections remain as dated history. See `reports/FINAL-OPERATIONAL-ACCEPTANCE-20261117.md`. **Publication and formal closure are not complete.**

## 17 November 2026 — Operational repositories published

Both Playbooks and the private Ansible-controller parent were published with remote-SHA verification. The first Playbooks commit `a1f27ddf20e6c9668c6ad8f0d801de0233695ccc` included an unintended executable-mode regression (`100755` to `100644`) for `roles/snapshots/files/diaries-backup-history.py`. The mode-only correction commit `b0063d455faf4b264504405f9db72ab21c692741` restores `100755` without changing file contents.

The final private Ansible-controller commit `28e394b48ba91479b147452d70adb39ff3b84559` pins corrected Playbooks `b0063d455faf4b264504405f9db72ab21c692741`; private inventory remains at `ebcce026723db37b9b53b76ba21903a351d48466`. Original first-publication and correction logs and their checksums are in `evidence/Step 4/`.

The running `backup` installation had previously been deployed using Ansible mode `0755`, and the accepted live 128-file content verification and strict idempotence are unchanged. No additional deploy or transfer is required for the source Git mode correction.

**Remaining:** commit/publish the complete Windows Diaries 0050 change-control records, capture the final Diaries revision, then obtain separate formal closure approval before marking steps CLOSED or relocating to `change-control/complete/`. The earlier dated "publication pending" status remains in place solely as historical progression.

## 17 November 2026 — Formal closure approved (supersedes earlier status)

Feature owner explicitly approved formal closure after verification that the 0050 Diaries evidence commit `06ae009f2b840a9021045a9da3266d022ab6c65d` was published and all three repositories were in their expected revisions. The last accepted operational evidence has been carried forward under this feature directory, including the **strict `changed=0` receiver reapply**, the **11 naturally retained receiver-only backups**, and the **128-file full-content verification** of a selected received backup.

Steps 1–4 are accepted **CLOSED**, with approval and limitations recorded in `reports/FORMAL-CLOSURE-DECISION-20261117.md`. This feature is ready to be archived from `change-control/in-progress/` to `change-control/complete/` and published in one guarded Diaries commit. The closure takes effect only after the helper confirms that remote commit readback. Earlier pending statements above are retained as dated historical progress, not current status.
