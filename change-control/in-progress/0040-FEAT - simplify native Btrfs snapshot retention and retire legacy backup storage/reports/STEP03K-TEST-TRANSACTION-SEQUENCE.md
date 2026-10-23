# 0040-FEAT — Step 3K: Disposable transaction sequencing

Status: **intermediate gate; Step 3 remains OPEN**.

The manager adds `receiver_transaction_test_sequence`, an internal (no CLI) coordinator requiring injected disposable snapshot deletion, receipt removal and protection-verification callbacks. It verifies the receipt identity, calls source-protection test callback, durably journals, calls deletion callbacks in sequence, checks postconditions, and clears the journal only after complete success. An exception preserves the journal for the existing `receiver-recovery-plan` classifier.

Nine mocked/disposable-directory tests passed locally. This is **not** a real Btrfs deletion implementation and does not establish cross-host pin lifetimes, safe automatic recovery, receipt unlink durability, or lock-held production deletion. Existing `receiver-prune` remains unconditionally blocked.

To test on mango from Windows Cygwin:

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries || exit 1
ssh mango 'python3 - /home/richard/playbooks/roles/snapshots/files/btrfs-snapshot-manager.py' < 'change-control/in-progress/0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage/tests/step03k-transaction-sequence.py'
```

Next acceptance: establish receiver writer-lock lifetime, durable receipt removal, cross-host source protection pin release semantics, and real disposable Btrfs fault injection. No production approval.
