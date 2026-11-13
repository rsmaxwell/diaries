# 0048 Step 3 — Validate Git-native modes without explicit directory settings

**Operator decision (13 November 2026):** do not hard-code `0755` for the five
synchronized backup directories merely to match historical values. The revised
Playbooks ZIP removes those mode settings. User cron and log directories remain
explicitly `0750` because they are not synchronized from Git; root-side
creation keeps its original no-mode policy. Templated launchers retain `0744`.

Apply the **Diaries** ZIP to your authoritative Windows Diaries repository and
the separate **Playbooks** ZIP to `/home/richard/ansible-controller/playbooks`
on `mango` using Beyond Compare 4. The ZIPs contain complete replacement files:
they work whether the earlier explicit-`0755` proposal was applied or not.
Preserve other local changes; review the diff before copying.

Run `tests/verify-0048-step3-proposed-convergence.sh` by streaming it from a
Windows Cygwin terminal over SSH to `mango`, recording all output under
`evidence/Step 3/`. It uses the candidate **real task definitions** from the
Playbooks checkout and **source content from a new Git clone** pinned to the
controller's current Playbooks submodule revision. A `umask 022` checkout is
expected to yield synchronized dirs `0755` and nine filters `0644`.

The script tests two disposable scenarios on `mango`:

- Fresh target: two Ansible directory-creation + archive-mode rsync runs;
  the second must report zero changes.
- Existing `0750` target: two identical runs against an isolated simulation
  of the previously installed directory modes; again, the second must have
  zero changes. This is **not** a clone of the real production directory.

It also reads existing `/home/richard` and `/root` protections on `mars`
through the known-good `mango -> mars` SSH path and tests both allowed and
disallowed file reads. There are **no writes to mars**.

**Important:** The test prints `WORKING_COPY_MODE_DIFFERENCES`; any differences
must be reconciled before a production deployment, because rsync copies the
working tree's actual modes, not Git's abstract defaults. The existing `mango`
checkout was `0775`/`0664` in Step 1; the clean clone was `0755`/`0644`.
Do not automatically run `chmod` or deploy just because this disposable test
passes. The 0047 `source-modes.json` and historical evidence remain untouched
until formal retirement acceptance.

Expected: `FRESH_RUN2_CHANGED=0`, `EXISTING-0750_RUN2_CHANGED=0`, verified modes
and parent/access PASS. If any check fails, do not deploy; retain the evidence
and correct the candidate design.
