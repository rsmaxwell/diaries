# 0050 — Playbooks implementation file manifest (source package)

- Source bundle: `playbook-sources-20261117-081247.zip`
- Playbooks baseline: `a2508ad61f479c1b2bc20cb39896006c1f2906e1` (`main`, `mango`)
- Controller baseline: `a81eafdf1fccf6bcd7d9d1b3dfa77143872682e8`
- Private inventory submodule baseline: `ebcce026723db37b9b53b76ba21903a351d48466` (unchanged)
- Change applies to **public Playbooks checkout** `/home/richard/ansible-controller/playbooks`; none of these files belong in the private inventory or Diaries application submodules.
- Complete Playbooks change package: 8 paths (source/tree tested locally, not deployed).

| Repository-relative path | SHA-256 of intended new content |
|---|---|
| `roles/snapshots/files/diaries-backup-history.py` | `8777e4903de0fbbee89b7a7cc1c582fc3675cd3430af0fb8af1ef61c6d185a99` |
| `roles/snapshots/files/diaries-backup-status.py` | `a8be00be52ecf3a585aabd2868f90ad51b952bdd22305fe4da99a6bbca7f5afb` |
| `roles/btrfs-replication/templates/btrfs-receiver-manager.json.j2` | `542c8b0479b4b68b89e49dbf0e75eb2fcd8bea3a87bb6822144d3297dbc12307` |
| `roles/btrfs-replication/tasks/native.yaml` | `73241fd408d67a59669c9e9f916d6c4ed780e1893a40ece52536c2e4c42287e4` |
| `roles/btrfs-replication/tasks/receiver-diaries-history.yaml` | `d8fd2853b42eb2d34d543005ee33de24d84a60337a4c8ad30ab082025005de7f` |
| `roles/btrfs-replication/README.md` | `a95f3ef0cf939d7220c750c64c61396eb6254df312196d2d6587c10090145f08` |
| `roles/btrfs-replication/tests/README.md` | `c1a8933fac6bdcdf6d2e1dc868e6ebb2c127c1981d6b60083ea9dc364e3b65b0` |
| `roles/btrfs-replication/tests/verify-0050-receiver-history-contract.py` | `85a10a328d620cf3f0464b473a8a2ca98a2f156b4bd924d863d1a0f6071b30fa` |
