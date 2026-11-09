# 0040-FEAT — Increment 3G — Shared pruning protection candidate

Source baseline: playbook-sources-20261030-130134.zip. Apply to repository root via Beyond Compare.

Adds `agreed_parent_pins(config)` to the shared snapshot manager. The source `prune()` keep set and receiver's *read-only* `receiver_plan()` keep set include established, pending and previous snapshot timestamps. Missing state retains legacy behaviour. Unsafe or corrupt present state fails closed. This does not enable receiver pruning, alter retention buckets, or initialise any agreed-parent records. The existing receiver guarded prune remains disabled.

Local: `verify-0040-agreed-parent-prune-guard.py` 10/10 PASS; `py_compile` PASS.

Gate: run regression on mango, inspect source diff and run Ansible `--check --diff` separately for mars and backup using relevant playbooks/roles; do not apply or alter timers/state until reviewed. Existing scheduled replication and pruning must not be assumed frozen.

Caveat: this is *retention selection* protection, not yet full parity for destructive receiver pruning. Source protection identity and snapshot-presence validation and cross-host transition sequencing need an additional gate before agreed-parent state bootstrap. The current receiver observer and source release-guard remain separate safety layers.
