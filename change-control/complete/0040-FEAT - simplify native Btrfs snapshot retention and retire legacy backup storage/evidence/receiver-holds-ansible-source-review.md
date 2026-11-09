# 0040-FEAT receiver checkpoint hold configuration

Source package based on playbook-sources-20261023-170120.zip. Historical UUIDs independently verified on backup, October 23, 2026.

Scope: add root-controlled hold file under /etc, initialise when absent, verify existing mandatory identities and receiver receipts, add required true to manager config. No pruning enablement or endpoint sudoers changes.

Local regression: 8/8 passed (Python unittest, PyYAML). No Ansible check, deployment, live manager validation, or destructive exercise performed.

Important: first deployment with absent hold file must be reviewed in Ansible --check --diff; subsequent source and deployed manager should be verified before any executor work.
