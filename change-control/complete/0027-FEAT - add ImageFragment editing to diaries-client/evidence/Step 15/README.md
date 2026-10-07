# Step 15 evidence — production deployment and deliberate authoring enablement

## Status

**COMPLETE — production run `20261006-133404` PASSED on 2026-10-06.**

The guarded rollout was executed after Step 14 run `20261006-093834` passed. Production run `20261006-133404` completed the disabled-gate smoke, deliberate enablement, controlled IMAGE lifecycle, restart/replay, cleanup and rollback-readiness checks. The verified images were client `0.0.9-build-76`, responder `0.0.9-build-84` and reader `0.0.9-build-8`. `MANUAL-EVIDENCE.md` is the retained portable production acceptance record.

## Safety model

Step 15 now has one explicit production control:

```yaml
diaries_image_fragment_writes_enabled: false
```

The Playbooks role defaults it to false, validates it as a boolean, renders it into `config/responder/responder.json`, and validates the rendered JSON. The only supported production enablement is an explicit inventory override to `true` after the disabled-gate client smoke and pre-enable evidence are green. Setting the same inventory value back to false is the non-destructive rollback; no database rollback or Files-root re-pointing is required merely to stop new Image-reference authoring.

## Tooling

- `tooling/step15-begin.ps1` creates a run only after a PASSED Step 14 closure summary is found.
- `tooling/step15-preflight.ps1` checks the fail-closed Playbooks contract and the currently disabled production gate without changing production.
- `tooling/step15-capture-production.ps1` captures non-sensitive gate/container/database/Files evidence for the required rollout boundaries and validates the expected gate state.
- `tooling/step15-finalize.ps1` refuses closure until all automatic captures and run-local manual acceptance records are complete.
- `RUNBOOK.md` defines the exact deploy-disabled → smoke → capture → enable → lifecycle → cleanup/rollback sequence.
- `CHECKLIST.md` and `MANUAL-EVIDENCE.md` are copied into each run directory so source templates remain reusable.

Feature-specific tooling remains under change-control evidence rather than the live production script directory, consistent with 0032's anti-accumulation policy.

## Playbooks integration

The Playbooks Diaries role now:

1. defaults `diaries_image_fragment_writes_enabled` to false;
2. rejects non-boolean values;
3. renders the value into the responder JSON instead of hard-coding false;
4. validates the rendered gate during `copy` deployment;
5. documents deliberate enablement and non-destructive rollback;
6. extends the permanent production deployment contract regression for this behaviour.

The Step 14 rollout rehearsal was updated to recognise this fail-closed variable/template pair while preserving its existing pass phrase and guarantee that Step 14 itself never enables authoring.

## Execution boundary

Installing these source changes is not approval to set the production value true. The first production action is allowed only after the real Step 14 finalizer has produced a PASSED summary. The exact 0027 client image must then be deployed and smoke-tested with the gate still false before the inventory override is changed to true.
