# 0034/0036 mango closure evidence — protected archive record

Date: 2026-10-18 (UTC). Source host: `mango`; staging/held snapshot host: `mars`; receiving host: `backup`.

- Archived data: `closed-0034-0036-evidence-20261018.tar.gz`
- Checksum sidecar: `closed-0034-0036-evidence-20261018.sha256`
- Source copy: `/home/richard/feature-evidence-archive/` on `mango`
- Local Btrfs copy: `/media/usb/@data/backup/mars/home/richard/feature-evidence-archive/` on `mars`
- Held Btrfs snapshot ID: **`20261018-165453Z`** (includes `@data`); hold reason: `Permanent 0034/0036 mango closure evidence archive`
- Off-site received snapshot: `/@data/mars-received/@data/20261018-165453Z` on `backup`
- Off-site receipt: `/@data/mars-received/.replication-state/20261018-165453Z.json`
- Archive inside received snapshot: `/@data/mars-received/@data/20261018-165453Z/backup/mars/home/richard/feature-evidence-archive/closed-0034-0036-evidence-20261018.tar.gz`

## Accepted verification evidence

1. `archive-mango-feature-evidence.sh richard@mars --collect-only` verified tar SHA-256 locally and on `mars`.
2. `--publish` created and held timestamp snapshot `20261018-165453Z`, sent incremental from parent `20261018-030006Z`; receiver returned `ACCEPTED`.
3. On `backup`, `sudo sha256sum -c closed-0034-0036-evidence-20261018.sha256` returned `...tar.gz: OK`.
4. On `backup`, `sudo tar -tzf ...` succeeded and enumerated **140** archive entries, including the 0034 step-11 collections and 0036 Gate B/D material.

The sidecar checksum supplies the authoritative exact digest; do not manually transcribe or assume a digest. The source cleanup procedure additionally verifies the file contents on `mango` against every archived file and refuses unexpected files.

## Retention policy

Keep the `mars` snapshot **held** and the corresponding off-site received snapshot **protected**. Do not remove either snapshot or its receipt during normal housekeeping. Check that future changes to off-site pruning explicitly respect this retained checkpoint.

## Cleanup status

The separately supplied `cleanup-mango-feature-evidence.py` defaults to a dry run. Only an explicit interactive `--apply` deletes the corresponding original 0034/0036 evidence entries on `mango`. It never modifies the archive directory or either snapshot. Record actual cleanup console results before marking removal complete.
