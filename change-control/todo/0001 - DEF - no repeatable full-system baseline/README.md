# 0001 - DEF - no repeatable full-system baseline

## Summary

There is currently no single repeatable procedure that proves a compatible `diaries-client` and `diaries-responder` revision works as a complete Diaries system.

The client and responder can be built and tested separately, but there is no recorded baseline covering PostgreSQL, Mosquitto, MQTT RPC, retained topic-tree state, static file serving and the main browser workflows together.

## Problem

A change can pass the client and responder unit tests while still breaking an interaction between the two applications. Typical examples include mismatched RPC payloads, retained topics not being updated, stale browser state, lock races, restart reconciliation problems and incorrect static-file URLs.

Without a repeatable baseline, it is difficult to determine whether the latest committed revisions are known to work together before further changes are made.

## Expected behaviour

The project should provide a documented, repeatable full-system verification procedure that:

1. Builds and tests both the Angular client and Java responder.
2. Starts or connects to the required PostgreSQL and Mosquitto services.
3. Starts the responder and client using known test configuration.
4. Exercises the main diary, page, fragment, marquee, authentication and file workflows.
5. Records the expected browser, responder, MQTT and database results.
6. Can be repeated after future changes to establish whether the system remains healthy.

## Scope

The baseline should include at least:

- client dependency installation, unit tests and production build;
- responder clean build and tests;
- sign-in and token use;
- opening a diary and page;
- adding a fragment and marquee;
- editing fragment content;
- moving and resizing a marquee;
- browser refresh and persistence checks;
- two-client lock contention;
- stale-lock recovery;
- fragment and marquee deletion;
- responder restart and retained-state reconciliation;
- file upload, listing, display and deletion;
- verification of browser console and responder logs.

## Acceptance criteria

- A Markdown test procedure exists in the Diaries repository.
- All commands, prerequisites and configuration assumptions are documented.
- Each manual step states its expected result.
- The procedure identifies which browser console messages, responder log entries, MQTT topics and database state should be checked.
- The complete procedure has been run successfully against one recorded pair of client and responder revisions.
- Any test data created by the procedure can be removed or reset safely.
