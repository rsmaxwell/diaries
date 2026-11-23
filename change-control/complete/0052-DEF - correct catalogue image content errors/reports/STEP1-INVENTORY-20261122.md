# 0052-DEF Step 1 inventory, 22 November 2026

Step 1 is open. Live inventory and Whitley Park candidate selection are pending.

| Component | Windows checkout revision |
| --- | --- |
| Diaries parent, main | 0818179be4b207bcd9600e1e70c4870f6f9823d4 |
| Client | 4faeac6af36913a947e7947c7adb17856bd86e19 |
| Responder | 4109c37eb64ea8f8f513a439628d75145f658634 |
| Web | 6d1b289bc5a7983cbf36fe771f8c11dc4725813b |

The parent already contained local changes. The three application submodules matched the parent gitlinks and had clean working trees.

The 11:27 UTC Hermitage diagnostic manifest recorded the selected source as a 935,720-byte PNG at 720 x 480, SHA-256 9cbe68505a023ad9db4898914c5bf763cce4fb33b6689364586350d58d6411e0. Both Files copies then held the old 3,840,009-byte PNG, SHA-256 2097979bd1ca47370a55c0f6053167a96f541a5c04adfe4ff52dc564ccc97d5a. The manifest predates the final copy into metadata images. The later match is recorded in the evidence notes. Rehash all four copies and capture fresh St Isaac and Jordan Staircase baselines.

The preserved 0028 draft (91) contains the Hermitage filename. Neither Hermitage hash nor the reported Whitley Park source basename appears literally in the draft. Trace both images through the frozen inventory and review inputs by fragment, Image ID and actual URL before deciding which records need review. The draft was left intact.

## Whitley Park NAS inventory

Read-only SSH output captured from the owner's Windows Command Prompt confirmed that the metadata source and production Files copies of img2840-image-map-whitley-park.jpg are both 97,518 bytes and share SHA-256 0ec1199bb262f2c720737a6fcd71549549ea8727784d5b09e3602fcd6d2d69ba. This establishes the NAS file baseline. The live HTTP response and catalogue row still need verification.

The reported prefix resolves to the directory metadata/images-root/source/img2840-whitley-park-map/. Its PNG files are:

| Filename | Bytes | SHA-256 |
| --- | ---: | --- |
| map2026-11-21_085923.png | 24,767,056 | f62302468687a82367fc72e1890bcc7b956c06170b9e65e72f07b878cda231b8 |
| whitley-park-historical-map.png | 3,798,628 | bc681da1dc800ceb55212d65b3b957250945d346280c9686bebac96bace411c2 |
| whitley-park-modern-map.png | 71,106 | b58871fa9d61fdc39e9638508d9020568365f3ebfb6bd83d456a8752ec404ffd |

All three SHA-256 values were captured over SSH. The NAS does not have the file utility. PNG signature, dimensions and visual selection are pending.

## Pending live checks

- The automated session could not access the NAS directly. Use the working SSH alias from the owner's Command Prompt to hash and identify the listed candidates, inspect them at full resolution and record the selection.
- The configured SSH hostname for pluto did not resolve. Record the production deployment and recovery-point identities, then inspect the catalogue, fragment references, retained topics, served URLs and storage paths.
- Docker denied access to the local engine. Identify the active development mode and database/Files pair, then perform the equivalent read-only inspection. Resolve Hermitage by canonical path separately in each database.

No live data changes were made.
