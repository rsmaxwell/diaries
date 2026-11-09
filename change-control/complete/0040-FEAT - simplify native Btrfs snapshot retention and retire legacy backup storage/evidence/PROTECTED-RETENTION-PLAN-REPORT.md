# 0040-FEAT — Protected retention decision (accelerated integration)

The sender now has `--protected-prune-plan` (separate from `--latest`). It obtains a durable source pruning pin and requests a receiver writer-lock-held common-policy retention plan. The response is advisory (`authorizes_prune=false`, `deletion_executed=false`).

A root-owned public 0644 policy template contains only the retention settings (equal to the 0600 root-only snapshot-manager configuration). The Ansible role installs it only with the existing receiver-manager opt-in.

Tests: five sender contract tests and four configuration/lock tests passed locally. Python compilation passed. No production deployment, live cross-host test, or deletion authority.

Remaining: a sender-coordinated receiver transaction and narrowly authorised privileged deletion, lock-held revalidation, journaling, and recovery acceptance. Keep production prune disabled until all complete.
