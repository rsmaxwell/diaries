# 0047-FEAT — Step 2 installation-equivalence acceptance

**Decision:** ACCEPTED (11 November 2026), based on final corrective and
idempotent application against accepted 0045 installed-state baseline.

## Corrective timeline

1. First attempt with Playbooks `833da94`: `backup-collection.yaml` on
   `mars` returned `changed=2`, with the two rsync copy tasks changing
   timestamp and permissions on filter files. The gate correctly failed.
2. Rejected blanket `--chmod` rules; adopted source-specific modes with
   archive-mode rsync and `--omit-dir-times`. On `mango`, restored all 14
   historical source modes (five directory modes `0750`; nine filter file
   modes `0664`) after hash validation. Source regression and deployment
   syntax check passed; published Playbooks `dca638c`.
3. The first correction apply on `mars` reported exactly the two expected
   filter-copy changes, now permission-only in rsync itemized output. The
   guard accepted only those named tasks; static installed-state comparison
   immediately afterward matched the 0045 baseline on both endpoints.
4. The second consolidated normal apply returned **zero changes, failures
   and unreachable hosts** on the `mars` collection play and the `mars`/
   `backup` native replication play. Filter synchronization stdout was empty.
5. Final installed-static fingerprint comparison passed for `mars` and
   `backup`. Five systemd `ExecStart` history digests were reconciled as
   runtime-only, with unchanged installed units and loaded properties.
   Docker signing key remained SHA-256
   `1500c1f56fa9e26b9b8f42452a553675796ade0807cdce11975eb98170b3a570`.
   Read-only Btrfs health checks on both hosts passed.

## Accepted idempotence recaps

| Target | Normal apply | Changed | Failed | Unreachable |
|---|---|---:|---:|---:|
| `mars` | `backup-collection.yaml` | 0 | 0 | 0 |
| `mars` | `btrfs-replication.yaml` | 0 | 0 | 0 |
| `backup` | `btrfs-replication.yaml` | 0 | 0 | 0 |

## Durable evidence paths (existing files under this feature)

- `evidence/Step 2/metadata-correction-20261111-160642Z/`
- `evidence/Step 2/deployment-20261111-160900Z/`
- `evidence/Step 2/source-mode-restoration-*.txt`
- `reports/STEP2-SOURCE-MODE-PRESERVATION-20261111.md`

The accepted comparison scope is the schema-v2 0045 static managed-asset
baseline. Historical runtime execution-history digests are not proof of
changed installed unit content; full replication, snapshot restoration and
destructive retention were not rerun, based on prior accepted correctness.

**Residual constraint for 0048:** Git does not version group-write or
specific directory modes. Source-mode restoration on a fresh `mango` clone
may remain necessary until the 0048 permission-requirements review proves
otherwise. This is explicitly tracked, not silently assumed away.
