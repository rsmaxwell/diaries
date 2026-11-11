#!/usr/bin/env python3
"""0045: Read-only legacy entry-point reference scan on a managed host.

Run over SSH as: ssh HOST 'sudo -n python3 -' < this-file
Returns file paths, not matching file contents or secret values.
"""
import datetime
import json
import os
import re
import socket
from pathlib import Path

PATTERN = re.compile(rb"(?:local-backup|remote-backup)\.(?:yaml|sh)")
IGNORED_DIRS = {"builds", "workspace", "workspaces", "archive", "logs", ".git", "node_modules", "@tmp", "__pycache__"}
LIMIT_BYTES = 5 * 1024 * 1024
COMMON = [
    "/etc/crontab",
    "/etc/cron.d",
    "/etc/cron.daily",
    "/etc/cron.hourly",
    "/etc/cron.weekly",
    "/etc/cron.monthly",
    "/var/spool/cron/crontabs",
    "/var/spool/cron",
    "/etc/systemd/system",
    "/usr/lib/systemd/system",
]
JENKINS = ["/var/lib/jenkins/jobs", "/srv/jenkins/jobs", "/var/jenkins_home/jobs"]


def scan_file(path, matches, failures, skipped):
    try:
        if path.is_symlink() or not path.is_file():
            return
        stat = path.stat()
        if stat.st_size > LIMIT_BYTES:
            skipped.append(str(path))
            return
        if PATTERN.search(path.read_bytes()):
            matches.append(str(path))
    except OSError as exc:
        failures.append({"path": str(path), "error": str(exc)})


def scan_root(root, matches, failures, skipped):
    path = Path(root)
    if not path.exists():
        return "absent"
    if path.is_symlink():
        # The same /usr/lib/systemd tree is covered via its real location.
        return "symlink_not_followed"
    if path.is_file():
        scan_file(path, matches, failures, skipped)
        return "scanned_file"
    if not path.is_dir():
        return "unsupported_type"

    def onerror(exc):
        failures.append({"path": getattr(exc, "filename", root), "error": str(exc)})

    for base, dirs, files in os.walk(path, followlinks=False, onerror=onerror):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not Path(base, d).is_symlink()]
        for name in files:
            scan_file(Path(base, name), matches, failures, skipped)
    return "scanned_directory"


def main():
    host = socket.gethostname().split(".")[0]
    roots = COMMON + (["/etc/ansible"] if host == "mango" else []) + (JENKINS if host == "pluto" else [])
    matches, failures, skipped, coverage = [], [], [], {}
    for root in roots:
        coverage[root] = scan_root(root, matches, failures, skipped)
    result = {
        "schema": "0045-legacy-caller-audit-v1",
        "host": host,
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "searched_reference_names": ["local-backup.yaml", "remote-backup.yaml", "local-backup.sh", "remote-backup.sh"],
        "coverage": coverage,
        "matching_files": sorted(set(matches)),
        "unreadable_paths": failures,
        "large_files_skipped": skipped,
        "jenkins_filesystem_visible": any(coverage.get(p, "absent").startswith("scanned") for p in JENKINS) if host == "pluto" else None,
        "limitations": [
            "File-path matches only; indirect invocations and code-generated commands are not detected",
            "Jenkins jobs deployed in containers/Kubernetes or accessible only via Jenkins API are not covered by host filesystem scanning",
            "Unregistered external automation and other machines are outside this host audit",
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    if failures:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
