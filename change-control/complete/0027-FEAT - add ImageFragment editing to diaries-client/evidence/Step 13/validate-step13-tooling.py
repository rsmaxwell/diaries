from pathlib import Path
import sys
root=Path(__file__).resolve().parents[5]
errors=[]
acl=(root/'config/mosquitto/aclfile.txt').read_text(encoding='utf-8')
block=acl.split('user diaries-client',1)[1].split('user diaries-responder',1)[0]
if 'topic read diaries/images/+' not in block:
    errors.append('diaries-client block does not grant diaries/images/+ read')
step=Path(__file__).resolve().parent
required=['step13-common.ps1','step13-begin.ps1','step13-preflight.ps1','prepare-step13-gate-config.ps1','run-responder-step13.ps1','step13-capture-state.ps1','step13-run-path.ps1','step13-import-rpc-diagnostics.ps1']
for name in required:
    if not (step/'tooling'/name).is_file(): errors.append('missing '+name)

diag=root/'diaries-client/src/app/mqtt/step13-rpc-diagnostics.ts'
if not diag.is_file(): errors.append('missing client Step 13 RPC diagnostic capture')
else:
    text=diag.read_text(encoding='utf-8')
    for marker in ['__diariesStep13RpcDiagnostics','imageIdState','addImageFragment','updateFragment']:
        if marker not in text: errors.append('client Step 13 RPC diagnostics missing '+marker)
impl=(root/'change-control/in-progress/0027-FEAT - add ImageFragment editing to diaries-client/IMPLEMENTATION-STEPS.md').read_text(encoding='utf-8')
if 'Status: IMPLEMENTED / LIVE EXECUTION' not in impl:
    errors.append('Step 13 implementation/live-execution status not recorded')
if errors:
    print('\n'.join('FAIL: '+x for x in errors)); sys.exit(1)
print('PASS: Step 13 tooling, redacted RPC diagnostics and client Image-topic ACL are present')
print('PASS: feature-specific tooling lives under change-control evidence, not live scripts/')
