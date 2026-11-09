# 0040-FEAT — Step 04 evidence and closure

**Status: CLOSED — 24 October 2026 (accelerated technical acceptance).**

## Scope and acceptance

Step 04 implements configurable snapshot-source requirements and creation lists in the shared Playbooks snapshot manager. The default remains the original paired `root` and `@data` contract. Existing paired history remains recognised when an eventual `@data`-only configuration is selected. Deployment of the compatible manager to `mars` was an additional, controlled action beyond the original source-only scope.

## Recorded evidence

| Evidence | Result |
|---|---|
| `note(20261024-213017).txt` | Migration/default/legacy compatibility tests PASS; Step 3 privileged suite PASS; diff check clean |
| `note(20261024-213622).txt` | Targeted Ansible dry run exposed unsafe proposed receiver configuration overwrite on `backup`; deployment blocked |
| `note(20261024-214041).txt` | `mars` snapshot manager and config deployed by `snapshots.yaml --limit mars --tags snapshots`; changed=2, failures=0; Diaries verification valid |
| `note(20261024-214311).txt` | `mars` status: 61 complete pairs, zero incomplete; both source lists `['root','@data']`; Ansible check-mode idempotency changed=0 |
| `note(20261024-214855).txt` | Receiver guard static regression PASS, Ansible syntax PASS, `mars` check-mode idempotency changed=0 |
| `note(20261024-214956).txt` | `backup` generic role intentionally refused before any mutating task; changed=0 (expected failure) |
| `note(20261024-215639).txt` | Source plus regression files committed as Playbooks revision **`b51a5b0`**; clean working tree |

The Step 04 implementation report was separately prepared in `reports/STEP04-SOURCE-IMPLEMENTATION.md`; the later acceptance report was supplied as `reports/STEP04-SOURCE-IMPLEMENTATION.md` in the final-evidence ZIP. The terminal logs above are operator-provided evidence; this index does not claim those log files have been archived into this ZIP.

## Residual risk and controls

- `mars` production is still paired `root`/`@data`; **no `@data`-only cutover** was authorised or performed.
- Generic `snapshots.yaml` execution on `backup` is rejected; receiver configuration is managed by the dedicated native receiver path.
- `backup` receiver pruning remains disabled on the last verified production configuration. No receiver deletion was authorised.
- Full cross-host disposable sender/receiver deletion rehearsal was waived on the accelerated path; do not claim PASS.
- `mars` showed 218 stale qgroups (371 total), tracked separately.

**Decision:** Step 04 source, regression, controlled `mars` deployment and receiver guard acceptance are CLOSED. Subsequent retention-plan and migration/cutover steps remain independent, open gates.
