#!/usr/bin/env python3
"""Ensure backup-collection operator launcher never enables Ansible --diff by default.

Run on the Playbooks ZIP or the live mango checkout by passing the script path.
"""
import os
import pathlib
import subprocess
import sys
import tempfile


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python3 test-0045-backup-collection-launcher.py PATH_TO_LAUNCHER')
    launcher = pathlib.Path(sys.argv[1]).resolve()
    if subprocess.run(['bash', '-n', str(launcher)]).returncode:
        raise SystemExit('FAIL: launcher syntax')
    with tempfile.TemporaryDirectory() as td:
        base = pathlib.Path(td)
        (base / 'playbooks').mkdir()
        (base / 'bin').mkdir()
        cmd = base / 'bin' / 'ansible-playbook'
        cmd.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n', encoding='utf-8')
        cmd.chmod(0o755)
        env = dict(os.environ, HOME=str(base), PATH=str(base / 'bin') + os.pathsep + os.environ['PATH'])
        for opts, want_check in (([], True), (['--apply'], False)):
            p = subprocess.run(['bash', str(launcher), *opts], env=env,
                               capture_output=True, text=True, check=True)
            args = p.stdout.splitlines()
            assert args[0] == 'backup-collection.yaml', args
            assert '--limit' in args and 'mars' in args, args
            assert ('--check' in args) == want_check, args
            assert '--diff' not in args, args
        print('PASS: new launcher check/apply arguments; no automatic --diff')


if __name__ == '__main__':
    main()
