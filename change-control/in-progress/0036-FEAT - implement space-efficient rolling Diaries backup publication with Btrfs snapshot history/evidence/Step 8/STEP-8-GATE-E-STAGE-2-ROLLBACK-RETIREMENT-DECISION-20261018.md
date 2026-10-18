> **Final disposition (2026-10-18): Gate E, Step 8 and 0036-FEAT CLOSED — PASS.** Refer to `evidence/Step 8/STEP-8-GATE-E-FINAL-CLOSURE-20261018.md` in the feature root. Earlier pending language is historical. No permanent deletion authorised.

# 0036-FEAT Step 8 Gate E — Stage 2 final rollback-retirement decision

**Date:** 2026-10-18  
**Status:** PROPOSED / PENDING EXPLICIT OPERATOR APPROVAL. NOT EXECUTED. Gate E and 0036 remain OPEN.

## Accepted evidence

- Gates A–D closed; the 17 and 18 October unattended production backup cycles passed, including off-site incremental receipts.
- Compatibility-first Playbooks deployment passed with identical `pluto` systemd service candidate, validated fixed-capture commands, and unchanged `mars` guarded pull.
- Stage 1 postcheck reports all six non-alias generation directories in reversible hold (three each on `pluto` and `mars`); fixed repositories and active timers preserved.
- Legacy source scans found no direct deployed code reference to a specific historical generation ID, but general legacy publisher compatibility remains present.
- All four `mars` historical generation manifests matched retained Btrfs snapshot contents at collection time. This is not proof of every file's completeness or indefinite retention.

## Final rollback assets requiring a deliberate decision

| Host | Rollback alias | Protected generation |
|---|---|---|
| `pluto` | `/home/richard/projects/diaries/data/diaries-backup.pre-0036-rollback` | `/home/richard/projects/diaries/data/.diaries-backup-generations/20261016-003019Z` |
| `mars` | `/media/usb/@data/backup/pluto/diaries-backup.pre-0036-rollback` | `/media/usb/@data/backup/pluto/.diaries-backup-generations/20261016-003019Z` |

**Recommended decision:** Approve the *end of operational reliance* on pre-0036 rollback aliases only after a final read-only preflight and explicit operator agreement. Preserve both generation directories (and the six Stage 1 held generations) during a reversible retirement stage. Do **not** approve permanent deletion as part of this decision.

Do not remove an alias yet: doing so eliminates a convenient rollback pointer. When approved, a separate implementation must atomically retire the symlink **without following it**, retain its full original target and rollback instructions, and verify that fixed repositories, all five timers, snapshot protection and off-site receipts are intact. Any relocation of the protected target must be separately guarded and approved. If any check fails, do not proceed.

## Stage 2 preflight

From `mango`:

```bash
cd ~/playbooks
python3 -m py_compile verification/0036-gate-e/assess-final-rollback.py
set -o pipefail
python3 verification/0036-gate-e/assess-final-rollback.py | tee ~/0036-gate-e-stage2-readonly.txt
```

This is read-only, uses SSH to inspect `pluto` and `mars`, checks schema-2 identity, protected aliases, Stage 1 held-generation counts and relevant service/timer status. It does **not** test Btrfs subvolume type or approve deletion. Collect the output before requesting operator approval for a separate reversible change.

## Explicit exclusions

- No permanent deletion, `rm -rf`, Btrfs subvolume deletion, or Snapper cleanup.
- No modification to production fixed repositories, NAS mount, runtime configuration, timer schedules, Btrfs receipt lineages or checkpoint holds.
- Do not remove legacy publisher code until all historical restore and compatibility consumers have been reconciled.
- Do not call Gate E, Step 8 or 0036 formally closed at this stage.
