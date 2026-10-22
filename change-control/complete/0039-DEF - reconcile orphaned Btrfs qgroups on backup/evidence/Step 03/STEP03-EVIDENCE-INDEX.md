# 0039-DEF — Step 03 accepted evidence index (interim)

**Recorded:** 2026-10-21. **Status:** Step 03 IN PROGRESS; evidence gates below accepted, remediation NOT authorised. This is a documentary reconciliation of operator-provided terminal transcripts and captures, not a new live test. No raw evidence or inventory content has been modified.

## Evidence storage contract

Keep all evidence beneath this defect, under `evidence/Step 03/`; historical Steps 01/02 stay unchanged. Operator captured the full manifests and identity documents *directly in the Windows Diaries working tree* at:

- `inventory/mars/qgroup-manifest.json` (73 KB; SHA256 `d743c95c8862411a872f217c48c3a6dd18d59a9a9a7ea86ccfae4f8dc2589b6c`)
- `inventory/backup/qgroup-manifest.json` (7.6 MB; SHA256 `ada3f6c59a5d58dfba4a49f1965daa75cf0e80b355eb01c70cafe890b94eecf5`)
- `inventory/mars/filesystem-identity.txt` (SHA256 `787313342f9c0a4f8f3d5bb1bab44b2efd4aecdcf83b68c46794c8f1fed9cca0`)
- `inventory/backup/filesystem-identity.txt` (SHA256 `cc85c290a0c4e76d83d81a44499d5f43d4d53821de7cd8dc7ca17cde8cbed9b6`)

**Important:** The latest uploaded Diaries source bundle predates these operator-generated captures and does **not** contain these four files. Preserve the actual files already on the Windows checkout; do not replace them with this documentation ZIP, and do not claim they are included in it. Keep future regression captures, terminal logs and acceptance records beside them under `evidence/Step 03/`.

## Accepted source and execution evidence

- Read-only `btrfs-qgroup-audit.py` source review: only `btrfs subvolume list -a`, `subvolume list -d`, and `qgroup show -pcre`, with a repeated active list; unknown formats fail closed. Neither quota mutation nor cleanup implemented.
- `mango` isolated regressions and `py_compile` and `git diff --check` passed after the multiword `Max referenced`/`Max exclusive` compatibility correction, and again after complete-manifest/targeted-ID enhancement. The 31,001-row stress fixture and failure cases passed (`note(20261021-113645).txt`, `note(20261021-114730).txt`).
- Live read-only audit on `mars`: 191 qgroups, 145 listed subvolumes, 146 active qgroups (including `0/5`), 21 unmatched candidates and 24 limited/protected, zero pending deletion. Fingerprint `84655523aaaf069a7f9501fe9c8e6bbc07997a8932dc4259757df153c9f1f9e3`. Targeted `0/20919` is `<stale>`, `unmatched-candidate`, no limit; `0/20920` is `<stale>`, `limited-protected`, `3.64TiB` max referenced (`note(20261021-114006).txt`, `note(20261021-114824).txt`).
- Live read-only audit on `backup`: 29,571 qgroups, 133 listed subvolumes, 134 active (including `0/5`), 15,475 unmatched candidates, 13,962 limited/protected, zero pending deletion. Fingerprint `6a197a84a7c4a59bdfb3ac9e347755f2bf86621556385f2b87da9ecda570adc3` (`note(20261021-114130).txt`). Older Btrfs output lacks `<stale>` annotation: absence of marker is not proof of no orphans.
- `note(20261021-115603).txt`, `note(20261021-115730).txt`: Cygwin captures into defect directory succeeded; both saved files passed JSON syntax checks and file hashes recorded.
- `note(20261021-115840).txt`, `note(20261021-120303).txt`, `note(20261021-120518).txt`: saved manifest summary and full record-level checks passed, including unique qgroup/subvolume IDs, count reconciliation, safety flags, conservative candidate invariants and both targeted IDs. Earlier ad hoc validation attempts (`note(20261021-120106).txt`, `note(20261021-120205).txt`) failed due to incorrect validator assumptions about actual list/field layout, not corrupted manifests.
- `note(20261021-120919).txt`: `btrfs quota status` unsupported on both hosts; this is a CLI compatibility error. Corrected capture used read-only `btrfs quota rescan -s`, which does not start a rescan.
- `note(20261021-121050).txt`, `note(20261021-121141).txt`: identity capture succeeded for both hosts; neither had a quota rescan running. `mars`: UUID `72d1d8ea-900e-4fca-837f-1b1febec036c`, `/dev/sdb1`, `/media/usb`, Btrfs 6.6.3. `backup`: UUID `b915f967-7cb4-4c14-b11b-f52209637a22`, `/dev/sda2`, `/`, Btrfs 5.16.2. Both mounted at top-level subvol ID 5. Capture times 12:10:30 and 12:10:32 UTC on 2026-10-21.

## Limitations / gates remaining

1. Produce a permanent, independently tested Playbooks validator of the saved complete manifest: uniqueness, counts, category invariants, recomputed fingerprint and identity mapping. The prior ad hoc tests did **not** recompute fingerprints or reparse raw Btrfs output.
2. Reconcile receiver read-only/received UUID/replication parent chains, `.replication-state` receipts, protected snapshots and operator holds against any *future* candidate proposal. The present manifests are observation-only and are not an authorised deletion list.
3. Document recurrence/root-cause hypothesis, supported remediation options, installed utility semantics, concrete rollback/recovery limitations, operational cost and a separate operator approval gate before any mutation. Consider supported OS/Btrfs updates independently; neither upgrade nor rescan is authorised.
4. Capture updated exact Git revisions, review Playbooks source regression and state, and record evidence closeout. The captures are not atomic and current filesystem state may evolve with normal scheduling.

**Decision:** retain Step 03 IN PROGRESS. No `btrfs qgroup destroy`, quota disable/enable/rescan, snapshot deletion, restore, scheduler or replication changes are approved. Existing Step 02 remains CLOSED.

## 2026-10-21 protection and offline validation addendum

Evidence subsequently captured in the Windows Diaries defect directory (not included in this ZIP, except for the two original terminal logs below):

- `inventory/{mars,backup}/manifest-validation.json`: permanent offline Playbooks validator reported `PASS` for both actual saved complete manifests (`note(20261021-125243).txt`). `mars`: 191 qgroups, 145 active subvolumes, 21 unmatched, 24 limited/protected, UUID `72d1d8ea-900e-4fca-837f-1b1febec036c`, fingerprint `84655523aaaf069a7f9501fe9c8e6bbc07997a8932dc4259757df153c9f1f9e3`. `backup`: 29,571 qgroups, 133 active subvolumes, 15,475 unmatched, 13,962 limited/protected, UUID `b915f967-7cb4-4c14-b11b-f52209637a22`, saved-manifest fingerprint `dd2f90fa766164e17a38ca665b11a1f188559f33353a66536845a6fc196f8bd1`. All deletion-authorised flags remain false. Synthetic regressions and >31k-row adversarial tests passed (`note(20261021-125039).txt`).
- `protection/{mars,backup}/configuration-inspection.txt` and `protection/{mars,backup}/protection-state.json`: captured deployed configuration and state (operator logs `note(20261021-125726).txt`, `note(20261021-125828).txt`, `note(20261021-125937).txt`, `note(20261021-130037).txt`). On `mars`, `.replication-protection.json` and `.checkpoint-holds.json` under `/media/usb/@snapshots` are root-owned, mode `0600`, with protection required. On `backup`, protections are not required by the deployed snapshot-manager configuration. This does not remove receiver-side replication dependencies.
- Active `mars` replication pin `20261021-030006Z` identifies `@data` source UUID `c0ad8538-dc61-bc48-8922-6c37eaf1a902`. Held checkpoints `20261013-171228Z` (pre-cleanup recovery) and `20261018-165453Z` (permanent closure evidence) each identify `root` and `@data` source UUIDs. All six source snapshot UUIDs were found (`note(20261021-130137).txt`).
- All three protected `@data` source UUIDs match the receiver's `received_uuid` on `backup` for the same timestamps (`note(20261021-130310).txt` and `note(20261021-130423).txt`). Playbooks `roles/remote-backup/README.md`, `btrfs-native-endpoint.py`, and `btrfs-native-push-receiver.py` confirm only `@data` is sent to `/@data/mars-received/@data/`; absence of received `root` counterparts is expected (`note(20261021-130526).txt`).
- **Original terminal evidence included in this ZIP, retained byte-for-byte with original filenames:**
  - `protection/mars/note(20261021-130702).txt`: `ro=true` for `root` and `@data` at each of `20261013-171228Z`, `20261018-165453Z`, `20261021-030006Z` (six checks).
  - `protection/backup/note(20261021-130727).txt`: `ro=true` for received `@data` at the three timestamps (three checks).
  These nine read-only property checks passed. The two original log SHA256 values are recorded below.

**Protection/log SHA256 (original uploaded bytes):**

- `mars/note(20261021-130702).txt`: `475f78f6be00748e324c20f400aef983d22433d3a59bea595123b63ddfb05a8a`
- `backup/note(20261021-130727).txt`: `87bb009c61be7c2fe6b4a626dfeb8541d953bae8a2874877e591f50c4a701d83`

**Still outstanding:** independent receiver receipt/active-incremental-parent validation beyond three matching received UUIDs; qgroup-specific candidate exclusion immediately before any contemplated mutation; mechanism/recurrence and safe remediation/recovery plan; explicit operator approval. Historical manifest captures and identity evidence were taken at different times and are not atomic. **Step 03 remains IN PROGRESS; no deletion is authorised.**

## Receiver receipt and historical-parent evidence — 2026-10-21

- Findings, UUID reconciliation and historical-versus-current parent distinction: `STEP03-RECEIVER-PARENT-RECONCILIATION.md`.
- Captured receiver receipt inventory and contents already stored in the Windows checkout: `protection/backup/receiver-receipt-inspection.txt` (not overwritten by this ZIP).
- Original logs, included byte-for-byte: `protection/backup/note(20261021-131622).txt`, `protection/mars/note(20261021-131715).txt`, `protection/backup/note(20261021-131807).txt`. SHA256 values are documented in the reconciliation record.
- Three protected receipts and three historical received parents **match**. The active pinned 21 October snapshot is present on both hosts; earlier historical parents may already be pruned on the source.
- **Outstanding:** qgroup-specific safety, recurrence/mechanism, non-reversibility/rollback, independent explicit approval before any possible mutation. Step 03 OPEN.

## 2026-10-21 — offline assessment and historical patterns (Step 03 open)

Both actual saved manifests passed the fail-closed offline safety assessor: `mars` 191 total (140 active-excluded, 6 protected, 24 limited, 21 unmatched investigation-only) and `backup` 29,571 total (131 active-excluded, 3 protected, 13,962 limited, 15,475 unmatched investigation-only). Source-fingerprint and SHA256 verification passed. No deletion commands were generated or authorised.

Read-only historical analysis found `backup` has 29,437 unmatched qgroups over IDs 276–55746, concentrated nearly continuously from ~27000 onward, with limited and unlimited records interleaved; near the end, odd limited/even unlimited IDs alternate. This *suggests* a repeated historical pair workflow but proves neither source nor eligibility. Current snapshot-manager pruning logs exact subvolume IDs before deletion and does not explicitly reconcile qgroups; its second deletion call is creation rollback. Native receiver failed-transfer destinations are left for inspection. Causality is unresolved.

See `evidence/Step 03/STEP03-OFFLINE-ASSESSMENT-AND-HISTORICAL-PATTERN.md` for exact sources, original logs and checksums. Both locally saved assessment JSON files remain in `evidence/Step 03/assessment/` and are not overwritten. **Step 03 IN PROGRESS; 0039-DEF OPEN; no production mutation authorised.**

## 2026-10-21 — Snapper-pair linkage and disposable stale-qgroup reproduction (Step 03 OPEN)

Seven surviving `backup` Snapper `@data`/`root` snapshot pairs have adjacent subvolume IDs, and the validated manifest shows `@data` at 1.00TiB max referenced versus unlimited `root` for all seven. Historical cleanup ran for both configurations. The 2026-10-21 `backup` baseline confirms no pending deletions and idle quota rescan. This strongly supports, but does not exhaustively prove, historical Snapper association of the 29,437 unmatched qgroups.

On an isolated 512 MiB loopback Btrfs filesystem on `mango` (UUID `8346c9fd-6dbb-45b6-94dc-e8b4728e2757`), successful synchronised deletion left **both** unlimited qgroup `0/257` and 1 TiB-limited qgroup `0/259` `<stale>`. A later read-only check showed 0 B usage for both while the 1 TiB limit remained. These results do not establish backup's exact Btrfs mechanism or safety of destroying any qgroup. Original logs and hashes, limitations and next acceptance gates are in `evidence/Step 03/STEP03-STALE-QGROUP-REPRODUCTION.md`. The disposable filesystem remains intact. **Step 03 / 0039-DEF IN PROGRESS; no production mutation authorised.**

## 2026-10-21 — disposable qgroup reconciliation Gates A–D (Step 03 OPEN)

On the identity-verified 512 MiB `mango` loopback Btrfs filesystem (UUID `8346c9fd-6dbb-45b6-94dc-e8b4728e2757`), the four guarded rehearsal gates **passed**. Gate A recorded live IDs and limits; Gate B destroyed only stale unlimited `0/257`; Gate C destroyed only stale 1 TiB-limited `0/259`; Gate D verified the exact three original active qgroup rows and the two active subvolumes remained, no deleted snapshot reappeared, no pending deletions/rescan, and read-only stale selection returned zero. See `evidence/Step 03/STEP03-RECONCILIATION-GATES-A-D.md` and original logs in `evidence/Step 03/reconciliation/mango/`. The separate SHA256 manifest uses defect-root-relative paths. This supports **disposable removal feasibility only**, not any production candidate eligibility or production remediation authorisation. Gates A–D accepted on observed outputs; preservation checksum verification in local checkout remains pending. **Step 03 and 0039-DEF stay IN PROGRESS**; do not dismantle test image yet.

## 2026-10-21 — offline investigation planner adversarial regression accepted (Step 03 OPEN)

The offline planner passed complete saved `backup` (29,571 qgroups) and `mars` (191 qgroups) baselines, five command-line negative tests, and **12 adversarial evidence-tampering regressions**. The first regression attempt exposed an unhandled manifest-validator exception; the subsequent targeted fix was verified by controlled `PLAN UNAVAILABLE:` errors for all 12 cases. Python compilation, source-evidence SHA256 unchanged, and `git diff --check` passed. Original successful terminal log, defect-root-relative SHA256 manifest, individual rejection cases and acceptance limits: `evidence/Step 03/STEP03-PLANNER-REGRESSION-ACCEPTANCE.md` and `evidence/Step 03/planner-regression/note(20261021-151658).txt`.

**Offline planner adversarial gate ACCEPTED; Step 03 remains IN PROGRESS.** Live protection, receipt/hold and fingerprint revalidation and any production deletion authorisation remain outstanding. This assessment does not approve production mutation. Evidence installation and checksum verification in the user's local repository are pending.

## Production remediation evidence addendum — 2026-10-22

See `STEP03-PRODUCTION-REMEDIATION-ACCEPTANCE.md` for the 29,437 deleted qgroups, interrupted-journal reconciliation, original batch journals and checksums under `reconciliation/backup/`, the independent zero-orphan verification, and the manual mars→backup incremental receive. Production remediation and replication gates PASSED. Recurrence/prevention and remaining overall defect gates remain OPEN.
