# 0006 - DEF - Diaries versions and protocol compatibility are not managed consistently

## Summary

The client and responder currently use unrelated placeholder or snapshot versions and do not expose a clear compatibility relationship.

## Problem

A deployed client can connect to a responder with an incompatible MQTT contract without receiving an early, understandable warning. Failures then appear later as missing fields, rejected RPC calls, invalid topics or incorrect UI state.

The client and responder also lack a single visible Diaries release version for troubleshooting and support.

## Expected behaviour

Each release should identify:

- the Diaries system release version;
- the client build version;
- the responder build version;
- the MQTT protocol version;
- whether the connected client and responder protocol versions are compatible.

The versions should be generated consistently by the build and made visible in logs or an application information view.

## Scope

The implementation should consider:

- one source of the system release version in the top-level build or release configuration;
- propagation into Angular build metadata;
- propagation into the responder manifest or build metadata;
- responder protocol-version reporting during sign-in, connection setup or a dedicated information RPC;
- a clear client warning or refusal for incompatible protocol versions;
- version information in diagnostic logs without exposing secrets.

## Acceptance criteria

- The client no longer reports only a hard-coded `0.0.0` placeholder for a release build.
- The responder and client expose their build versions.
- The MQTT protocol has an explicit version.
- Compatibility is checked before normal editing operations begin.
- An incompatible client/responder combination produces a clear user-facing and logged error.
- Release documentation explains how all versions are set and advanced.
