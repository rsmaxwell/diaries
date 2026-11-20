#!/usr/bin/env python3
"""0051 Step 4 local read-only source/deployment contract check.

No network, Ansible invocation, database connection, MQTT or production writes.
Never call this a completed deployment or live-compatible rollback rehearsal.
"""
import argparse
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone


def git_state(repo):
    if not (repo/'.git').exists():
        return {'available':False,'reason':'Source bundle contains no Git metadata'}
    def git(*args):
        r=subprocess.run(['git','-C',str(repo)]+list(args),capture_output=True,text=True)
        return r.stdout.strip() if r.returncode==0 else 'UNKNOWN'
    return {'available':True,'head':git('rev-parse','HEAD'),
            'branch':git('branch','--show-current'),
            'submodules':git('submodule','status'),
            'dirty':bool(git('status','--porcelain'))}


def check(repo,playbooks):
    prefix=Path('change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees')
    old=Path('change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments')
    paths={
        '0051_model':repo/'diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/model/Fragment.java',
        '0051_config':repo/'diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/config/Config.java',
        '0051_migration':repo/prefix/'migration/001-add-image-link-url.sql',
        '0028_inventory':repo/old/'tools/step1_inventory.py',
        '0028_checker':repo/old/'tools/step4_0051_compatibility_review.py',
        '0029_invariants':repo/'change-control/todo/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling/README.md',
    }
    texts={k:p.read_text(encoding='utf-8') for k,p in paths.items()}
    results={
       'nullable_image_link_model':'imageLinkUrl' in texts['0051_model'],
       'extensions_gate_independent':('imageFragmentExtensionsWritesEnabled' in texts['0051_config'] and
                                      'imageFragmentWritesEnabled' in texts['0051_config']),
       'additive_migration':'image_link_url' in texts['0051_migration'] and
                             'IF NOT EXISTS' in texts['0051_migration'].upper(),
       'no_obsolete_0028_image_marquee_exception':"'issue': 'IMAGE_HAS_MARQUEE'" not in texts['0028_inventory'],
       'fresh_marquee_geometry_collected':"'version',m.version" in texts['0028_inventory'] and
                                          "'width',m.width" in texts['0028_inventory'],
       '0028_checker_never_authorises_apply':"'productionApplyAllowed':False" in texts['0028_checker'],
       '0029_preserves_image_marquee':'IMAGE   => zero or one Marquee' in texts['0029_invariants'],
    }
    if playbooks:
        role=playbooks/'roles/diaries'
        defaults=(role/'defaults/main.yaml').read_text(encoding='utf-8')
        template=(role/'templates/config/responder/responder.json.j2').read_text(encoding='utf-8')
        main=(role/'tasks/main.yaml').read_text(encoding='utf-8')
        copy=(role/'tasks/copy.yaml').read_text(encoding='utf-8')
        results.update({
            'existing_image_authoring_remains_enabled': 'diaries_image_fragment_writes_enabled: true' in defaults,
            'extensions_gate_default_false':'diaries_image_fragment_extensions_writes_enabled: false' in defaults,
            'extensions_gate_rendered':'"imageFragmentExtensionsWritesEnabled": {{ diaries_image_fragment_extensions_writes_enabled | bool | lower }}' in template,
            'extensions_gate_type_asserted':'diaries_image_fragment_extensions_writes_enabled is boolean' in main,
            'extensions_gate_render_checked':'Validate rendered 0051 extension authoring gate' in copy,
        })
    return results


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--repo',type=Path,required=True)
    a.add_argument('--playbooks',type=Path)
    a.add_argument('--output',type=Path)
    args=a.parse_args()
    result={'step':'0051-Step4-source-preflight','readOnly':True,
            'timestampUtc':datetime.now(timezone.utc).isoformat(),
            'git':git_state(args.repo),'checks':check(args.repo,args.playbooks),
            'liveServicesChecked':False,'productionApproval':False,
            'mixedVersionDeploymentRehearsed':False}
    result['status']='PASS_STATIC_ONLY' if all(result['checks'].values()) else 'FAIL_STATIC'
    if args.output:
        if args.output.exists():raise SystemExit('Refusing to overwrite evidence')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status']=='PASS_STATIC_ONLY' else 1)


if __name__=='__main__':main()
