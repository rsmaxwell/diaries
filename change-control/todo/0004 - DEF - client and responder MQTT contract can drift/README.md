# 0004 - DEF - client and responder MQTT contract can drift

## Summary

The Angular client and Java responder duplicate MQTT topic names, RPC operation names, property names and JSON object shapes without an executable shared contract.

## Problem

A change on one side can compile and pass its local tests while becoming incompatible with the other side. Possible failures include:

- different RPC operation names;
- different argument names;
- incompatible reply payloads;
- mismatched retained topic paths;
- changed fragment or marquee JSON fields;
- inconsistent delete or tombstone semantics;
- incompatible file URL conventions;
- different protocol assumptions between deployed versions.

Documentation describes the intended agreement but does not prevent drift.

## Expected behaviour

The project should define a canonical, versioned MQTT protocol contract consumed or verified by both client and responder.

## Scope

The contract should define at least:

- RPC operation names;
- request argument and user-property names;
- response status and error shapes;
- retained topic naming rules;
- diary, page, fragment and marquee payload shapes;
- lock fields and lock-owner representation;
- delete, tombstone or retained-topic clearing behaviour;
- static file metadata and URL fields;
- protocol version.

The implementation may use shared constants, JSON Schema, generated TypeScript/Java models, canonical fixtures, or contract tests, provided both applications are verified against the same definitions.

## Acceptance criteria

- A canonical protocol definition exists in an appropriate shared project or directory.
- Both client and responder builds validate their protocol usage against it.
- Contract tests cover representative request, success reply, error reply and retained-object payloads.
- Topic builders are centralized or tested against canonical examples.
- A deliberate incompatible contract change requires an explicit protocol-version change.
- The development documentation explains how to update the contract safely on both sides.
