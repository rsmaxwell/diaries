# 0005 - DEF - client retained-state transitions lack focused tests

## Summary

The client has component and service tests, but important UI behaviour driven by asynchronous MQTT RPC replies and retained topic updates is not sufficiently covered.

## Problem

The client should treat retained topics as the live model. MQTT timing is nondeterministic, so an RPC reply may arrive before or after the associated retained publication. Reconnects, duplicate messages, retained deletions and lock changes can also alter selected or editing state.

Without focused tests, the UI may display stale objects, retain deleted selections, enable invalid actions or lose state after reconnecting.

## Expected behaviour

Client tests should prove that UI and local interaction state are derived safely from retained MQTT messages regardless of normal message ordering.

## Required test cases

Tests should cover at least:

1. RPC success arriving before the retained update.
2. Retained update arriving before the RPC reply.
3. Duplicate retained publications being harmless.
4. A retained delete or cleared topic removing the object from the UI.
5. Deleting the selected object clearing or safely changing selection.
6. Lock ownership changes updating edit, move, resize and delete action enablement.
7. Losing a lock while editing stopping or safely cancelling the operation.
8. New-fragment enablement following diary/page/selection changes.
9. MQTT reconnect rebuilding the visible retained object model.
10. Token refresh preserving subscriptions and pending request handling.

## Scope

Tests should concentrate on the MQTT service, retained topic-tree service or model, selection/editing modes, fragment component and marquee interaction code. Broker and responder dependencies may be represented by deterministic test doubles at the client unit-test level.

## Acceptance criteria

- Automated client tests cover all required cases above or document why a case belongs in system testing instead.
- Tests do not depend on real-time delays where observable or fake-timer control is possible.
- Tests assert both rendered/action state and underlying selected/editing state.
- Deleted or unavailable objects cannot remain editable.
- The normal client test command runs the new tests reliably in headless mode.
