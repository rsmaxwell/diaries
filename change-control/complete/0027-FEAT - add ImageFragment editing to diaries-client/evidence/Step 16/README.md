# Step 16 evidence — documentation and 0027 close-out

## Status

**COMPLETE — 2026-10-07.**

Step 16 converts the implemented/verified 0027 behavior into durable developer and operating documentation, records the final evidence/release inventory, reconciles the production authoring-gate default, and closes the feature.

## Inputs

- final Diaries source bundle: `diaries-sources-20261007-085928.zip`;
- final Playbooks source bundle: `playbook-sources-20261007-085936.zip`;
- Step 14 accepted workstation run: `20261006-093834`;
- Step 15 production run: `20261006-133404`;
- production images: client `0.0.9-build-76`, responder `0.0.9-build-84`, reader `0.0.9-build-8`;
- checked-in Diaries repository head observed during close-out: `c3528b0ea135ac2773855ec524605bd3910b5db8` (`Step 15 listFiles timeout correction`).

The source bundle intentionally excludes ignored run directories, so the run-local Step 14/15 JSON/begin files are not re-created here. The retained Step 15 `MANUAL-EVIDENCE.md` records the production acceptance and exact image tags; Step 15 could only begin after a PASSED Step 14 final summary.

## Durable documentation updated

- `diaries-client/README.md` — IMAGE vs MARQUEE authoring, retained Image topics, chooser semantics, tri-state `imageId`, deletion and gate behavior, implementation map.
- `ARCHITECTURE.md` — ImageFragment data/transport boundaries, create/update/delete flow, authoring gate and production release baseline.
- `docs/IMAGE-FRAGMENT-AUTHORING.md` — durable developer/operator runbook and troubleshooting checklist.
- `diaries-responder/README.md` — 0027 production handoff and production client retained-Image ACL requirement.
- Playbooks `roles/diaries/README.md` — post-0027 production operating contract and deliberate inventory enablement.

## Playbooks default reconciliation

The latest Playbooks bundle contained an inconsistency: `roles/diaries/defaults/main.yaml` already had `diaries_image_fragment_writes_enabled: true`, matching the successfully enabled Step 15 end state, while older comments, role documentation and the permanent deployment-contract regression still described/expected the pre-rollout fail-closed default.

Step 16 resolves that inconsistency in the completed-feature direction: the normal shared role default remains `true`, and the stale documentation/regression are updated accordingly. `false` remains the tested non-destructive rollback/emergency stop. This keeps ImageFragment creation and Image-reference editing available as normal Diaries functionality after 0027 close-out while preserving the responder-side safety control.

A follow-up documentation correction also removes the stale pre-rollout local-mode guidance from `config/environments/local.env.example` and makes the local configuration paths explicit in the durable documentation. Direct development and both Docker local modes now document `imageFragmentWritesEnabled: true` as normal operation; missing/null/false is reserved for deliberate disabled-gate/rollback testing.

## Tooling classification

No 0027 step-specific helper is left in the normal Diaries or production live-script trees. Step 13–15 feature tooling remains beneath the completed change-control evidence tree. The reusable ImageFragment reader/regression helpers promoted by the completed tooling-cleanup feature remain under `scripts/windows/validation/` with behavior-oriented names.

No new live operating script is required by Step 16.

## Validation

Static close-out validation checks:

- feature status and Step 14/15/16 closure markers;
- all 0027 detailed/acceptance checkboxes closed;
- durable docs contain retained Image topic and tri-state `imageId` contract;
- production image/run identities appear in the durable guide and final record;
- Playbooks role default is `true`, `false` is documented as rollback, and the permanent production contract validator passes;
- no 0027/Step 13–16 feature-specific helper exists in normal live script trees;
- final SHA-256 inventory exists for every Step 16 changed file.

See `validation.txt`, `changed-files.txt`, `source-files.sha256`, `MOVE-INTEGRITY.md`, `RELEASE-IDENTITY.md` and `ACCEPTANCE-MATRIX.md`.
