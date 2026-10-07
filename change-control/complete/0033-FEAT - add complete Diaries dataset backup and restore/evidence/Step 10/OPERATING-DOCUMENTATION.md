# Step 10 operating documentation update

The close-out documentation update deliberately changes operating guidance rather than backup media semantics. Schema 2 remains unchanged.

## Diaries `README.md`

The durable dataset section now gives the operator decision rule between database-only and complete-dataset backup, summarises the complete restore safety model and states the explicit backup boundary/exclusions.

## `scripts/windows/README.md`

The local runbook now explicitly documents:

- when to choose database-only versus complete-dataset backup;
- the application-dataset boundary;
- the writer-quiescence window and failure state;
- independent schema-2 completed-media verification;
- the already-supported prepare/apply/postflight/rollback flow.

## Playbooks `roles/diaries/README.md`

The role documentation now provides a production-oriented runbook covering backup choice, `preflight`, production backup location/identity, expected responder downtime, fail-stopped behaviour, independent verification, phased restore, safety backup, replacement Files semantics, rollback and exclusions.

## Deployed `scripts/README.md`

The operator-facing deployed README now gives a concise normal production command sequence and states what to do on failed capture or failed restore/postflight.
