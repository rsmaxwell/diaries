# 0028 Step 1 — Review portal defaults (2026-11-18)

**Status:** reviewer interface enhancement, NOT approval to migrate.

The offline reviewer now supports three requested defaults:

1. A blank **Caption override** resolves to a single unambiguous caption
   extracted from the verified original `<figcaption>`. For Fragment 84, the
   result is `Whitley Park`. The exported draft includes the resolved value
   and provenance, which the offline checker recomputes from the trusted
   proposal evidence. Ambiguous/missing source captions fail closed.
2. A reviewer identity entered once is carried to subsequent fragments during
   the current browser session; an imported draft restores reviewer identity.
3. The first substantive edit records the current UTC timestamp for that
   fragment (not when its page is merely viewed). Manual timestamps and the
   explicit restamp operation are retained.

This update supports draft v1 import/export without discarding existing
reviewed rows. Other source text, unsafe caption markup and missing captions
still need explicit human allocations or acknowledgement. Linked-image,
Page-provenance and suffix-matching blockers are unchanged. The utility never
applies migrations, and `productionApplyAllowed=false` remains unconditional.

**Step 2 obligation:** the actual migration utility must implement the same
caption resolution and verify first-class IMAGE caption rendering end to end.
The Step 1 reviewer does not by itself modify Image metadata, the diary database
or the public reader.
