# 0049 — Evidence index

**Status:** live technical acceptance passed on 16 November 2026. This directory contains actual terminal logs, source regressions and hash manifests, not placeholder evidence. Git finalisation and publication have passed. Formal operator approval was granted on 16 November 2026; final relocation and closure publication are recorded by the closure command.

- `source-regression/`: consolidated source tests and regressions (11 scripts passed in implementation bundle).
- `Step 3/`: source and Ansible check-mode on both hosts.
- `Step 4/`: receiver-first deployment and read-back; sender deployment; live sender push; final receiver UUID/readonly/retention read-back; final two-host Ansible idempotence.
- `Step 4/FINAL-LOG-SHA256-20261116.md`: original two final read-back log hashes.
- `Step 4/WINDOWS-DIARIES-PUBLICATION-20261116.txt` and `Step 4/WINDOWS-DIARIES-PUBLICATION-LOG-SHA256-20261116.md`: final Diaries GitHub publication receipt and checksum; other Playbooks/controller publication evidence is also under Step 4.

All raw evidence belongs to this Diaries parent feature directory. Historical evidence should not be edited to retroactively change old command names. All four steps were marked CLOSED after the owner explicitly accepted the verified technical, publication, revision and rollback-readiness evidence on 16 November 2026. Historical source and terminal logs remain unchanged.
