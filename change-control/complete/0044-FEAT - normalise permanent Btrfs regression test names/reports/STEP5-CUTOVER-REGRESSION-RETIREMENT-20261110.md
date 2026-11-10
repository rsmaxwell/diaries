# 0044 Step 5 — Retire historical cutover-readiness regression

**Status:** Prepared for the `mango` source-only regression and commit. No production changes.

## Decision

The cutover-readiness script verified the one-off 0040 migration and retired
fallback mechanisms. Following accepted 0040/0042 cutover and retirement, its
migration checks add little permanent value. Retire it from Playbooks rather
than keep obsolete-specific assertions as a perpetual obligation.

Keep one ongoing safety assertion in `verify-simplified-protection.py`:
`prune`, `receiver_plan`, and `receiver_simple_plan` must continue to consult
`simplified_agreed_parent_pins`, so agreed-parent protection cannot silently
be disconnected from a pruning path. The existing unit tests already verify
valid pins and fail-closed handling of unsafe records. Normal replication and
shared-retention regression suites remain unchanged.

## Historical preservation

The prior test is preserved byte-for-byte in
`tests/historical-verify-simplified-cutover-readiness.py`.
SHA-256: `b8962ef9d36f82f0c5fd44483bfb8eda17a04332e52f918a7ecfeac8565c5b18`. Its six passing checks are recorded in the original
Step 4 consolidation output and Playbooks commit
`b393602f3086a570e429dbec57d1a9ff1db7304b`.
The migration's service wiring, install gates, and legacy file absence remain
traceable in Git history, but need not be permanent checks.

## Intended Playbooks source changes

- Modify `roles/btrfs-replication/tests/verify-simplified-protection.py` with
  the current three-planner pin guard.
- Remove the retired cutover-readiness command from
  `roles/btrfs-replication/tests/README-0040-SIMPLIFIED.md`.
- Delete `roles/btrfs-replication/tests/verify-simplified-cutover-readiness.py`
  via guarded `git rm`.

Run the feature-local `tools/retire-cutover-regression.py --check`, then
`--apply` from `/home/richard/playbooks` after applying the Playbooks ZIP.
The tool checks the exact baseline, stages only three paths and runs the
replication, protection and retention tests. Preserve the execution transcript
and Playbooks commit receipt under `evidence/Step 5/`. 0044 stays IN PROGRESS
until the source-control and change-control closure evidence is accepted.
