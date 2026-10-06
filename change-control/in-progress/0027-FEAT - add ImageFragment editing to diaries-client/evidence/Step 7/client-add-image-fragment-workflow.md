# Client Add Image Fragment workflow contract

## Entry point

The page header emits a dedicated `addImageFragment` action. It does not overload the existing `add` event used by **Add fragment with default marquee**.

Availability is derived from `canAddImageFragment(diary, page, fragment)` and requires:

- positive diary ID and non-empty diary name;
- positive active Page ID belonging to that diary;
- a selected Fragment with authoritative `pageId` equal to the active Page;
- valid selected Fragment year/month/day;
- finite Fragment sequence.

Both MARQUEE and IMAGE Fragments can provide the source chronology context.

## Chooser boundary

The workflow captures the source context and opens:

```text
path: /<diary.name>/images
select: true
selectionMode: catalogue-image
```

The chooser contract established in Step 4 means directories and uncatalogued files cannot provide Fragment identity. Creation additionally checks that the returned `imageId` is a positive integer.

No Fragment lock is requested while the chooser is open or during creation.

## Cancellation

An undefined/empty chooser result returns immediately:

```text
no addImageFragment RPC
no Fragment selection change
no Marquee selection change
no navigation
```

## Context revalidation

After a catalogue Image is selected, live context is read again. Creation proceeds only if:

- the same source Fragment ID is active;
- the same Page ID is active;
- the same diary ID is active;
- source year/month/day are unchanged;
- the refreshed context still satisfies the authoring predicate.

Sequence/version changes that do not move the Fragment to a different day do not force an abort. The latest sequence list is used when calculating the insertion point.

## Common chronology

The old MARQUEE-only private gap calculation was extracted to `nextFragmentSequence()` and is now called by both creation paths.

For source sequence `1000` followed by `2000`, both paths choose `1500`. At the end of a list they retain the historical `+1000` fallback.

## Create request

The normal first-release UI always supplies the selected persisted Image ID:

```text
pageId    = active Page
year      = source Fragment year
month     = source Fragment month
day       = source Fragment day
sequence  = shared common-chronology gap calculation
text      = ""
imageId   = selected positive catalogue Image ID
```

The client sends exactly one call to `RpcService.addImageFragment$()` for the user action.

## Success

The reply must be an explicit IMAGE Fragment with `marqueeId=null` and an authoritative `pageId`.

On success the client:

1. updates Page selection to the returned `pageId`;
2. selects the returned Fragment ID;
3. clears Marquee selection;
4. navigates to `/diary/<diaryId>/<returnedPageId>/<fragmentId>`;
5. does not push the reply into the day list — retained MQTT state remains authoritative.

## Errors and non-idempotency

- `403` -> `ImageFragment authoring is disabled in this environment.`
- `500` or timeout/unknown transport status -> tell the user that creation outcome could not be confirmed and to refresh before retrying.
- other errors -> generic create failure.

There is deliberately no retry operator around creation. `addImageFragment` is not idempotent and a responder publication failure may occur after the database commit.
