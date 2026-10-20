# Step 4 — Snapper CSV compatibility correction (19 October 2026)

On mars, the read-only `legacy-plan` failed closed with:

`ERROR: unexpected Snapper CSV columns: ['active', 'cleanup', 'config', 'date', 'default', 'description', 'number', 'pre-number', 'subvolume', 'type', 'used-space', 'user', 'userdata']`

Snapper provides `number` in its installed CSV output, whereas the initial parser required `#`. The inventory parser now supports exactly one of `number` and `#`, preserving required type/date/cleanup validation and rejecting ambiguous headers. This does not change native `prune`, `run`, or scheduled operations; `legacy-plan` remains read-only.

## Regression evidence

Local synthetic tests: modern empty + numbered inventories PASS; historical empty + numbered inventories PASS; ambiguous dual ID headers rejected PASS. Empty-config regression and original Step 4 plan regression also pass locally. These tests do not establish live host acceptance.

## Deployment boundary

Only the Python manager source belongs in Playbooks on mango. The regression and Cygwin launcher stay in the Diaries 0037-FEAT tests directory. After copying source to mango, rerun Cygwin regression, then deploy only the executable to mars with Ansible `backup=yes`. Re-run `legacy-plan` and inspect results before Step 4 closure. No deletion is authorised by this patch.
