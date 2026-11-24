# 0028 Step 1 — evidence register (OPEN)

The read-only collection produces evidence at
`evidence/Step 1/private/<timestamp>/` **in the Diaries parent repository** on
mango. This path is ignored by Git. It contains the live Fragment HTML,
embedded-image source strings and Image catalogue metadata; it is **private**.
Do not move its raw contents into public Playbooks, source ZIPs, Git commits or
ordinary chat logs.

Record the following after actual execution; all are currently **NOT RUN**:

| Evidence | State / receipt |
|---|---|
| Windows Git parent/submodule HEAD, branch, dirty status | NOT CAPTURED |
| mango Git parent/submodule HEAD, branch, dirty status | NOT CAPTURED |
| Deployed Compose services/image identities and authoring gate | NOT CAPTURED |
| Historic 0022 candidate CSV location and SHA-256 (if recovered) | NOT LOCATED |
| Historic 0022 review ledger version/hash | Source bundle available; not yet live-copied |
| Historic 0024 path/catalogue cross-reference and SHA-256 | NOT LOCATED |
| New consistent current-schema DB snapshot and SQL export hash | NOT RUN |
| Read-only Files-root to Image catalogue integrity reconciliation | NOT RUN |
| Candidate coverage, drift, ambiguous source matches | NOT REVIEWED |
| Filled dispositions and occurrence decisions, reviewer approval | NOT REVIEWED |
| Manifest freeze/sign-off and Step 1 gate | OPEN |

Run the tests and collector only after applying the parent-only package to the
Windows checkout and verifying/synchronizing its copy on mango. No application,
Playbooks, DB or MQTT modifications are part of this Step 1 increment.

See `../../tools/STEP1-COLLECTION-RUNBOOK.md` for host-labelled commands.
