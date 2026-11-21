# 0051 Step 1 — Source audit and implementation map

**Inspected:** supplied `diaries-sources-20261120-093345.zip` and `mqtt-rpc-sources-20260926-092542.zip`, on 20 November 2026. **No active Git checkout, runtime, production database or broker connection is available from this inspection.** The uploaded bundle takes precedence over public GitHub. Local baseline revisions/dirty state are already preserved in `evidence/Step 1/local-source-baseline.json`.

This is an audit of **current source paths**, not passing tests or claims about actual deployed behaviour.

## Verified current exclusions, preservation paths and required changes

| Subsystem / exact active path | Current source observation | 0051 consequence |
|---|---|---|
| `diaries-responder/.../model/Fragment.java` | `Fragment` has nullable `Image`, `page`, `type`, but **no link URL**; DBDTO/PublishDTO copy paths distinguish persisted Image IDs | Add occurrence URL to JPA and both DTO conversion paths without losing it on inflation or copying |
| `.../dto/FragmentDBDTO.java`, `.../dto/FragmentPublishDTO.java` | Neither carries URL. Retained publish DTO includes `imageId` and `marqueeId` and publishes both canonical and per-date topics | Add URL to both; preserve JSON null, topic symmetry and confirmed-transaction publication |
| `.../repositoryImpl/FragmentRepositoryImpl.java` | Native ordered fields/value list and hand-indexed SELECT mapping (`imageId` at index 9), plus separate `findAllWithoutMarquee`, `findAllFragmentsWithMarqueesonDate` and other SELECTs | Update **every** SELECT list, DTO index, insert/update field/value mapping and roundtrip test; avoid one-index omissions |
| `.../utilities/DiaryContext.java` | `resolveFragmentState` tolerates unresolved Image references, reads Marquee independently; `loadFromDatabase` publishes Marquees and Fragments independently; `copyFragment` copies via publish DTO | Preserve URL in `copyFragment`, reload/replay and postcommit reload; do not turn unresolved records into tombstones |
| `.../utilities/ImageFragmentWritePolicy.java`, `.../config/Config.java` and Playbooks `roles/diaries/defaults/main.yaml`, responder config template | Existing `imageFragmentWritesEnabled` defaults to `true` in the supplied Playbooks role, after feature 0027; this controls **ordinary IMAGE authoring**, not the proposed extension | Add a **separate fail-closed extension gate** and Playbooks setting during rollout, without disabling already supported IMAGE functionality |
| `.../utilities/ResolvedFragmentState.java` | `validateForWrite` explicitly throws for IMAGE with a Marquee, but already checks that any Marquee belongs to same Fragment and Page | Remove type-exclusive rejection while retaining Page/identity check |
| `.../handlers/UpdateFragment.java` | `findByFragment` rejects IMAGE with a Marquee; builder copies Image but no URL; already honours `imageId` absent vs null and version + lock | Allow valid IMAGE/Marquee on text/link/reference edits; copy URL from persisted original, add clear flag with version/lock checks |
| `.../handlers/AddMarquee.java` | Requires MARQUEE-compatible Fragment, rejects duplicate, and **sets `fragment.type=MARQUEE` unconditionally**; add flow currently does not call `FragmentLocking.requireLockedByCaller` | New IMAGE path must never change type; require lock/version and Page/uniqueness under same transaction; publish committed version |
| `.../handlers/UpdateMarquee.java` | Requires `requireMarqueeCompatible` and Fragment lock, checks Fragment and Page IDs and Marquee version | Extend compatibility predicate for IMAGE; preserve lock/version/geometry and Page invariants |
| `.../handlers/DeleteMarquee.java` | Requires owning Fragment lock, deletes row, updates retained Fragment/Marquee, but has **no Marquee version arg** | Add IMAGE-specific optimistic version requirement without breaking old MARQUEE clients; verify exact tombstones |
| `.../handlers/DeleteFragment.java` | Explicitly rejects deleting IMAGE with Marquee; otherwise deletes its Marquee and Fragment together and publishes tombstones after commit | Remove invalid guard and retain atomic dependent removal; preserve shared Image catalogue/files |
| `.../utilities/FragmentLocking.java` | `requireMarqueeCompatible` rejects IMAGE; lock clear writes Fragment row through native update | Make type policy support IMAGE, preserve URL across lock clear, avoid old MARQUEE regression |
| `.../utilities/ImageFragmentMessageHandler.java` and bundled `mqtt-rpc-common/.../Request.java` | `Request` uses `Map.copyOf(args)` which **throws on null**; special adapter routes only `imageId:null` update/add | Explicit non-null clear flag for URL; preserve existing adapter and prove combined clear handling |
| `diaries-client/src/app/model/fragment.ts` | Type `ImageFragment` requires `marqueeId:null`; `isImageFragment` and `UpdateImageFragmentRequest` reject Marquee-present IMAGE | Widen type guard, keep authoritative fields omitted on ordinary edits; add explicit URL intent |
| `diaries-client/src/app/mqtt/rpc.service.ts` | `JSON.stringify` serialises payload; ordinary edits omit image reference and deliberate edits provide imageId; Marquee add/delete callers have no optimistic version argument | Add URL set/clear API; extend Image-specific Marquee version contract; retain old MARQUEE path compatibility |
| `diaries-client/src/app/model/model-context.ts` | `matchingMarqueeForFragment` and selected Marquee projection require `isMarqueeFragment` | Accept IMAGE whose same-Page Marquee is valid; select/highlight independently of image link |
| `diaries-client/src/app/fragment/fragment.component.ts`, image-reference and image-viewer components | IMAGE reference workflows require `isImageFragment` (currently excludes Marquee); Marquee create/edit/delete reject non-MARQUEE and existing add uses Fragment lock | Coherent guard and authoring change, URL edit control, separate navigation/selection and geometry locks |
| `diaries-client/src/app/dayview/dayview.component.html` and `.ts` | Image label already appears **immediately after Position**, but says `Image N`, not `Image ID: N`; returns `No Image selected` when null | Minimal label update; test with Marquee present and with catalogue data not loaded; no need to invent a new header slot |
| `diaries-web/.../model/FragmentItem.java` | Retained record/JSON creator handles type, imageId, marqueeId; no URL field | Add nullable URL to parsing with compatible old-message constructors and validate render side |
| `diaries-web/.../projection/ProjectionSnapshot.java` | IMAGE branch explicitly discards its linked Marquee and increments `imageFragmentsWithMarquee` anomaly | Resolve same-page IMAGE Marquee, preserve diagnostics for inconsistent relationships/duplicates and replay order |
| `diaries-web/.../http/WebServer.java` | `fragmentMediaView` sets `hasMarquee` only for MARQUEE, and resolves catalogue image to `mediaUrl` separately | Keep mediaUrl as file URL; add independently validated click URL; support IMAGE source highlight in both views |
| `diaries-web/src/main/resources/templates/{month-reader,source-page}.peb` | IMAGE media is plain `<img>`, fallback separately links to media file; source view has selector button | Wrap resolved image with safe hyperlink only when URL present; use separate source control for IMAGE + Marquee |
| `diaries-web/src/main/resources/static/js/diaries.js` | Month/source page selection and image load/error logic are separate; selectors bind to transcript elements | Avoid link-click bubbling to fragment selectors; keyboard and missing-image tests |
| `diaries-responder/.../sync/Synchronise.java`, `.../dto/MarqueePublishDTO.java` | Retained/startup paths exist; full end-to-end replay not exercised in this audit | Exercise missing/older messages, tombstones, date topics, startup/reconnect ordering in Step 2–4 |

## Live state and database constraints NOT asserted by this audit

The supplied source bundle also contains an ignored private `evidence/Step 1/private/production-container-baseline.json` dated by the bundle to 20 November 2026 09:27 UTC. It reports these *captured* running/healthy service versions: responder `0.0.9-build-84`, editor `0.0.9-build-77`, web `0.0.9-build-8`. They are **not** inferred from source HEAD and are not live-verified in this assistant session. Recheck before rollout and keep the raw container inspect outside the public report. No schema/DB constraint query, actual MQTT projection inspection, or **live configured value** of the authoring gate has been provided. The supplied Playbooks role default is `diaries_image_fragment_writes_enabled: true`, which is not proof of the live setting. This prevents Step 1 from being CLOSED.

Before Step 2, obtain read-only evidence for `information_schema.columns`/`pg_constraint`/`pg_indexes` for `fragment` and `marquee`, including `fragment.type/page_id/image_id` and `marquee.fragment_id/page_id` nullability/uniqueness/checks. Record active writer configuration/feature gate and deployment image digests. Do not assume the JPA annotation reflects production constraints.

## Risks requiring explicit regression coverage

1. **Data loss:** native SQL DTO index or `Fragment` copy/update loses `imageLinkUrl` on ordinary text edit, chronology normalisation, lock clear or replay.
2. **Wrong type:** old `AddMarquee` writes `MARQUEE` into a linked IMAGE and discards Image/link references.
3. **Unsafe RPC null:** `imageLinkUrl:null` causes Map.copyOf failure before handler runs; new clear intent must be routed as non-null flag.
4. **Writer races:** `AddMarquee` presently checks ownership outside its transaction, `UpdateMarquee` checks `version`, `DeleteMarquee` currently does not, and old `AddMarquee` type conversion must be removed for IMAGE.
5. **Reader data loss:** web projection drops valid IMAGE Marquee; client selection filter likewise hides it. Both must change before activation.
6. **Misnavigation:** linked media click must not trigger month/source selection or drag-and-drop; fallback `Open image directly` is **not** the external destination.
7. **Rollback:** existing binaries are demonstrably unaware of new URL/IMAGE-Marquee combinations; switching back to them after new writes is unsafe even with additive schema.

## Evidence classification

**Passed as source inspection:** above named code paths read; client Day reader existing `Image N` state confirmed; old RPC null problem reproduced from bundled `Map.copyOf` source. **Not run:** responder JUnit, Angular tests, reader tests, local integration, DB query, MQTT replay, actual link/Marquee 4-way synthetic runtime test, production deployment or mutation. Refer to the matrix for future test IDs and expected evidence; do not mark them passed.
