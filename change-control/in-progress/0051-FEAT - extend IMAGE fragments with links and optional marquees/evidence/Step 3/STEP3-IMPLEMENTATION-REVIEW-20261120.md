# 0051 Step 3 — implementation review and remaining acceptance

**Prepared:** 20 November 2026  
**Status:** implementation prepared, runtime regression/smoke verification OPEN; not CLOSED.

## Integrated changes

- Angular Fragment DTOs, update requests, RPC calls and retained-context Marquee association now support IMAGE with a same-page Marquee. Version-bearing IMAGE Marquee add/delete requests and explicit link SET versus CLEAR avoid null-valued MQTT-RPC arguments; old ordinary updates preserve the link.
- Editor provides a validated external HTTP(S) image link field, Save/Clear link, an independently clickable resolved image and separate Show on source page action. Existing selection/drag and file fallback are not converted into external links. Source Marquee selection uses the actual same-page relation rather than relying on optional Fragment `marqueeId`.
- Pageheader and ImageViewer allow source region operations for IMAGE while retaining existing MARQUEE behaviours and version checks. Day reader header uses `Image ID: N`, preserving the existing no-reference fallback.
- Public reader retained Fragment model exposes nullable `imageLinkUrl`; projection accepts same-page IMAGE Marquees. Safe link checking is independent from responder; month and source templates wrap only a resolved Image in the external hyperlink. Show-on-source selection stays separate; unsafe and unavailable media remain non-clickable.
- Synthetic model, component, projection, retained decode and rendering tests updated/added for link and Marquee behaviour. No responder or Playbooks code changed in this package.

## Verification boundary

Locally in the packaging environment, TypeScript source syntax was transpilation-checked, Java link-validation class was compiled with `javac`, and templates/source were inspected. These are NOT equivalent to Angular app compilation, full web Gradle tests or runtime visual checks. No production data or services touched.

Required on the Windows authoritative checkout after applying ZIP:

1. Inspect `git status --short`, parent/submodule revisions and patch in Beyond Compare (keep pre-existing dirty changes).
2. Run `bash "$feature/tools/verify-step3-local.sh"` from the Windows Cygwin Diaries parent repository, after assigning `feature` as below. It captures the web Gradle build/test and Angular Chrome Headless suite plus production build together with Git revisions, into timestamped `evidence/Step 3/private/run-*/` logs. Review individual failures rather than masking them.
4. Run local integrated client/responder/web against the same isolated fixture, with the Step 2 extension gate enabled **only there**, and verify all combinations (external link absent/present × same-page Marquee absent/present). Check set/preserve/clear, stale versions, rejected unsafe URLs, source highlight, keyboard interaction, missing media, legacy MARQUEE/HTML and desktop/mobile layout. Capture representative screenshots/logs and component revisions.
5. Record failures and correct together; accept Step 3 only when these results and full client/web regression are reviewed. Avoid rerunning the accepted Step 2 isolated migration merely to generate duplicate evidence.

## Safety and rollback

The Step 3 package changes only Diaries client/web code and the 0051 change-control feature. It does not modify production DB schema, retained topics or deployed images. The independent responder extension-write gate remains default-off; rollouts must follow Step 4 once the client and web reader are both compatible. Existing 0028 migration remains paused. Restore the prior submodule file versions using Beyond Compare if inspection identifies a regression; do not overwrite unrelated local changes.
