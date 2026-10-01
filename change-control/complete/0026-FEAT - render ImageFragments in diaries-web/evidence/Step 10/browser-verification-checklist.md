# Step 10 focused browser verification checklist

Start the test-only mixed-media fixture with:

```powershell
.\gradlew.bat :diaries-web:runSyntheticSite
```

Open `http://127.0.0.1:18082/diaries/11/2026/09?fragment=33#fragment-33`.

1. Confirm Fragment 33 (MARQUEE) is selected, its source rectangle is visible, and **Fit selection** / **Use highlight style** are enabled.
2. Select Fragment 35 (IMAGE) on the same Page using mouse, then repeat using keyboard Enter/Space on its selector. Confirm the previous selected rectangle/dimming disappears, the Page remains visible, region-only controls are disabled, and the IMAGE row remains selected.
3. Use browser Back and Forward. Confirm MARQUEE 33 and IMAGE 35 are restored without a stale rectangle or stale `aria-pressed` state.
4. Select a MARQUEE on another Page (for example Fragment 34) and then return to IMAGE 35. Confirm the Page heading/source changes correctly and returning to IMAGE does not retain the other Page's selected region.
5. Use the generated Previous/Next fragment links. Confirm selection changes and keyboard focus remains visibly on the selected Fragment selector after the navigation link is replaced.
6. Open `http://127.0.0.1:18082/diaries/11/pages/22#fragment-33`. Select IMAGE Fragment 35. Confirm the selected Marquee disappears, the IMAGE article gains selected/pressed/current state, and the URL becomes `#fragment-35`.
7. Use browser Back/Forward on the source page. Confirm the earlier MARQUEE/IMAGE selection and URL hash are restored.
8. Because the synthetic fixture points catalogue media at `content.example.test`, allow the browser request to fail. Confirm the affected media figure shows `The image file could not be loaded.`, the broken image itself is hidden, and **Open image directly** remains a normal keyboard-accessible link.
9. Confirm a media-file failure does not replace an `Image unavailable`/`No image selected` retained-metadata message belonging to a different Fragment and does not change the left-hand source-image error/status text.
10. In the browser console, confirm there are no uncaught JavaScript errors during selection, history navigation or media failure handling.

Stop `runSyntheticSite` with Ctrl+C after the check. This fixture is read-only and does not connect the browser to MQTT or mutate NAS files.
