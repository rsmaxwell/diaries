# 0045-FEAT — Step 3 final deployment and equivalence acceptance (11 November 2026)

**Decision: CLOSED — source refactor deployed and installation-equivalent; second normal apply zero-change.**

## Revision, baseline and evidence

- Deployed Playbooks: `1939a0984934062d03c01de826ad4a5a87d3338d` (`main`, clean, published).
- Approved rollback source: `7dfa93fef6d975aa82f5f4cfdf54497b106e7645`; rollback *not* executed or needed.
- Authoritative pre-refactor baseline: `evidence/Step 1/baseline-20261111-111819Z/` (schema `0045-static-installed-v2`).
- First real apply: `evidence/Step 3/deployment-20261111-130143Z/` (`note(20261111-130525).txt`). The standard collector found five differences in `mars` one-shot systemd ExecStart digests, and none on `backup`. No Ansible changed tasks.
- Read-only reconciliation `note(20261111-131849).txt`: nine focused comparison tests PASS; five differences attributed to systemd execution-history digests only (actual unit files, drop-ins, stable service properties, permissions unchanged); all five units loaded with no pending daemon reload; Docker signing key unchanged.
- Second real apply: `evidence/Step 3/deployment-20261111-132219Z/`; operator terminal `note(20261111-132632).txt`. The second-run wrapper still prints its generic “APPLY 1”/“initial apply” labels, but the directory timestamp and independent invocation establish this was the second deployment.

## Second normal application: Ansible recaps

| Playbook | Host | OK | Changed | Failed | Unreachable | Skipped |
|---|---|---:|---:|---:|---:|---:|
| `backup-collection.yaml` | `mars` | 61 | **0** | **0** | **0** | 12 |
| `btrfs-replication.yaml` | `mars` | 15 | **0** | **0** | **0** | 27 |
| `btrfs-replication.yaml` | `backup` | 26 | **0** | **0** | **0** | 16 |

The second run's exact static-metadata comparator reported **PASS for both `mars` and `backup`** against the accepted 11:18 UTC baseline. The same five `mars` ExecStart runtime-only digests were reconciled, not ignored generically. Any change in a managed unit file, drop-in, service user or timer policy remains a hard failure.

The Docker apt signing key checksum remained `1500c1f56fa9e26b9b8f42452a553675796ade0807cdce11975eb98170b3a570` before and after. Live `mars` snapshot manager readback showed `qgroups_stale=0`, `qgroups_under_deletion=0`, zero incomplete timestamp sets, and a valid Diaries verification marker. Existing 0039/0043 natural-scheduler correctness evidence is retained; no manual snapshot/prune/replication or full restore was performed for 0045.

## Findings and acceptance limits

- Check mode reported one *predicted* Docker signing-key task change, but both actual applications reported that task `ok`, and the signing-key checksum did not change.
- The initial five unit differences were systemd process-history data, not installation changes. Correction was focused and regression-tested rather than a blanket exclusion.
- The accepted installation comparison covers the managed assets and security/schedule fields enumerated in the Step 1 schema-v2 collector and 0045 installation map. Regular mutable snapshot datasets are checked through read-only operational health, not whole-tree hashes.
- No failed or unreachable hosts, service restart, changed managed resource, or altered backup policy appears in the second application evidence.
- Preserve original raw Ansible logs and manifests under `evidence/Step 3/`, and review logs for sensitive metadata before public Git publication; the terminal output includes encoded checkpoint receipts.

**Step 3 technical gate: ACCEPTED.** The remaining Step 4 gate is repository evidence review/publication and formal feature closure, not another Ansible application.
