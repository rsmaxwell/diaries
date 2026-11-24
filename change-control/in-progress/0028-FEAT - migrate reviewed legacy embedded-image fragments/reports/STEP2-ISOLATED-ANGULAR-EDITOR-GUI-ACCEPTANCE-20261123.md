# 0028-FEAT — Isolated Angular Editor GUI acceptance

Status: **IMPLEMENTED, OFFLINE-VERIFIED; LIVE GUI ACCEPTANCE PENDING** (23 November 2026).

## Starting point and already accepted evidence

- 71 approved conversions and one DEFER (Fragment 1564) passed the isolated PostgreSQL 18 rehearsal, rollback/restart and idempotence.
- Replayed retained MQTT state passed 71/71 Fragment and 22/22 Marquee checks.
- Read-only Reader HTTP and original manuscripts `img2839` and `img2840` passed. Forty-one original page scans were copied privately, verified by SHA-256, loaded into a labelled read-only Docker volume, and served through the existing localhost gateway.
- Owner independently confirmed that the three Whitley Park maps come from distinct Fragments: 84 (MARQUEE), 2334 (IMAGE) and 2332 (IMAGE). Preserve all three.
- Owner accepted Marquee location/size changes occurring after the frozen review, while requiring missing, replaced, added or reassigned Marquees to fail. The conversion must not itself alter current geometry.
- None of these already accepted tests need repeating. The production migration remains **NOT AUTHORISED**.

## Isolation design

The Editor is built from the **current Windows `diaries-client` checkout** into a local-only Docker image. We do not modify the client submodule or publish the image. The runtime config overrides its original development `assets/config.json` **inside the disposable container**:

- Browser URL: `http://127.0.0.1:58083/diaries/`
- Browser MQTT: WebSocket `/mosquitto/` on the **same** localhost origin, MQTT protocol v5.
- Browser responder: `/diaries-responder` on the same localhost origin; source scans and catalogue image endpoints route into already isolated services.
- A dedicated, locally built Node `ws` binary WebSocket-to-TCP bridge connects **only** to `diaries-0028-replay-broker:1883` on the **internal** Docker network. The bridge publishes no host port.
- The Editor Nginx runtime and bridge are **backend-only**. The new, labelled Nginx Editor proxy is the only additional dual-homed component and exposes **only `127.0.0.1:58083`**. The previously accepted Reader proxy at ports 58081/58082 stays untouched.
- Original scans remain in the isolated Docker-managed volume. The restored PostgreSQL 18 dataset, migration journal, reader and broker are reused unchanged.

An Angular Editor sign-in does authenticate through the copied production data's responder RPC. To avoid reusing real passwords during this test, you may register and use a **new disposable rehearsal-only account** through the isolated Editor at the localhost origin. Registration modifies only the isolated DB copy; it does not create a production user. Credentials should not be copied into reports or screenshots. Do not use browser session tokens from your production Editor tab.

## Start — Windows PC, Cygwin terminal

From the authoritative Windows Diaries parent working copy:

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/start-0028-step2-isolated-editor.sh'
```

The script checks branch/revision, submodule status, existing labelled Docker networks and containers, accepted journal counts, Marquee fingerprint, original scan availability, Reader readiness and free port `58083`. It builds two local images, starts three **new, labelled** disposable containers without replacing existing ones, then calls an independent verifier. It never runs a database migration or publishes a Docker image. Failure leaves labelled containers and private diagnostic evidence for inspection; **do not rerun start** if some already exist.

For read-only re-verification after a completed start:

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/verify-0028-step2-isolated-editor.sh'
```

## Manual GUI acceptance (record real outcomes, not planned outcomes)

1. Open a fresh Edge InPrivate window, not the signed-in production Editor session. Open `http://127.0.0.1:58083/diaries/`. Verify the `assets/config.json` is rehearsal-only and the `/mosquitto/` socket connects (see DevTools Console/Network). Neither `pluto.rsmaxwell.co.uk` nor your normal development MQTT URL should appear in its network requests.
2. Sign in with a separate rehearsal identity if available; alternatively register a new throwaway account **only in this localhost app**. Do not use an existing production browser tab or copy its access tokens.
3. Open `http://127.0.0.1:58083/diaries/diary/1/692/85` (1828 March 20). Confirm the original manuscript `img2840` on the left, selected original Marquee highlight, and the diary content and images on the right. Verify the unchanged distinct Fragments 84, 2334 and 2332 and their existing captions.
4. Navigate to one or more migrated IMAGE Fragments (for example IDs 680 and 1251, using their authoritative Page IDs), and verify actual catalogue Image IDs, captions, links, Page membership and sequence. They should be IMAGE Fragments, not legacy embedded HTML pictures.
5. Review at least one preserved Marquee associated with a converted image. Its existence and association must match the review, while its **current** position and size (possibly updated after the review) must remain intact.
6. Test a read-only selection, navigation and image-viewer zoom/pan. Check no browser console errors, failed MQTT RPCs or unexpected calls to live services.
7. For interaction/locking acceptance, exercise edit **entry and Cancel** on a non-migrated scratch entry. If you choose to save a controlled test edit, do so only on the **isolated DB copy**, record exactly which Fragment changed, and understand that the earlier unchanged-DB baseline will no longer apply until reviewed. Never edit production for this test.
8. Capture screenshots and browser console/network findings inside `change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/evidence/Step 2/private/`. Do not place login credentials, tokens or private manuscript images in public Git history.

## Acceptance gates

The offline tests and initial automated isolated Editor HTTP + MQTT v5 smoke may pass before the manual GUI checks. **Neither is a substitute for owner-observed visual and functional acceptance.** The GUI step remains OPEN pending that evidence. Production preparation, approval and apply remain separately gated; no test script authorises production changes.

## Cleanup

The existing `tools/remove-0028-mqtt-replay.sh --confirm-remove-isolated-replay` is extended to include the new Editor proxy, runtime and WebSocket bridge, and still checks labels. It removes only the disposable replay services, source scans volume and bridges; it does **not** remove the isolated PostgreSQL database/volume, NAS data or private evidence. **Do not run cleanup until GUI acceptance is complete.**
