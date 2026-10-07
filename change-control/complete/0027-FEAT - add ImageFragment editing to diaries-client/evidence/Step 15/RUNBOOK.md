# Step 15 runbook — deploy non-destructively and enable production authoring deliberately

Step 15 performs the first real 0027 production action. It must not start until Step 14 has a `PASSED` final summary. The implementation intentionally separates the deployment into two safety boundaries: first deploy/smoke the 0027 client while the responder gate remains false; only after that evidence is green may the Playbooks inventory override enable Image-reference authoring.

## 1. Install the Step 15 source changes

Apply both source sets from this implementation:

- Diaries: `change-control/in-progress/0027-FEAT - add ImageFragment editing to diaries-client/evidence/Step 15/` plus the Step 14 rehearsal compatibility update.
- Playbooks: the Diaries role changes that introduce `diaries_image_fragment_writes_enabled`, default it to `false`, render it into responder JSON and validate it.

Do not set the inventory override to true yet.

## 2. Prove Step 14 is actually closed

From the Diaries project root on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File ".\change-control\in-progress\0027-FEAT - add ImageFragment editing to diaries-client\evidence\Step 15\tooling\step15-begin.ps1"
```

`step15-begin.ps1` searches `build\0027-step14\runs` for a `step14-final-summary.json` whose status is `PASSED`. It refuses to create a Step 15 run otherwise. An explicit `-Step14Summary <path>` can be supplied if the closure file was archived elsewhere.

The current source bundle still has Step 14 source documentation marked execution pending, so this guard is intentional: installing Step 15 tooling is safe now, but no production deployment/enablement is authorised until the real Step 14 workstation run has passed.

## 3. Run Step 15 preflight with the gate false

If Playbooks is available on `mango` at `/home/richard/playbooks`:

```powershell
powershell -ExecutionPolicy Bypass -File ".\change-control\in-progress\0027-FEAT - add ImageFragment editing to diaries-client\evidence\Step 15\tooling\step15-preflight.ps1" `
  -PlaybooksRoot /home/richard/playbooks `
  -PlaybooksHost mango `
  -PlutoHost pluto
```

The preflight checks the Step 14 closure summary, the fail-closed Playbooks gate contract, SSH access to production, the installed production project, and that the currently rendered responder config is still false. It does not modify production.

Capture the initial state:

```powershell
powershell -ExecutionPolicy Bypass -File ".\change-control\in-progress\0027-FEAT - add ImageFragment editing to diaries-client\evidence\Step 15\tooling\step15-capture-production.ps1" -Phase pre-deploy
```

## 4. Deploy the 0027 client without enabling authoring

Publish/select the exact 0027 client image that corresponds to the Step 14 release candidate. Record the tag in the run-local `CHECKLIST.md` and `MANUAL-EVIDENCE.md`. Update the normal Playbooks client image tag/inventory as required, but keep:

```yaml
diaries_image_fragment_writes_enabled: false
```

Run the normal Diaries playbook deployment. In the supplied Playbooks bundle, `scripts/diaries.sh` currently invokes the role with `--tags copy`; that is sufficient for this Step 15 template/image rollout because the `always` guards still run, the Compose/responder templates are rendered, and changed templates notify the existing stack-restart handler. The existing role deployment is non-destructive with respect to durable storage: `docker compose down --remove-orphans` does not remove named volumes, the NAS Files selector is unchanged, and Step 15 performs no database or Files migration.

After deployment, capture the state and, optionally, assert the exact client image:

```powershell
powershell -ExecutionPolicy Bypass -File ".\change-control\in-progress\0027-FEAT - add ImageFragment editing to diaries-client\evidence\Step 15\tooling\step15-capture-production.ps1" `
  -Phase post-client-disabled `
  -ExpectedClientImage "rsmaxwell/diaries-client:<0027-tag>"
```

Then perform the disabled-gate smoke tests in the real client:

1. edit an existing MARQUEE Fragment;
2. view/edit ordinary text/date/sequence on an existing IMAGE Fragment if production has one;
3. attempt Add Image Fragment or attach/replace/clear Image reference and confirm the expected 403/client disabled-gate message;
4. confirm the 0026 reader still renders the affected day correctly.

Do not proceed if any of those checks fail.

## 5. Capture the pre-enable boundary

Run:

```powershell
powershell -ExecutionPolicy Bypass -File ".\change-control\in-progress\0027-FEAT - add ImageFragment editing to diaries-client\evidence\Step 15\tooling\step15-capture-production.ps1" -Phase pre-enable
```

Also capture/review the relevant retained `diaries/fragments/<id>` and `diaries/images/<id>` topics with MQTT Explorer, plus the controlled test day/Image IDs. Do not place MQTT passwords, JWTs, transcription text or responder secrets into evidence files.

## 6. Enable production authoring deliberately

On the Ansible controller, edit the production Diaries inventory (currently `/etc/ansible/host_vars/pluto/diaries.yaml`) and add/change:

```yaml
diaries_image_fragment_writes_enabled: true
```

Run the normal Diaries playbook again. The role renders:

```json
"imageFragmentWritesEnabled": true
```

and validates the rendered value. The existing template notification restarts the Diaries stack through its systemd service; this is a configuration restart, not a storage reset, and does not remove named volumes.

Verify/capture immediately:

```powershell
powershell -ExecutionPolicy Bypass -File ".\change-control\in-progress\0027-FEAT - add ImageFragment editing to diaries-client\evidence\Step 15\tooling\step15-capture-production.ps1" -Phase post-enable
```

The capture fails if the rendered gate is not true, Compose validation fails, a required container is missing/unhealthy/stopped, or the database shows an orphan IMAGE→Image reference.

## 7. Run one controlled production IMAGE lifecycle

Use one known diary/day and one known catalogued test Image. Record only IDs and operational results in `MANUAL-EVIDENCE.md`; do not copy transcription text into the evidence.

Verify, in order:

1. create one IMAGE Fragment referencing the chosen Image;
2. confirm the client and 0026 reader show the same Fragment/Image relationship;
3. confirm retained Fragment/Image topics and the database agree;
4. perform an ordinary text/date/sequence edit and prove the Image reference is preserved;
5. if useful, exercise replace/clear/reattach deliberately;
6. prove Image deletion is blocked while referenced;
7. restart/redeploy the responder/stack and prove retained replay/database recovery recreates the same relationship and chronology;
8. remove the controlled Fragment/Image only if they existed solely for verification, then reconcile retained/database/Files state again.

## 8. Rollback if any authoring defect appears

Do not undo database rows or Files content merely to stop authoring. Set the production inventory back to:

```yaml
diaries_image_fragment_writes_enabled: false
```

rerun the Diaries playbook, then capture:

```powershell
powershell -ExecutionPolicy Bypass -File ".\change-control\in-progress\0027-FEAT - add ImageFragment editing to diaries-client\evidence\Step 15\tooling\step15-capture-production.ps1" -Phase rollback-disabled
```

Existing IMAGE data stays intact. Ordinary edits that do not change `imageId` and established deletion semantics remain governed by the responder contract; new ImageFragment creation and Image-reference mutations stop.

### Retry after a rolled-back production defect

If the rollback was caused by a code defect, do not resume at the enablement boundary after publishing a fix. Deploy the corrected client/responder images with the gate still `false`, repeat the disabled-gate smoke test (including opening the Image Catalogue and reaching the expected 403 on the actual Image-reference mutation), then take a fresh `pre-enable` capture. Only after that boundary is green may the gate be deliberately enabled again and `post-enable` recaptured. Preserve the failed attempt and rollback evidence; do not rewrite it as a successful first pass.

`step15-capture-production.ps1` preserves retries automatically: if the canonical `production-<phase>.txt` already exists, it is moved to the run-local `history` directory with a timestamp before the fresh canonical capture is written. The finalizer therefore sees the latest successful boundary while the earlier attempt remains auditable.

The 2026-10-06 first production attempt exposed a `listFiles` timing mismatch: the NAS-backed responder request completed successfully after roughly 11.8 seconds while the client used the generic five-second RPC timeout. `LISTFILES-TIMEOUT-CORRECTION.md` records the correction and retry rule.

## 9. Close Step 15

Complete the run-local copies under `build\0027-step15\runs\<run-id>`:

- `CHECKLIST.md`
- `MANUAL-EVIDENCE.md`

Then run:

```powershell
powershell -ExecutionPolicy Bypass -File ".\change-control\in-progress\0027-FEAT - add ImageFragment editing to diaries-client\evidence\Step 15\tooling\step15-finalize.ps1"
```

The finalizer requires the Step 14 PASSED summary, preflight, pre-deploy, post-client-disabled, pre-enable and post-enable captures, plus fully completed run-local manual evidence/checklist. A passing `step15-final-summary.json` is the Step 15 closure signal and the prerequisite for Step 16 documentation/final feature close-out.
