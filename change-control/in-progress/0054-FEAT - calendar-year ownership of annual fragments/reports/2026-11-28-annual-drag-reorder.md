# 0054 Step 2 — Annual fragment drag-and-drop ordering

Status: IMPLEMENTED IN REVIEW PACKAGE; verification pending. Step 2 remains OPEN.

## Behaviour

PREAMBLE and EPILOGUE use the DATED Day Reader-style row treatment, left-hand ⠿ drag handles, and Angular CDK vertical drag-and-drop. Reordering is limited to the current calendar year and section; it is disabled while editing or during another RPC. The moved item acquires its fragment lock and uses the existing updateFragment RPC with a midpoint/end sequence. Retained MQTT supplies the canonical new order. On failure, the original order is restored, the held lock is released and an error is displayed. Existing Edit/Delete features remain. Up/Down controls are replaced by the drag handle.

## Verification required

1. `diaries-client`: `npm run build`; run existing Jasmine/Karma tests with the repository's supported browser runner.
2. In development editor, drag EPILOGUE 2356 above 2355 for 1830; check Editor and development Reader ordering, including refresh.
3. Drag back; verify other years and PREAMBLE lists are unaffected.
4. Confirm Edit/Delete and Save failure/retry still function and a drag is not offered during editing.
5. Test failed reorder RPC with responder unavailable, then retry after restart.

Source basis: supplied 2026-11-27 Diaries bundle plus current 0054 Step 2 edits already prepared during this conversation. The user's live Windows checkout and build have not been accessed.
