# 0003 - DEF - retained MQTT state is not contract-tested against transactions

## Summary

There is insufficient automated verification that retained MQTT state is published only after a successful database commit and is not published when a transaction fails or rolls back.

## Problem

The intended Diaries architecture treats PostgreSQL as the durable source of truth and retained MQTT topics as the distributed live model. If retained messages are published too early, omitted, or contain data different from the committed row, connected clients can display state that is not actually durable.

This risk affects create, update, lock, unlock, move, resize and delete operations.

## Expected behaviour

For every state-changing RPC operation:

1. The responder validates the request.
2. The database transaction completes successfully.
3. The transaction commits.
4. The responder publishes retained state representing the committed result.
5. The responder returns a consistent RPC reply.

If validation or persistence fails, the transaction should roll back and no misleading retained update should be emitted.

## Required coverage

Tests should cover representative operations including:

- add fragment;
- add marquee;
- update fragment;
- update marquee;
- lock fragment;
- unlock fragment;
- update page or diary metadata;
- delete marquee;
- delete fragment.

## Acceptance criteria

- Tests observe the database and MQTT broker for each representative operation.
- Successful tests prove that the retained payload matches committed database values and identifiers.
- Failure tests prove that rollback leaves both the database and retained state unchanged.
- Publication order is verified sufficiently to prevent retained state from becoming visible before commit.
- RPC replies and retained objects use consistent identifiers and object shapes.
- The behaviour is documented as a responder invariant for future handlers.
