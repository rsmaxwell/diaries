# 0046 Step 1 — Inventory security triage (11 November 2026)

**State: OPEN — REVIEW REQUIRED.** The 20:13 UTC read-only classifier operated normally and detected 33 **candidate** plaintext secret fields in the 44-file inventory. This is not proof of 33 exposed credentials.

## Observed evidence

- One whole-file Vault (`host_vars/pluto/vault.yaml`) decrypted in the initial audit; four additional files contain 16 inline Vault scalars; no malformed inline Vault tags or audit errors.
- 33 candidate locations were reported by relative pathname and line number only. Candidate fields arise in bootstrap and application host variables, especially `host_vars/pluto/diaries.yaml`.
- Actual inventory file hashes and effective-inventory fingerprint were captured in `evidence/Step 1/inventory-baseline-20261111-193110Z.txt`.
- Before migration, identify any actual plaintext credentials. Encrypted Vault material may be version-controlled only in the new **private** inventory repo. Vault password and plaintext credentials remain outside all Git repositories.

## Next acceptance work

Use `tools/classify-0046-inventory-candidates.py` on `mango` over SSH stdin. It emits only candidate file, line and **syntactic category**; it does not print values or keys. It specifically distinguishes simple whole-expression variable references from literal values, complex templates, path references and credential-bearing URLs. All categories are heuristic; a reference may ultimately point to a secret, and non-candidate fields may still contain secrets.

Human verification of residual candidates must occur locally in the controlled `mango` session without collecting plaintext values into Diaries evidence. If a genuine plaintext credential is found, arrange encryption within the trusted environment and validate equivalent Ansible resolution. Do not stage or publish the inventory until source classification, destination privacy and security review are accepted.

**No infrastructure change or private repo creation is claimed.** Step 1 remains OPEN until accepted baseline/security evidence is complete. No backup restore, manual prune, replication or redundant end-to-end deployment is required for this triage.
