# 0025 Step 11 - Database-backed ImageFragment integration

Completed 2026-09-27. Authoritative result: `verified-run/result.json` and
`verified-run/integration-test.xml`: **2 tests passed, zero failures/errors/skips**.

## Implementation

Extended `ImageWiringIntegrationTest` with
`imageFragmentDatabaseLifecycleWithRealRetainedTopics`. It creates its own Diary,
Page, two catalogued Images with temporary files, three IMAGE Fragments (two sharing
one Image, one initially unselected), and one MARQUEE Fragment with its Marquee.
Creation and lifecycle operations call the actual responder handlers and repositories.

The Step 11 runner also executes the existing
`referenceAwareDeletionSerializesWithAttachment` test from Step 9, so the concurrency
requirement is verified against the same final source rather than inferred from old evidence.

The fixture uses the production EntityManagerFactory/context wiring with
`hibernate.hbm2ddl.auto=validate`. The runner restores the SHA-verified frozen 0024 dump
into disposable PostgreSQL 18, then applies the 0024 Image schema and 0025 migration.
Mosquitto is a separate disposable container. Both expose random loopback-only ports.
All physical Image bytes live in JUnit temporary directories, never on the NAS.

## Scenario evidence

| Step 11 scenario | Verified behavior |
| --- | --- |
| 1. FK accepts existing Image | Real addImageFragment calls persist two references to the first Image; direct repository reads match. |
| 2. FK rejects missing Image | Direct SQL update to a nonexistent Image fails with SQLSTATE 23503 and rolls back. |
| 3. MARQUEE + image_id rejected | Direct SQL conversion of a referenced IMAGE to MARQUEE fails with SQLSTATE 23514; type remains IMAGE. |
| 4. IMAGE + optional selection | Handler creates two selected and one unselected IMAGE Fragment; persisted type/Page/Image match. |
| 5. No Marquee for IMAGE | Marquee repository lookup is empty for each created IMAGE Fragment. |
| 6. Reuse | Both IMAGE Fragments reference the same existing Image row. |
| 7. Update selection and locking | Attach first Image, replace with second, clear selection; version increments and successful edits clear the lock. Stale version returns 400 and wrong owner returns 409 without changing row or retained topics. |
| 8. Mixed chronology | IMAGE sequences 40/20/10 plus MARQUEE sequence 30 normalize together to 1..4, preserving references. |
| 9. Delete one reference | Actual DeleteFragment removes only its row and retained aliases; the other Fragment, shared Image metadata/topic and physical bytes remain unchanged. |
| 10. Referenced Image conflict | Actual DeleteImage returns 409 with two and then one reference; row/file/broker snapshots remain unchanged. Direct SQL Image deletion is also blocked by FK 23503. |
| 11. Delete after last reference | Last Fragment deletion leaves Image intact. Explicit DeleteImage then removes row/file and actual broker retained Image topic, preserves the other Image, and leaves no staging backup. |
| 12. Concurrent attach/delete | Separate test observes real PostgreSQL lock waits in both orderings. Attachment winning causes deletion 409 and staged-file restoration; deletion winning makes attachment fail without a dangling FK. |

Fresh MQTT observers subscribe after operations to inspect actual retained messages.
A non-retained barrier on the publishing connection flushes preceding asynchronous
messages and bounds each snapshot. Initial Image and Fragment payloads, both Fragment
aliases, reference edits, conflict preservation and successful tombstones are checked.
The concurrency test retains its recording publication seam; the combined lifecycle
test exercises real Mosquitto publication and acknowledged Image deletion.

## Results and safety

- Dedicated integration run: **2 passed, 0 skipped**.
- Full responder regression/build: **310 discovered, 276 passed, 34 environment-gated skips, 0 failures/errors**. The two integration tests above were run separately with their environment variables supplied.
- `git diff --check` passed.
- Original Diary/Page/Fragment/Marquee/Image row counts and JSON row hashes match after fixture cleanup; see `database-before.txt` and `database-after.txt`.
- Both owned containers were successfully stopped/removed; cleanup exit codes are zero.
- No live database, production deployment, NAS file, client source or application implementation changed.
- Gradle's existing deprecation/Shadow warnings remain non-fatal.

`run-01` also passed. The final `verified-run` adds explicit positive assertions for
all initial Image and ImageFragment retained payloads, avoiding a comparison of two
missing values being accepted as preservation. Source and migration hashes are recorded
in `source-sha256.csv`; the working tree includes prior uncommitted feature changes.
Row-hash equality concerns table contents; disposable sequence counters can advance.

## Files

- `ImageWiringIntegrationTest.java`: new combined fixture and SQL/MQTT observation helpers.
- `run-integration.ps1`: reproducible two-test PostgreSQL/Mosquitto runner with backup verification, schema setup, row snapshots and owned-resource cleanup.
- `fixture-mosquitto.conf`: fixture-only listener, anonymous access and disabled disk persistence; never deployed.
- Feature plan/README and responder README: completed status and test instructions.

## Reproduction and scope

From PowerShell 7 with Docker running:

```powershell
.\run-integration.ps1 -EvidenceDirectory <new-evidence-directory>
```

The runner requires the existing frozen backup and local PostgreSQL/Mosquitto images.
It refuses an existing evidence directory and restores the previous test environment
variables after execution. `final-test-build.log` records the full Gradle test/build run.

Handlers are invoked directly in this step. This is not browser verification or a
complete live MQTT request-dispatch/restart test. Step 12 remains responsible for
live RPC transport, startup replay and fresh-client end-to-end checks. Production
migration/deployment is still separate work.
