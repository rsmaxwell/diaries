# 0026 handoff to 0027 and 0028

## Production reader baseline handed off

```text
production target: pluto
Git commit: e5aa410bcf83e73f83bf81cb5aee9571ccba2755
diaries-web: rsmaxwell/diaries-web:0.0.9-build-7
  image ID: sha256:fac8a20418d26a86bbb49bea359fbd3fba271c8aa95f0510147da382f12a6e9f
diaries-responder: rsmaxwell/diaries-responder:0.0.9-build-82
  image ID: sha256:27d58edf958a95c7c7dcca4688bb0203fc96f23f7bda5b82fde154acb79607ba
diaries-client: rsmaxwell/diaries-client:0.0.9-build-74
  image ID: sha256:efe5e8b7c0a969ba0821d04a3b31cc0c83b079fd2d11a5e3c86cda2aa94ef45d
content.filesPath: files
web Image ACL: read-only diaries/images/+
web RPC: denied
imageFragmentWritesEnabled: false
production IMAGE Fragment rows at Step-15 close-out: 0
```

## 0027 — add ImageFragment editing to diaries-client

Reader readiness is satisfied. 0027 may build against the above deployed reader/responder baseline, but must not infer permission to author merely from the availability of 0025 RPCs. 0027 owns Angular retained Image handling/editor UX, its own production feature gate, smoke verification, and the separately approved transition of `imageFragmentWritesEnabled` from false when authoring is ready.

Before enabling production authoring, verify the deployed web reader is still at or above the 0026 baseline and its Image subscription/Files route are healthy. After the first production IMAGE Fragment is created, do not roll the reader back to a pre-0026 version that omits IMAGE chronology.

## 0028 — migrate reviewed legacy embedded-image fragments

Reader readiness is satisfied, but migration remains blocked on 0027/editor availability and 0028's own operational prerequisites. 0028 must freeze/review the 0022/0024 inventories, produce a reviewed disposition manifest, rehearse against restored production data/Files content, take fresh production backup/snapshot evidence, stop writers, then apply only approved conversions.

0026 supplies no migration authorization and performed no legacy conversion. Its production close-out contained zero IMAGE Fragment rows.

## 0029 boundary

0029 remains independent. Destructive legacy cleanup, final relationship constraints and removal of compatibility behavior are explicitly outside 0026 and must not be folded into 0027/0028 merely because the reader is ready.
