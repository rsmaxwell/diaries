# 0049 — Playbooks source change manifest

Baseline Playbooks main HEAD: `0904bc7ebe801e391a3aa4dc59bbc9ccc7dfa532` (latest uploaded 2026-11-16 bundle).

Each file is relative to the Playbooks Git root. No deletion of stored backup data, snapshot state, or private inventory is included.

| Status | Path | SHA256 of packaged file |
| --- | --- | --- |
| MOD | `roles/backup-collection/tasks/source_snapshot_access.yaml` | `1711d390819bf98d3720c7283bf9dad5b4eaecbf14168c68819d0f05d835c5fb` |
| MOD | `roles/btrfs-replication/README.md` | `a45c41272a4ba69bac84a7930ae2b5b0f6d5d344536c61c9ab6634d156d78be4` |
| MOD | `roles/btrfs-replication/defaults/main.yaml` | `2fee4b5d502d55ff6b4090422180e410d75dae110ac46d81d96ef53de46b8a5d` |
| MOD | `roles/btrfs-replication/files/btrfs-replication-receiver-gate-0041.py` | `9ba800110626ce870a4752709ab093d24c37df2e295ebb7bd35a8c81db46ed6e` |
| MOD | `roles/btrfs-replication/files/btrfs-replication-sender-cycle-0041.sh` | `edf27767c82def46cf988f41914658dbae24b83df725c18d222fdc0688fda4f9` |
| NEW | `roles/btrfs-replication/files/btrfs-replication.py` | `e9ac02ed561d4fcda44825c9a73eaef8b0caeed9d81aaebcf5cbbb28a2d3c369` |
| MOD | `roles/btrfs-replication/tasks/endpoint-setup.yaml` | `d1eea1267f2b258cf916fea0533346d29387ae34be05a0091f2edef7565a7a7c` |
| MOD | `roles/btrfs-replication/tasks/native.yaml` | `ae0a9c73d2dc128ab1efe1a44dcfed691e451536c2489cafd7d7dc51abb6273b` |
| MOD | `roles/btrfs-replication/tasks/receiver-config.yaml` | `b18c6a58cc511be14f79ac6ac82d25252822cd181c923920344db25a7fc60f5f` |
| MOD | `roles/btrfs-replication/tasks/receiver-retention.yaml` | `f8ed448159e129bd4bcc5bfe797a5d0aee1538c7df3c2cab1d1f6d13c382fb2f` |
| NEW | `roles/btrfs-replication/tasks/retire-0049-interfaces.yaml` | `3fc886a7779123eb4af6251278c5557421e111006574a5e041a2caf641d6ce55` |
| MOD | `roles/btrfs-replication/tasks/service-identities-0041.yaml` | `6938366c619fa48c9e21c8ab39fca7a1b606e82799c22250caa02ddcd094c6e1` |
| MOD | `roles/btrfs-replication/tasks/simplified-runtime.yaml` | `5172d8a0e34cd066ef4226d736f6e8b9ddaa61dee0689c98b982267f986d7359` |
| MOD | `roles/btrfs-replication/tasks/source-scheduling.yaml` | `cd03a5dd02b24598915123f5c05de26abd3b360aa87414ec8796709c166ea802` |
| NEW | `roles/btrfs-replication/templates/btrfs-push-0041.service.j2` | `0750d67103d6838fefbbac364915bb283a00387c77e7e1ad80b7f2aeed39dc4f` |
| NEW | `roles/btrfs-replication/templates/btrfs-push.service.j2` | `92e92307cd28b87f049863a1b1587e8af547aaec3171d0a910085dee06ad016a` |
| NEW | `roles/btrfs-replication/templates/btrfs-push.timer.j2` | `21fd7e7ea51b459e6087af17d79a408693992f0e41b2aa8e94e2b5d1e94291e0` |
| MOD | `roles/btrfs-replication/templates/btrfs-receiver-manager.json.j2` | `1772055db4da185b8a8de1b3b9cd14b36b7cb4e380f06062689dd40002457382` |
| NEW | `roles/btrfs-replication/templates/btrfs-receiver-prune.service.j2` | `0848a231bd53fd01c56eda1ba5fbbc7111e5659e05123be7bbb2476fbd35bda6` |
| NEW | `roles/btrfs-replication/templates/btrfs-receiver-prune.timer.j2` | `c42933a14ec2b709f08e00fc3d002593a234113e70b73a5d9deb45b7a04f04ed` |
| MOD | `roles/btrfs-replication/tests/README.md` | `f536dc1e62a27bf074c9220e366a3c7a53a1033fe1b253dcd44da82b8cd9685c` |
| MOD | `roles/btrfs-replication/tests/verify-0041-restricted-identity.py` | `e61204f6a37113d65b708e8ad73f81016ee7292925432066288d3f258427cb37` |
| NEW | `roles/btrfs-replication/tests/verify-0049-backup-management.py` | `22fb33f8f53809d8ca45c0e79634f18a83687b29c5609f2123b7d65e146b2658` |
| MOD | `roles/btrfs-replication/tests/verify-replication.py` | `0bdfffe6123a2768f774ff4eed38ae3e240f3d1a1e20ad191a9780f3abc7fb35` |
| MOD | `roles/snapshots/README.md` | `36b0ccec3000b71bc86bce57a421667a4e02115fc1cc731713c180c1cd127da4` |
| NEW | `roles/snapshots/files/btrfs-backup-status.py` | `b7d0ac8a8cb3944f16a2b85bd60e95a82ef6816f36b6808d23334749883e8456` |
| MOD | `roles/snapshots/files/btrfs-snapshot-manager.py` | `bcb0afe3a2a2dc5047bb59672d28df72ffe522774221d014c7f235fb8c63aedc` |
| MOD | `roles/snapshots/files/diaries-backup-history.py` | `8992d548d7820537765dd607345ccdc70afc1a43ace232ead4147dd70e7ca0c0` |
| MOD | `roles/snapshots/files/diaries-backup-status.py` | `feed0027b7fa9e510ef5524cd3f2dcfad9deb9417ede8016636f032a0b1b0d13` |
| MOD | `roles/snapshots/tests/verify-0040-simplified-receiver-retention.py` | `622051b7cf51952724aca7f8e37a19b7391799cc3687e14b7320a5de863dd686` |
| MOD | `roles/snapshots/tests/verify-0040-step13-source-prune-cap.py` | `7be2f99c91858c9cb20e54b0a6d4cfc096348a604fc0ff852c4c64d6bebce362` |
| MOD | `roles/snapshots/tests/verify-diaries-backup-status.py` | `0b73b52ae345a7e6b244a676f20b406c378ec8af47f7d641ec7a2d8ae47eedfa` |

Total source files: **32**.

The original retired service/runtime source examples are not installed by the updated active tasks and remain in Git history/source for rollback reference. Their old names are removed from installed operational entry points.
