# 0045-FEAT — Step 1 dpkg metadata parsing correction

**Date:** 11 November 2026. **State:** Step 1 remains OPEN until both v2 manifests pass and coverage is accepted.

## Observed failure

The corrected, definitive v2 baseline capture at `20261111-110959Z` recorded the Windows Diaries revision and `mango` inventory source successfully. It stopped while capturing `mars` static installed metadata:

```text
FAIL: 0045 managed-host fingerprint: Unexpected package metadata format: acl
```

The first v1 baseline remains available as historical evidence; the incomplete v2 run remains a diagnostic record. No configuration, package, snapshot, replication or service change was performed.

## Cause and narrow correction

The v2 collector used `.strip()` on `dpkg-query -W -f=${Status}\t${Version}` output. An absent package can be recorded as `unknown ok not-installed` with an empty `Version`, yielding `unknown ok not-installed\t`. `.strip()` removes the trailing tab; splitting no longer yields two fields and causes a false error.

The collector now removes only trailing CR/LF line separators with `.rstrip('\r\n')`, preserving the version delimiter and correctly returning `present: false` for not-installed packages. All installed package version comparisons and unexpected-format checks remain intact. No package installation is required.

## Verification

`tests/test-0045-package-metadata.py` exercises installed, unknown-not-installed, config-files-only, no-matching-package and malformed output. The fix was checked with Python syntax validation and these focused cases. The collector remains read-only and continues to exclude temporary files from installation comparisons.

## Next Step

Apply the correction to the authoritative Windows Diaries feature, run the focused offline regression, then recapture the definitive Step 1 v2 baseline. Review both `mars` and `backup` manifests before accepting Step 1. Preserve raw diagnostic evidence. No changes to Playbooks or managed hosts are necessary.
