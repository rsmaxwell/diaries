# 0025 Step 15 — Development deployment, controlled validation and close-out

**PASSED.** Step 15.1 had already verified the real development schema/backup/candidate readiness. The authoritative Step 15.2/15.3 run is `C:/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries/change-control/in-progress/0025-FEAT - add responder ImageFragment persistence and RPC/evidence/Step 15/deployment/revalidation-20260928` and deployed candidate JAR SHA-256 `5963f8fbaf744d782b4ac88738132f3bb082ed6a26ec5030588e0bd4519a8df1` against disposable PostgreSQL/Mosquitto and a private filesystem tree.

## 15.2 — gate disabled smoke validation

The candidate started with `imageFragmentWritesEnabled=false`. Evidence proves sign-in and existing retained reads, controlled MARQUEE create/edit/delete, upload/catalogue behavior, generic `DeleteFile` protection, unreferenced `DeleteImage`, and 403 rejection of `addImageFragment`. See `disabled-rpc.json`, `existing-read-summary.json`, `disabled-responder.log` and `result.json` in the deployment run.

## 15.3 — controlled IMAGE validation

With the gate deliberately enabled only for the disposable fixture, evidence preserves the IMAGE Fragment row, Image row, zero Marquees, canonical/date retained Fragment state, retained Image state, 409 reference protection, Image-reference clear/reattach behavior and old-date tombstone. Retained state was then deliberately corrupted, the responder restarted, and startup replay reconstructed it from the database. After deleting the final Fragment reference, `DeleteImage` completed and DB rows, retained topics and the physical fixture file were removed. See `enabled-rpc.json`, `state.json`, `corrupt-rpc.json`, `replay-delete-rpc.json`, `replayed-retained.json` and the responder logs.

## Safety and cleanup

`productionModified=false`, `liveDatabaseUsed=false`, `nasUsed=false`; the original disposable application rows matched before/after fixture cleanup; the private fixture file was absent; all owned Docker containers and the temporary responder work tree were removed. The runner verified the application source still matched the Step 14 SHA-256 inventory before deployment.

## 15.4 — change-control close-out

`../CHANGED-FILES.md`, `../DESIGN-DECISIONS.md` and `../TEST-BUILD-SUMMARY.md` record the exact implementation scope, test/build totals, migration/integration evidence, final `updateFragment.imageId` semantics, attach/delete locking protocol, authoring-gate policy and 0026–0029 deferrals.

## 15.5 — acceptance decision

The responder capability, persistence integrity, retained contract, reference-aware Image deletion, safe authoring gate and controlled deployment/replay lifecycle are all evidenced. 0025 is technically complete. Production migration/deployment and enabling IMAGE authoring are deliberately **not** performed by this step; production authoring remains disabled until the later reader/client rollout prerequisites are approved.
