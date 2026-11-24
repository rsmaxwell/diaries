#!/usr/bin/env python3
"""Inspect/repair ONLY the local 0028 rehearsal JWT secret (never print it)."""
import argparse
import base64
import binascii
import json
import secrets
from pathlib import Path


def valid_standard_secret(s):
    if not isinstance(s, str) or not s:
        return False
    try:
        raw = base64.b64decode(s, validate=True)
    except (ValueError, binascii.Error):
        return False
    return len(raw) >= 32


def new_standard_secret():
    return base64.b64encode(secrets.token_bytes(48)).decode('ascii')


def load_config(path):
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise ValueError('Config is missing, is not a regular file or is a symlink')
    with path.open('r', encoding='utf-8') as stream:
        data = json.load(stream)
    if not isinstance(data, dict) or not isinstance(data.get('secret'), str):
        raise ValueError('Rehearsal config has no JWT secret')
    return data


def repair(config_path, backup_path):
    """Refuse valid secret and backups that exist; in-place write retains Docker bind mount."""
    original = load_config(config_path)
    if valid_standard_secret(original['secret']):
        raise ValueError('JWT secret is already valid standard Base64; do not rotate; inspect responder logs')
    backup_path = Path(backup_path)
    if backup_path.exists() or backup_path.is_symlink():
        raise ValueError('Private backup already exists; refusing overwrite')
    if not backup_path.parent.is_dir() or backup_path.parent.is_symlink():
        raise ValueError('Private backup parent missing or symlinked')
    # Backup is private; no password, JWT secret or account details are printed.
    data = Path(config_path).read_bytes()
    with backup_path.open('xb') as stream:
        stream.write(data)
    updated = dict(original)
    updated['secret'] = new_standard_secret()
    if not valid_standard_secret(updated['secret']):
        raise ValueError('Generated invalid JWT secret')
    # DO NOT use os.replace here: the config is already mounted into the
    # isolated responder as a read-only *file* bind mount.
    with Path(config_path).open('r+', encoding='utf-8') as stream:
        stream.seek(0)
        json.dump(updated, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.truncate()
    after = load_config(config_path)
    if not valid_standard_secret(after['secret']) or after['secret'] == original['secret']:
        raise ValueError('JWT secret repair did not persist')
    if {k:v for k,v in after.items() if k != 'secret'} != {k:v for k,v in original.items() if k != 'secret'}:
        raise ValueError('Unexpected config change outside secret')
    return after


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['inspect','repair'])
    parser.add_argument('config', type=Path)
    parser.add_argument('--backup', type=Path)
    args=parser.parse_args()
    data=load_config(args.config)
    if args.mode == 'inspect':
        if valid_standard_secret(data['secret']):
            print('VALID: standard Base64 JWT secret decodes to at least 32 bytes; investigate other sign-in causes')
        else:
            print('INVALID: isolated JWT secret cannot be decoded by Java standard Base64 or is too short')
    else:
        if args.backup is None:
            parser.error('repair requires --backup')
        repair(args.config, args.backup)
        print('PASS: isolated JWT secret repaired to standard Base64; all other config fields preserved')


if __name__ == '__main__':
    main()
