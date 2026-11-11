# 0045 Step 2 — External legacy entry-point audit

**State:** Read-only collection tool; audit conclusions require operator review.

Run `bash "change-control/in-progress/0045-FEAT - reorganise backup and Btrfs Ansible deployment/tools/audit-0045-cross-host-callers.sh"` **from Windows Cygwin** after applying this ZIP to the authoritative Windows Diaries repository.

The wrapper checks `mango`, `mars`, `backup`, and `pluto` over SSH, runs a restricted filesystem-content scan using `sudo -n`, and writes JSON evidence and diagnostic logs under `evidence/Step 2/caller-audit-<UTC>/` in the Windows repo. It does not print matching lines, any credentials or entire configuration file contents; only filenames containing legacy launcher/playbook references.

A PASS means the accessible host filesystems were scanned successfully, **not** that all external callers are absent. It separately notes if Jenkins job files are not accessible on `pluto` (e.g. when running inside Kubernetes); inspect those jobs via Jenkins UI/API separately. It also cannot establish absence of indirect references or configuration located outside inspected directories. Read any matches and migrate callers before retiring legacy entry points. Do not delete any legacy files merely because this scan completes.

The script checks standard cron, per-user cron spool, persistent systemd unit files, `/etc/ansible` on `mango`, and conventional Jenkins job directories on `pluto`. It skips build artifacts, temporary caches and files larger than 5 MiB, reporting skipped files. Permission/SSH failures cause FAIL rather than a false no-match result. It makes no installation, retention, Btrfs or snapshot changes.
