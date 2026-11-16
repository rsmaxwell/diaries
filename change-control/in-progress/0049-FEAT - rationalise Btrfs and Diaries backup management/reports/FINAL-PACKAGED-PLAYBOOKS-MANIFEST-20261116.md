# 0049 — Final packaged Playbooks source manifest (16 November 2026)

These SHA-256 values are calculated from the **32 final files** after applying, in order, the Playbooks implementation ZIP, the naming-corrections ZIP and the dedicated-sender-status correction ZIP. This supersedes the **pre-correction** packaged hashes in `PLAYBOOKS-CHANGE-MANIFEST-20261116.md` without altering that historical report.

**Source baseline:** Playbooks `main` commit `0904bc7ebe801e391a3aa4dc59bbc9ccc7dfa532` (observed on `mango` before the 0049 commit). The final implementation Git commit does not yet exist in the supplied logs; the hashes below describe source bytes, **not a committed or installed-host revision**.

This manifest is used by `tools/verify-and-stage-0049-playbooks.py` to refuse staging if files have drifted. It excludes generated `__pycache__/` and all private inventory/vault content. After a successful commit, record the new child revision, Ansible-controller parent pin and Windows Diaries parent revision in `reports/REPOSITORY-REVISION-RECORD.md` (do not fabricate values).

```
1711d390819bf98d3720c7283bf9dad5b4eaecbf14168c68819d0f05d835c5fb  roles/backup-collection/tasks/source_snapshot_access.yaml
6767a45845e69f13cd60e1b05050f0e23b7996cf2d91b5338bff8c6923f81843  roles/btrfs-replication/README.md
2fee4b5d502d55ff6b4090422180e410d75dae110ac46d81d96ef53de46b8a5d  roles/btrfs-replication/defaults/main.yaml
9ba800110626ce870a4752709ab093d24c37df2e295ebb7bd35a8c81db46ed6e  roles/btrfs-replication/files/btrfs-replication-receiver-gate-0041.py
edf27767c82def46cf988f41914658dbae24b83df725c18d222fdc0688fda4f9  roles/btrfs-replication/files/btrfs-replication-sender-cycle-0041.sh
7b4e4e99a2031cca6c82adc8fb3d59d59cdd66ef5aa7d6ce79a23baba6804ff2  roles/btrfs-replication/files/btrfs-replication.py
d1eea1267f2b258cf916fea0533346d29387ae34be05a0091f2edef7565a7a7c  roles/btrfs-replication/tasks/endpoint-setup.yaml
ae0a9c73d2dc128ab1efe1a44dcfed691e451536c2489cafd7d7dc51abb6273b  roles/btrfs-replication/tasks/native.yaml
b18c6a58cc511be14f79ac6ac82d25252822cd181c923920344db25a7fc60f5f  roles/btrfs-replication/tasks/receiver-config.yaml
f8ed448159e129bd4bcc5bfe797a5d0aee1538c7df3c2cab1d1f6d13c382fb2f  roles/btrfs-replication/tasks/receiver-retention.yaml
3fc886a7779123eb4af6251278c5557421e111006574a5e041a2caf641d6ce55  roles/btrfs-replication/tasks/retire-0049-interfaces.yaml
6938366c619fa48c9e21c8ab39fca7a1b606e82799c22250caa02ddcd094c6e1  roles/btrfs-replication/tasks/service-identities-0041.yaml
5172d8a0e34cd066ef4226d736f6e8b9ddaa61dee0689c98b982267f986d7359  roles/btrfs-replication/tasks/simplified-runtime.yaml
71bc528d8d9fefae2888732a42ad65b02ff37c2671bdbb5a374c43a88f02b2f1  roles/btrfs-replication/tasks/source-scheduling.yaml
0750d67103d6838fefbbac364915bb283a00387c77e7e1ad80b7f2aeed39dc4f  roles/btrfs-replication/templates/btrfs-push-0041.service.j2
92e92307cd28b87f049863a1b1587e8af547aaec3171d0a910085dee06ad016a  roles/btrfs-replication/templates/btrfs-push.service.j2
21fd7e7ea51b459e6087af17d79a408693992f0e41b2aa8e94e2b5d1e94291e0  roles/btrfs-replication/templates/btrfs-push.timer.j2
1772055db4da185b8a8de1b3b9cd14b36b7cb4e380f06062689dd40002457382  roles/btrfs-replication/templates/btrfs-receiver-manager.json.j2
0848a231bd53fd01c56eda1ba5fbbc7111e5659e05123be7bbb2476fbd35bda6  roles/btrfs-replication/templates/btrfs-receiver-prune.service.j2
de164438471ae48c1fa62985c86b545b818fe815d82e468fcc1c81481e863b0b  roles/btrfs-replication/templates/btrfs-receiver-prune.timer.j2
f536dc1e62a27bf074c9220e366a3c7a53a1033fe1b253dcd44da82b8cd9685c  roles/btrfs-replication/tests/README.md
e61204f6a37113d65b708e8ad73f81016ee7292925432066288d3f258427cb37  roles/btrfs-replication/tests/verify-0041-restricted-identity.py
9fec2442b449daefb08faa57a453f78cc942e63b78913b6862f0e4c00b0fb9e1  roles/btrfs-replication/tests/verify-0049-backup-management.py
0bdfffe6123a2768f774ff4eed38ae3e240f3d1a1e20ad191a9780f3abc7fb35  roles/btrfs-replication/tests/verify-replication.py
36b0ccec3000b71bc86bce57a421667a4e02115fc1cc731713c180c1cd127da4  roles/snapshots/README.md
af73740c4dfb8b5c78c9f343ac46d3861e01fa950d07ab7ac2f51b9a1eeb8370  roles/snapshots/files/btrfs-backup-status.py
e84e6c394920867793ecac52b33b4c09f518bf9223a383c3d74a52acd1fccbf0  roles/snapshots/files/btrfs-snapshot-manager.py
8992d548d7820537765dd607345ccdc70afc1a43ace232ead4147dd70e7ca0c0  roles/snapshots/files/diaries-backup-history.py
feed0027b7fa9e510ef5524cd3f2dcfad9deb9417ede8016636f032a0b1b0d13  roles/snapshots/files/diaries-backup-status.py
eab031c441a9922a5fe7d0e1a085d37243616f4dc99787278524cbd456fcba47  roles/snapshots/tests/verify-0040-simplified-receiver-retention.py
7be2f99c91858c9cb20e54b0a6d4cfc096348a604fc0ff852c4c64d6bebce362  roles/snapshots/tests/verify-0040-step13-source-prune-cap.py
0b73b52ae345a7e6b244a676f20b406c378ec8af47f7d641ec7a2d8ae47eedfa  roles/snapshots/tests/verify-diaries-backup-status.py
```
