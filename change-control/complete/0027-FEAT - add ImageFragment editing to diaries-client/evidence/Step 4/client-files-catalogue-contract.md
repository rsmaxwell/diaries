# Step 4 client Files/Image catalogue contract

The client now treats filesystem location and reusable Image identity as separate concepts.

## `FileEntry`

`listFiles` entries retain the existing filesystem fields and may additionally carry:

```text
imageId?: positive persisted Image id | null
image?: retained/catalogue Image metadata | null
```

A file is attachable to an IMAGE Fragment only when `imageId` is a positive integer. Filename and URL are presentation/location data and are never used to derive database identity.

## `UploadFileResponse`

The upload RPC is typed separately from a `FileEntry`, matching the responder's additive response:

```text
name
subdir
size
path
url
imageId
image
```

Generic/non-image uploads retain `imageId=null` and `image=null`.

## Files dialog selection modes

The historical `{ select: true }` mode is unchanged and returns exactly:

```text
{ url, name }
```

The new explicit catalogue mode is requested with:

```text
{ select: true, selectionMode: 'catalogue-image' }
```

Only files with a positive `imageId` can close the chooser in this mode. A successful selection returns:

```text
url
name
imageId
image       optional metadata/null
relativePath optional when metadata supplies it
```

Uncatalogued files remain visible so the user can understand the directory contents, but are visually dimmed, marked `aria-disabled=true`, and clicking them does not open or select them. Normal browse/delete behaviour remains available outside catalogue selection mode.
