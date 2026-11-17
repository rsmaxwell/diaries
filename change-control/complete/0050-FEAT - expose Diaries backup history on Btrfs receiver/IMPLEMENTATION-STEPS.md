# 0050 — Implementation steps

**State:** FORMAL CLOSURE APPROVED; Steps 1–4 accepted CLOSED; archive publication awaits the guarded closure helper. Historical pending statements below are dated checkpoints, not current blockers.

## Step 1 — Capture actual baseline and confirm receiver layout (CLOSED)

- **Windows Cygwin terminal**, Diaries root `C:\Users\Richard\git\github.com\rsmaxwell\diaries-application\diaries`: record branch, HEAD, `git status --short`, `.gitmodules`, and `git submodule status`; do not assume Windows and `mango` are synchronised.
- **mango SSH terminal**, `/home/richard/ansible-controller`: record parent, `playbooks` and `inventory` submodule HEADs/branches/dirty states; ensure the Playbooks baseline is or descends from published 0049 `a2508ad61f479c1b2bc20cb39896006c1f2906e1`. Do not copy inventory/vault secrets into the public repo or evidence.
- **mars and backup SSH terminals**: record `command -v diaries-backup-status diaries-backup-history`, `/etc/btrfs-snapshot-manager.json` with secrets filtered if any, existing independent schema-2 verifier availability, timer/retention and backup inventory read-only. Verify actual received layout (root `/@data/mars-received/@data`), marker and manifest paths and whether the receiver account/root can traverse them. On `backup`, inspect two representative retained snapshots *without writing them*.
- Record the difference between source snapshot manager verification and *read-only inspection of already received* markers. Establish a specific disposable receiver-only backup-ID fixture; production receiver-only ID is optional, not a precondition.

**Evidence:** `evidence/Step 1/` — revision manifests, installed command/config checks, snapshot structure/permissions and decision record. No destructive command.

## Step 2 — Implement both receiver commands and preserve source behaviour (CLOSED)

Implement one coherent Playbooks source change set:

1. Extend `roles/snapshots/files/diaries-backup-history.py` to select reader metadata for a receiver using a separate **read-only** `diaries_history` config section in the existing manager JSON. Source continues using existing `verification` metadata. Support receiver `sources[].snapshot_directory` (or an equivalently explicit, strictly validated receiver snapshot path); do not enable receiver `verification.required`.
2. Update `roles/btrfs-replication/templates/btrfs-receiver-manager.json.j2` with the reader-only configuration: root, `@data`, embedded dataset and verified marker relative paths, and existing schema-2 verifier path. Validate the receiver tree/root is canonical and within the approved fixed repository. Ensure the snapshot manager ignores this additive reader section without changing pruning or other behaviour.
3. Extend `roles/btrfs-replication/tasks/simplified-runtime.yaml` or a clearly named imported task to install **both** `/usr/local/sbin/diaries-backup-history` and `/usr/local/sbin/diaries-backup-status` on `backup`, plus `/usr/local/lib/diaries-backup/complete-dataset-manifest.py` with its parent directory. Keep installation root-owned (`0755` scripts, appropriate directories) and idempotent, within the normal active role. Existing source-only `snapshots` provisioning remains valid; avoid creating duplicate permanent copies of the reader or verifier.
4. Make `diaries-backup-status.py` work in either endpoint mode using the same local `diaries-backup-history --config ... --json list` and preserve existing JSON fields, exit 0/1/2 interpretation, warnings and tabular output. Human heading may identify `backup (receiver)` as an additive enhancement, without changing `mars` output.
5. Preserve `list --all`, `show`, `path`, `verify`, `--snapshot`, `--logical-dataset`, marker/manifest identity checks, full schema-2 verification and all negative/path-containment checks. In particular, absent or damaged received snapshots must warn/degrade rather than silently vanish from the history; a missing receiver root/config must fail visibly.
6. Update permanent role docs and regression tests in Playbooks; place only feature-specific fixtures, temporary tools and evidence in this Diaries feature directory.

**Evidence:** `evidence/Step 2/` — coherent Playbooks diff, regression/source output, Ansible syntax/check results, versioned change manifest. No deployment implied by source completion.

## Step 3 — Consolidated regression, controlled deployment, live read-only acceptance (CLOSED)

- Run `tests/verify-0050-receiver-history-fixtures.py` (once code is implemented), and permanent Playbooks history/status/snapshot-manager/replication/0041 regressions. Fixtures must include a backup ID only on receiver, manifest mismatch, missing/unsafe marker, conflicting identity, empty inventory and explicit `verify` delegation. The feature fixture uses a disposable verifier stub **only to test CLI invocation**; actual verifier integrity must be proved with the production schema-2 tool in a separate integration test.
- Run Ansible syntax check and receiver-limited `--check --diff`; review changes to paths, ownership, binary hashes, config and effective permissions. Deploy to `backup` using the normal playbook only after safe preflight; verify both commands and independent verifier installed. Reapply to check `changed=0` on `backup` and, where appropriate, `mars`.
- From the **backup SSH terminal**, run local `sudo -n diaries-backup-status`, `sudo -n diaries-backup-status --json`, `sudo -n diaries-backup-history --json list`, `list --all`, `show`, `path`, and a selected `verify` (I/O cost accepted). Check no SSH to `mars` and no changes to root/marker/manifests/parents/holds/services. Compare `mars` output for output and exit-status regressions.
- Prove the important receiver-only condition on disposable Btrfs fixtures **and** validate on real receiver if a historically unique ID actually exists. Do not prune `mars` to create an example.
- Check the receiver prune planner, agreed parent/prior and held checkpoints still match pre-deployment results; *dry run only*. Preserve the 0049 and 0041 security and protocol baselines. Repair any defects and rerun only affected tests.

**Evidence:** `evidence/Step 3/` — consolidated test results, receiver deployment and read-only reports, independent verifier output, Ansible idempotence and non-mutation proof.

## Step 4 — Final review, publication and closure (CLOSED)

- Compare acceptance matrix to logs and produce final implementation/rollback report. Record known limitations (manifest identity versus explicit full verification, independent retention and read-only rights).
- Commit Playbooks to its own repository, then pin/publish the updated `playbooks` submodule in private `ansible-controller`. Keep private inventory unchanged unless an explicitly justified variable is required; never publish vault contents to the public Playbooks repo.
- Commit/publish Diaries parent change-control evidence and record all three actual revisions, deployment hashes and rollback guidance. Confirm no application submodule changed unexpectedly.
- **Only upon formal feature closure approval:** mark accepted Steps 1–4 CLOSED, move the whole 0050 directory to `change-control/complete/` and commit/publish the relocation. Do not repeat a costly restore or transfer after accepted correctness evidence.

**Evidence:** `evidence/Step 4/` — Git manifests, publication receipts, accepted closure decision and retained rollback record.

## Implementation progress note — 2026-11-17

The source implementation described in Step 2 has been packaged and tested
against the 0049 Playbooks bundle. Tests cover receiver-only and source
compatibility, conflict/marker/symlink/empty paths, complete schema-2 file
verification, 0041/0049/0040 regression and YAML/Python parsing. This is
pre-deployment evidence, **not** live acceptance or a CLOSED step.
Steps 1 and 3 require the stated live read-only preflight and Ansible results
before acceptance. Do not repeat costly replication or destructive retention.

## Step 3 progress — First receiver deployment, 17 November 2026

- Receiver Ansible deployment **PASS** (`ok=37 changed=2 failed=0`).
- `diaries-backup-status` / history list / list --all **PASS**: 30 backup IDs,
  42 occurrences, no manifest identity conflicts; Btrfs receiver HEALTHY.
- Live schema-2 `verify` **FAIL** (`backupId must use UTC ...`): the shared
  reader omitted the verifier's existing fixed-working-root option for
  `diaries-backup` directories. This is a **remaining Step 3 acceptance
  blocker**, not evidence of corrupt backup data.
- Minimal Playbooks correction and new disposable fixed-root/source/generation
  integration test **PASS** locally. Live re-deployment, selected received
  backup `verify`, idempotence and final repository publication still pending.

See the first live deployment report and original logs in `evidence/Step 3/`.

## Step 3 final operational acceptance — 17 November 2026

- Full receiver schema-2 verification of a selected completed Diaries backup: **PASS** (128 files), following the existing fixed-root verifier-option correction.
- Receiver Diaries status: **HEALTHY**; 30 distinct backups, 42 retained occurrences, no reported identity conflicts. Receiver infrastructure: **HEALTHY**.
- Strict Ansible reapply to `backup`: **PASS** (`ok=37 changed=0 unreachable=0 failed=0`).
- Host-local history comparison: **PASS** — 19 shared identities, **11 receiver-only** and 3 source-only; independent retention is valid.
- Disposable receiver-only selection/verification and malformed/corrupt/conflicting identity tests had already passed, as had relevant 0041/0049 security and protocol regressions. No production pruning or restore was performed.

See `reports/FINAL-OPERATIONAL-ACCEPTANCE-20261117.md` and `evidence/Step 3/`. The earlier stage-specific failures remain as historical evidence; they are no longer active blockers. **Step 4 publication and formal closure are pending; no step is marked CLOSED without accepted closure evidence.**

## Step 4 publication progress — 17 November 2026

- Playbooks implementation **published** at `a1f27ddf20e6c9668c6ad8f0d801de0233695ccc`, following source-only acceptance.
- Git source mode `diaries-backup-history.py` initially changed `100755` → `100644` unintentionally; corrective **mode-only** commit `b0063d455faf4b264504405f9db72ab21c692741` restored `100755` (0 insertions/deletions). No application logic change.
- Ansible-controller's final published revision is `28e394b48ba91479b147452d70adb39ff3b84559`, pinning Playbooks `b0063d455faf4b264504405f9db72ab21c692741`; private `inventory` remains `ebcce026723db37b9b53b76ba21903a351d48466`. Both repositories passed remote SHA verification.
- No Btrfs transfer, pruning, restore or Ansible deployment was performed as part of the mode-only correction. Already accepted live verification and strict idempotence are sufficient.
- **Still pending:** publication of Windows Diaries change-control documentation/evidence, final revision receipt, then formal feature closure approval and directory relocation. Do not mark Step 4 or other steps CLOSED yet.

See `reports/FINAL-REPOSITORY-PUBLICATION-20261117.md` and the two verbatim Git logs under `evidence/Step 4/`.

## Formal closure decision — 17 November 2026

The feature owner approved formal closure after accepted technical tests, live backup readback, strict receiver Ansible idempotence, independent receiver-only history comparison, and publication of Playbooks, Ansible-controller and Diaries evidence. All four steps are marked **CLOSED** by approval. The accepted evidence is listed in `reports/FORMAL-CLOSURE-DECISION-20261117.md`, `reports/FINAL-PUBLICATION-AND-REVISION-RECORD-20261117.md`, and the original logs under `evidence/`.

The previous Step 4 publication-pending statement is a historical checkpoint. Actual Diaries evidence publication succeeded at `06ae009f2b840a9021045a9da3266d022ab6c65d`. The full feature history is archived through `tools/close-0050-feature.sh` only after checking the current origin, revision, migration completeness and remote readback. Formal archival is complete only when that command reports PASS; the archival commit SHA cannot be predeclared.
