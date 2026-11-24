# 0028-FEAT — Original page-scan Docker I/O failure and volume-backed correction

Date: 2026-11-23. Status: **proposed correction; live acceptance pending**.

## Evidence and diagnosis

- The 41 original scans were staged in private Step 2 evidence and their SHA-256 values were independently verified; the NAS originals were unchanged.
- Nginx on the isolated backend returned HTTP 500 even when queried directly from the proxy container. Its logs showed `open() ... img2839.jpg failed (5: I/O error)`, not 404 or an upstream proxy error.
- Reader `/health/ready` stayed HTTP 200. Responder's 71-fragment replay and all 22 preserved Marquees had already passed.
- The Windows filename mounted into the old Nginx scan sidecar is approximately 290 characters long for `img2839.jpg`. This is a **plausible** Docker Desktop Windows bind-mount/file-sharing issue; the exact underlying Windows error is not proven by the Nginx log.

## Correction

The existing Step 2 source-scan verification script now streams **the 41 already-staged files** via `tar` to `docker cp -` into a labelled, Docker-managed local volume. A temporary container has **no network** and mounts the volume writable only during import/verification. Docker's own `sha256sum -c` verifies each file. The temporary loader is then removed.

The existing disposable source-scan Nginx container is first checked for its expected label, image, isolation and mounts; only that container is replaced with a service whose media volume is mounted **read-only**. The proxy, Reader, responder, broker, PostgreSQL 18 isolated database and all production services remain untouched. On rerun, an existing labelled volume is revalidated; an invalid or partially populated volume is not overwritten automatically.

An updated **explicitly-confirmed** isolated replay cleanup command removes only the labelled new scan volume after stopping its labelled consumers. It does not remove the isolated PostgreSQL volume or any private evidence.

## Acceptance

- Existing staged scan identities and SHA-256 values pass. No re-copy from NAS.
- Docker volume identity, labels and exact 41-file manifest validated. No foreign container attachments.
- Source scan Nginx runs backend-only, serves from the read-only volume and returns HTTP success for all 41 scan URLs; the HTTP bytes of `img2839` and `img2840` match their recorded digests.
- Reader stays HTTP 200; migration journals remain 71/71 and Marquee fingerprint is unchanged.
- Browser visual acceptance and interactive Angular Editor GUI acceptance remain separate.
- **Production apply remains prohibited.**

Run on **Windows PC, Cygwin** at the Diaries parent repository root:

```bash
bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/verify-0028-step2-source-scans.sh'
```

No production dump, migration apply, MQTT replay, or image-catalogue mutation is involved.
