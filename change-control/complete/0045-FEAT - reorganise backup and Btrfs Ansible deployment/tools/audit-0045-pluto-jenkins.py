#!/usr/bin/env python3
"""Read-only audit of live Jenkins job definitions inside the Jenkins Kind pod.

Expected invocation: ssh pluto 'python3 -' < audit-0045-pluto-jenkins.py
The Kubernetes hostPath used by Kind is on its containerised node, not necessarily
on pluto's root filesystem. This script uses the running Jenkins pod directly.
Prints matching file paths, never matching lines or file contents.
"""
import json
import shutil
import socket
import subprocess
import sys

# POSIX shell, grep and find are present in the Jenkins container. No Python there is required.
SCAN = r'''
job_root=/var/jenkins_home/jobs
if [ ! -d "$job_root" ]; then
    echo "INCOMPLETE: Jenkins jobs not accessible inside pod at $job_root"
    exit 3
fi

# Count job definitions. Do not traverse build logs/workspaces in the search.
count=$(find "$job_root" -type f -name config.xml 2>/dev/null | wc -l)
echo "job_config_files: $count"

# Restrict to job definitions and scripts. Exclude transient/build subtrees.
# grep -l emits filenames only, never the corresponding matched configuration text.
result=$(grep -RIlE \
  --include=config.xml --include=Jenkinsfile \
  --include='*.groovy' --include='*.sh' \
  --include='*.yaml' --include='*.yml' \
  --exclude-dir=builds --exclude-dir=workspace --exclude-dir=workspaces \
  --exclude-dir=archive --exclude-dir=logs --exclude-dir='@tmp' \
  '(local-backup|remote-backup)\.(yaml|yml|sh)' "$job_root" 2>&1)
status=$?
case "$status" in
  0) printf 'MATCH: %s\n' "$result"; echo 'FOUND: Legacy caller references need review'; exit 5 ;;
  1) echo 'PASS: No legacy backup playbook or launcher references in scanned Jenkins job files'; exit 0 ;;
  *) printf 'INCOMPLETE: Jenkins job scan failed: %s\n' "$result"; exit 4 ;;
esac
'''


def run(args):
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def main():
    host = socket.gethostname().split('.')[0]
    if host != 'pluto':
        print(f'FAIL: Expected pluto but connected to {host}', file=sys.stderr)
        return 2
    if shutil.which('kubectl') is None:
        print('INCOMPLETE: kubectl is unavailable in this pluto SSH environment', file=sys.stderr)
        return 3
    print('=== 0045 Jenkins live-pod caller audit (read-only) ===', flush=True)
    p = run(['kubectl', '-n', 'jenkins', 'get', 'pods', '-l', 'app=jenkins',
             '--field-selector=status.phase=Running', '-o', 'json'])
    if p.returncode != 0:
        print(f'INCOMPLETE: Cannot list Jenkins pods: {p.stderr.strip()}', file=sys.stderr)
        return 3
    try:
        items = json.loads(p.stdout)['items']
    except (ValueError, KeyError, TypeError) as exc:
        print(f'INCOMPLETE: Invalid Kubernetes pod response: {exc}', file=sys.stderr)
        return 3
    if not items:
        print('INCOMPLETE: No running Jenkins pod; the job-store audit has not been performed', file=sys.stderr)
        return 3
    results = []
    for item in items:
        pod = item['metadata']['name']
        print(f'pod: {pod}', flush=True)
        status = {c.get('name'): c.get('ready', False)
                  for c in item.get('status', {}).get('containerStatuses', [])}
        if not status.get('jenkins', False):
            print(f'INCOMPLETE: Jenkins container is not ready in {pod}', file=sys.stderr)
            results.append(3)
            continue
        scan = run(['kubectl', '-n', 'jenkins', 'exec', pod, '-c', 'jenkins',
                    '--', 'sh', '-c', SCAN])
        if scan.stdout:
            print(scan.stdout, end='' if scan.stdout.endswith('\n') else '\n')
        if scan.stderr:
            print(f'pod stderr: {scan.stderr.strip()}', file=sys.stderr)
        if scan.returncode == 0:
            results.append(0)
        elif scan.returncode == 5:
            results.append(5)
        else:
            print(f'INCOMPLETE: Pod {pod} scan exited {scan.returncode}', file=sys.stderr)
            results.append(4)
    if any(rc in (3, 4) for rc in results):
        return 4
    if 5 in results:
        return 5
    print('PASS: All running Jenkins pods scanned; no legacy callers found')
    print('NOTE: Jenkinsfiles fetched dynamically from SCM and external schedulers are not covered')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
