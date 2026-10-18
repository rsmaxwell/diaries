# 0036 Gate E — compatibility-first Playbooks cleanup

Scope: Ansible-level stable aliases only. No change to deployed runtime `.env` variable names, the existing NAS credentials filename, fixed capture command lines, the rollback-compatible publisher branch, or live host vars.

Stable variables (`diaries_fixed_capture_enabled`, `diaries_host_nas_*`) default to corresponding `diaries_0036_*` values. Therefore existing `pluto` host inventory continues to select fixed capture. Later stable variable overrides may be migrated one host at a time.

**Apply:** overlay `playbooks/` onto `~/playbooks/` on mango. Do not deploy to production yet.

**Source checks on mango:**

```bash
cd ~/playbooks
python3 verification/0036-gate-e/verify-stable-aliases.py
python3 roles/diaries/tests/verify-0036-integration-safety.py
python3 roles/diaries/tests/verify-0036-fixed-direct-capture-disposable.py
python3 roles/diaries/tests/verify-production-publication-wiring.py
git diff --check
```

Review actual test output; tests may have environmental prerequisites. Before any Ansible apply, compare rendered service and `.env` for `pluto` against deployed values. **Do not run the legacy Gate C scheduler deployment playbook while its timer is active**; it explicitly refuses active timers. Do not restart timers, remove generations, or retire Snapper as part of this source patch.

No Docker builds required.
