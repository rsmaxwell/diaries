# 0007 - DEF - no combined CI verification for compatible client and responder revisions

## Summary

The project does not have one CI workflow that verifies the client, responder and shared system assumptions together as a compatible release candidate.

## Problem

Separate pipelines can report success even when the selected client and responder revisions are incompatible. They may also omit PostgreSQL, MQTT broker, retained-state, static-file and browser-level verification.

This allows integration failures to be discovered only during manual testing or deployment.

## Expected behaviour

A combined CI workflow should build and test the complete Diaries revision set and provide a single pass/fail result before release or deployment.

## Required stages

The workflow should include at least:

1. Checkout the top-level Diaries repository and the intended child revisions.
2. Validate submodule or component revision consistency.
3. Install client dependencies using the lock file.
4. Run client unit tests headlessly.
5. Build the client in production mode.
6. Run responder unit and integration tests.
7. Build the responder distributable artifact.
8. Start test PostgreSQL and Mosquitto services.
9. Run protocol and retained-state integration tests.
10. Exercise the static file server.
11. Run a minimal end-to-end smoke test.
12. Archive useful test reports and logs on failure.

## Scope

The workflow may be implemented in the existing pipeline repositories or moved into a top-level CI definition, but it must identify exactly which client and responder commits were tested together.

## Acceptance criteria

- A single CI result represents the compatible Diaries system revision set.
- The job records the client, responder and protocol versions and commit SHAs.
- Client and responder unit tests are mandatory stages.
- Integration services are isolated and repeatable.
- Failures retain enough browser, responder and broker diagnostics to investigate the problem.
- Release or deployment jobs depend on the successful combined verification result.
- The workflow and local equivalent commands are documented.
