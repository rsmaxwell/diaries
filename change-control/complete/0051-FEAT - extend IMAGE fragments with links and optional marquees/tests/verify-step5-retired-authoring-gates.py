#!/usr/bin/env python3
"""0051 Step 5: static contract validation for retired IMAGE authoring gates.

Run from the Diaries parent repository root, optionally passing the Playbooks role:
  python3 'change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees/tests/verify-step5-retired-authoring-gates.py' [--playbooks-role /home/richard/ansible-controller/playbooks/roles/diaries]
"""
import argparse
from pathlib import Path
import sys

GATES = ("imageFragmentWritesEnabled", "imageFragmentExtensionsWritesEnabled",
         "ImageFragmentWritePolicy", "ImageFragmentExtensionsWritePolicy")
ANSIBLE = ("diaries_image_fragment_writes_enabled", "diaries_image_fragment_extensions_writes_enabled")

def no_gates(path):
    if not path.is_file():
        raise AssertionError("Missing file: " + str(path))
    text = path.read_text(encoding="utf-8")
    found = [key for key in GATES + ANSIBLE if key in text]
    if found:
        raise AssertionError(str(path) + " retains: " + ", ".join(found))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--playbooks-role', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4] # change-control/in-progress/0051/tests -> Diaries
    assert (root / 'diaries-responder/src/main/java').is_dir(), root
    java = root / 'diaries-responder/src/main/java/com/rsmaxwell/diaries/responder'
    for source in java.rglob('*.java'):
        no_gates(source)
    for klass in ('ImageFragmentWritePolicy.java','ImageFragmentExtensionsWritePolicy.java'):
        assert not (java/'utilities'/klass).exists(), klass
    no_gates(root/'scripts/windows/validation/smoke-imagefragment-reader.cjs')
    no_gates(root/'change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees/tests/step3-isolated-reader-smoke.cjs')
    no_gates(root/'config/environments/local.env.example')
    print('PASS: Responder and disposable reader smoke have no retired authoring gates')
    if args.playbooks_role:
        role = args.playbooks_role
        for rel in ('defaults/main.yaml','tasks/main.yaml','tasks/copy.yaml',
                    'templates/config/responder/responder.json.j2','README.md'):
            no_gates(role/rel)
        print('PASS: Playbooks role has no retired authoring gates')
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (AssertionError, OSError) as exc:
        print('FAIL:', exc, file=sys.stderr)
        sys.exit(1)
