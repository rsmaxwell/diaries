# 0029-FEAT — Step 3 published-image acceptance and production release candidate

Date: 2026-11-26. Status: Step 3 OPEN. Production deployment NOT authorised.

## Evidence accepted

Operator confirms all six local-published-smoke browser tests passed, with all five containers healthy:
- Client `rsmaxwell/diaries-client:0.0.9-build-81`; source `cc826a8254b0e6d989755dc880d3023dae9e3416`; Docker manifest `sha256:0e25de1343b583bee6d02b31ea0fcfa817920eb74f3b73d601a4459984068ce6`.
- Responder `rsmaxwell/diaries-responder:0.0.9-build-87`; source `a49c6abd0ce005d58eb516770f6515313e40cdf6`; Docker manifest `sha256:9fba097b3c429babae5131978643d406026d4c068deb6b53ba7420a8b0c72713`.
- Web Reader `rsmaxwell/diaries-web:0.0.9-build-10`; source `363ca8f425b811eeedff47486092b1f63c403ab0`; Docker manifest `sha256:b7b2d6de1abfbb825ee69705b34d40805f2b5c139e908415eda4c6c4d7b6728c`.
- Jenkins build numbers 81, 87 and 10 all SUCCESS; parent source `216413468fbaae21dbfbfe36e92c05cd87cba907`.
- Browser checks: Editor loads; Reader annual 1828 PREAMBLE; dated text/images; Whitley Park/Hermitage; annual PREAMBLE editing; dated image creation/editing. Operator-reported, no screenshots supplied.
- Local published-smoke database is the explicitly paired development dataset `data/database/common` and Files selector `files-development-common`.

## Configuration

Playbooks release candidate updates only role defaults for three image tags. Existing Playbooks ACL source already contains client read, responder readwrite, web read for `diaries/years/#` (supplied `playbook-sources-20261126-131142.zip`). Effective production inventory overrides have not been verified and mango Git state must be inspected before applying package.

Rollback images to retain:
- client `0.0.9-build-80`
- responder `0.0.9-build-86`
- web `0.0.9-build-9`

## Remaining production gates

1. Confirm Playbooks/ansible-controller/inventory Git revisions and dirty state; effective production image variables and ACL source versus deployed ACL.
2. Complete independent published Files restore verification (published 128 Files SHA-256 and isolated PostgreSQL restore already passed; prior container Files tar transfer stalled).
3. Confirm fresh paired production database/Files recovery point and the current read-only production 11-row guard; do not repeat accepted isolated migration/rollback rehearsal without new reason.
4. Prepare coordinated downtime: stop writers, transactional Step 2 hybrid SQL then Step 3 Marquee column retirement, deploy corrected ACL and compatible images, reconcile MQTT retained state, complete production postflight.
5. Obtain explicit production cutover approval before executing any production mutation or Ansible deployment.

Do not mark Step 3 CLOSED or move feature to complete until accepted postflight and formal closure.
