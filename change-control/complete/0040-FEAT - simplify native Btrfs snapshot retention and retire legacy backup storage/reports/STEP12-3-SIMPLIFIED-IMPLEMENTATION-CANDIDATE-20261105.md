# 0040-FEAT — Simplified runtime candidate and conservative test cleanup

**Date:** 5 November 2026. **Status:** SOURCE-LEVEL CANDIDATE — NOT DEPLOYED; STEPS 12.1–12.4 OPEN.

## Functional scope delivered in separate Playbooks ZIP

- Single native `btrfs send -p` → SSH → `btrfs receive` replacement binary.
- One 0600, atomically updated parent/prior state file per host; receiver advances
  before sender, and sender reconciles a lost acknowledgment on the next run.
- Host-local nonblocking `/run/lock/btrfs-snapshot-manager.lock` shared by the
  existing snapshot manager and candidate replication command; defer on collision.
- Retry the *oldest* unreplicated candidate next scheduled invocation. A clearly
  writable, unreceived, unprotected interrupted subvolume is deleted with the
  Btrfs command after readback, then exactly one new receive occurs. Ambiguous
  states are not deleted. Existing historical holds/receipts are preserved.
- Source and receiver pruning state-file pins protect current and immediate
  prior snapshots. **Receiver pruning remains disabled** pending its separate
  receipt/retention integration and operational approval.
- Opt-in Ansible installation on both hosts, opt-in service ExecStart cutover
  on mars; **existing 03:30 timer is unchanged**, old native sender retained
  for rollback. All enable flags default false.

## Validation and outstanding operational gates

Local isolated Python tests (mocked Btrfs/SSH): normal advancement, parent
protection, incomplete/complete/ambiguous candidate handling, lock back-off,
reconciliation and source/receiver state persistence. Existing source pruning
regressions were also exercised. This is **not** live `mango`, `mars` or `backup`
acceptance. The uploaded Playbooks source baseline is dated 2 November and
may lack the user's newer working-tree changes. Apply using Beyond Compare
and inspect local differences before deployment.

A disposable actual Btrfs interrupted-receive/retry integration and a
controlled sender↔receiver operational acceptance are **still required**.
Existing native reader receipts are not created by this simplified command;
receiver pruning must remain gated and cannot be claimed functional.

## Revised obsolete-test retirement

The tool `tools/retire-obsolete-playbooks-step12-tests.py` is narrowed:
- It automatically considers only **untracked** `verify-0040-step12-3-*`
  prototypes and their matching README/guide files.
- It retains *all tracked or modified tests*, general agreed-parent, native
  Btrfs, source/receiver pruning, and shared-retention tests.
- `--plan` changes nothing. `--apply` requires both replacement regressions
  present, archives full bytes plus checksums to this Diaries feature, and only
  then removes exact archived untracked files.
- **No retirement has been applied.** Apply only after replacement tests are
  accepted on mango; the accepted historical raw logs remain unchanged.
