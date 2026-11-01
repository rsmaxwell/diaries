# 0040-FEAT Increment 3G — Production initialiser candidate

Status: **SOURCE CANDIDATE ONLY — NO PRODUCTION INSTALLATION OR STATE WRITE AUTHORISED**.

Source evidence: `note(20261030-150529).txt`; receiver receipt and both read-only Btrfs identities match 20261030-030033Z/d901ddd2-66c7-0b42-b26c-ab6886273b7a; agreed-parent files absent; source push/prune timers stopped as of 15:04 UTC; receiver pruning disabled. Time-dependent facts MUST be rechecked immediately before application.

The implementation provides explicit endpoint-specific `--plan` and `--apply`. Both acquire pre-existing locks: source `.native-push.lock` then snapshot-manager lock; receiver snapshot-manager lock then receiver writer lock. It verifies live Btrfs UUID/read-only status; source legacy pins; receiver receipt and receiver-prune disabled state; source timer/service isolation. Existing state must match exactly; malformed state fails closed. Write uses the established state module's atomic save and root-only 0600 permissions. Source apply requires explicit `--receiver-confirmed`; no peer SSH verification is performed by the tool.

**Critical review items before any production use:** (1) install source state module and candidate in approved fixed locations on both hosts with Ansible and check/diff; (2) peer confirmation is currently human-supplied, not cryptographically bound to remote state; (3) add simulated end-to-end interruption / retry regressions under both locks, root metadata, and failure injection; (4) verify the correct source lock ordering with the deployed push code; (5) verify manual prune or other deletion actors cannot bypass the manager lock; (6) plan recovery and timer restoration. Do not use `--apply` until these gates are closed.

Receiver first then source; keep timers stopped until both states are confirmed and sender integration is reviewed. Snapshot creation remains running. No changes to pruning authority.

Tests: 13 disposable local tests PASS; not yet run on mango. Existing 3G candidate and pruning regressions must also run. Do not mark Increment 3G closed.
