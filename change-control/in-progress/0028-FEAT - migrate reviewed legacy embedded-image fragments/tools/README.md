# 0028 one-off tools and templates

Keep feature-specific execution helpers here. Maintained Java migration code,
Gradle integration and permanent tests belong in `diaries-responder`, not here.

`templates/0028-dispositions.template.csv` is a **header-only** reviewed
Fragment disposition manifest. `templates/0028-image-decisions.template.csv`
is a **header-only** occurrence allocation manifest. They contain no real
Fragment rows or approvals. Make versioned, reviewed copies under controlled
feature evidence only after current candidate inventories have been frozen.

Do **not** run `apply` or install any production executable from this planning
package: the `migration0028ReviewedFragments` task is not yet implemented.
When later writing scripts for Windows Cygwin or mango SSH, label the intended
host and working directory, preserve interactive shells (no bare `set -e`),
and check exit codes. Run normal Ansible on mango only if deployment changes
actually become necessary. Never place temporary migration scripts in
permanent Playbooks roles.

## 0051 compatible offline reviewer (v2)

`step4_0051_compatibility_review.py` is read-only; it does not implement or
authorise production migration. To generate a *private, unapproved* review
from the original frozen inventory (use the exact reviewed input versions):

```text
python3 tools/step4_0051_compatibility_review.py prepare
  --proposals <private/0028-proposed-review.PRIVATE.csv>
  --frozen <private/20261118T093606Z>
  --prior-v1-draft <private/20261120-export-15-review-check/0028-human-review.DRAFT.PRIVATE.json>
  --output <new-private-evidence-directory>
```

Use `check` with `--decisions <exported-v2-private.json>` and optionally
`--current-snapshot <new-readonly-current-schema-snapshot.PRIVATE.csv>`.
The checker never produces an apply authorisation, even with no blockers.
Keep the original 0028 v1 portal and all exports untouched.

## Resume after 0051 formal closure (21 November 2026)

Run from the **Windows Cygwin Diaries repo root**, using the newer Windows
source checkout rather than assuming `mango` has been synchronized:

```bash
feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
bash "$feature/tools/resume-step1-post0051-readonly.sh"
```

The wrapper verifies the historic source hashes, runs the existing synthetic
unit tests, collects new read-only PostgreSQL evidence via `ssh pluto`, and
prepares/checks a **PRIVATE, UNAPPROVED v2** review using the frozen
18 November inputs and export (15) as nonbinding hints. Production operations
are exclusively `docker compose ps` and a PostgreSQL `COPY (SELECT ...)
TO STDOUT` with transaction read-only enforced. It never invokes apply.

The wrapper creates timestamped outputs **only** in ignored
`evidence/Step 1/private/`. Do not copy the raw HTML, v2 review portal,
review decisions or current-schema CSV to Git, chat, Jenkins or `pluto`.
Fresh Image Files-root verification and manually approved decisions still
remain outstanding after successful collection.
