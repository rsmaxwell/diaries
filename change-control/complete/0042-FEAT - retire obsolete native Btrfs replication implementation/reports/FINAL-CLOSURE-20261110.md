# 0042-FEAT — Final acceptance and closure (10 November 2026)

**Decision:** Accept the verified source retirement and close Steps 1–4, with the formal feature move from `change-control/in-progress/` to `change-control/complete/` in a dedicated Diaries close-out commit. The closure commit must explicitly track the verified rollback archive and must exclude all 0039 changes.

## Accepted evidence

| Gate | Acceptance result | Evidence |
|---|---|---|
| Source retirement | 215 obsolete Playbooks files verified by exact-path SHA-256 manifest; archived before removal; 8 consolidated suites passed | `evidence/Step 1/0042-source-retirement-20261110-081412Z.json`, `source-verification-20261110.txt`, rollback archive |
| Deployment | Syntax, preview and Ansible live deployment passed; `mars` 14 OK/0 changed, `backup` 25 OK/0 changed | `evidence/Step 2/deployment-20261110.txt` |
| Legacy host absence | 39/39 previously removed paths absent on `mars`; 35/35 absent on `backup` | `evidence/Step 3/post-deployment-20261110.txt` |
| Simplified runtime | Active sender invokes simplified replication; receiver independently agrees on parent `20261110-030004Z`; identity verified | `evidence/Step 3/post-deployment-20261110.txt`, `final-readback-20261110.txt` |
| Backup and snapshots | `mars` 70 complete/0 incomplete sets, valid Diaries backup `20261110-003113Z`; `backup` 33 complete/0 incomplete | Step 3 logs and readback |
| Timers | Sender, receiver retention and both qgroup-maintenance timers enabled and active | Step 3 post-deployment log |
| Archive integrity | Receipt's SHA-256 exactly matched the copied 215-member archive | `evidence/Step 3/final-readback-20261110.txt` |
| Isolated source control | 0042 Playbooks commit `328b81b3606ebff98fc8787d2a08eff3627d2a78` and Diaries acceptance commit `e8907ba9c7544d239671e6acf6fedc7eaa194947`; 0039 work left out | `evidence/Step 4/playbooks-source-commit-20261110.txt`, `diaries-evidence-commit-20261110.txt` |

## Rollback and evidence retention

Rollback archive: `evidence/Step 1/0042-retired-playbooks-20261110-081412Z.tar.gz`.

SHA-256: `d00f75fd7d3d5000f234f633ad65887331f122f57a58c3e9b1302971facba37b`.

The archive is intentionally added with `git add -f` because the generic evidence ignore rules exclude `.tar.gz`; then `git mv` carries it into the completed feature in the final closure commit. This creates a durable, versioned rollback artifact without globally relaxing evidence exclusions. Original raw Ansible output, manifests and receipts are preserved unchanged. Previously accepted 0040 restore/transfer evidence is reused. No production snapshot manipulation, replication rerun, quota rescan or host-file deletion is required for closure.

## Scope and disposition

- **Step 1 — CLOSED:** verified and archived the 215 obsolete source files, retired them, and passed retained regression suites.
- **Step 2 — CLOSED:** simplified-only deployment passed on both hosts without changes or failures.
- **Step 3 — CLOSED:** live-host absence, protected parent and backup checks passed.
- **Step 4 — CLOSED upon final commit:** source-control isolation, permanent rollback evidence and feature move accepted.
- **0042-FEAT — CLOSED upon final commit.** The final close-out commit hash is obtained from the Git log after the operator executes the closure command; do not invent a receipt in advance.

**Independent work:** 0039-DEF remains open and uncommitted and is excluded from this closure.
