# 0029 Step 2 — IMAGE Fragment creation: missing DATED placement

Date: 2026-11-26  
Status: FIX PREPARED — build/integration acceptance outstanding

## Evidence

On 2026-11-26 around 09:09 UTC, an `addImageFragment` request with Page 692, date 1828-03-23 and catalogue Image 3 returned RPC status 500. The read-only database check showed no new IMAGE row. The responder logging returned `Unable to save Image Fragment` without preserving the underlying stack trace.

The current migrated database has `fragment.placement NOT NULL` plus `fragment_placement_check` and `fragment_owner_check`. Ordinary `AddFragment` explicitly creates `placement=DATED`. `AddImageFragment` created its candidate with type `IMAGE`, Page and Image ID but omitted placement. The persistence DTO converts missing placement to SQL NULL. This mismatch is a concrete cause of a failed IMAGE insertion; the precise exception has not yet been observed in production logs.

## Change

- `AddImageFragment.java`: set `FragmentPlacement.DATED` on new IMAGE candidates; log a full exception stack trace with non-secret Page/date/Image identifiers if persistence fails; retain the generic internal error response and no automatic retries.
- `AddImageFragmentTest.java`: verify `DATED` placement for creation and generated DTOs, including nullable and existing catalogue Image references.
- `FragmentLifecycleContractTest.java`: assert created row has `DATED` placement in sequence-normalisation integration contract.

No migration, SQL, image catalogue or MQTT ACL change. Existing TEXT / PREAMBLE paths are unmodified. Uncommitted changes in other submodules must be preserved.

## Validation / execution

ZIP integrity checked. Gradle tests **not executed** in the packaging environment: the Gradle 9.6.1 wrapper distribution was unavailable offline and network DNS resolution failed. This does not establish a source test failure.

**Windows 11 — Cygwin Bash, repository root**:

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
./gradlew :diaries-responder:test --tests '*AddImageFragmentTest' --tests '*FragmentLifecycleContractTest' --console=plain
```

If those pass, rebuild/restart the local responder using the existing `diaries-responder/scripts/windows/run-responder.bat` workflow, and refresh the Angular Editor. Reattempt exactly one IMAGE creation on the development database, using existing Image ID 3. Verify returned ID, `placement=DATED`, Reader display, and deletion without deleting catalogue Image 3 or existing Fragment 2338. If it fails, capture the newly logged original Java stack trace and do not blindly retry. Production is excluded.

Feature Step 2 remains OPEN until acceptance.
