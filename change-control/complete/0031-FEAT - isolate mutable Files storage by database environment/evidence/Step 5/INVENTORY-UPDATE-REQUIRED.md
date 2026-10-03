# 0031 Step 5 — production inventory update required

The reusable Diaries role intentionally does not define a default for `diaries_files_dir`.

Before deploying the updated role, edit the existing production inventory variable file that owns the Diaries production settings (the same configuration domain that supplies values such as `diaries_nas_content_path`) and add:

```yaml
diaries_files_dir: files
```

The source bundle does not contain `/etc/ansible/group_vars/` or `/etc/ansible/host_vars/`, so the exact live inventory filename cannot be established safely from the supplied files and has not been invented here.

Expected behaviour after the source update:

- with `diaries_files_dir: files`: preflight passes and production retains the existing `.../diaries-content/files` mutable root;
- with the variable missing or invalid: the role fails before deployment;
- no role default should be added to bypass the guard.
