# 0028 Step 1 — v2 portal refresh test fixture reconciliation (2026-11-21)

## Observed Windows failure

The user's Cygwin regression run on 2026-11-21 executed 27 tests: 26 passed, one failed:
`test_sealed_v2_regeneration_and_no_overwrite` reported `ValueError: Source SHA256SUMS.txt missing`.
The test fixture in the first improved-portal package created only the v2 draft and
its SHA256SUMS.txt, but newer private-source rendering requires the separate
frozen production snapshot plus its own SHA256SUMS.txt. The test fixture was
out of sync with the current generation contract. Failure occurred inside the
unit test, prior to portal regeneration, and does not establish missing
production evidence.

## Change

* `tests/test_step4_0051_portal_refresh.py`: replace the original, incomplete
  fixture with a sealed synthetic snapshot + sealed v2 draft. Assert non-overwrite,
  unchanged evidence, and rejection of tampered draft/snapshot.
* `tests/test_step4_0051_original_html.py`: include the original-HTML rendering
  safety tests from the earlier source-viewer package, bringing the checkout to
  the consolidated intended test set.

No runtime code, database access, private HTML/CSV/JSON, migrations, or approval
logic changed. Only feature-specific tests and this report are distributed.

## Verification

In an isolated staging directory assembled from the uploaded source bundle and
current preceding packages, ran:

```
python3 -m unittest discover -s tests -p 'test_step4_0051*.py' -v
```

Result: `Ran 31 tests ... OK` (31 passed, 0 failed). Synthetic refresh
produced `0028-0051-review-v2.SOURCE-SUGGESTIONS.PRIVATE.html` and did not
modify its sealed source evidence.

## Windows acceptance

Apply this ZIP to the Windows Diaries root via Beyond Compare 4, reviewing
existing uncommitted changes, then rerun the 31-test suite. On success,
regenerate the private source-suggestions portal from the existing sealed v2
draft as documented in the preceding package. This test repair does not by
itself indicate acceptance against private live source evidence.

0028 Step 1 remains OPEN. `productionApplyAllowed` remains false.
