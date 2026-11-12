# 0046 inventory candidate triage

The classifier is a **read-only, no-values** second pass following `audit-0046-inventory-readonly.py`. It is intended to reduce manual inspection of the 33 candidate plaintext fields found on `mango` on 2026-11-11. The Python source and report belong only to the 0046 Diaries change-control feature directory.

Invoke the script from the **Windows Cygwin** checkout, streaming its contents to `python3 -` on `mango`. The script requires PyYAML on `mango` but no inventory export or extra credentials.

Output never includes candidate key names or values. Categories:

- `REFERENCE_ONLY`: entire YAML scalar is a simple `{{ variable }}` expression with no literals, functions or filters; does not contain a literal credential.
- `PUBLIC_KEY_FORMAT`: SSH public key syntax; public key, not private-key material.
- `PATH_REFERENCE_REVIEW`: path string, may point to protected material and still requires review.
- `COMPOSITE_OR_COMPLEX_TEMPLATE_REVIEW`: template text with other content, filters or expressions; can contain hardcoded fallback secrets.
- `PLAINTEXT_LITERAL_REVIEW`: sensitive-named key has a literal string; needs local inspection.
- `HIGH_RISK_LITERAL_OR_CREDENTIAL_URL`: embedded private key header or URL credentials; treat as a likely security issue until resolved.

A script exit of `2` means human review is required (not that execution failed), `1` is an audit error, and `0` means structural triage has no unresolved candidate shape; **all outputs still require human acceptance before Git staging**. Never paste candidate values in chat or commit logs containing values.
