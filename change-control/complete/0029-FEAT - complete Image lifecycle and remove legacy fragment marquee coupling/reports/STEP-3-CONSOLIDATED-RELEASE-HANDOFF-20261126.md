# 0029-FEAT — Step 3 recovery and release handoff (26 November 2026)

## Accepted evidence
- Development: responder regression suite, derived Marquee Page schema migration, MQTT reconciliation, six Editor/Reader checks passed.
- Production read-only baseline: 2,331 Fragments, 2,270 Marquees, 11 reviewed Page-less Fragments.
- Isolated production migration: hybrid conversion, Marquee Page retirement, both rollbacks, original baseline recovery and reapplication passed. Corrected hybrid rollback SHA-256: `9c730377288482e38a2633aee078cbc47def064039083657f45bf1b4cf9812a7`.
- Published production backup: ID `20261126-003058Z`; metadata and database archive hashes passed, but full restored recovery unverified as of this report.
- MQTT Playbooks source includes annual topic ACL entries; production deployed ACL does not yet include them.

## Consolidated next readiness procedure
1. Run `tools/run-step3-production-recovery-verification.sh` in the **Windows Cygwin Diaries parent checkout** with Docker running and SSH access to `pluto`. No production writes: reads the published backup, verifies every Files and database payload checksum, restores the published custom dump into disposable `postgres:18-alpine`, copies the 128 Files into that isolated container and re-hashes them. Retains only a log in this feature directory. This test verifies the *published* backup; do not confuse it with a restore of live source files.
2. Run `tools/run-step3-release-source-manifest.sh` on **Windows Cygwin**. This captures the exact modified/new source-file SHA-256s while leaving Git untouched. Review submodule scopes against 0029; stage and commit Client, Responder and Reader independently; update the parent submodule pointers and commit the parent feature files. Do not accidentally commit generated caches, temporary root-level README files, or large recovery dumps. Keep recovery dumps under feature evidence as required and use Git ignore/LFS policy where appropriate.
3. Build the three release images from those *committed* revisions using the existing Jenkins pipelines, and record tags, registry digests, exact component commits and build receipts in 0029 evidence.
4. Review `mango:/home/richard/ansible-controller/playbooks/roles/diaries/defaults/main.yaml`, and the MQTT ACL source `roles/diaries/files/sync/config/mosquitto/aclfile.txt`. Production rollback image tags are Client `0.0.9-build-80`, Responder `0.0.9-build-86`, Reader `0.0.9-build-9`. Verify Ansible effective configuration before modifying tags, and preserve unrelated edits in `defaults/main.yaml` and `scripts/diaries.sh`.
5. Prepare the coordinated release sequence: pre-cutover fresh complete production backup and recovery identifier, stop application writers, guarded production preflight, hybrid Fragment migration, Marquee column retirement, deploy matching responder/client/web and MQTT ACL, validate retained state, then Editor/Reader browser acceptance. Take the fresh database and Files recovery point before any production schema change.
6. Document the rollback decision tree: if no post-cutover edits occurred, use rehearsed reverse SQL stages with the old images; if data changed after cutover, require a separately reviewed consistent complete-dataset restore plan, never assume reverse SQL retains newer edits. Preserve source state, backup snapshots and explicit deployment approval.

## Acceptance status
This package only supplies *read-only* verification and source provenance. Bash syntax and ZIP integrity were validated at creation. It has not been run against production; no Git commits, image builds or deployments have been executed. Step 3 and 0029-FEAT remain OPEN.
