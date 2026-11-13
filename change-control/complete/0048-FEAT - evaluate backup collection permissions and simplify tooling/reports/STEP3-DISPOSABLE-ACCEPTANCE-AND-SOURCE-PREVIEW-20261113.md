# 0048-FEAT — Step 3 disposable verification acceptance and next controlled operation

**Recorded:** 13 November 2026 (UTC)
**State:** Disposable two-run convergence and read-only mars access checks PASS. Real deployment not yet run; Step 3 implementation/Step 4 acceptance remain OPEN.

## Accepted diagnostic observations

The operator's `note(20261113-075051).txt` reports the Step 3 disposable regression at controller `f6ba7fec7752f4bbfa1535958500bde9dea3ea84`, Playbooks `df68a0e3bc57bae29a76f46a58c30835126d7f20` and inventory `ebcce026723db37b9b53b76ba21903a351d48466`.

- Fresh Git checkout with umask `022`: five synchronized directories `0755`, nine filter files `0644`; all nine frozen filter hashes verified.
- Existing `mango` Playbooks checkout: 14 local metadata differences (`0775` directory and `0664` filter file modes) against the clean checkout.
- Candidate role does **not** set modes for synchronized directories; user cron and log directories retain `0750`, while separately templated launchers retain `0744`. Native rsync archive-mode permissions remain intact.
- Fresh disposable target: first run `changed=4`, second run `changed=0`; `FRESH_RUN2_CHANGED=0`.
- Simulated existing-`0750` disposable target: first run `changed=3`, second run `changed=0`; `EXISTING-0750_RUN2_CHANGED=0`.
- Read-only `mars` ancestry and intended reader checks PASS; no production deployment or dataset mutation.

The test establishes **disposable convergence**, not live `mars` correctness or authorisation to relax the installed backup directory permissions.

## Next operation and boundaries

Run `tools/verify-0048-step3-source-normalisation-and-preview.sh` on `mango` from the authoritative Windows Diaries copy through SSH. It:

1. Checks exact parent/Playbooks/inventory revisions and confirms the previously reviewed candidate files, with no staged or unexpected tracked changes.
2. Records current source metadata and normalises **only** the five Playbooks working-copy directories to `0755` and the nine filter files to `0644`. Does not modify Git content or `mars`.
3. Runs the updated source-mode/hash preflight, targeted Ansible syntax check and `--check` preview for the `user,machine` tags, limited to `mars`, using the post-0046 inventory and existing vault password file.
4. Records the Ansible results and Playbooks Git status; requires operator review before real deployment.

Capture output in `evidence/Step 3/` in the Windows Diaries repository. A failing check leaves Step 3 OPEN and does not authorise a deployment; `chmod` may already have normalised local source modes before a later failure.

## Required next review

Verify that the preview contains only intended changes to permissions and backup-collection files and does not unexpectedly alter cron jobs, mounts, snapshot or replication services. Preserve the historical `source-modes.json` and completed 0047 evidence until the real deployment is accepted. After that, retire the **active** 0047 restoration dependency, retain historical records, publish both repository changes with the parent submodule pin, run consolidated second-pass idempotence and confirm operational readiness without destructive snapshot tests.
