# 0044 Step 4 — Permanent regression consolidation

**Status:** Prepared; local source-only check passed. Live `mango` verification and Playbooks commit pending.

## Rationale

The old `verify-legacy-retirement-source.py` was a one-time retirement acceptance guard. Rechecking that obsolete files and configuration were removed adds little long-term value after accepted 0042 removal and 0044 rename commits. The historical script is copied byte-for-byte to `tests/historical-verify-legacy-retirement-source.py`, and its earlier passing output remains in Step 2 evidence.

## Permanent checks retained

The existing `verify-simplified-cutover-readiness.py` retains its five tests and adds a sixth check for fail-closed runtime and qgroup maintenance defaults. It also verifies root group execution, simplified executable conditions, simplified command installation and the status-report provisioner. The current cutover test continues to inspect the active sender service, state paths, lock and prune safety. Obsolete filenames, retired sudoers and removed historical activation flags are not carried forward as an ongoing regression burden.

## Files

Playbooks: update `roles/btrfs-replication/tests/verify-simplified-cutover-readiness.py` and `roles/btrfs-replication/tests/README-0040-SIMPLIFIED.md`; remove `roles/btrfs-replication/tests/verify-legacy-retirement-source.py` with guarded `git rm`.

Diaries: this report, updated feature README, historical script, and `tools/retire-legacy-regression.py`. Operational settings and Btrfs snapshots are untouched.

## Acceptance

Local reconstruction: six cutover-readiness tests passed. On `mango`, verify the committed baseline, run the four remaining permanent tests, check three exact staged paths, commit separately and preserve the transcript and commit receipt under `evidence/Step 4/`. Close 0044 only after these accepted results.
