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
