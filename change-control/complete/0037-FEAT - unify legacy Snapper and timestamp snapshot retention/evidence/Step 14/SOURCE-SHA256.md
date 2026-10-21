# Step 14 — latest supplied source reconciliation

Source bundles: `diaries-sources-20261020-184607.zip` and `playbook-sources-20261020-184604.zip` (uploaded; not asserted identical to Git HEAD).

| Playbooks file | SHA-256 (uploaded content) |
| --- | --- |
| `roles/local-backup/tasks/main.yaml` | `3fccb0f3ba156f9484e5259026c8bf8a2f61515f8b43ea920eb273f23506d468` |
| `roles/local-backup/tasks/diaries_pull.yaml` | `8bc771fe5cb21a25069da83dd77ce89f56aafd5638515034a3751ca6400ab565` |
| `roles/local-backup/defaults/main.yaml` | `1b3dcabde4ab81e038e24429ee62a34f340864e391296478c3c9a9cc6ba2385b` |
| `roles/local-backup/tests/verify-diaries-pull.py` | `7f2ae8e1ec954e4a94bf50468374097daa27faee3726d5f20b295880e80d34f7` |
| `roles/local-backup/tasks/install_user_scripts.yaml` | `6317e61c383f3ef833125eb25cc0dafaf001a1ef8fcd8ca0114a3417d910d423` |
| `roles/local-backup/tasks/install_machine_scripts.yaml` | `449449e0d7cd9dc1000591118f5c41c24f449676e88400f07f72ec49afff0cd1` |
| `roles/snapshots/files/btrfs-snapshot-manager.py` | `dc7dc489a7f8a0683224eaf426a1d70f34c1cf794744ddf5e4860bab4e8f1e4c` |

**Findings:** obsolete root-helper cleanup flag/task absent in source; `normal_user_home` prerequisite has `always` tag. Final Git HEAD and repository dirty-state acceptance pending.
