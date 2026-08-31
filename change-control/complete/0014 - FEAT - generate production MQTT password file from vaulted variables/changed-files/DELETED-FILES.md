# File to delete from the Playbooks repository

- `roles/diaries/templates/config/mosquitto/pwfile.source.txt.j2`

The template is intentionally not reproduced because the proposed `pwfile.yaml` writes temporary content directly from Vault-backed variables under `no_log: true`.

No `misc/config/mosquitto/pwfile.source.txt` deletion is proposed because that path does not exist in the authoritative current Playbooks tree.

