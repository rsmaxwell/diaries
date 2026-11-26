# 0029-FEAT — Step 3 production-readiness source assessment (2026-11-26)

**Status: PREPARATION ONLY — production deployment NOT authorised, Step 3 OPEN.**

## Inputs and provenance

- Diaries source bundle `diaries-sources-20261126-114732.zip` (11:47 snapshot); Playbooks source bundle `playbook-sources-20261126-114726.zip`.
- Step 2 development acceptance based on `final-development-integrity-20261126-115229.log`, TEXT/IMAGE browser tests and 1828 PREAMBLE recovery/reconciliation. The Step 2 closure document package was prepared separately; its application to the Windows working tree is not proven by source bundles.
- Source ZIPs exclude live Git metadata and do not establish current production revisions, inventory overrides, deployed images, Docker containers, active ACL or database contents. Check these before any production actions.

## Confirmed source-level finding: production Mosquitto ACL gap

`playbooks/roles/diaries/files/sync/config/mosquitto/aclfile.txt` is missing `diaries/years/#` grants for three principals. The equivalent development file `config/mosquitto/aclfile.txt` in the Diaries bundle grants them. Without the Playbooks grants, annual PREAMBLE/POSTAMBLE retained topic reads and responder writes may be denied after deployment.

Proposed separate Playbooks-only patch adds:

| Principal | Required grant |
|---|---|
| diaries-client | `topic read diaries/years/#` |
| diaries-responder | `topic readwrite diaries/years/#` |
| diaries-web | `topic read diaries/years/#` |

No broader `diaries/#` permission changes. Apply to the Playbooks working tree using Beyond Compare; do **not** execute Ansible or restart the production broker as part of this source preparation.

## Production data migration: guarded and separate from development-only conversion

The existing `tools/step2-hybrid-schema-and-data.sql` is production-shaped and transactional. Its guard expects exactly **11** Page-less Fragment IDs: `1,2,3,387,806,1177,1563,1564,1738,1926,2061`. It explicitly rejects the additional 49 development-only Page-less image sources. It assigns the nine annual PREAMBLE Fragments to Diary/year; attaches DATED exceptions `1738` to Page `1005` and `2061` to Page `1078`; migrates `MARQUEE`/null content types to TEXT, and adds ownership/type constraints. **It does not retire `marquee.page_id`.** **Do not apply the development-only `step2-49-live-development-conversion.sql` to production.**

The live production row set and schema have **not** been rechecked in this assessment; if different, stop and revise the migration rather than weakening guards.

## Additional implementation gap: redundant Marquee Page persistence

The 11:47 Diaries source still defines `Marquee.page` with `@ManyToOne` and `@JoinColumn(name = "page_id")`; `DeleteMarquee.java` and other handler code use that relation. `step2-hybrid-schema-and-data.sql` contains **no** `ALTER TABLE marquee DROP COLUMN page_id`. This is a specific unimplemented part of the 0029 objective and Step 2 checklist, despite the accepted database/browser integrity gates. It must either be completed coherently in the responder, DTOs, tests, schema migration and rollback **before production release**, or be explicitly deferred by a documented scope decision. Do not drop the column in production while application code still references it.

The Step 2 development closure therefore certifies the observed successful workflows and database gates, **not** the completed retirement of Marquee Page coupling. This gap needs reconciliation in the change-control report/plan before declaring the entire feature ready.

## Existing production deployment architecture

- Playbooks `diaries.yaml` runs `roles/diaries` and renders a Compose stack containing PostgreSQL, Mosquitto, responder, Angular client and public Reader (`diaries-web`).
- Role defaults in the supplied Playbooks snapshot specify client `0.0.9-build-80`, responder `0.0.9-build-86`, web `0.0.9-build-9` **as defaults only**. Inventory can override them; they are not evidence of live deployed versions or of 0029-compatible published images.
- `roles/diaries/templates/compose.yaml.j2` makes Reader dependent on the MQTT and responder health checks. Deployment must coordinate the schema, responder, client, Reader and broker ACL to avoid a mixed contract.

## Step 3 consolidated acceptance / execution approach

1. **Read-only readiness (now):** verify Windows parent/submodule dirty revisions; `mango` Diaries, Playbooks and inventory working copies; effective production image tags and deployed image digests; production DB schema and 11-row Page-less guard; live Mosquitto ACL and Reader route; backup health and actual restore options. Store logs/manifest under this feature's `evidence/step-3-production-readiness/` in the Diaries parent repository, not under Playbooks.
2. **Build and release candidate:** build and test client/responder/reader from a pinned, coherent set of revisions; include corrected IMAGE `placement=DATED` handler, annual projection, and new ACL; publish versioned images only after matching the accepted source and passing consolidated regression.
3. **Resolve residual model gap:** decide and implement removal of `marquee.page_id` (including Java handler and DTO dependencies) or document explicit approved deferral; run affected tests before release.
4. **Before production writes:** capture and verify a fresh **restorable** PostgreSQL backup plus relevant mutable Files-root and MQTT recovery state. Rehearse the exact guarded production SQL on an isolated copy of the current production data. Identify a compatible old-stack rollback and validate restoration procedures. Obtain explicit authorisation for production changes.
5. **Controlled deployment:** quiesce Editor/responder writes; apply the pre-reviewed schema/data migration under guard; deploy matched responder/client/Reader images and ACL via existing Playbooks procedures, then reconcile retained MQTT state by normal responder startup. Do not clear `diaries/#` wholesale. Capture rollback/receipts.
6. **One consolidated postflight:** prove nine annual PREAMBLEs including 1828/1832 HTML, 1738/2061 DATED ownership, normal dated editing/locking, IMAGE lifecycle and catalogue preservation, POSTAMBLE synthetic fixture in a safe test system, MQTT annual topic ACL/replay, zero orphan ownership/Marquee relationships and Reader smoke tests.

## Immediate read-only operator baseline (do not deploy)

**Windows Cygwin terminal — Diaries repo**

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
git status --short --branch
git rev-parse HEAD
git submodule status
for sub in diaries-client diaries-responder diaries-web; do git -C "$sub" status --short --branch; done
```

**Windows Cygwin terminal — via SSH to mango**

```bash
ssh mango 'cd /home/richard/diaries && git status --short --branch && git rev-parse HEAD && git submodule status'
ssh mango 'cd /home/richard/playbooks && git status --short --branch && git rev-parse HEAD && git remote -v'
```

**Windows Cygwin terminal — via SSH to pluto (read-only)**

```bash
ssh pluto 'docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" | grep -E "NAMES|diaries|mosquitto|nginx"'
ssh pluto 'systemctl list-timers --all --no-pager | grep -Ei "diaries|backup" || true'
```

Record outputs in the 0029 feature directory. Do not assume these commands prove effective Ansible inventory or database backups: those need separate targeted verification.

## Blocking conditions / no-go

- Live production dataset does not match the guarded 11-ID migration baseline.
- Unknown inventory image-tag overrides or no release images containing Step 2 code.
- Production Mosquitto annual-topic ACL missing or not staged for the coordinated rollout.
- Remaining `marquee.page_id` persistence/Java dependence not resolved or explicitly deferred.
- Missing verified point-in-time restorable production backup/Files-root protection and rollback procedure.
- Unreviewed local changes/submodule mismatch between Windows and `mango`.

**Decision:** prepare and review the Playbooks ACL correction; run read-only baseline. Keep Step 3 OPEN and production unchanged until evidence and explicit deployment approval.
