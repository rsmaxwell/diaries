# 0045 Step 2 — Jenkins caller audit correction (11 November 2026)

The 20261111-123007Z attempt reported `INCOMPLETE` at `/mnt/jenkins-data/jobs` on the `pluto` host. The Builder role deploys Jenkins through a **Kind** Kubernetes cluster; its Jenkins persistent volume uses `hostPath: /mnt/jenkins-data`, resolved on the Kind **node container**, not necessarily on the `pluto` host itself. The Jenkins deployment mounts that volume inside the Jenkins container at `/var/jenkins_home`.

The revised audit uses `ssh pluto` and `kubectl -n jenkins exec` to scan `/var/jenkins_home/jobs` in the **running Jenkins container**. It reads only selected job definition and script extensions and prints matching filenames, not Jenkins job contents or credentials. It skips build logs, workspaces and transient paths. It returns a distinct nonzero status when the pod is inaccessible, the job directory is absent, or a legacy launcher reference is found. No Kubernetes resources, files, jobs or services are changed.

A successful scan covers Jenkins job definitions physically stored in the running Jenkins instance, not Jenkinsfiles loaded on demand from Git/SCM, external schedulers, or a stopped Jenkins instance. Preserve the earlier incomplete attempt as diagnostic evidence. Do not retire legacy launchers solely on the strength of this narrower scan.
