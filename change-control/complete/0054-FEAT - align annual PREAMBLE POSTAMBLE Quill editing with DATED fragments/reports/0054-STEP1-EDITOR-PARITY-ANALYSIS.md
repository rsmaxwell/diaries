# 0054-FEAT — Step 1: Quill editor parity analysis and proposed contract

**Review date:** 26 November 2026  
**Review status:** Static source analysis complete; functional contract **proposed for owner acceptance**. Step 1 remains OPEN until that acceptance.  
**Source of truth:** `diaries-sources-20261126-190728.zip`, generated at 2026-11-26 19:07:35 UTC. This is newer than the source bundle cited in the feature README.  
**Scope of this deliverable:** Documentation only. No application changes, builds, deployments or browser tests performed.

## 1. Repository evidence supplied with the source bundle

The bundle includes `SOURCE-REVISIONS.txt`, captured from the Windows working copy. Its results, not a fresh Git command run by this review, are:

| Checkout | Branch | HEAD | Status at capture |
|---|---|---|---|
| Diaries parent `diaries/` | `main` | `f79c3f0a641103cfa2913dfbb784583650b300c1` | `?? change-control/in-progress/` |
| `diaries-client/` | `main` | `cc826a8254b0e6d989755dc880d3023dae9e3416` | No reported changes |
| `diaries-responder/` | `main` | `a49c6abd0ce005d58eb516770f6515313e40cdf6` | No reported changes |
| `diaries-web/` | `main` | `363ca8f425b811eeedff47486092b1f63c403ab0` | No reported changes |

`.gitmodules` names those three submodules using parent-relative Git URLs. The bundle excludes Git internals; run `git status` and `git submodule status` again on Windows before applying source changes in Step 2. Preserve the untracked `change-control/in-progress/` work, including 0054 itself.

## 2. Current behaviour and gaps

| Area | DATED TEXT editor | PREAMBLE / POSTAMBLE TEXT editor | Gap / implication |
|---|---|---|---|
| Quill availability | `ngx-quill`, HTML form content | `ngx-quill`, `format="html"`, for both creation and editing | Quill **already exists** in annual editor; do not reinstall it |
| Toolbar | Bold/italic/underline, headings, lists, links, image, font, size, text/background colours | Bold/italic/underline, headings, lists, links | Additional controls differ; annual IMAGE Fragment is a distinct catalogue-backed object |
| Presentation | Dedicated responsive SCSS; panel height, toolbar, typography, focus/lock/read-only cues | Annual editor has no component stylesheet; Quill appears within the annual list/form | Visually and ergonomically different |
| Dirty state | Compares canonical Quill Delta operations; avoids treating equivalent HTML serialisation as an edit | Compares `editText !== fragment.text` raw HTML | Opening/re-saving untouched HTML may cause needless writes / version updates |
| Existing legacy HTML images | Resolves `images/<filename>` URLs before editing, restores original references on save | Passes fragment HTML straight into Quill; preview uses Angular `[innerHTML]` | Existing markup/image URLs require regression coverage before making changes |
| Locks | Reactive dirty/lock reconciliation and serialised transitions | Explicit `lockFragmentForEdit` on Edit; Save or Cancel unlock; failed Save keeps lock for retry | Need to protect unchanged/cancel/retry/navigation; do not assume DATED and annual state machines are interchangeable |
| Server updates | `updateFragment$` | Same update RPC for edit; `addAnnualFragment$` for creation | Preserve annual identity (diary/year/placement) and retained MQTT flow |
| Validation | No annual-only length rule | `AddAnnualFragmentRequest` checks max 4096 HTML chars; annual edit checks max 4096; responder add checks 4096 and Fragment DB text has `@Column(length = 4096)` | Show helpful limit/error for both create/edit, reject before RPC, never truncate |
| Tests | `text-panel.component.spec.ts` exercises editor/lock scenarios | Annual model/request tests exist, but **no** `annual-editor.component.spec.ts` in snapshot | Add component tests before claiming parity |
| Reader | Uses HTML sanitizer for DATED text | Uses the **same** sanitizer for annual text | Rendering can be tested consistently; current sanitizer removes arbitrary inline `style` and only allowlists some Quill classes |

Directly examined: `diaries-client/src/app/diary/annual-editor/annual-editor.component.{ts,html}`; `diaries-client/src/app/fragment/text-panel/text-panel.component.{ts,html,scss,spec.ts}`; `diaries-client/src/app/model/annual-fragment-request.ts`; `diaries-client/src/app/utilities/legacy-fragment-html.pipe.ts`; `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/{handlers/AddAnnualFragment.java,handlers/UpdateFragment.java,model/Fragment.java}`; `diaries-web/src/main/java/com/rsmaxwell/diaries/web/{http/WebServer.java,rendering/FragmentHtmlSanitizer.java}`.

### Specific implementation hazards

1. **Read/edit/write round-trip:** Quill normalises markup when loading it. The annual component currently sees a bytewise text difference and may overwrite unchanged stored HTML. Keep the original server HTML for a true no-op, and use a semantic dirty comparison for edited HTML.
2. **Reader fidelity:** The shared Reader sanitizer allows basic HTML, links, images and selected Quill alignment/size classes; it strips arbitrary CSS styles, such as text/background colour and some font markup. Exposing those controls without safe Reader support would create a misleading "saved but not displayed" experience.
3. **Image semantics:** The DATED editor's `image` control opens `FilesListDialogComponent` and inserts an HTML image reference. Annual `IMAGE` Fragments refer to catalogue Image IDs and carry their own metadata. Treat these as distinct facilities; do not silently switch annual images to a different storage model.
4. **Lock transitions:** Annual edit starts only after explicit lock acquisition. Save succeeds through `updateFragment$` (which clears the lock); Cancel/unchanged save use explicit unlock. Failed updates deliberately retain the edit buffer/lock for retry or cancel. On destroy a best-effort asynchronous unlock is issued. Group/input transitions and failed release must be tested, without racing an in-flight save.
5. **Create vs edit:** Both Quill bindings must share the same rules; the create path currently delegates its length exception to a request constructor while the edit path checks explicitly.

## 3. Proposed functional contract for owner acceptance

**A. Common TEXT editing experience.** Keep separate create/edit controls but align them with DATED Quill's formatting experience, responsive sizing, typography and keyboard usability. Both PREAMBLE and POSTAMBLE must behave identically. Extract a shared toolbar definition only where it avoids drift without a large editor refactor.

**B. Formatting.** Support the DATED text-format controls: bold, italic, underline, headings, ordered/bullet lists, links, font, size and foreground/background colours. Before claiming fidelity, either make the existing Reader sanitizer safely preserve any added formatting (allowlisted classes/styles only), or omit controls that cannot display reliably in the Reader. Do not weaken the sanitizer to arbitrary HTML/style acceptance. This is a narrowly scoped compatibility correction, not a Reader redesign.

**C. Embedded images — deliberate exception.** **Do not add the DATED file-picker/image-insertion toolbar button to annual TEXT in 0054.** Preserve annual IMAGE Fragment creation and catalogue linkage as the supported new-image workflow. Existing inline `<img>` markup in stored annual TEXT must not be lost merely by opening/cancelling/unchanged saving. Reconsider new inline image insertion only as a separate explicit policy decision.

**D. Persistence and unchanged content.** Persist HTML through the existing annual add/update RPCs and retained topics, with no schema change or migration. When semantically unchanged, exit the edit safely without rewriting canonicalised HTML. When editing legacy markup, preserve existing relative-image reference semantics and avoid inserting deployment-specific URLs.

**E. Lock lifecycle and errors.** Keep the annual explicit Edit / Save / Cancel model (different from DATED auto-lock-on-dirty). Do not allow edits before a lock is granted. Show meaningful locked/failed state. Successful update releases lock as part of server transaction; unchanged save and Cancel explicitly release it; failed Save keeps user content available for retry or Cancel. Navigation or group change releases an owned lock and never races in-flight save/unlock operations. Failed unlock must be visible/recoverable rather than silently treated as success.

**F. Validation and regression.** Apply the current 4096-character limit to **serialised HTML** for create and edit; count consistently with the current client/server contract and never truncate. Preserve annual year, placement, order, IMAGE catalogue/link operations, existing DATED editing and Reader rendering. Add focused annual component tests for these behaviours, followed by consolidated browser checks.

## 4. Step 2 implementation shape after contract acceptance

Prefer one coherent change package: (1) small shared Quill toolbar/configuration where sensible, (2) annual editor TypeScript, template and SCSS improvements for both create/edit, HTML no-op detection, lock transitions, validation and error UX, (3) minimal Reader formatting policy/style compatibility only if needed for the agreed formatting controls, and (4) focused Angular tests plus any affected Reader test. Keep all change-control documentation in this 0054 directory. Do not change responder annual schema, add migrations, or modify the Image Catalogue lifecycle.

## 5. Consolidated acceptance tests for Step 3

- PREAMBLE: create formatted TEXT, save, navigate, reload, edit/cancel, save again; verify actual HTML and Reader output.
- POSTAMBLE: repeat new/existing TEXT workflow, including links, font/size/colours where supported, and 4096-character boundaries.
- Existing HTML: open/unchanged-save does not write transformed HTML; any legacy relative image references survive read/edit/save.
- Locks: denied lock, undo to unchanged, Cancel, Save failure/retry, failed unlock, year/placement/diary switching, navigation mid-edit and mid-save; no stranded lock.
- Regressions: annual IMAGE catalogue/link and ordering, MQTT retained refresh, DATED TEXT editor, Reader sanitizer, and multiple browser sizes.
- Record source revisions, build/test/browser evidence and rollback. No acceptance or deployment is asserted by this Step 1 analysis.

## 6. Gate position

**Step 1 analysis deliverable ready for review. Contract A–F is a proposal, not yet recorded as approved.** Keep `IMPLEMENTATION-STEPS.md` Step 1 OPEN until owner accepts this contract. On acceptance, implement the full coherent Step 2 increment rather than introducing extra artificial gates.
