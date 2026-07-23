# 0002 - DEF - fragment and marquee locking lacks integration tests

## Summary

Fragment and marquee locking behaviour is central to safe editing, but the responder does not have sufficient automated integration coverage for lock acquisition, ownership, expiry, conflict and release.

## Problem

Recent changes added or adjusted fragment locking before editing and before marquee movement or resizing. These behaviours involve the browser, MQTT RPC handlers, persisted lock data and retained object publication.

A regression could allow two users to edit the same fragment, prevent a legitimate owner from saving, leave a fragment permanently locked, or allow marquee changes without the required lock.

## Expected behaviour

Responder integration tests should prove that lock rules are enforced consistently and that the resulting retained state matches the committed database state.

## Required test cases

The automated suite should cover at least:

1. An unlocked fragment can be locked.
2. The same owner can repeat a lock request safely.
3. A different owner cannot take an active lock.
4. The lock owner can update the fragment.
5. A non-owner cannot update the fragment.
6. The lock owner can move or resize the associated marquee.
7. A non-owner cannot move or resize the associated marquee.
8. The owner can unlock the fragment.
9. Repeating unlock is benign and idempotent.
10. An expired lock can be cleared or replaced according to the configured TTL.
11. Startup stale-lock cleanup removes only eligible stale locks.
12. Lock state is republished to the retained topic tree after successful changes.

## Scope

Tests should exercise the real responder handler and repository layers with representative MQTT request data. Where practical, PostgreSQL and an MQTT broker should run as test services rather than being replaced entirely by mocks.

## Acceptance criteria

- Automated tests cover all required cases above.
- Tests verify both database lock state and retained MQTT object state.
- Tests verify the returned RPC status and error details.
- Competing-user tests use distinct authenticated identities or equivalent verified caller contexts.
- Tests are deterministic and do not depend on execution order.
- The tests run as part of the normal responder test task or a clearly documented integration-test task.
