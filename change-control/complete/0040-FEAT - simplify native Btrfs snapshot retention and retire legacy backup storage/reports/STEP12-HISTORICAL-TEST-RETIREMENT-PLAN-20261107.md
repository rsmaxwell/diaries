# 0040-FEAT — Step 12 historical verification cleanup

**Status: PACKAGE PREPARED, NOT EXECUTED ON MANGO.**

## Evidence and scope

The `playbook-sources-20261107-113340.zip` source bundle contains 184 Python
verification files directly under `roles/btrfs-replication/tests/`.
A targeted review identified 141 old Step 12/agreed-parent test names from
superseded multi-phase designs. To preserve still-useful safety guards, the
cleanup explicitly retains four Step 12.3 scripts and the parent-boundary
check, while also capturing two Step 12.3c scripts and three guides that would
otherwise reference retired tests. The final planned scope from the bundle:

| Type | Archive candidates |
| --- | ---: |
| Superseded Step 12/12.3 Python prototypes | 100 |
| Earlier agreed-parent Python prototypes | 37 |
| Superseded unattended-gateway Python test | 1 |
| Historical Step 12 guides | 5 |
| Other linked historical guides | 3 |
| **Total** | **146** |

This retires 138 Python tests and eight historical guides, leaving 46 Python
tests in that Playbooks role. Source and receiver-pruning tests under
`roles/snapshots/tests/` remain unchanged.

The active simplified regression suite and accepted historical evidence are
preserved. No production binaries, Ansible tasks, timers, snapshot data,
Btrfs volumes or replication state are touched.

## Tool replacement

Revises the existing feature-local
`tools/retire-obsolete-playbooks-step12-tests.py` to include tracked and
modified historical files. It rejects staged candidate changes, active code
references, symlinks and conflicting archive bytes; requires an explicit
reviewed count for `--apply`; verifies all SHA-256 archival copies before
removing any source test. The manifest includes Playbooks branch, revision,
Git status, source path, original SHA-256 and exact archived bytes.

All archives belong in the Diaries parent repository under
`tests/retired-step12-3/`. This folder is deliberately not shipped in the
package: it must be populated from **mango's actual Playbooks working tree**,
which may contain uncommitted local changes not represented in an uploaded ZIP.

## Local verification (7 November 2026)

- Seven cleanup-tool fixture tests passed: read-only planning, tracked and
  untracked archival, exact hashes, staged-change refusal, active-reference
  refusal, symlink refusal and conflict protection.
- A disposable Git checkout recreated from the latest Playbooks bundle
  produced **146 planned candidates** with no active executable references.
- Its test retirement archived and removed all 146 files; all archive hashes
  were verified and its manifest contained 146 records.
- The surviving simplified replication, protection and shared-retention test
  suites passed (20 tests, 3 tests and the shared-retention check).

These are **local rehearsals**, not claims about the live `mango` tree.

## Operator acceptance and next steps

1. Apply the Diaries package to the authoritative Windows checkout and
   synchronise the feature tool to `/home/richard/diaries` on `mango`.
2. Run the read-only `--plan`, review actual candidate names and statuses.
3. For an accepted list, run `--apply --expect-count 146` from the supplied
   instructions. If the live count differs, stop and reconcile rather than
   automatically broadening removal.
4. Run retained regressions, capture the Git diff, synchronise the resulting
   archive and raw logs to Windows, then commit Playbooks deletions and the
   Diaries evidence separately after review.
5. Independently verify the first scheduled receiver pruning run on
   8 November; Step 12 remains OPEN until that evidence is accepted.
