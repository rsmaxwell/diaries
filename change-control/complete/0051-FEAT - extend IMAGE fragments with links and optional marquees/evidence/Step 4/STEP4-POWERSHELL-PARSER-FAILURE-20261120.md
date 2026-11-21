# 0051 Step 4 — PowerShell parse failure and correction (20 November 2026)

**Status:** corrected in package, Windows rerun pending. **Step 4 remains OPEN.**

## Observed failure

The first invocation of `tools/verify-step4-disposable-rollout.ps1` failed to parse at line 114:

```text
ParserError: Variable reference is not valid: ':' was not followed by a valid variable name character
Write-Host "Candidate $part: $($details.Id)"
```

PowerShell interprets `$part:` as a scoped variable form in interpolated strings. It cannot parse this expression, so **no statements in the rehearsal script executed**. In particular, no candidate Docker image was built or container started by this invocation.

## Change

Change that output expression to `Write-Host "Candidate ${part}: $($details.Id)"`. This is an output-only correction; the image identities, gate policy and container operations are unchanged. Add an offline Node regression assertion to prevent reintroduction of the malformed interpolation. The previously issued rollout package and historical logs are left intact.

## Acceptance / next validation

1. Apply this correction to the Windows Diaries checkout.
2. Run PowerShell's `[System.Management.Automation.Language.Parser]::ParseFile(...)` on the file and confirm zero errors before invoking it.
3. Rerun the same disposable Step 4 rehearsal using the verified frozen fixture.
4. Capture the Docker image IDs, gate-disabled/activation receipts, rollback boundary, cleanup and evidence checksums.

The runtime rehearsal is **not** accepted until the Windows run succeeds. No deployment to `pluto` or production schema change is authorised.
