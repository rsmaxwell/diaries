# Step 07 — Idempotency and negative regression

**IN PROGRESS (opened 21 October 2026).** The Step 5 accepted `mango` Ansible check-mode convergence (`changed=0`) is reusable evidence. It is not equivalent to the Step 7 implementation-plan requirement for a repeated **real** Ansible invocation; that separate production-changing operation needs its own explicit acceptance.

Start with the read-only/source checks in `STEP07-REGRESSION-PLAN.md`, review outputs, then decide whether the controlled real repeat is justified. No local snapshot timers, receiver data, replication receipts or retention settings are to be changed.
