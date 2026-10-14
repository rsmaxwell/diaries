# 0034 Step 1 apply notes

Overlay this package onto the Diaries repository root.

This Step-1 package adds **change-control evidence/tooling only**. It does not replace any live Diaries script and does not require a Docker image build or production deployment.

Run the source regression from the Diaries repository root:

```text
python "change-control/in-progress/0034-FEAT - make production complete-backup repository Btrfs-aware/evidence/Step 1/tooling/verify-frozen-0033-contract.py"
```

Then run the read-only production capture on `pluto` as described in `README.md` and retain the resulting transcript as `RUNTIME-PRODUCTION-STORAGE-BASELINE.txt` under this Step-1 evidence directory.

Step 1 should not be marked complete until that runtime transcript has been reviewed.
