# 0028-FEAT — Step 2 isolated MQTT retained replay and Reader HTTP smoke

Date: 2026-11-23. Status: **PREPARED, not yet executed**.

## Accepted preceding result

The read-only production dump was restored to separately labelled PostgreSQL 18
`diaries-0028-rehearsal-db`, and the completed Step 2 database rehearsal
`20261123T185712Z-isolated-db-rehearsal` verified 71 reviewed conversions,
one explicit DEFER (Fragment 1564), all journal rows, rollback, resume,
idempotence, preservation of existing Marquees and unchanged unrelated rows.
All production and existing development services were outside this test.

## Purpose

This package tests the next application-level boundary by starting the actual
current responder and the actual current read-only Reader on a fresh disposable
Mosquitto broker. The responder synchronises the retained topic tree from the
**already migrated isolated PostgreSQL database**, not from any production or
existing development database. No new dump or database restore is performed.

The package intentionally changes **no** source code and does not update
Playbooks, existing MQTT brokers or Docker publication tags. It locally builds
two unpushed runtime images. All related scripts/tests are feature-specific.

## Safety controls

- The existing DB must have the expected 0028 label, `postgres:18-alpine`
  image, exact independent volume and localhost:55428 binding, 2,331 Fragment
  rows, and 71+71 journal rows.
- Requires previously successful `RESULT.txt`, frozen manifest checksums,
  and the already staged independent Files-root.
- Refuses to reuse or overwrite an existing replay Docker container or
  network of the reserved names.
- A new `--internal` Docker bridge carries only the isolated database,
  isolated broker, responder and Reader; the broker has **no host MQTT port**.
  The HTTP endpoints alone are bound to Windows loopback 58081 and 58082.
- Responder config is generated for this rehearsal alone, with a new local
  secret, isolated DB, isolated broker, staged files and
  `normaliseOnStartup=false`. No production credential is copied.
- The current Files root is bind-mounted read-only; original NAS sources are
  not mounted. Original page scans are **not** staged.
- A replay of 71 explicit retained Fragment topics must exactly match reviewed
  Image ID, Page ID, preserved hyperlink, existing Marquee ID and caption.
  All 22 separate retained Marquee topics must also have the correct current
  Fragment/Page association and numerically valid rectangles.
  Marquee locations/dimensions are not compared to the frozen review because
  legitimate owner updates are allowed. The current Marquee table is
  fingerprinted before and after startup to reject replay-induced mutation.
- Local Reader readiness and representative routes plus static catalogued
  image URLs are tested via HTTP. These are **not** full visual checks.
- No automatic cleanup: if something fails, the labelled Docker network,
  containers, and evidence remain for diagnosis.
- No production apply approval is generated or granted by this package.

## Execute

In the **Windows PC Cygwin terminal** from the Diaries parent checkout:

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'

bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/rehearse-0028-step2-mqtt-reader.sh'
```

Expected private receipts live under a new folder
`evidence/Step 2/private/<UTC>-mqtt-reader-replay/`, including current checkout
identity, generated private configs, local Docker build logs, 71 retained
payloads, validation results, Reader HTML for sample fragments and response
headers, responder/Reader logs, and `RESULT.txt` on success. Do not commit
private credentials, page data or retained MQTT payloads.

If successful, browse the isolated Reader at `http://127.0.0.1:58082/`.
The responder serves the staged catalogue media at
`http://127.0.0.1:58081/files/...`. **Missing original page scans do not
indicate a migration failure:** this package does not mount the original
`diaries/` scan tree. The remaining full browser acceptance must provide an
isolated copy of required scans, and the Angular Editor must be connected to
this disposable broker rather than the ordinary development broker.

### Optional disposal (explicit, restricted)

After acceptance or evidence inspection, the replay containers and network
can be removed without touching the retained isolated database or volume:

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/remove-0028-mqtt-replay.sh' --confirm-remove-isolated-replay
```

The cleanup script refuses unlabelled resources; it never removes
`diaries-0028-rehearsal-db` or `diaries-0028-rehearsal-pgdata`.

## Remaining open acceptance work

1. Check visual rendering of selected converted IMAGE fragments, image links,
   preserved Marquees and actual scan overlays, using an **isolated** page-scan
   source with no source mutation.
2. Check Angular Editor and read-only Reader end-to-end using the same
   disposable retained MQTT state, including the explicit DEFER.
3. Agree Step 1's formal acceptance record and Step 2 gate with owner.
4. Plan the production maintenance window/backup checkpoint and require
   separate explicit production migration approval. Do not deploy or enable
   writers merely because these technical tests pass.
