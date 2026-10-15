# 0035-FEAT Step 4 — History locator on `mars` and `pluto`

**Status: CLOSED — 2026-10-15 (scoped live acceptance, recorded verification gaps).**

## Source regression and `mars` compatibility

Operator ran `python3 roles/snapshots/tests/verify-diaries-backup-history.py` on `mango`: the six reported checks passed, including duplicated backup IDs, conflicting manifest identities, unsafe symlink escape, ext4 fixed publication and invalid publication rejection.

`ansible mars -b -m command -a '/usr/local/sbin/diaries-backup-history list --all'` returned `rc=0`. It reported verified snapshot occurrences for two production backup IDs, `20261009-154847Z` and `20261015-003023Z`. The latter appears in timestamped snapshots beginning `20261015-030004Z`. The standard Ansible ad-hoc display says `CHANGED`, but this is the command module's reporting convention, **not evidence of filesystem modification**.

## `pluto` live deployment

- `verification/0035-step4/install-pluto-history.yaml --ask-vault-pass --check --diff`: recap `ok=4 changed=3 failed=0`; expected *predicted* installation changes; live history query skipped in check mode.
- Same playbook applied normally: recap `ok=5 changed=3 failed=0`; installed the read-only locator and independent schema-2 verifier, creating its parent directory.
- Post-install list reported `production 20261015-003023Z live live 1 verified`. `live` is a fixed ext4 publication, **not a Btrfs snapshot**. Identity agrees with the earlier Step 1 production publication capture.
- No snapshot/prune role, receiver transfer or scheduler change was invoked by this installation playbook.

Complete operator transcript: `step4-mango-verification-20261015-090136.txt` in this folder.

## Acceptance and limitations

**Accepted:** existing `mars` history behaviour remains usable, ext4 `pluto` sees its verified current publication without fabricated snapshot history, and the narrow install playbook succeeds.

**Not demonstrated in the supplied live transcript:** separate production `show`, `path` and `verify` commands on `pluto`, `mars` compact `list` and locator restore path, and a second no-change (`changed=0`) run proving installation idempotency. Previous open-gate wording requested these checks; closure here is a **documented scoped acceptance/deviation**, not a claim they were performed. They remain recommended follow-up verification and may be required before depending on `path` or `verify` for a live restore.

Optional follow-up on `mango`:

```bash
ansible-playbook verification/0035-step4/install-pluto-history.yaml --ask-vault-pass
# Expected on an unchanged target: changed=0
```

Run `show`, `path`, and `verify` using the deployed locator's documented published-root arguments; avoid printing or interpreting any backup contents as changed. Do not perform a restore as part of this step.

**Scope:** documentation and read-only history installation. No permission to prune historical numeric Snapper snapshots, alter receiver retention, change timers, run restores or delete the legacy `/@data/backup` data. No Diaries Docker image build required.
