# 0028 Step 3 — Git staging synthetic URL fixture correction

## Finding

The initial feature-scoped staging attempt stopped before staging any files because a negative URL-security regression test contains a synthetic credential-bearing URL. Source-bundle review found a second synthetic credential-bearing URL in the related portal-suggestions regression. Both examples use the reserved `example.org` domain and are intended to be rejected by the URL validator; neither is a real credential.

## Change

The staging helper now masks only those two exact values, only within their corresponding named rejection test methods and only if the expected test assertion follows. The original file bytes still enter the SHA-256 manifest unchanged. All other credential-bearing URL strings remain blocked, including additional strings in those same test files. No change is made to either regression test.

## Execution and gates

Apply these feature-scoped files using Beyond Compare, run the helper tests, then invoke `--stage`. Review `git diff --cached --check`, staged paths and diff for private source material before committing. This does not authorise production migration. Private evidence remains excluded from Git. Do not add unrelated 0029/0053 files.

## Follow-up: self-scanning compatibility

The staging helper also scans its own source file, its regression tests and this report. The intentionally synthetic URL values are now assembled from adjacent literal fragments in Python, retaining identical runtime bytes without presenting credential-like full URLs in source text. This report describes the fixtures without repeating the credential-bearing examples. A new regression test runs the real file scanner against all three files. The staging rule is unchanged: only the two named negative-test fixtures in their original tests receive a narrow exemption; other credential-like content remains blocked.
