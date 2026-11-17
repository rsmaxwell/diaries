# 0050 fixture test — how to run

This is a **feature-specific, non-destructive acceptance test**, stored only in the Diaries parent repository. It creates temporary directories on the machine that executes it and does not interact with the live Btrfs roots, services, keys or remote receiver.

The test expects the proposed read-only receiver `diaries_history` config namespace in `DESIGN-AND-INTERFACE-CONTRACT.md`, and source-mode compatibility. It intentionally fails against the as-closed 0049 reader because 0049 rejects receiver `verification.required=false`.

## Run from Windows Cygwin, using the Playbooks checkout on mango

After applying the 0050 ZIP to the authoritative Windows Diaries repository:

```bash
(
  cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries || exit 1

  test_file="change-control/in-progress/0050-FEAT - expose Diaries backup history on Btrfs receiver/tests/verify-0050-receiver-history-fixtures.py"
  test -f "$test_file" || exit 1

  # Safe baseline before 0050 implementation: only source compatibility test.
  ssh mango 'python3 - --playbooks-root /home/richard/ansible-controller/playbooks -k source' < "$test_file"
)
result=$?
echo "0050 SOURCE COMPATIBILITY FIXTURE EXIT STATUS: $result"
```

**Once the Playbooks 0050 implementation has been applied to mango**, run the full acceptance suite with the same Windows Cygwin terminal:

```bash
(
  cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries || exit 1
  test_file="change-control/in-progress/0050-FEAT - expose Diaries backup history on Btrfs receiver/tests/verify-0050-receiver-history-fixtures.py"
  test -f "$test_file" || exit 1
  ssh mango 'python3 - --playbooks-root /home/richard/ansible-controller/playbooks' < "$test_file"
)
result=$?
echo "0050 RECEIVER FIXTURE ACCEPTANCE EXIT STATUS: $result"
```

The test is piped through SSH: it **does not assume** the Windows Diaries checkout was synchronised to `/home/richard/diaries` on mango. The approved permanent code is loaded from mango's actual Playbooks working checkout; inspect its branch/HEAD/status first.

## Cases covered

Source 0049 compatibility; receiver-only identity and occurrence; receiver-local `show`, `path`, `--snapshot`; JSON and human status; full verifier CLI delegation and failure propagation via a disposable stub; tampered manifest SHA marker; manifest identity conflicts; unsafe symlink; empty history.

**Important:** The stub does not prove the real schema-2 verifier checks all files. Acceptance requires an additional real-schema verification test and a live selected received backup read-back. A `PASS` from this fixture is not evidence of deployment or live data integrity.

## Initial harness self-check, 17 November 2026

- Against 0049 implementation, the **source-only** test passed.
- Against 0049 implementation, the **receiver-only** test failed with the expected error: `Diaries verification is not enabled in snapshot-manager configuration`.
- The full nine-test harness passed against a **disposable, locally modified config-loader proof-of-concept copy**, which was used only to validate the fixture expectations. That temporary modification is **not** a 0050 implementation, was not added to the ZIP and has not been deployed.

## 0050 integrated source verification (new)

From the **mango SSH terminal**, working in `/home/richard/ansible-controller/playbooks`,
after applying the Playbooks ZIP, run the new permanent contract and existing
regressions, and use the Windows Cygwin terminal to stream the feature-specific
tests to mango without copying them into a permanent controller directory.
The second feature test, `verify-0050-real-schema2.py`, calls the actual
Playbooks schema-2 tool's `write` and `verify` subcommands against a **temporary**
valid received-generation fixture; it must pass before/after tampering.

Neither fixture reads/updates live Btrfs snapshots, and the feature tests
run solely with standard Python libraries. The permanent contract test uses
PyYAML (already an Ansible prerequisite).

## 17 November 2026 fixed-root regression extension

`verify-0050-real-schema2.py` now exercises both a symlink to a
backupId-named generation **and** a real directory named `diaries-backup`,
with tamper detection in both layouts and source-mode compatibility.
`verify-0050-receiver-history-fixtures.py` now expects the existing schema-2
`--allow-fixed-working-root` flag when the selected local dataset is a fixed
`diaries-backup` directory. The permanent Playbooks deployment contract also
asserts this narrowly scoped mode selection.
