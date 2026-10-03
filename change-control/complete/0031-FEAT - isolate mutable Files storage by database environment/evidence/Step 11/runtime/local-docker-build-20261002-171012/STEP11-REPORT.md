# 0031 Step 11 runtime capture

- Mode: local-docker-build
- Captured: 2026-10-02T17:10:12.2814349+01:00
- Status: **FAIL**
- Database data: C:\Users\Richard\git\github.com\rsmaxwell\diaries-application\diaries\data\database\common
- Database backing: C:\Users\Richard\git\github.com\rsmaxwell\diaries-application\diaries\data\database\common
- Files selector: files-development-common
- Files backing: nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content/files-development-common
- Public Files route: /files/...
- Responder log captured: False

## Checks

- PASS - effective Files selector is non-production: files-development-common
- PASS - rendered Compose database mount matches the effective database data directory
- PASS - rendered Compose binds selected NAS subpath to /data/files
- PASS - rendered Compose keeps the shared /data/diaries mount read-only

## Error

Responder container is not available: diaries-local-responder
