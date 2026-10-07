# Step 14 manual evidence

Complete this after the workstation regression and rollout rehearsal.

## Run identity

```text
Step 14 run ID:
Date/time:
Tester:
Parent Diaries commit:
diaries-client commit:
diaries-responder commit:
diaries-web commit:
Playbooks commit:
```

## Step 13 handoff

```text
Closed Step 13 run/evidence:
Representative IMAGE Fragment ID used by Step 13:
Representative Image ID used by Step 13:
Final Step 13 gate state: false
Notes:
```

Confirm that the closed Step 13 evidence proved the editor-authored Fragment shape consumed by Step 14 reader regression:

```text
[ ] type=IMAGE
[ ] authoritative pageId
[ ] no Marquee relationship
[ ] imageId null or one positive catalogue Image ID
[ ] date/sequence immediately normalised
[ ] retained/database state agreed after restart/replay
```

## Full regression result

```text
Client tests:
Client production build:
Responder tests/build:
Web tests/build:
Disposable reader/browser verification:
Required report checker:
Local Compose render checks:
regression-summary.json status:
```

Record any warning and its disposition. A required test skip is not an accepted warning.

## Reader baseline

```text
Backup filename:
Backup SHA-256:
Disposable reader evidence directory:
Reader summary status:
Cleanup failures:
```

Confirm:

```text
[ ] MARQUEE-only baseline content still rendered
[ ] owned IMAGE fixture rendered with the current reader candidate
[ ] restart/replay restored the same relationship
[ ] configured Files route served the owned Image bytes
[ ] Image delete guard detected the owned reference
[ ] cleanup affected only disposable/owned fixture state
```

## Production-order rehearsal

```text
Playbooks root:
Playbooks commit:
roles/diaries responder template gate value:
roles/diaries web filesPath value:
rehearsal result:
```

The rehearsed order is:

```text
1. existing responder capability present/healthy with authoring false
2. 0026 reader capability present/healthy
3. deploy compatible 0027 client while authoring remains false
4. run disabled-gate production smoke checks
5. capture pre-enable evidence
6. only Step 15 may deliberately change authoring to true
```

Confirm Step 14 stopped before item 6:

```text
[ ] yes
```

## Deviations / follow-up

```text
None / describe here.
```
