# 0040-FEAT Step 12.3 — Live A→B recovery and previous-parent acknowledgement evidence

Date: 2026-11-01. **Status: Step 12.3 OPEN; live cycle and previous acknowledgement accepted; final protection reconciliation pending.**

## Observed outcomes

- The initial `--execute-prepared` refused with `receiver promotion acknowledgement refused` after candidate B had been received and receiver promotion persisted. Receiver inspection showed B present, readonly, and `Received UUID: a9b78fb9-4da6-cf4f-b242-13909f574193`, established=B, previous=A. Sender still showed established=A, pending=B. This was a receiver-promoted/source-pending state, not evidence of a failed stream.
- The acknowledgement-contract fix was applied on mango. The nine sender-promotion regressions passed. Ansible deployment reported mars changed=1, backup changed=0, failed=0. `--resume-committed` returned `both-promoted-previous-pinned`, with matching source/receiver state established=B, pending=null, previous=A. No repeat of `--execute-prepared` was performed.
- Independent readback returned matching A/B state; `btrfs-native-push.timer` was `active`.
- Source and receiver Btrfs `subvolume show` verified A (`20261030-030033Z`), B (`20261030-170009Z`) and native checkpoint (`20261101-140039Z`) present readonly on both hosts, with receiver `Received UUID` equal to the corresponding source UUID.
- The native source registry still protected A in both `protected` and `prune_protected`, and protected the newer native checkpoint in `protected`. B was not present in that native registry; code-level agreed-parent pin regression evidence is separate, and deployed pruning integration must not be claimed from this registry alone.
- Repeat-cycle acknowledgement regressions on mango: sender 4, receiver 4, sender workflow 9, sender promotion runtime 9, runtime manifest 4 = **30 PASS**; `git diff --check` showed no errors. Mango Playbooks branch `main`, HEAD `bdba058b0f3b634f94e7da4b7ab62eeadfa625b6` at log time, with substantial pre-existing modified/untracked Step 12.3 files; do not clean/reset them.
- Repeat-cycle Ansible deployment: `mars ok=27 changed=0 failed=0`, `backup ok=42 changed=0 failed=0`. Installed sender CLI advertises `--acknowledge-previous`; receiver advertises `--acknowledge-previous` and `--previous-readback`.
- Live sender `--acknowledge-previous` returned **`both-previous-acknowledged`**, with both returned states: `established=B`, `previous=null`, `pending=null`; `authorizes_prune=false`, `authorizes_release=false`. No deletion or native release authorization was returned.

## Identities

- A (`20261030-030033Z`): `d901ddd2-66c7-0b42-b26c-ab6886273b7a`
- B (`20261030-170009Z`): `a9b78fb9-4da6-cf4f-b242-13909f574193`
- Native checkpoint (`20261101-140039Z`): `69ef9a57-50ff-9a4e-92ed-8f10560ab1f2`

## Outstanding acceptance / next cycle

1. After acknowledgement, independently read both on-disk state files and all three readonly snapshot identities again; verify the native registry, independent receiver holds, agreed-parent pruning configuration and actual `btrfs-native-push.timer` schedule. The last snapshot and timer checks preceded the acknowledgement, and must not be represented as post-ack checks.
2. Do not manually clear holds or delete A. Clearing `previous` ends agreed-parent referencing of A but does not override native or historical recovery holds.
3. Candidate C preparation and integration into normal scheduled replication are not demonstrated or authorised by these logs. Preserve the current native 03:30 schedule until replacement is validated.
4. Formal Step 12.3 closure requires final verification results, evidence acceptance and documented scope boundary; feature 0040-FEAT remains in progress.

## Archived raw logs (verbatim)

| Filename | SHA-256 |
|---|---|
| `note(20261101-194002).txt` | `6243df622ea051f561b164d913052289a7cae7726b96451858697af02ea60ef4` |
| `note(20261101-194146).txt` | `01f19c201b8cf5675fe3874e84de5af9d9fa1a9d3849e0ac32be892af90014b2` |
| `note(20261101-201009).txt` | `91a4913d0d22b7e953deed72d5557eec6e4be8fa2c0ff84089edf13c0278a0b8` |
| `note(20261101-201043).txt` | `109ae540a71c0088c93cee224cbf07d9e0f0f7cd9b236a4d08d996cb0640de9f` |
| `note(20261101-201425).txt` | `0def5f3fa5ab040f691a3ced0fb2ff5e3cec640d817e714ef71a73f8de2ad229` |
| `note(20261101-202454).txt` | `695d45c6492c0b9a24ec7474b73c1aa0f3a7e38b64194df8a8e72bc69336c83b` |
| `note(20261101-203259).txt` | `a00d07871bc03f030ccfc7525ecac7d9c2e4087af419cb02333ee22f8ba6228e` |
| `note(20261101-203314).txt` | `2635e94d3631550e96c5f8c90e03f37bc80478c7f07a2b0f9dee3483dc2f533c` |
| `note(20261101-203350).txt` | `d708ff5201c89fde37e20d5b87b4f8ee2cdf710ae2c17cef147398aec812c4a8` |

Logs archive is a companion to this report under `evidence/Step 12/raw-logs/`; files are copied byte-for-byte from the user-uploaded terminal output. Nothing in this report asserts a new command was executed on the live hosts.
