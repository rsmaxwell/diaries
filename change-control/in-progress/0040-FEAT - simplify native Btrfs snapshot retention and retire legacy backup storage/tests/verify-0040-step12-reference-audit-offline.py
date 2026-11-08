#!/usr/bin/env python3
"""Regression: compiled bytecode is not an operational dependency, live scripts are.

Run with ordinary Python; no SSH connections or host changes are performed.
The tested scanner is extracted from the exact remote command built by the tool.
"""
import importlib.util
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
from unittest.mock import patch

feature = Path(__file__).resolve().parents[1]
source = feature / 'tools/retire-0040-obsolete-code.py'
spec = importlib.util.spec_from_file_location('retire_0040', source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

candidates = [
    {'path': '/usr/local/bin/btrfs-native-push'},
    {'path': '/usr/local/libexec/btrfs-native-endpoint'},
]

with tempfile.TemporaryDirectory() as temp:
    root = Path(temp) / 'bin'
    root.mkdir()
    libexec = Path(temp) / 'libexec'
    libexec.mkdir()
    bytecode = root / '__pycache__' / 'btrfs-native-pushcpython-312.pyc'
    bytecode.parent.mkdir()
    bytecode.write_bytes(b'\x00pyc\x00' + b' '.join(c['path'].encode() for c in candidates))
    operational = root / 'operational-health.py'
    operational.write_text('print("healthy")\n')

    def local_scanner(host, command, *, data=None, binary=False):
        assert host == 'mars'
        assert command.startswith('sudo -n python3 -c ')
        # Run the exact scanner from the command, substituting only its host
        # identity and search roots so the fixture never reads production paths.
        scanner = shlex.split(command)[-1]
        assert "'/usr/local/libexec'" in scanner, 'Audit must cover retained libexec scripts'
        host_guard = "assert os.uname().nodename.split('.')[0] == req['host']"
        assert scanner.count(host_guard) == 1
        scanner = scanner.replace(host_guard, "assert req['host'] in ('mars', 'backup')")
        scanner, changed = re.subn(
            r'roots=\(.+?\)\nextra=\(.+?\)\nchecks=',
            'roots=(' + repr(str(root)) + ', ' + repr(str(libexec)) + ')\nextra=()\nchecks=',
            scanner,
            count=1,
            flags=re.S,
        )
        assert changed == 1, 'Could not isolate audit search roots'
        completed = subprocess.run(
            [sys.executable, '-c', scanner],
            input=data,
            text=True,
            capture_output=True,
            check=False,
            timeout=15,
        )
        assert completed.returncode == 0, completed.stderr
        return completed.stdout

    with patch.object(module, 'ssh', side_effect=local_scanner):
        # Bytecode from retired modules may mention the entire legacy stack;
        # the cache is inert and must not block the audited removal set.
        module.audit_unretired_references('mars', candidates)

        # A remaining executable/source reference is a real dependency, and
        # must still block deletion of the legacy executable(s).
        operational.write_text('LEGACY = "/usr/local/bin/btrfs-native-push"\n')
        try:
            module.audit_unretired_references('mars', candidates)
        except RuntimeError as error:
            assert 'unretired references' in str(error)
            assert 'operational-health.py' in str(error)
            assert '/usr/local/bin/btrfs-native-push' in str(error)
        else:
            raise AssertionError('Active legacy reference was not detected')

        # Non-retired /usr/local/libexec scripts are scanned too.
        operational.write_text('print("healthy")\n')
        libexec_live = libexec / 'active-helper.py'
        libexec_live.write_text('ENDPOINT = "/usr/local/libexec/btrfs-native-endpoint"\n')
        try:
            module.audit_unretired_references('mars', candidates)
        except RuntimeError as error:
            assert 'active-helper.py' in str(error)
            assert '/usr/local/libexec/btrfs-native-endpoint' in str(error)
        else:
            raise AssertionError('Active libexec legacy reference was not detected')
        libexec_live.unlink()

        # Legitimate scripts without references remain eligible.
        operational.write_text('print("healthy")\n')
        module.audit_unretired_references('mars', candidates)

print('PASS: ignore compiled caches, continue blocking live legacy references')
