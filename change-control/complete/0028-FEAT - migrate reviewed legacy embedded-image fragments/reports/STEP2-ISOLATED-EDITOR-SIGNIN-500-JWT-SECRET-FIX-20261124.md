# 0028 Step 2 — isolated Editor sign-in 500, JWT secret format

**Status:** Code remediation prepared; Windows live verification remains OPEN. No production migration authorised.

## Evidence and analysis

On 24 November 2026, the Angular Editor at localhost:58083 returned RPC 500 (`internal error`) during an attempt to sign in using a restored production user. The MQTT WebSocket connection, Reader and existing retained data had previously passed verification. A registration attempt using an existing production username returned 400, consistent with the restored user table.

The isolated MQTT/Reader fixture generator (0028-replay-verify.py) produced `secret` with `secrets.token_urlsafe(48)`, which uses *URL-safe* Base64 (`-` and `_`). The responder's `Authorization.getTokenWithClaims` uses `Base64.getDecoder().decode(secret)`, which requires *standard* Base64. The failure would occur during JWT issuance, **after** password checking and account-status validation. This is a strong likely cause of the reported 500, not yet proven by the running responder's stack trace.

## Correction

* Future isolated fixtures generate `secret = base64.b64encode(secrets.token_bytes(48)).decode('ascii')`, compatible with Java's standard Base64 decoder.
* The guarded isolated-only repair tool verifies container label, network, config bind mount, source/occurrence journal counts, Fragment count, existing Reader readiness and Marquee fingerprint.
* If the existing JWT secret is invalid for standard Base64, it writes a private backup and replaces **only the `secret` field** in the existing JSON, using an in-place write to preserve the existing file bind mount. It checks the mounted content and restarts only `diaries-0028-replay-responder`.
* After restart, it checks Reader health and unchanged DB journals/Marquees. Existing production accounts and password hashes remain unchanged. It does not rebuild or re-run the migration.
* If the key is already valid, it refuses to rotate anything and directs investigation to responder exception logs.

## Running the repair

**Windows PC — Cygwin Bash, from the Diaries parent repository root:**

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/repair-0028-step2-isolated-signin.sh'
```

Reopen the isolated Editor at `http://127.0.0.1:58083/diaries/` and retry sign-in with the existing account. **Do not put a password into terminal logs or evidence.** If the sign-in still fails, inspect recent logs for an exception type and stack trace, but do not publish configuration or password hashes.

## Remaining gates

Interactive Editor sign-in, migrated-image GUI inspection, navigation, Marquee positioning and locking still require acceptance. Production apply remains separately controlled and is not authorised by this repair.
