# Step 3L — Read-only Btrfs rehearsal preflight

Status: preflight source implemented; execution on mars pending. Step 3 remains OPEN.

The preflight inspects /media/usb as a dedicated Btrfs mount, verifies the existence of /media/usb/@data, rejects an existing or symlinked /media/usb/@data/0040-step03l-rehearsal directory, and checks required utilities. It does not create, modify, or delete any filesystem object.

Local regression on implementation workstation: 4/4 tests PASS. No test has yet been run on mars. The next acceptance gate is the read-only preflight result from mars. Any actual disposable subvolume create/delete must be separately designed and approved, and must not touch production replication datasets.
