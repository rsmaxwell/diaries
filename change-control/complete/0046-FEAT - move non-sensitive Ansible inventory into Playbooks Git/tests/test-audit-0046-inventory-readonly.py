#!/usr/bin/env python3
"""Offline tests for audit-0046-inventory-readonly.py using fake secrets only."""
import importlib.util
from pathlib import Path
import tempfile

TARGET = Path(__file__).resolve().parents[1]/'tools'/'audit-0046-inventory-readonly.py'
spec=importlib.util.spec_from_file_location('audit0046',TARGET)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    (root/'hosts').write_text('[all]\nexample\n')
    (root/'group_vars').mkdir()
    (root/'host_vars').mkdir()
    (root/'group_vars'/'all.yaml').write_text('normal: okay\nsecret_password: !vault |\n  $ANSIBLE_VAULT;1.1;AES256\n  abcdef\n')
    (root/'host_vars'/'example.yaml').write_text('password: not_a_real_password\n')
    assert m.audit(root,Path('/nonexistent'),check_decrypt=False)==2
    (root/'host_vars'/'example.yaml').write_text('password: !vault |\n  $ANSIBLE_VAULT;1.1;AES256\n  abcdef\n')
    assert m.audit(root,Path('/nonexistent'),check_decrypt=False)==0
    (root/'host_vars'/'example.yaml').write_text('password: !vault |\n  not-a-vault-string\n')
    assert m.audit(root,Path('/nonexistent'),check_decrypt=False)==1
print('PASS: audit script detects heuristic plaintext candidates and malformed Vault markers')
