# 0046 — Protected inventory preparation

This feature-specific tool runs on mango using stdin from the Windows Cygwin terminal.
It copies the existing 44 inventory files into the proposed private inventory submodule
working directory without copying the 14 identified plaintext secrets unencrypted.
The old `/etc/ansible` inventory and public Playbooks checkout are not changed.

Run self-test before use. The tool fails closed if paths/lines drift, or if old/new
`ansible-inventory --list` data differ. A failure does **not** mean the destination is
safe to commit. The output directory is deliberately left for secure inspection and
must not be blindly overwritten or uploaded. No Git commands are executed.

The full inventory comparison is stronger than a file-hash comparison, and may detect
path-dependent variables after moving inventory. Such differences require analysis,
not automatic normalization of values.

Do not commit any sensitive execution log (including `ansible-inventory --list` raw
output). Secret/ciphertext values must not be displayed. The Vault password remains
`/home/richard/.vault_pass.txt` on mango, outside all Git repositories.
