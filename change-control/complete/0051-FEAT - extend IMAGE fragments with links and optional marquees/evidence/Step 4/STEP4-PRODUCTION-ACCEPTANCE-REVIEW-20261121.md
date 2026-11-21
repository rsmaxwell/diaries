# 0051 Step 4 — production acceptance review

**Prepared:** 21 November 2026 (UTC)  
**Disposition:** **READY FOR FORMAL OWNER ACCEPTANCE**. Production capability and activation evidence are positive; this document does **not** itself close Step 4.  
**Source boundary:** The last uploaded full Diaries source archive is `diaries-sources-20261120-171523.zip` (prior to the later changes). Later results below come from the owner's terminal logs and confirmations in the Diaries project conversation, not from a refreshed full Git checkout or independent inspection of private run directories. Review against the actual Windows working copy before applying.

## Gate reviewed

The authoritative `IMPLEMENTATION-STEPS.md` Step 4 gate is: **“supported behaviour exists in production and migration tools model it accurately. Passing a draft checker alone does not satisfy this gate.”** The Step 4 work covers 0028 migration preservation, isolated compatibility/rollback rehearsal, actual published images in supported local modes, controlled production rollout and the old-binary rollback cutoff.

## Acceptance matrix

| Requirement | Evidence and scope | Review |
| --- | --- | --- |
| 0028 preservation contract | 20 Nov offline v2 reviewer, updated read-only inventory and tests; explicit link set/clear and Marquee preserve/remove with geometry/version checks; old reviewer decisions are not automatically approved. `STEP4-MIGRATION-COMPATIBILITY-IMPLEMENTATION-20261120.md`. | **PASS for tooling contract**, not an approved 0028 conversion |
| Protected schema, mixed-version and gate rehearsal | Published-image run `20261120T210259Z-de695753`, with frozen database copy and disposable Linux Files volume; runner reports pre-write rollback, re-upgrade and forward-only activation **PASS**; private receipts retained on Windows. | **PASS** |
| Jenkins binary provenance | Responder `0.0.9-build-85` / `sha256:07432f88b5ae412c9c2954944144e009e3fcf004a79e915dae0324a3bd3b3686`; Web `0.0.9-build-9` / `sha256:8e80e05affce6e80c3b7a2222364ca7f327ad3248d7f182f7ea3d621981fe932`; initial Client `0.0.9-build-78`; corrected Client `0.0.9-build-79` / `sha256:d0202347952543b34db301a74a413068c15f765763d0d402f00f742f94e60f93`. Jenkins #79 finished SUCCESS. | **PASS** |
| Local published-image integration | Five services healthy with client build-79, responder build-85, reader build-9. Corrected NAS Docker CIFS *volume definition* without removing NAS data; startup warning eliminated. 244 Angular tests and Angular build passed. Owner's 21 Nov screenshot showed new local IMAGE Fragment 2338/Image ID 3 rendered beneath header; adjacent legacy content still displayed. | **PASS** |
| Production recovery preflight | 20 Nov `mars` and `backup` manifest reports HEALTHY/zero conflicts, same production backup `20261120-003112Z`; pull, push and snapshot-create service results success. 21 Nov activation log again reports HEALTHY on both, latest production backup `20261121-003236Z`. These are manifest/service reports, **not full file-content restore tests**. | **PASS for agreed preflight** |
| Production deploy, schema and gate-off verification | 20 Nov Ansible `pluto ok=55 changed=3 failed=0`; responder 85/client 78/web 9 healthy, PostgreSQL/MQTT healthy; `fragment.image_link_url` is nullable VARCHAR(4096), existing IMAGE writes on, extensions off. | **PASS** |
| Day Reader defect correction | Production IMAGE Fragment 2332 / Image ID 3 initially omitted the media. Client-only change `7e0251d1c47720397504f3fd43fff09b6b7f2bb3`; parent pin `aace22faa2f2bf64f146b33dfc8714e43005cf1d`; client Jenkins #79 successful. 21 Nov deployment `pluto ok=55 changed=3 failed=0`; client 79 and other four services healthy, extension gate still off. Owner explicitly confirmed image rendered correctly in production. | **PASS** |
| Extension activation and production runtime | 21 Nov `production-activation-20261121T090357Z.log`: `mars` and `backup` HEALTHY, Ansible `pluto ok=55 changed=2 failed=0`, all five containers healthy, existing IMAGE gate true and extension-write gate true. | **PASS** |
| New-feature production functional acceptance | On 21 Nov the owner explicitly stated: **“0051 production activation functional checks all passed.”** This refers to the controlled feature checklist for IMAGE creation, safe link set/click/clear, optional Marquee add/remove, persistence and reader reflection. The chat confirmation is an **owner-attested acceptance**, not a newly uploaded independent screenshot/RPC/database readback for each action. | **OWNER ATTESTED PASS** |
| Rollback compatibility and data preservation | Protected rehearsal established old-binary rollback is valid only **before** the first new-format extension write. After activation/first write, old binaries are *not* approved rollback targets. 0028 production conversion and 0029 destructive cleanup remain unperformed. | **BOUNDARY RECORDED** |

## Evidence register

See `STEP4-PRODUCTION-EVIDENCE-REGISTER-20261121.md` for the specific terminal-log names and working-copy evidence roots. Failed intermediate harness runs (CONFIG_FILE selection, Windows-mounted Files capability, digest identity) remain historical evidence and must not be relabelled as application defects or deleted.

## Exceptions and unrelated work

- **0052-DEF**: wrong Whitley Park map content on 20 March 1828 (Fragments 84, 2332, 2333; Image ID 3). A TODO defect ZIP was prepared on 21 Nov; its application to the owner's repository is not evidenced here. This is a separate *content-correctness* issue; the IMAGE rendering mechanism passed. Do not replace NAS files as part of 0051 closure.
- **0028**: v2 private review drafts are not approved; migration remains a separately gated feature. **0029**: destructive schema/contract cleanup is not approved.
- A separate post-build-79 run of `local-docker-build` was **not independently reported** in the evidence supplied for this review; source-built and published-image modes have other accepted coverage. The owner may explicitly accept this as covered by the consolidated rehearsal/production checks or request a separate mode run before Step 4 closure. No PASS for this unreported run is claimed.
- 0051 release builds include npm dependency audit findings (55 total, including 2 critical and 35 high) and non-fatal bundle warnings; do not silently classify the security findings as resolved.
- No formal owner decision to **close Step 4** or the entire 0051 feature is claimed by this review. Retain all existing uncommitted parent/Playbooks work.

## Proposed decision

**Recommendation: accept and close Step 4**, subject to the owner's explicit acceptance of this review and confirmation that the referenced evidence exists in the authoritative Windows feature directory. Step 5 may then proceed to documentation/handoff closure. **Do not move 0051 to `complete` from this report alone.**

**Owner Step 4 decision:** PENDING (CLOSED only upon explicit owner approval).  
**Decision date / evidence receipt:** To be recorded after approval.
