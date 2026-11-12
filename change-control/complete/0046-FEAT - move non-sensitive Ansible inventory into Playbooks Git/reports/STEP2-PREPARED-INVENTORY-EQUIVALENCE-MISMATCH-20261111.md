# 0046 — Step 2: protected inventory preparation mismatch, diagnostic pending

Date: 2026-11-11

## Observed result

The protected-inventory preparation self-test passed. The preflight confirmed the
expected clean public Playbooks revision and absence of a prepared inventory tree.
The tool created `/home/richard/ansible-controller/inventory` on `mango`, but the
full `ansible-inventory --list` JSON comparison reported a difference. The script
correctly declined acceptance and left the new tree uncommitted. No old inventory,
Playbooks checkout or remote managed host was modified.

## Next action

Run `tools/diagnose-0046-inventory-equivalence.py` read-only against both inventory
trees on `mango`. It checks file-change scope, independently Vault-decrypts all 14
transformed scalar values and compares them in memory with original values, and
lists only differing JSON key paths and difference categories. It prints no values,
ciphertext, hashes of secrets or decrypted secrets.

Do not delete, overwrite, commit or publish the prepared inventory until the cause
has been identified and the authoritative installed-equivalence contract satisfied.
The original `/etc/ansible` remains the active inventory. Step 2 remains OPEN.
