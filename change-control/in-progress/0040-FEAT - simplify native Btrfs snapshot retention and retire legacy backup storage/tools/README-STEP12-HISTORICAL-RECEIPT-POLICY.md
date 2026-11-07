# 0040 Step 12 — Historical receipt retention-policy correction

## Repository handling

Use Beyond Compare 4: apply the **Playbooks** ZIP to `/home/richard/playbooks` on `mango`, and **Diaries** ZIP to the Windows Diaries checkout. Check `git status` and the parent/submodule revisions first. The source bundle used was `playbook-sources-20261106-163125.zip` with the accepted 7 November receiver-retention package overlaid; do not overwrite unrelated newer local modifications. Evidence belongs under `0040-FEAT/evidence/Step 12/raw-logs/` in the authoritative Windows Diaries repo; logs produced on mango must be copied/synchronised there.

## Safety scope

Pruning remains false and its timer disabled. Historical receipts remain at their current path unchanged. This change fixes their retention exemption and allows receipt files to outlive deleted subvolumes. Parent/prior, holds, legacy pins, and newer-than-parent snapshots are unaffected. Nothing in the package deletes or reconfigures a production snapshot or changes the 03:30 replication sender.

## Consolidated verification and installation

In SSH terminal to **mango**, from `/home/richard/playbooks`, run the verified command provided with the package. The intended Ansible invocation is:

```bash
ansible-playbook btrfs-replication.yaml --limit backup --tags simplified-receiver-retention --check --diff --vault-password-file ~/.vault_pass.txt
```

Confirm the diff changes only the shared manager executable (the already-installed receiver configuration and dormant timer should be unchanged). Apply the same command without `--check --diff` only if the preview passes and pruning remains disabled. Verify SHA-256 and inspect the `receiver-simple-plan` output on `backup`. Never enable pruning as an incidental part of this deployment.

## Interpretation of the plan

A zero-candidate plan is valid: the shared retention policy retains the last 48 *occupied hourly buckets*. The prior receiver inventory had only 30 subvolumes; removing a legacy receipt retention pin does not necessarily make any currently eligible. Look for these metadata fields:

- `historical_receipts_preserved` — evidence files still on disk, regardless of snapshot presence.
- `historical_receipts_on_candidates` — how many policy-eligible snapshots currently have historical receipt evidence.
- `historical_receipts_orphaned` — historical receipt files whose snapshots were previously removed.

The planner validates Btrfs state for every existing snapshot and the specific parent and holds; historical receipt metadata is not trusted. No receipt file is deleted by the prune operation.

## Real-Btrfs fixture and later authorisation

The modified Diaries test `tests/verify-0040-step12-receiver-retention-real-btrfs.py` retains its `--run` explicit opt-in and uses isolated temporary loop Btrfs filesystems. It now checks a receipt-backed snapshot is physically deleted when eligible, the immutable receipt bytes remain and the subsequent plan reports an orphan receipt. Only re-run the disposable test when the updated script is available on `mango` or stream it via SSH from Windows Cygwin. Any live `receiver-simple-prune` or activation of its 04:15 timer is still a separate **destructive approval** decision and is not authorised by this package.
