# 0049 — Published revision and deployment record (16 November 2026)

**Record status:** FINAL GIT PUBLICATION VERIFIED; **feature closure still requires explicit operator acceptance**. This report records actual revisions and observed deployment state; it does not claim a new rollback test.

## Published repository revisions

| Repository | Remote (as verified) | Published `main` revision | Verification |
| --- | --- | --- | --- |
| Playbooks | `git@github.com:rsmaxwell/playbooks.git` | `a2508ad61f479c1b2bc20cb39896006c1f2906e1` | `git push` and `git ls-remote` exact SHA match (mango) |
| Ansible-controller (private) | `git@github.com:rsmaxwell/ansible-controller.git` | `a81eafdf1fccf6bcd7d9d1b3dfa77143872682e8` | `git push` and `git ls-remote` exact SHA match (mango) |
| Diaries parent | `git@github.com:rsmaxwell/diaries.git` | `34be53fe219dbe773b516596e3d36fa5b29801bb` | `git push` and `git ls-remote` exact SHA match (Windows Cygwin) |

The three repositories were published in dependency order: Playbooks, Ansible-controller, Diaries. The pushes included earlier accepted **0041** commits:

- Playbooks `0904bc7` (0041), followed by `a2508ad` (0049).
- Ansible-controller `e325227` (0041), followed by `a81eafd` (0049).
- Diaries `b3bb0b5` (0041), `f48f09d` (0049 implementation/evidence), `34be53f` (0049 publication evidence).

The controller's published commit pins Playbooks `a2508ad61f479c1b2bc20cb39896006c1f2906e1`. Its private inventory gitlink remains `ebcce026723db37b9b53b76ba21903a351d48466`. Diaries application gitlinks are unchanged in the publication receipt:

- `diaries-client`: `e45ae170017fdf4974f642f654d7f709269af711`
- `diaries-responder`: `bd65d08435c0f5d240337cd6479cb41befe4d8c1`
- `diaries-web`: `cc147426e93ee6952558b65147e444d38316b3ce`

The baseline Playbooks revision before the 0049 source changes was `0904bc7ebe801e391a3aa4dc59bbc9ccc7dfa532` (post-0041). Do not infer the full parent 0041 SHA from abbreviated Git-log output; read it from the repository if a rollback requires it.

## Accepted installed state (dated observation, not live status now)

- `mars`: `btrfs-push.timer` active/enabled; former `btrfs-native-push.timer` removed; service executes under `btrfs-send` through the accepted 0041 sudo wrapper; next push 03:30 UTC.
- `backup`: `btrfs-receiver-prune.timer` active/enabled; former `btrfs-receiver-simple-prune.timer` removed; receiver service bounded by `--max-delete 10`; next prune 04:15 UTC.
- First post-0049 incremental push completed 16 November 2026 at 15:56:28 UTC. Both ends' agreed parent advanced from `20261116-030016Z` to `20261116-150008Z`, with received UUID `818b8956-76de-564f-8351-37cc89037d14` and `readonly` flag confirmed on `backup`.
- Receiver final read-back: 41 retained sets, 2 independent holds, 27 historical receipts, 0 proposed prune deletions; qgroups `ok` with 0 stale.
- Source and receiver `btrfs-backup-status`: `HEALTHY`; Diaries-only status: `HEALTHY`; Ansible final reapply: `mars changed=0 failed=0`; `backup changed=0 failed=0`.
- `mars` previously reported 2 stale qgroups while overall qgroups_status was `ok`; separate 0039-DEF. An independent `last verified transfer` receipt was unavailable and explicitly reported `unknown`, rather than inferred from the successful push.

## Rollback readiness and immutable state

The source-level post-0041, pre-0049 Playbooks revision `0904bc7ebe801e391a3aa4dc59bbc9ccc7dfa532` is a **reference** for planning rollback, not an executable rollback instruction. Any rollback must retain current 0041 dedicated users, keys, forced SSH dispatcher, sudo restrictions, existing data, historical receipts, and unchanged `.simple-agreed-parent.json` records. Disable replacement timers before enabling old ones, check both services inactive, and deploy a matched runtime/wrapper/unit set on both endpoints. Refer to `reports/ROLLBACK-READINESS-20261116.md` for the conditional procedure. No rollback was executed or required. No destructive prune or restore was run under 0049.

## Provenance

- `evidence/Step 4/MANGO-PLAYBOOKS-CONTROLLER-PUBLICATION-20261116.txt` — both pushes, their remote SHA readback and dependency order.
- `evidence/Step 4/WINDOWS-DIARIES-PUBLICATION-20261116.txt` — Diaries push, full SHA readback, application gitlinks and clean final status.
- `evidence/Step 4/MANGO-PUBLICATION-AUDIT-20261116.txt` and `evidence/Step 4/WINDOWS-PUBLICATION-AUDIT-20261116.txt` — prior remote-history and gitlink audits.
- `reports/FINAL-TECHNICAL-ACCEPTANCE-20261116.md` — tested runtime functionality and acceptance limits.
- `evidence/Step 4/WINDOWS-DIARIES-PUBLICATION-LOG-SHA256-20261116.md` — raw final publication log checksum.

**Formal closure gate:** await explicit operator approval; then move the entire 0049 directory from `change-control/in-progress/` to `change-control/complete/`, reconcile the living status documents to CLOSED and commit/publish the relocation from the Windows Diaries parent. That final closure commit is not yet included in the published Diaries SHA above.
