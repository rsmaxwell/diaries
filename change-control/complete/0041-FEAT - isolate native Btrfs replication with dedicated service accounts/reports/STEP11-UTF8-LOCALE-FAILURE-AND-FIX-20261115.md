# 0041-FEAT — Step 11 UTF-8 locale correction (15 November 2026)

## Actual failed run

Evidence: `evidence/Step 11/service-execute-20261115-151430Z.txt`.

* Source checksum and installed-program checks passed.
* Both agreed-parent records matched and dedicated read-only status passed.
* Ansible stopped at the **check-mode preview**, with `ERROR: Ansible requires the locale encoding to be UTF-8; Detected None.`
* **No live Ansible cutover was attempted**, and no transfer, timer change, or agreed-parent edit was requested. Step 11 remains OPEN.

## Root cause and correction

The original Step 11 remote script explicitly exported `LC_ALL=C`, a non-UTF-8 POSIX locale. In contrast with the earlier Ansible launchers, Step 11 retained this value when invoking `ansible-playbook`.

The corrected script no longer exports `LC_ALL=C`. After sourcing the existing `/home/richard/ansible-controller/enter.sh`, it selects an actually supported UTF-8 locale (`C.UTF-8`, `C.utf8`, `en_GB.UTF-8`, or `en_US.UTF-8`), validates its C locale encoding with Python, and logs the selected `LANG`, `LC_ALL`, and codeset. If no UTF-8 locale is available, it refuses to continue **before Ansible**. Selection is applied equally to the preview, cutover and rollback branches.

No Playbooks source, service-account permission, receiver gate, SSH key, privileged helper, or production Btrfs state changes are required.

## Verification and continuation

The new remote script passes `bash -n`; its locale-selection routine was exercised in a non-production sandbox with an initial C locale, confirming that it chooses UTF-8. The Cygwin launcher is unchanged and still captures a new timestamped Step 11 evidence log.

Apply this patch ZIP to the **Windows Diaries repository** with Beyond Compare, preserving the earlier Step 11 files and other local changes. Rerun `--execute` through the existing Cygwin launcher. It repeats all existing-source and live preconditions, performs the Ansible check-mode preview first, and only then installs the Ansible-managed dedicated service. It does not invoke Btrfs replication. On any failure, inspect the log and loaded unit before retrying.

**Acceptance still outstanding:** successful live Step 11 cutover and the subsequent scheduled 03:30 replication journal plus health verification. No step is marked CLOSED by this patch alone.
