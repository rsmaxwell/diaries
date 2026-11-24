#!/usr/bin/env python3
'''0028 Step 4 non-destructive status updater for live Windows Diaries checkout.

Only adds/replaces a clearly identified current-status section. Does not replace
historic plan text. Leaves Step 4 OPEN and feature under in-progress.
'''
from pathlib import Path
import subprocess, sys

FEATURE = Path('change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments')
START = '<!-- 0028-STEP4-CURRENT-STATUS-BEGIN -->'
END = '<!-- 0028-STEP4-CURRENT-STATUS-END -->'
README_NOTE = '''**Current accepted status (24 November 2026):** Steps 1 and 2 technical
acceptance recorded; **Step 3 CLOSED by explicit owner acceptance** after 71
production conversions, database postflight, MQTT startup synchronisation and
Editor/Reader visual acceptance. Fragment **1564 remains DEFERRED**.
The temporary production migration stage has been SHA-256 archived to ignored
private evidence and removed from `pluto`. **Step 4 remains OPEN** pending
final documentary reconciliation and explicit *feature* closure approval.
See [Step 4 closure review](reports/STEP4-CLOSURE-REVIEW-20261124.md).

Historical planning/status paragraphs below describe earlier checkpoints, not
current production state.'''
STEPS_NOTE = '''**Current step status (24 November 2026):** Step 1 accepted;
Step 2 accepted; **Step 3 CLOSED (owner accepted 24 November)**; **Step 4 OPEN**.
The 71-conversion production apply and postflight succeeded; Fragment 1564 is
DEFERRED. The accepted Editor/Reader checks and MQTT startup synchronisation
are documented in `reports/STEP3-PRODUCTION-ACCEPTANCE-20261124.md`.
The staged production migration files were archived and the exact `pluto`
transient stage removed. See `reports/STEP4-CLOSURE-REVIEW-20261124.md`.
**Do not mark Step 4 CLOSED or move the feature to `complete` without explicit
owner approval.** Earlier OPEN labels in historical step headings are retained
for traceability and superseded by this current status.'''

def update(path, note):
    if not path.is_file():
        raise RuntimeError(f'Missing current checkout document: {path}')
    old=path.read_text(encoding='utf-8')
    if not old.startswith('# '):
        raise RuntimeError(f'Unexpected document structure: {path}')
    section=START+'\n\n'+note+'\n\n'+END
    if START in old or END in old:
        if old.count(START)!=1 or old.count(END)!=1:
            raise RuntimeError(f'Conflicting status markers: {path}')
        a=old.index(START); b=old.index(END)+len(END)
        new=old[:a]+section+old[b:]
    else:
        idx=old.find('\n')+1
        new=old[:idx]+'\n'+section+'\n'+old[idx:]
    if new!=old:
        path.write_text(new,encoding='utf-8')
        print('UPDATED:',path)
    else:
        print('UNCHANGED:',path)

def main():
    if not (Path('.git').exists() and FEATURE.is_dir()):
        raise RuntimeError('Run at the Windows Diaries parent repository root')
    report=FEATURE/'reports/STEP4-CLOSURE-REVIEW-20261124.md'
    if not report.is_file():
        raise RuntimeError('Merge the ZIP before running this helper')
    for path,note in ((FEATURE/'README.md',README_NOTE),
                      (FEATURE/'IMPLEMENTATION-STEPS.md',STEPS_NOTE)):
        update(path,note)
    print('PASS: current status recorded; feature remains in-progress')
    print('Review: git diff -- "'+str(FEATURE/'README.md')+'" "'+str(FEATURE/'IMPLEMENTATION-STEPS.md')+'"')

if __name__=='__main__':
    try: main()
    except Exception as e:
        print('FAIL:',e,file=sys.stderr); sys.exit(1)
