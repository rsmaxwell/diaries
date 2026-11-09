# Step 12.3 — Obsolete verification-script cleanup (design revision 2026-11-05)

**Status: PREPARED; not executed against `/home/richard/playbooks`.** No runtime modules, deployed files, Ansible tasks or services are removed by this document.

## Rationale

The 2 November 2026 uploaded Playbooks source bundle already contains many feature-specific Step 12.3 `verify-0040-*` files for the superseded journal/scope/receipt-promotion/staged-receive architecture. Additional prototype tests were added in successive 3–5 November packages. These should not remain as the permanent regression suite for the simplified design. Earlier test outcomes remain valid **historical evidence** even after the test files are retired.

## Scope of guarded cleanup

The feature-local tool `tools/retire-obsolete-playbooks-step12-tests.py` inventories **only** these Playbooks paths under `roles/btrfs-replication/tests/`:

- `verify-0040-step12-3*.py` (including staged, scoped, journal, private stream and promotion prototypes)
- `verify-0040-agreed-parent-*.py` (earlier Step 12 transition/transport prototypes)
- `verify-0040-step12-parent-boundary.py` and `verify-0040-step12-unattended-gateway.py`
- Step 12.3-specific README/experiment markdown in that same test directory, when matching the explicit safe filename patterns

The tool **does not** touch the native Btrfs `verify-native-*`, retention/prune/snapshot manager, Step 3 accepted tests, binaries in `roles/.../files`, Ansible tasks, timers, or any snapshot/backup data. No blanket `find -delete` or role-directory rewrite.

`--plan` is the default. `--apply` first copies every selected file byte-for-byte into `tests/retired-step12-3/`, records SHA-256 and Playbooks Git status in a manifest, verifies all copies, and **only then** removes the selected source test files. It refuses symbolic links and conflicting archive copies, and checks active code/task references to candidate test filenames. Existing uncommitted test modifications are preserved in their archived form; nevertheless review the plan and Git diff before accepting changes.

**Review before execution:** run on `mango` against its actual current branch/revision and local changes, not the 2 November ZIP alone. The user may apply tests added in later ZIPs; the runtime inventory catches them. Synchronise the Diaries feature-directory ZIP to `mango` before invoking its tool. Run cleanup after ensuring replacement compact tests are in place, or explicitly accept temporarily reduced Step 12 prototype test coverage. Preserve the archival directory as historical evidence and commit it through the normal Windows Diaries workflow.

## Replacement verification (small, maintained)

Name replacement tests `verify-0040-simplified-*.py` so they are unambiguously outside the retired prototype filename families. Keep a few implementation-neutral tests for: agreed-parent state/hold protection; native transport with lost ACK; receiver lock-back-off/prune exclusion; interrupted disposable Btrfs receive cleanup/retry and ambiguity refusal; controlled scheduled cycle. Permanent reusable native/retention tests remain in Playbooks. Run these as a consolidated suite once the replacement is implemented—do not carry the old 100+ module-specific tests forward unchanged.

## History and status

Previous successful test logs and historical Step 12.3 reports stay in this feature's `reports/` and `evidence/` locations. The new decision does **not** retroactively invalidate past observed results. No test removal or deployed runtime cleanup is claimed until a `--apply` output and Git status have been captured.
