# Step 12 development-run compilation fix — 2026-10-03

The first Step 12 run in the normal Windows development tree reached Angular bundle compilation successfully, proving that the local test runner and dependencies are available. The run then stopped on TypeScript compilation errors in two tests introduced/modified during earlier 0027 steps.

## Fix 1 — Files dialog compatibility DOM typing

`files-list-dialog.compatibility.spec.ts` called the generic DOM method `querySelectorAll<HTMLAnchorElement>()` through `fixture.nativeElement`, whose type is `any` in the Angular fixture API. Under the Angular compiler this produces TS2347 and causes the resulting array elements to become `unknown`/`{}`.

The test now first narrows `fixture.nativeElement` to `HTMLElement`, then calls the typed DOM API through that value:

```ts
const element = fixture.nativeElement as HTMLElement;
const cards = Array.from(element.querySelectorAll<HTMLAnchorElement>('a.file-card'));
```

This preserves the test semantics and makes `datedCard`/`plainCard` correctly typed as `HTMLAnchorElement`.

## Fix 2 — complete CatalogueImage fixture

`image-fragment-reference.accessibility.spec.ts` constructed a `CatalogueImage` with only `id`, `version`, `relativePath`, and `mimeType`. The production `CatalogueImage` contract also requires:

- `originalFilename`
- `width`
- `height`
- `checksum`
- `caption`
- `altText`

The test fixture now supplies all required metadata fields. No production model is weakened and no runtime code changes are made.

## Scope

This correction changes only two existing test files plus Step 12 evidence/documentation. There are no production client or responder changes.

## Next verification

Re-run from `diaries-client`:

```bat
npm test -- --watch=false --browsers=ChromeHeadless
```

Step 12 remains open until that run is green (or exposes further regressions that must be fixed).
