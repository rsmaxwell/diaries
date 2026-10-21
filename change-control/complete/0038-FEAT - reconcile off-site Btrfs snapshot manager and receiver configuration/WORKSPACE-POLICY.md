# Mandatory feature workspace and target hygiene

The authoritative feature workspace is `diaries/change-control/in-progress/0038-FEAT - reconcile off-site Btrfs snapshot manager and receiver configuration/` until closure, then move it wholesale to `complete/`.

| Material | Location |
| --- | --- |
| Experimental code, ad-hoc SSH capture wrappers | `tools/` |
| Synthetic fixtures, ad-hoc acceptance tests | `tests/` |
| Analysis, interpreted inventories, human-readable dry-run reviews | `reports/` |
| Raw command logs, approval records, screenshots/text captures | `evidence/Step NN/` |
| Generated/transient inputs, extracted intermediate files | `scratch/` (do not commit bulky/sensitive material) |
| Approved, genuinely reusable production changes | `playbooks/roles/...` and record in `PROMOTION-MANIFEST.md` |

**Keep the installed production trees clean.** Never copy feature diagnostics, experiments or evidence permanently into `/usr/local/sbin`, `/etc`, `/root/scripts`, `~/scripts`, or Playbooks role directories. Run existing commands in SSH terminals, or from Cygwin with `ssh backup '...'`/`ssh mango '...'` and redirect output to the feature workspace. If a host-side transient file is unavoidable, use a restrictive bounded location, record why, and clean it before closure. Rollback copies are a deliberate **exception**: preserve only those necessary to restore previous installed state, record precise location/ownership/retention, and never delete before acceptance.

Maintain local working evidence away from commits when it contains credentials, machine secrets, private paths or excessive output; review and redact before promotion. No snapshot/receipt/replication-state modifications are authorised by this policy.
