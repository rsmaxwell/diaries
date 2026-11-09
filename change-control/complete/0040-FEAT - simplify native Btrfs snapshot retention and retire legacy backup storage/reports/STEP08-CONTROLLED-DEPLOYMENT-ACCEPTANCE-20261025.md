# 0040-FEAT — Step 08 controlled deployment acceptance

**Decision: CLOSED — 25 October 2026 (accelerated path; apply accompanying evidence file).**

Step 8's non-destructive shared-manager deployment was already performed in the controlled Step 7 sequence and verified without redeployment. Accept source/installed manager SHA-256 parity on `mars` and `backup`, push executable parity on `mars`, receiver inventory (21 verified, 0 problems), receiver recovery CLEAN, disabled receiver pruning, schedule enabled/active at 03:30 UTC, receipt file presence through 25 October, paired source configuration, rollback copies and Ansible check-mode repeat `changed=0` for both hosts. Playbooks HEAD `a8f857c`.

**Recorded exceptions:** no new full cross-host deletion rehearsal; no second actual `ansible-playbook` apply to demonstrate real-mode idempotency specifically for this installation (check-mode `changed=0` accepted, with earlier deployment regression evidence); no exhaustive independent receipt-vs-live-source UUID audit; no live prune or `@data` cutover. These limits do not invalidate the agreed non-destructive gate.

**Step 9 — native incremental and pruning safety acceptance** remains OPEN. Verify a recent successful scheduled incremental transaction and source/received UUID correspondence; reuse Step 3/5 disposable adversarial and deletion regressions where adequate. Receiver pruning stays disabled. Do not issue a new live deletion without separate identity-specific approval, and do not interpret Step 2 retirement scope approval as deletion authorisation.
