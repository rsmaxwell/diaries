# 0046 Step 1 — Literal secret assessment (2026-11-11)

State: REVIEW COMPLETE FOR IDENTIFIED CANDIDATES; repository migration NOT STARTED.

The source classifier reported 44 files, one whole-file Vault, 16 inline Vault values,
18 simple references, and 15 literal candidates. A read-only key-name review found:

- 12 password-named plaintext literals across bootstrap and application host_vars.
- 2 Cloudflare tunnel token-named plaintext literals.
- 1 Jenkins credential ID (`jenkins_github_ssh_credential_id`), an identifier rather
  than a secret value; this stays unchanged subject to any later manual review.

Security decision: conservatively Vault-encrypt all 14 credential-named scalars in the
new private inventory copy, leaving the existing `/etc/ansible` reference unchanged.
The migration preparation tool refuses any line/key drift, missing files, unexpected
file count, destination overwrite, or wrong Vault discovery. It does not publish to Git.
The resulting effective Ansible inventory must equal the baseline; any difference is a
review blocker. No secret values, plaintext, ciphertext, or decrypted inventory dumps
are recorded in change-control evidence.

The heuristic review is not a proof that there are no other secrets; conduct a final
private repository staged-content check and verify remote privacy before any push.

Pending: run the protected-copy preparation; inspect any semantic mismatch; configure
private parent/inventory repositories and GitHub access; estate-wide installation/caller
parity; reversible cutover and formal closure.
