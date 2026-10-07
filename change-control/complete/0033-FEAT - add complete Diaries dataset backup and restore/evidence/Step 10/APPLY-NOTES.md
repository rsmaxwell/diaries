# Step 10 application notes

The Step-10 Diaries package places the complete 0033 record under `change-control/complete/`. A ZIP overlay cannot remove the previous directory, so after extracting the package over the Diaries repository remove the old duplicate:

```bat
rmdir /s /q "change-control\in-progress\0033-FEAT - add complete Diaries dataset backup and restore"
```

Alternatively, if applying the changes manually with Git, use `git mv` for the feature directory and then apply the Step-10 edits/evidence.

The Playbooks source bundle contained generated `roles/diaries/files/sync/scripts/__pycache__/` files. They are not supported source or deployed tooling; the managed Ansible sync already excludes/deletes them. If they are still present in the working tree, remove them before the final Git review:

```bash
rm -rf playbooks/roles/diaries/files/sync/scripts/__pycache__
```

Step 10 changes documentation/change-control state only. No client/responder/web source, Docker image, Compose template, Ansible task or operational backup/restore implementation changes in this package. No new Docker images are required and no production redeployment is required merely to apply the Step-10 close-out documentation.
