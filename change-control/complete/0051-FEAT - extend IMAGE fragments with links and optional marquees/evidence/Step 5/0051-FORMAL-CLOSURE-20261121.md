# 0051-FEAT — Formal feature closure

**Decision date:** 21 November 2026  
**Decision:** APPROVED — formal closure of 0051-FEAT by the feature owner.  
**Disposition:** CLOSED; archive the complete change-control directory from `change-control/in-progress/` to `change-control/complete/` with historical evidence preserved.

## Delivered capability

The existing IMAGE Fragment supports independent optional external HTTP/HTTPS links and optional source-page Marquees. The editor’s Day reader exposes the authoritative Image ID. The responder, Angular editor and public web reader maintain the accepted link/Marquee persistence, navigation and authoring contracts. Development authoring flags `imageFragmentWritesEnabled` and `imageFragmentExtensionsWritesEnabled` and their Playbooks equivalents have been permanently retired; ordinary permissions, locks and optimistic-version checks remain.

## Acceptance and evidence

- **Step 1 — CLOSED:** baseline and cross-component contract, accepted 20 November 2026.
- **Step 2 — CLOSED:** responder/database/MQTT implementation, integration and evidence, accepted 20 November 2026.
- **Step 3 — CLOSED:** editor, reader and Day reader Image ID, with cross-component UI coverage, accepted 20 November 2026.
- **Step 4 — CLOSED:** compatible rollout and original owner production acceptance, subsequently superseded operationally by the Step 5 gate-free responder deployment. Preserve the Step 4 evidence as historical proof.
- **Step 5 — CLOSED:** Java regression; five healthy local Docker containers; five owner-confirmed local IMAGE GUI tests; Jenkins build-86 SUCCESS; coordinated production Ansible run (51 OK, 2 changed, 0 failed); five healthy production containers; obsolete responder JSON keys absent; Playbooks contract PASS; owner-confirmed production IMAGE browser test. The final production acceptance receipt and original deployment log were pushed in parent commit `bb9a1cbf1b1e7a20de67703961d598ccbf0505dc`.

[Step 5 production acceptance receipt](STEP5-PRODUCTION-CLEANUP-ACCEPTANCE-20261121.md)  
[Step 5 production deployment log](production-gate-cleanup-20261121T115921Z.log)  
[Step 4 production acceptance review](../Step%204/STEP4-PRODUCTION-ACCEPTANCE-REVIEW-20261121.md)

## Production identity at acceptance

| Component | Published version |
|---|---|
| Client | `0.0.9-build-79` |
| Responder | `0.0.9-build-86` |
| Web | `0.0.9-build-9` |

Responder image: `docker.io/rsmaxwell/diaries-responder:0.0.9-build-86`  
Published image digest: `sha256:69823881bb5347eb11ddf2302871c3af2760ad6dc2e660fcfa38d9c46949d51c`.

## Git traceability

| Repository | Accepted revision |
|---|---|
| Diaries parent, implementation | `94d2b91ac06a7fba9594e2c2b41edcfe10dccc30` |
| Diaries parent, final production evidence | `bb9a1cbf1b1e7a20de67703961d598ccbf0505dc` |
| Diaries responder | `4109c37eb64ea8f8f513a439628d75145f658634` |
| Diaries client | `4faeac6af36913a947e7947c7adb17856bd86e19` |
| Diaries web | `6d1b289bc5a7983cbf36fe771f8c11dc4725813b` |
| Playbooks | `417de0887109324b5f78ba0fc1bd5591625e4f12` |
| Ansible controller | `8efacfa26acaddbea2e0dd2eeab7c8947b29462a` |

## Boundaries, rollback and handoff

- Legacy 0028 embedded-image conversion is **not** authorised by this closure. Its review/manifest decisions and separate production migration acceptance remain required.
- 0029 IMAGE lifecycle/legacy coupling work remains separate; it must preserve valid optional IMAGE Marquees and link behaviour.
- 0052 Whitley Park map-content defect remains an independent TODO.
- Older responder/client/web binaries are not safe rollback targets after extended IMAGE records exist. Removing or disabling feature flags is no longer an option; use compatible forward recovery or an independently verified restore plan.
- No database data, Files dataset, backup snapshots or unrelated Git changes are altered by the closure archive move.

**Owner decision:** “I approve of the formal closure of 0051-FEAT” (21 November 2026).
