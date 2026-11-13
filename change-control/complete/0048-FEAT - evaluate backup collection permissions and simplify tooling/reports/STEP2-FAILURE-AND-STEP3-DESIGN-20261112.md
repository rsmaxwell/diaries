# 0048-FEAT — Step 2 outcome and proposed Step 3 design (12 November 2026)

**Status:** Step 2 diagnostic completed; B1 PASS, B3 FAIL for the historic design; corrective design proposed. No Playbooks change or production deployment has yet occurred. Step 1 awaits formal acceptance; Step 3/4 remain OPEN.

## Grounded Step 2 evidence

The disposable test ran on `mango` at `2026-11-12T21:45:51Z` from the Windows Diaries checkout; its original output resides under `evidence/Step 2/clean-clone-and-ansible-20261112-214551Z.txt` (created by the user's command). Frozen revisions: controller `f6ba7fec7752f4bbfa1535958500bde9dea3ea84`, Playbooks `df68a0e3bc57bae29a76f46a58c30835126d7f20`, inventory `ebcce026723db37b9b53b76ba21903a351d48466`.

- A clean published Playbooks checkout produced `0755` on **five** synchronized directories and `0644` on **nine** include/exclude filter files, with paths/types and all nine 0047 content hashes verified. No mode restoration was used.
- Disposable Ansible run 1 returned `changed=4`, `failed=0`; run 2 returned `changed=2`, `failed=0` and `RUN2_CHANGED=2`. Two user-side directory-creation items changed on run 2 and the user archive-mode rsync changed again. The machine-side tasks converged.
- The mode conflict was verified in the final target: after both runs the user `backup` and `home` directories were `0755` (from rsync), although the preceding Ansible `file` task set them to `0750`. This is a repeatable installation-design defect, not a production failure.
- The diagnostic intentionally reports an experiment PASS for successfully exposing the failure; **B3 itself is FAIL until the corrected design is tested**.

## Access/security and disposition (proposal; not yet approved for production)

| Class | Number | Historical installed mode | Proposed Git-native mode | Access justification / required evidence |
|---|---:|---|---|---|
| User synchronized directories (`backup`, `backup/home`) | 2 | `0750` | `0755` | Only the backup account and installer need access. `/home/richard` remains `0750`; test other-user denial and no alternate access route before approval |
| Machine synchronized directories (`backup-machine`, `home`, `remote`) | 3 | `0750` | `0755` | Root backup reader and installer only; `/root` remains `0700`, with negative unprivileged access test |
| User filter files | 3 | `0664` | `0644` | rsync reads filters; no required group writer found; owner remains writable |
| Root-machine filter files | 6 | `0664` | `0644` | Root rsync reads filters; no required group writer found; owner remains writable |
| User cron/log and templated launchers | out of 14 | `0750` / `0744` | UNCHANGED | Not copied from Git `files/` directories; preserve existing Ansible task controls |
| Machine cron/log, ownership and adjacent helpers | out of 14 | mixed | UNCHANGED | Avoid unintended broader change |

This change deliberately broadens `other` read/traverse on five *child* directories but does not change the restrictive parents. Security acceptance depends on preserving `/home/richard` (`0750`) and `/root` (`0700`), absence of alternate traversable aliases, intended process users, and the explicit negative access checks. Changing `0664` to `0644` removes group-write permission on all nine filters. This policy is not a general permission-relaxation rule for other roles or backup datasets.

## Coherent implementation proposal

1. **Revised 13 November design:** Do **not** put a `mode` in the five rsync-backed Ansible directory-creation items. The actual clean checkout (`0755`) and archive-mode rsync establish their final modes. Keep user `cron`/`log` explicit `0750` as independent restricted directories, launcher templates `0744`, and the machine directory-creation task unchanged with no `mode`. Preserve archive mode and `--omit-dir-times`, without `--chmod` or `--no-perms`. This replaces the earlier proposal to hard-code `0755` on five directories.
2. Confirm the actual source modes used for a deployment: the tested clean checkout was `0755` for five source directories and `0644` for nine filters; the current `mango` checkout was previously `0775`/`0664`. Do not silently deploy its different modes. At changeover, either use a reviewed clean checkout or perform a **one-time** source-only normalisation after inspection. Git itself records neither directory mode nor group write, so document the relevant umask and run the source-mode preflight.
3. Revise the source preflight to check the actual working-copy modes and role task policy, but keep the 0047 `source-modes.json` in place until the clean-clone convergence and security tests have passed. Remove it and the active restoration requirement only in the formally accepted changeover. Historical 0047 change-control tools and evidence remain untouched.
4. Prove the proposed task sequence against a fresh-clone source on two disposable `mango` targets: one empty and one populated with historical `0750` directory modes. Require **both** second runs to have `changed=0` and check effective directory/filter/script-related modes. Verify installed ancestry and denied unauthorized reads on `mars` without modifying it. Only then plan the single controlled production deployment, repeated run and reconciliation.

**Rollback:** freeze the real Playbooks commit immediately before deployment, preserve a 14-path installed permission and hash manifest plus ownership/ACL evidence, and restore the old revision and accepted modes if verification fails. Do not delete, snapshot, prune or transfer backup datasets during this feature.

## Operator preference recorded (13 November 2026)

Do not explicitly specify synchronized directory modes in Ansible when ordinary
checkout-and-rsync behaviour is sufficient. This is **not** authority to relax
unrelated parent, cron or log restrictions. The clean-checkout and installed
access evidence remain mandatory. No deployment has taken place.

## Applied-change status

The supplied Playbooks ZIP is a **proposal to apply and test**, not an execution receipt. The active `source-modes.json` deletion needs explicit manual review because ZIP overlays do not carry deletions. No code/tests were executed on `mango` at the time of authoring this report.
