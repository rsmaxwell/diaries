# 0036-FEAT Gate E — separate source audits

Replaces the previous two-root `audit-source-dependencies.sh` workflow. Run each audit **locally** in its own repository; neither machine needs access to the other repository. Both are read-only and emit the same six dependency keyword sections.

## `mango` — Playbooks (Bash)

```bash
cd ~/playbooks
bash verification/0036-gate-e/audit-playbooks-dependencies.sh \
  ~/playbooks > ~/0036-gate-e-playbooks-source-audit.txt
```

## Windows — Diaries (PowerShell)

From the `diaries` working directory:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\audit-0036-gate-e-source.ps1 > "$env:USERPROFILE\0036-gate-e-diaries-source-audit.txt"
```

Send both `.txt` files for combined dependency reconciliation. The original `playbooks/verification/0036-gate-e/audit-source-dependencies.sh` may remain in Git but **should not be used** for this split-host workflow. Delete it from source control at a later review if desired. No production deployments or snapshot deletions are included.
