#!/usr/bin/env python3
"""Copy *reviewed catalogue image files only* into private isolated rehearsal evidence.

No image data or source path is written to stdout, only to private evidence.
Requires Python 3.7+; uses manifest paths and SHA-256, not filename inference.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys


def sha256_file(path):
    digest = hashlib.sha256()
    with open(str(path), 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def overrides(path):
    found = {}
    if path.is_file():
        for raw in path.read_text(encoding='utf-8-sig').splitlines():
            line = raw.strip()
            if '=' not in line or line.startswith('#'):
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            if key in ('DIARIES_CONTENT_DIR', 'DIARIES_FILES_DIR'):
                found[key] = value.strip().strip('"').strip("'")
    return found


def candidates(repo, explicit):
    if explicit:
        return [Path(explicit)]
    if os.environ.get('DIARIES_0028_SOURCE_FILES_ROOT'):
        return [Path(os.environ['DIARIES_0028_SOURCE_FILES_ROOT'])]
    vars_ = {'DIARIES_CONTENT_DIR': './data/responder/diaries-content',
             'DIARIES_FILES_DIR': 'files-development-infrastructure'}
    vars_.update(overrides(repo / 'config/environments/development-infrastructure.env'))
    vars_.update(overrides(repo / 'config/environments/local.env'))
    roots = [Path(vars_['DIARIES_CONTENT_DIR']) / vars_['DIARIES_FILES_DIR'],
             Path('./data/responder/diaries-content/files-development-common'),
             Path('./data/responder/diaries-content/files-development-infrastructure')]
    seen = set()
    result = []
    for root in roots:
        absolute = root if root.is_absolute() else repo / root
        normal = str(absolute.resolve())
        if normal not in seen:
            result.append(absolute)
            seen.add(normal)
    return result


def validated_path(root, rel):
    # Exact case/Unicode file identity is checked by the Java ImagePathPolicy later.
    parts = rel.replace('\\', '/').split('/')
    if not parts or any(p in ('', '.', '..') or ':' in p or '\x00' in p for p in parts):
        raise ValueError('Invalid relative Image path in approved manifest')
    path = root.joinpath(*parts)
    real_root = root.resolve(strict=True)
    real_path = path.resolve(strict=True)
    try:
        real_path.relative_to(real_root)
    except ValueError:
        raise ValueError('Reviewed image escapes the supplied Files root')
    if not real_path.is_file() or path.is_symlink():
        raise ValueError('Reviewed Image is missing, unreadable or symlinked')
    return path


def read_manifest(directory):
    with (directory / '0028-image-decisions.csv').open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    # The frozen image-decisions contract includes 71 CONVERT_TO_IMAGE rows
    # and one explicit DEFER row (1564). Never stage or infer media for DEFER.
    if len(rows) != 72:
        raise ValueError('Expected exactly 72 reviewed occurrences (71 conversions and 1 DEFER), got {}'.format(len(rows)))
    deferred = [r for r in rows if r.get('occurrence_action') == 'DEFER']
    conversions = [r for r in rows if r.get('occurrence_action') != 'DEFER']
    if (len(deferred) != 1 or deferred[0].get('fragment_id') != '1564'
            or len(conversions) != 71):
        raise ValueError('Unexpected reviewed conversion/DEFER distribution')
    for r in deferred:
        if any(r.get(key) for key in ('resolved_relative_path', 'resolved_image_id', 'expected_image_checksum')):
            raise ValueError('Deferred fragment unexpectedly carries resolved Image data')
    seen_fragments = set()
    files = {}
    for r in conversions:
        fid = r.get('fragment_id')
        if (not fid or fid in seen_fragments or r.get('occurrence_action') != 'REMOVE_AS_IMAGE'
                or not r.get('resolved_image_id')):
            raise ValueError('Unreviewed Image conversion action or duplicate Fragment')
        seen_fragments.add(fid)
        rel = r['resolved_relative_path']
        digest = r['expected_image_checksum']
        if not rel or not digest or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('Invalid approved Image path/SHA-256 for Fragment {}'.format(fid))
        if rel in files and files[rel] != digest:
            raise ValueError('One Image path has conflicting approved checksums')
        files[rel] = digest
    return files


def run(repo, manifest, root, destination):
    files = read_manifest(manifest)
    if destination.exists():
        raise ValueError('Media destination already exists; never overwrite rehearsal evidence')
    available = []
    for option in candidates(repo, root):
        if option.is_dir():
            available.append(option.resolve())
    if not available:
        raise ValueError('No Files-root candidate exists. Set DIARIES_0028_SOURCE_FILES_ROOT to your verified local Files directory.')
    chosen = None
    problems = []
    for source in available:
        try:
            for rel, expected in files.items():
                real = validated_path(source, rel)
                if sha256_file(real) != expected:
                    raise ValueError('Image checksum mismatch relative to approved production catalogue: ' + rel)
            chosen = source
            break
        except (ValueError, OSError) as error:
            problems.append(str(error))
    if chosen is None:
        raise ValueError('No candidate Files root matches all approved Image SHA-256 digests. First mismatch: ' + (problems[0] if problems else 'unknown'))
    destination.mkdir(parents=True)
    manifest_rows = []
    for rel, expected in sorted(files.items()):
        from_path = validated_path(chosen, rel)
        target = destination.joinpath(*rel.replace('\\', '/').split('/'))
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(str(from_path), str(target))
        if sha256_file(target) != expected:
            raise ValueError('Copied media checksum changed: ' + rel)
        manifest_rows.append({'relativePath': rel, 'sha256': expected, 'bytes': target.stat().st_size})
    report = {'schema': '0028-rehearsal-media-v1', 'sourceRoot_PRIVATE': str(chosen),
              'destinationRoot_PRIVATE': str(destination.resolve()), 'reviewedOccurrences': 71,
              'uniqueFiles': len(files), 'files': manifest_rows}
    report_file = destination.parent / 'MEDIA-COPY-RESULT.PRIVATE.json'
    report_file.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print('PASS: staged {} uniquely reviewed image files; 71 conversions; SHA-256 checked twice'.format(len(files)))
    print('PASS: source is unchanged; staging and full report are PRIVATE')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--output-root', required=True)
    parser.add_argument('--source-root')
    args = parser.parse_args()
    run(Path(args.repo).resolve(), Path(args.manifest).resolve(), args.source_root, Path(args.output_root))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('FAIL: staged-media validation: {}'.format(exc), file=sys.stderr)
        sys.exit(1)
