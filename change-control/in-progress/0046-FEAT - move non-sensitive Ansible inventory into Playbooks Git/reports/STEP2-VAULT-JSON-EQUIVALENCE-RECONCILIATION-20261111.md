# Step 2 — Prepared inventory JSON Vault representation reconciliation (2026-11-11)

**State:** Verification prepared; Step 2 remains OPEN until live check is accepted.

## Observed evidence

- Read-only structural diagnostic: 44 original and 44 prepared files, exactly 12 changed files at the frozen credential locations.
- All 14 newly encrypted credential values decrypted exactly to the original YAML scalar strings.
- The initial `ansible-inventory --list` JSON comparison reported eight `TYPE_DIFF` results and no other categories.
- All eight mismatches were on active hosts at the freshly protected values. The six other protected values were in files whose hosts were absent from that inventory graph.

## Diagnosis

Ansible serialises a `!vault`-tagged value in inventory JSON as an object containing `__ansible_vault` rather than the plain value (even when a Vault password is provided). Comparing this JSON representation naively with the original ordinary scalar produces type-only differences. This representation is supported by Ansible's inventory JSON serialisation. The earlier strict file-level roundtrip established that all 14 original plaintexts survived encryption unchanged, but did not canonicalise the JSON representation.

## Acceptance correction

`tools/verify-0046-prepared-inventory.py` performs **read-only** comparison of the existing `/etc/ansible` source and `/home/richard/ansible-controller/inventory` prepared copy. It:

1. Requires the same set of 44 files and exactly the 12 anticipated changed files.
2. Compares the full YAML node structures of the changed files, decrypting only the 14 preapproved `!vault` scalars in memory. All other mappings, sequences, scalar tags and values must match exactly.
3. Resolves both inventories with the same playbook directory and Vault password file, decrypts `__ansible_vault` wrappers only at the frozen protected host-variable locations and compares everything else strictly.
4. Requires exactly eight normalised active host variables and rejects unexpected changes, missing fields, malformed wrappers or decrypt failures.
5. Never prints variable values, Vault content or the password, and never modifies either inventory or invokes Git.

The earlier preparation tool's raw inventory JSON equality guard produced a **false negative** because it did not account for Ansible's Vault JSON representation. The prepared destination should be **retained**, not overwritten or re-encrypted. The new verifier supersedes that one failed comparison for 0046 acceptance, without treating the previous run as a successful acceptance check.

## Follow-up gate

If live verification passes, proceed to the private-repository security and assembly work. Keep the private inventory uncommitted until repository visibility is verified and staged content has been audited. Preserve `/etc/ansible`, the original Playbooks checkout, and `~/.vault_pass.txt` during this stage.
