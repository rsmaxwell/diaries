# 0054 Step 2 — Shared fragment reordering

Status: **IMPLEMENTED IN REVIEW PACKAGE; VERIFICATION PENDING**.

## Scope

Extract the duplicated DATED Day Reader and annual PREAMBLE/EPILOGUE drag-reorder rules into an Angular singleton `FragmentReorderService`.

- `plan` validates indices, clones live fragments, uses neighbour-based sequence keys and prepares a contiguous optimistic display list. It does not mutate retained model objects.
- `persist` locks the moved fragment, publishes the existing `updateFragment` RPC and releases the lock on RPC failure. Successful `updateFragment` releases the lock and normalises sequences on the responder.
- Day Reader retains its `MatTableDataSource`, selection, 401 sign-in redirect and existing error notifications.
- Annual editor retains its year/placement MQTT subscriptions, editing restrictions, error notification, busy state and pending group refresh.
- No MQTT schema, responder, database, HTML markup, CSS, or Day Reader fragment navigation changes.

## Source/test changes

- Add `diaries-client/src/app/fragment/fragment-reorder.service.ts` and its unit tests.
- Refactor `diaries-client/src/app/dayview/dayview.component.ts` to call service.
- Refactor `diaries-client/src/app/diary/annual-editor/annual-editor.component.ts` to call service.
- Update `annual-editor.component.spec.ts` fixture with the shared service.
- Preserve existing Day Reader and annual reorder regression tests. Add service tests for DATED/annual moves, midpoint and edge sequences, lock denial, failed RPC unlock, no mutation.

## Verification required on Windows checkout

1. Apply review ZIP at Diaries parent root using Beyond Compare; inspect existing local changes before replacing any file.
2. From `diaries-client`, run `npm run build` and `npm test -- --watch=false --browsers=ChromeHeadless` (or the project's supported Angular test invocation).
3. In development Editor, reorder the two 1830 EPILOGUE fragments. Check both Editor and refreshed Reader order.
4. In development Day Reader, reorder two DATED fragments. Check order and retained state.
5. Confirm lock-denial/RPC-error tests pass, list rollback behaves correctly, and the normal edit/save workflow still works.

No tests executed in this packaging environment (Angular dependencies are not installed). Existing user evidence for earlier Step 2 checks is unchanged. The feature remains OPEN.
