# 0045-FEAT Step 3 — systemd ExecStart runtime fingerprint reconciliation

Date: 11 November 2026. Status: **PENDING live reconciliation**; Step 3 remains OPEN.

## Source evidence

- `mango` Playbooks change was committed/pushed as `1939a0984934062d03c01de826ad4a5a87d3338d`.
- The controlled apply `deployment-20261111-130143Z` produced zero changed Ansible tasks and zero failures on `mars` and `backup`.
- The original strict comparison passed `backup` and reported five `mars` *systemd_units* entries, with no `managed`, package, mount, ACL or cron mismatches.
- The original script exited on that comparison error **before** checking the post-deployment Docker key. Do not claim the Docker key check passed until run.

## Collector defect and narrow correction

The version-2 host collector computes `ExecStartSHA256` by hashing the full
`systemctl show ... ExecStart` output. That property includes runtime execution
metadata (PID, timestamps and exit state) in addition to the configured command.
As scheduled oneshot services run, the full hash changes despite identical
unit files. A before/after comparison of this unnormalised hash is not an
appropriate installation-equivalence criterion.

The corrected comparator reconciles a changed ExecStart digest **only** when:

1. This is a loaded `.service` unit with valid 64-character digest values.
2. Every other loaded-unit property is exactly identical, including User,
   Group, FragmentPath, DropInPaths, LoadState and UnitFileState.
3. The root-owned installed unit file's SHA-256 and ownership/mode fingerprint
   match the accepted baseline exactly.
4. All captured drop-in metadata and hashes match; every loaded drop-in is
   included in the collector's inventory.

Any genuine installed-file or service-property change still FAILS. Timer
activation/schedule checks remain strict. Temporary Python/editor artifacts
remain excluded only from scanned script trees.

The follow-up read-only script also requires `NeedDaemonReload=no` for the
five services and an exact Docker signing key hash match. No deployment,
restart, snapshot, prune or replication is performed.

## Acceptance and historical evidence

Original comparison failure: `evidence/Step 3/deployment-20261111-130143Z/installed-state-comparison.txt`.
Preserve this original record without edits. The reconciliation log and
`mars-docker-key-after.sha256` will be stored beside it.

Do not treat Step 3 as CLOSED until the follow-up readback passes and its
results, Ansible recaps and current Btrfs health are accepted.
