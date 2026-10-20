# 0034 Step 11.4 — mars user backup scheduling correction

The 2026-10-15 02:00 UTC user cron backup obtained the writer lock as the hourly snapshot service started. The 02:00 snapshot failed closed; 03:00 succeeded and 03:30 replication was accepted.

Move only the **normal-user** `backup` cron entry from 02:00 to 01:45 UTC. The **root** backup cron remains at 02:15 UTC and is not touched. Both schedules are interpreted in the host's configured cron timezone (mars logs show UTC).

On mango, after overlay:

```sh
python3 roles/local-backup/tests/verify-user-backup-cron.py
ansible-playbook diaries-user-backup-cron.yaml --syntax-check --vault-password-file ~/.vault_pass.txt
ansible-playbook diaries-user-backup-cron.yaml --check --diff --vault-password-file ~/.vault_pass.txt
ansible-playbook diaries-user-backup-cron.yaml --vault-password-file ~/.vault_pass.txt
ansible-playbook diaries-user-backup-cron.yaml --vault-password-file ~/.vault_pass.txt
```

On mars, verify `crontab -l` shows `45 1 * * *` for the user job. This change leaves the shared writer lock in place; if user backup lasts past 02:00 UTC a safe snapshot skip remains possible. Review the following night's journals for proof of non-collision.
