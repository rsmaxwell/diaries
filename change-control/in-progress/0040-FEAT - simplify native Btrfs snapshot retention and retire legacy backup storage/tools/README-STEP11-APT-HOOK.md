# 0040-FEAT Step 11 — One-off Snapper APT hook cleanup

**Scope:** `mars` only. Historical execution artifact, not production Playbooks code.

The obsolete `/etc/apt/apt.conf.d/80snapper` file remains after Snapper retirement. This one-time playbook verifies that the Snapper package is not installed and its executable and active configurations are absent; refuses an unexpected hook file type; preserves a root-only rollback copy on `mars`; and removes only the hook. It does not touch Btrfs snapshots, package installation, timers or receiver state. Run only with the user's approved Step 11 cleanup.

Place this file in the **Diaries** repository. To execute on the `mango` controller without adding to Playbooks, copy `step11-retire-orphaned-snapper-hook.yaml` to `/home/richard/temp/step11-retire-orphaned-snapper-hook.yaml` via WinSCP (or Cygwin `scp`), then use the **mango SSH terminal**:

```sh
cd /home/richard/playbooks
ansible-playbook /home/richard/temp/step11-retire-orphaned-snapper-hook.yaml \
  --limit mars --check --diff --vault-password-file ~/.vault_pass.txt
```

**Review check output before applying.** A missing hook should produce `changed=0`. With an existing hook and no previous rollback copy, check mode can report both a proposed backup copy and hook deletion (`changed=2`). Do not deploy if the preflight refuses or if unrelated changes appear. The actual apply, after review, is identical without `--check --diff` (add `--diff` if a diff is desired). Then rerun `--check --diff` and verify the hook is absent.

Keep `/home/richard/80snapper.0040-step11-before` until copied into Step 11 evidence and reviewed. Preserve evidence in Diaries; remove the temporary `mango` execution file after acceptance. Do not run this temporary artifact routinely or incorporate it into permanent Ansible roles.
