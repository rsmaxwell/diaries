# Step 2 — Authoring Action Matrix

| Selected state | MARQUEE Add | Add Image Fragment | Marquee create/edit/delete | Select/replace Image | Clear Image | Delete Fragment | Delete Image |
|---|---:|---:|---:|---:|---:|---:|---:|
| No Page | disabled | disabled | disabled | disabled | disabled | selection-dependent/disabled | Files catalogue only |
| Page, no Fragment/day context | existing behaviour | disabled | disabled | disabled | disabled | disabled | Files catalogue only |
| MARQUEE Fragment | unchanged | enabled when authoring gate/client rollout permits and context is valid | existing rules | disabled | disabled | enabled | Files catalogue only |
| IMAGE Fragment, `imageId=null` | unchanged | enabled when context is valid | disabled | enabled | disabled | enabled | Files catalogue only |
| IMAGE Fragment, `imageId=<id>` | unchanged | enabled when context is valid | disabled | enabled | enabled | enabled | separate catalogue action; responder may reject while referenced |

## Action ownership

```text
MARQUEE Add                -> existing addFragment RPC
Add Image Fragment         -> addImageFragment RPC
Select/replace Image       -> explicit updateFragment imageId=<positive id>
Clear Image                -> explicit updateFragment imageId=null
Ordinary text/date/reorder -> existing updateFragment path with imageId omitted
Delete Fragment            -> deleteFragment RPC
Delete Image               -> deleteImage RPC
```

No action is allowed to silently substitute another action because a request fails or a selected entity is missing.
