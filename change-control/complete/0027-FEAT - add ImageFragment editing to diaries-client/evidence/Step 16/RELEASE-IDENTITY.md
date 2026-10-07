# 0027 final release identity

## Development / regression

- Step 13 final development verification: complete, including Angular 229/229 and focused responder regression success recorded in existing Step 13 evidence.
- Step 14 workstation/rehearsal run: `20261006-093834`, PASSED prerequisite accepted by Step 15.

## Production

- Step 15 run: `20261006-133404`.
- Client: `rsmaxwell/diaries-client:0.0.9-build-76`.
- Responder: `rsmaxwell/diaries-responder:0.0.9-build-84`.
- Reader: `rsmaxwell/diaries-web:0.0.9-build-8`.
- Target: `pluto`.
- Files selector: production `files` root (unchanged by 0027).
- Authoring gate: deliberately controlled through `diaries_image_fragment_writes_enabled`; normal post-0027 role default is `true`, with `false` retained as rollback.

## Source identity

The Diaries repository head observed during final close-out is:

```text
c3528b0ea135ac2773855ec524605bd3910b5db8  Step 15 listFiles timeout correction
```

Final documentation was generated from:

```text
diaries-sources-20261007-085928.zip
playbook-sources-20261007-085936.zip
```

The source archives do not include the ignored Step 14/15 run-local `begin.txt` files. Therefore the exact production image tags above are the authoritative portable artifact identity retained by the feature evidence; this close-out does not manufacture a component-specific commit hash that is absent from the archived run evidence.
