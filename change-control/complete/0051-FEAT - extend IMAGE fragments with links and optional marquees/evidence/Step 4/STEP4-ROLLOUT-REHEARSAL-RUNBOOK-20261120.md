# 0051 Step 4 — compatible rollout rehearsal and activation runbook

**Status:** PREPARED, **NOT RUN** on `pluto`. Step 4 acceptance remains OPEN.
The release requires separately approved production deployment and a second
explicit approval before enabling new IMAGE link/Marquee writes.

## Source ownership and prerequisites

- Latest inspected Windows source export: `diaries-sources-20261120-152822.zip`
  (includes accepted 0051 Steps 1–3). This ZIP is a source export, **not**
  proof of current Git branch/status. Verify live Windows checkout before
  applying changes; preserve the uncommitted 0028/0029 changes.
- Playbooks reference export: `playbook-sources-20261118-112944.zip`, **older**
  than the current Diaries export. On `mango`, inspect `/home/richard/ansible-controller/playbooks`
  branch, revision and uncommitted changes before applying the separate
  Playbooks ZIP. Do not assume Git is synchronized with Windows.
- Separate Ansible variable: `diaries_image_fragment_extensions_writes_enabled`
  defaults to **false**. `diaries_image_fragment_writes_enabled` remains **true**.
  The rendered responder JSON must contain both boolean fields. Updating the
  Playbooks role is **not** permission to deploy it or enable the gate.
- Preserve 0028 frozen review evidence. No conversion, cleanup, snapshot
  deletion, backup replacement or restored-production overwrite in this step.

## Read-only source preflight (no network writes)

**Terminal: Windows 11 Cygwin**

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
feature='change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees'
if bash "$feature/tools/verify-step4-offline.sh"; then
  echo 'PASS: Step 4 offline source checks'
else
  echo 'FAIL: Step 4 offline source checks; inspect the generated evidence'
fi
```

This runs the 0028 Python regression suite and a source-contract preflight;
it records current Windows Git/submodule state in a new timestamped 0051
Step 4 private evidence directory. It does not re-run expensive 0051
Step 2 database restores or closed Step 3 browser checks.

**Terminal: existing SSH session on `mango`** (after Beyond Compare review of
the *separate* Playbooks ZIP and any pending commits):

```bash
cd /home/richard/ansible-controller/playbooks
git status --short
git branch --show-current
git rev-parse HEAD
ansible-playbook --syntax-check diaries.yaml --vault-password-file ~/.vault_pass.txt
```

Syntax-check is read-only and is not evidence that the configuration has
actually been rendered on `pluto`. Do not apply the Playbooks ZIP blindly if
the current working tree differs from the 18 November source export.

## Coordinated disposable rollout rehearsal (remaining)

Use the new [dedicated disposable rehearsal](STEP4-DISPOSABLE-ROLLOUT-REHEARSAL-20261120.md) instead of starting the current local Compose variants: those variants can write to NAS Files. The accepted Step 3 browser suite need not be repeated.

1. Record the exact *new* responder, client and web image build tags **and
   digests**, local Git/submodule commits and matching candidate JAR hashes.
   Do not infer image tags from role defaults.
2. Use the already accepted disposable restored fixture/migration result
   (`0051 Step 2 c1759df22f5f`) and isolated reader/editor results (Step 3)
   as functional correctness evidence. A new full restore is only justified
   where a different mixed-version compatibility/rollback path needs testing.
3. In a disposable stack, rehearse an additive `image_link_url` schema with
   the responder extension gate **false**. The existing IMAGE writing gate
   remains true. Verify old payloads and plain IMAGE / MARQUEE operations,
   HTTP health and MQTT retained-state replay with all three new components.
4. Rehearse the *mixed-version* sequence explicitly: old reader and old writer
   must not consume newly linked IMAGE or IMAGE-with-Marquee states. Drain or
   invalidate old authoring sessions before enabling the extension gate.
   Prove new writes are rejected while the extension gate is false.
5. Rehearse three-component rollback **before** the first extension write.
   Keep the additive column; verify old application behaviour is intact.
   **After the first extension write**, older binaries are unsafe rollback
   targets; use a coordinated forward fix or separately approved restored
   pre-activation recovery point. Never drop the column to fake rollback.
6. Run local-docker-build and local-published-smoke with recorded real image
   identities. Capture command logs, health, DB/retained hash receipts,
   empty browser errors, activation order and rollback test result under
   `evidence/Step 4/private/`. Until recorded, this runbook is not acceptance.

## Production gates — NOT authorised by this runbook

- Verify an approved fresh production DB + matching Files recovery point and
  its read-back before *any* live changes. Do not create/destroy Btrfs snapshots
  or touch backup datasets without the proper separate approval.
- Record `pluto` running container **image IDs** (not only tags), current
  responder JSON flags, PostgreSQL column/constraints, active writer sessions,
  source/target Pages, MQTT retained state and Files permissions.
- Obtain explicit approval for the **exact** production schema and coordinated
  deployment; apply the nullable migration only after that approval. Deploy
  three compatible components with extension writes **disabled**, verify
  service health, old-data rendering, retained replay and rollback receipt.
- Obtain separate explicit approval for activation; drain stale editors and
  set `diaries_image_fragment_extensions_writes_enabled: true` only after
  compatible writers/readers are verified. Retain old IMAGE authoring gate true.
- 0028 stays PAUSED; its reviewed HTML conversions have independent acceptance,
  fresh-inventory, durable-journal, rehearsal and apply approvals.

## What Step 4 has **not** demonstrated

The owner recorded Playbooks `main` revision `c13b1d5c690c879a4464b0a302aefda92d6335f8`
at `/home/richard/ansible-controller/playbooks`; `ansible-playbook --syntax-check
diaries.yaml --vault-password-file ~/.vault_pass.txt` passed on `mango` on
20 November 2026. This is not a live rendered-role or deployed-service check.
No `pluto` service audit, no local published-smoke image verification,
no cross-version rollback rehearsal, no production deployment or activation.
These omissions block formal Step 4 closure.
