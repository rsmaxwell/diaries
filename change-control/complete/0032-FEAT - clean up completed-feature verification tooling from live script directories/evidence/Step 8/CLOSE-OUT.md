# 0032 Step 8 close-out

## Status

**COMPLETE / FEATURE CLOSED — 2026-10-03**

Step 8 is complete. Final inventory reconciliation, the 60-row disposition, recurrence protection, portable/source regression and both host-capable regression gates have passed. All 11 feature acceptance criteria are now evidenced.

## Final regression gates

### Diaries / Windows host

`DIARIES-HOST-REGRESSION.txt` records a successful run of the Step 8 Windows runner. It proves:

- Windows live-script anti-accumulation policy PASS;
- dataset/storage-pair, backup/restore, direct-development and effective-path guards PASS;
- exact PowerShell dataset-pair cases PASS;
- all 11 Node validation tests PASS;
- responder/web Gradle tests finish `BUILD SUCCESSFUL`;
- Angular production build completes successfully;
- the runner ends `PASS: Diaries Step 8 host regression completed successfully.`

The Angular build emits the existing CommonJS/AMD optimization warnings for `quill-delta` and `buffer`; these are warnings and do not fail the build.

### Playbooks / `mango`

`PLAYBOOKS-HOST-REGRESSION.txt` records the successful rerun with `/home/richard/playbooks` supplied explicitly to the feature-scoped runner. It proves:

- production storage-isolation validator PASS;
- production backup/restore-semantics validator PASS;
- production deployment/managed-scripts contract validator PASS, including `--delete` + `--delete-excluded` management of the dedicated production `scripts/` directory and protection of templated permanent scripts;
- native `ansible-playbook --syntax-check diaries.yaml` PASS;
- the runner ends `PASS: Playbooks Step 8 host regression completed successfully.`

An earlier invocation from `/tmp` without the Playbooks root did not execute a validator because the runner looked for `/tmp/roles/...`; this was an invocation-path issue, not a regression failure. The explicit-root rerun is the authoritative result.

## Final inventory reconciliation

The final before/after evidence records:

- Windows live script files: **108 -> 72**;
- Playbooks production synchronized scripts: **14 -> 6**;
- Playbooks permanent tests: **7 -> 3**;
- deployed `pluto` scripts: **23 -> 15**;
- original cleanup candidates: **60 total, 43 archived, 17 promoted/renamed, 0 pending**.

Step 6 remains the authoritative deployed-production after-state. It removed exactly the eight approved retired production helpers while preserving the supported production script set and healthy services. Step 7's managed-directory refinement changes how that clean state is maintained on future deployments; it did not require another Step 8 production deployment.

## Data and runtime impact

0032 is a tooling/source hygiene feature. Its close-out introduces no database-row, schema, mutable Files, retained MQTT or application-behaviour migration. The final Java and Angular gates confirm the unchanged application sources still build/test successfully.

## Closure decision

All Step 8 completion conditions are met:

1. final Diaries regression passes;
2. final Playbooks/Ansible regression passes;
3. before/after inventories are reconciled;
4. every original candidate has a final disposition;
5. permanent recurrence guards are active;
6. `pluto` has no stale retired feature helpers;
7. all 11 acceptance criteria PASS.

The complete 0032 record is therefore moved to:

```text
change-control/complete/0032-FEAT - clean up completed-feature verification tooling from live script directories/
```

No further 0032 implementation or production action is required.
