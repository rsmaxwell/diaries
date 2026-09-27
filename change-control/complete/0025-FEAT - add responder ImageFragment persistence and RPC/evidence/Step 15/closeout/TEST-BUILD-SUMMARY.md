# Test/build and migration evidence summary

The authoritative pre-deployment regression baseline is **Step 14/revalidation-20260928**:

- responder: 322 discovered, 285 passed, 37 environment-gated skips, zero failures/errors; build passed;
- explicitly enabled PostgreSQL/MQTT integration: Step 11 lifecycle/race 2 passed; Step 12/13 live RPC/replay/gate 2 passed; Image catalogue MQTT 1 passed; large-tree MQTT regression 1 passed;
- diaries-web: 50 passed, zero skips; build passed;
- diaries-client: 132 passed; production build passed;
- deployed web/client compatibility probes passed against the actual deployed build artifacts recorded in Step 14.

**Step 15.1** then verified the real development database schema readiness, backup identity, preflight/postflight and the candidate responder identity without starting the responder. The database already contained the 0025 additive schema, so no DDL was reapplied.

The Step 15.2/15.3 deployment runner refuses to proceed if any file in the Step 14 source SHA-256 inventory has changed. Its successful `deployment/revalidation-20260928/result.json`, RPC transcripts, database before/after hashes, retained snapshots and responder logs become the final development-deployment evidence.

The fresh disposable database was also migrated before the candidate started: see 0024-schema.log and 0025-schema.log in the revalidation deployment. Production remains build 80 with the gate property absent (the candidate would interpret that as disabled). No production deployment was performed.
