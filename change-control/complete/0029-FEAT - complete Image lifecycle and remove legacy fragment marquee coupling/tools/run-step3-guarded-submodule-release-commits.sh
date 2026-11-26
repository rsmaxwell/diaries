#!/usr/bin/env bash
# 0029-FEAT: exact-source guarded submodule release commits.
# Interactive terminals remain safe: fail-fast applies to this child process only.
set -euo pipefail
MODE="${1:---plan}"
if [[ "$MODE" != --plan && "$MODE" != --commit ]]; then
  echo 'Usage: bash <script> [--plan|--commit]' >&2; exit 2
fi
ROOT="$(git rev-parse --show-toplevel)"
if [[ ! -f "$ROOT/.gitmodules" || ! -d "$ROOT/diaries-responder" ]]; then
  echo 'FAIL: run from the Diaries parent checkout' >&2; exit 1
fi
export DIARIES_0029_ROOT="$ROOT"
export DIARIES_0029_MODE="$MODE"
python3 - <<'PYINNER'
import hashlib,os,subprocess,sys
from pathlib import Path
root=Path(os.environ['DIARIES_0029_ROOT']); mode=os.environ['DIARIES_0029_MODE']
data={'diaries-client': ('1f470618fcd475d871ced79fe9752a99b1111240',
                    [('src/app/dayview/dayview.component.ts',
                      '8f34a342bb617e45797fabad1e4cf1cab83354db29a9249e46d867a60a5c1057'),
                     ('src/app/diary/annual-editor/annual-editor.component.html',
                      '95a545444fc15ddfbf1ad23c2509360e4b710214f6140da70c329ffc6b399a72'),
                     ('src/app/diary/annual-editor/annual-editor.component.ts',
                      '6078775ba99966c11e315b0d5d5449557895d63e99f999094afa191b7646ad27'),
                     ('src/app/diary/diary.component.html',
                      'dad2d93ee2c0a5191d0559ebd2e4230a1019933ce7eed57672f9149eb7328e67'),
                     ('src/app/diary/diary.component.spec.ts',
                      'ccce3d86addf2ea3a34af75ee27d046007391e8b2a1ad8e102321f712ef19eff'),
                     ('src/app/diary/diary.component.ts',
                      '61be7c73744d31ff3305a08ceb296dac35cfc8f893d2be7702c29d89e0f4f045'),
                     ('src/app/model/annual-fragment-request.spec.ts',
                      '85c2c2fce1bdaa2dc32b020c6d2ec3d52a2aa0b01993a2bf74f40066bf6b62eb'),
                     ('src/app/model/annual-fragment-request.ts',
                      'b05a7b1ca1810f8d7e76331b890bd3f0c6b3dbd8662667276938218998f72581'),
                     ('src/app/model/annual-fragments.spec.ts',
                      'd0828c942d13c4804b675b1958005ae07e8616437f37c1a178816adb9f72bceb'),
                     ('src/app/model/annual-fragments.ts',
                      'a03d5dc57da064d8478c552b01807576d43ea39d79c46bf5345aa06f640c7747'),
                     ('src/app/model/fragment.ts',
                      '835a762ff2fd3dee0e54c488300af237fa06220c5dff005618adc578caea39fa'),
                     ('src/app/mqtt/rpc.service.ts',
                      '2af9c1e9ac6b66d497fe7f54ef4464b5e8838ef54b3d891f87ab6677d7fd80c6')]),
 'diaries-responder': ('7aa6296e0c675b3d315e9a46bb0dd70202a8cd55',
                       [('src/main/java/com/rsmaxwell/diaries/responder/Responder.java',
                         '9ef6422b2e1a3c83d88d404b4eef5d7ef98481eb3f77b3702f5c42d550d80b9e'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/dto/FragmentDBDTO.java',
                         'f336cfd51ebd7f3ea089f126aba4823536ce437bde9beb2301f1f1b472fa256a'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/dto/FragmentPublishDTO.java',
                         '39aa76bae7c95d6f625fd14432e658852f489874274bfe7507cc5ba62372285a'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/dto/MarqueeDBDTO.java',
                         '978e3def8767e0da9e1aedfc8a9e84c30264d04828da6602e7d21af94f692222'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/handlers/AddAnnualFragment.java',
                         'c47bbd67930e02047e67113cd47cf03a44995149e1dfbc2d4b75db00912bff84'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/handlers/AddFragment.java',
                         'bad1d3a69e93e8c683113697d0fabac72dcf0669744b736d3f174327c59a386b'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/handlers/AddImageFragment.java',
                         '824687416272d67d5b59bbcf9c2ace2b91986d82deafb90414d298e69c1fbb42'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/handlers/AddMarquee.java',
                         '2909fb6212336cad4f7292ec21d11fb37171fe0adebff295465c8d3a16e8c630'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/handlers/DeleteFragment.java',
                         '73175d18ed330324215faf3f5e7c02d820d59ef08584d1ece4a9a310315a83d5'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/handlers/NormaliseFragments.java',
                         '002212e68f43114343e7db7cdecc6a3900ca3224d9b097923885ab6a1fd9730e'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/handlers/UpdateFragment.java',
                         '95fd2177e13ce2e42fc0b8f46bf8fd812e87cf0f30da4284f73726908626a5e9'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/handlers/UpdateMarquee.java',
                         '74a010323b2b08613678f0becdd29239f18ad2f2057a822318057050980e6586'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/migration/migration0022/Migration0022Inventory.java',
                         'aab15c47acaadb889455a74264fb6f3b8a39be5e5be549e7dea9a825dfae8d2a'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/migration/migration0028/MigrationStore.java',
                         '8100c29b541a2c45c23a9100bf0c20a7a01fa1a0774693458adccf0915e751d6'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/model/Fragment.java',
                         '2587a32ff6bc9c705ce13df047e4800239837a6b44452480ad989392dfde81b5'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/model/FragmentOwnership.java',
                         'e134cbebd18404d70ca7cb7281512fd7ba9f272e7bd74e5931a95ed0bf33c6b1'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/model/FragmentPlacement.java',
                         '78645e16c1dfca74aea8e43b7d5559e6ddeae60cf7006aa4dcf4febea6c392d2'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/model/FragmentType.java',
                         '73fb8fe97921e177938190f11f64b738f32ec4898015927bbbd41d33dc391b4f'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/model/Marquee.java',
                         'a3c000e1f0590ce0fdb4eda949404f3cc81951c0aa8d98f8890858e2435058de'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/repository/FragmentRepository.java',
                         'e8731e9aa156878987d4fbc8aa5faadf92a6946f2421de7350dfbed4aa5cdb71'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/repositoryImpl/FragmentRepositoryImpl.java',
                         '2ce295ba3beea4f223a4d4266ac56ee2d65cf9c3b0e916a2b0bf004ccb5f0d37'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/repositoryImpl/MarqueeRepositoryImpl.java',
                         '2b0d645afd2b7a79cb284534e2ac97a77db62a535c49c90f79e6096a03dd10d4'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/sync/Synchronise.java',
                         '9a3f975d00fcd30c441173f6bebbd84f4cd0f0284a78bffece63316fe513b42e'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/utilities/DiaryContext.java',
                         '5ce91a9d1e0a1405859dae3c59a86782396acbb853183c9d7bb8522398fe7d72'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/utilities/FragmentLocking.java',
                         '193e03feeb554b3dd444377f5d998eae280bf50b7bf89a260167c88758fc888f'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/utilities/FragmentSequenceNormaliser.java',
                         'cd5726bb08e53fca58ea7fb6447d2da86f857103dabbcc404f311971da72b177'),
                        ('src/main/java/com/rsmaxwell/diaries/responder/utilities/ResolvedFragmentState.java',
                         '04d138e395052484433f4c329793f8dfc98313c699a894701ac3ed1ab9578883'),
                        ('src/test/java/com/rsmaxwell/diaries/responder/ImageWiringIntegrationTest.java',
                         '6b4e2f1918543408f0452cf3028ba48fb1a343f72ed5fc0e5b5aa00a49549ca7'),
                        ('src/test/java/com/rsmaxwell/diaries/responder/dto/FragmentAnnualTopicTest.java',
                         'cb20829787f7ede550cccf2c68fa9ce36cb1b16e82c53572b3aaef8bce930b51'),
                        ('src/test/java/com/rsmaxwell/diaries/responder/dto/RetainedStateDtoContractTest.java',
                         'b37540421e5b8f1ce0126ede26e291a60228cd2a6d15288369d445efcde1e247'),
                        ('src/test/java/com/rsmaxwell/diaries/responder/handlers/AddFragmentContractTest.java',
                         'a1c7a6523fa833d002d9427dd75dfe3eb1702449b1cc3e069bb90ad5a20b8ee9'),
                        ('src/test/java/com/rsmaxwell/diaries/responder/handlers/AddImageFragmentTest.java',
                         '9f019cb95f790a7e98b3e2f2149b248ee7cca34ca7a276c257dd47982d2e8f82'),
                        ('src/test/java/com/rsmaxwell/diaries/responder/handlers/FragmentLifecycleContractTest.java',
                         '397c170c7e527d773aef41408341f343519ba2c24b8192f463de17bd0d9959e6'),
                        ('src/test/java/com/rsmaxwell/diaries/responder/handlers/UpdateFragmentImageTest.java',
                         'c0dc1a89d1e64b42d56f6ae44b702d656770e0e9119dac457ea887df8f2f3e55'),
                        ('src/test/java/com/rsmaxwell/diaries/responder/model/FragmentOwnershipTest.java',
                         '849a15fd1d6fd230f5bb3f79d1b945dc92aff74829fb78a4d3a4102270e3dde2'),
                        ('src/test/java/com/rsmaxwell/diaries/responder/model/MarqueeOwnerContractTest.java',
                         'e3f9aca7fbd442f0dc39e7eb3a86d288b9860d37470a75b5ca1b889f38e00f22'),
                        ('src/test/java/com/rsmaxwell/diaries/responder/repositoryImpl/FragmentRepositoryImplTest.java',
                         '0234b29af200e2db40cc47ccb601fa68998668b703f1a04385f53049774bdb61'),
                        ('src/test/java/com/rsmaxwell/diaries/responder/sync/SynchroniseCallbackTest.java',
                         '0db0cd4bdc58572fe7ae0ee6e6689600f73d9f10197454bb2dd3779033af2e69'),
                        ('src/test/java/com/rsmaxwell/diaries/responder/utilities/DiaryContextTest.java',
                         '909f1ec28ed1a35f2d1f4c2e1c61be1cb89d31d81279327071f8e41215f40d26'),
                        ('src/test/java/com/rsmaxwell/diaries/responder/utilities/FragmentSequenceNormaliserTest.java',
                         '254e15046d3afe01a1c6886d5cbf31c83f6c3bdb5a60012ac36d45c2dcd13cd9'),
                        ('src/test/java/com/rsmaxwell/diaries/responder/utilities/ImageLinkWritePolicyTest.java',
                         '8e9e616cabb6d0e2585f7531472eb141b5cdb930a1ce81db83414c1819aae9fc'),
                        ('src/test/java/com/rsmaxwell/diaries/responder/utilities/ResolvedFragmentStateTest.java',
                         '8a3e8fe954e68fb24c12a6334be6e0bbf2a6d3ed05b1284665c37f59a8e418ac')]),
 'diaries-web': ('6d1b289bc5a7983cbf36fe771f8c11dc4725813b',
                 [('src/main/java/com/rsmaxwell/diaries/web/http/WebServer.java',
                   '98b3c38e1ff6d45843e17f0043945d25ac86ad7e88af270769e85d41b493f8bf'),
                  ('src/main/java/com/rsmaxwell/diaries/web/model/FragmentItem.java',
                   '41a915b55186995cfc2b6ad3bf423ab3cbeb51a81855374b47782bfbd73d6159'),
                  ('src/main/java/com/rsmaxwell/diaries/web/model/FragmentPlacement.java',
                   '8a245192baeb5075e6bc830651acc870f187a6241bd0a261d2b4615745012186'),
                  ('src/main/java/com/rsmaxwell/diaries/web/model/FragmentType.java',
                   '8fa024d3a47994a8f66b15105fcd3f9b66d22c874f374ce9fe9cd1f7b1549365'),
                  ('src/main/java/com/rsmaxwell/diaries/web/projection/DiaryYearPlacementKey.java',
                   'b811566cfd2674242b85ac0db58cb9314e45ca605ef79c212f8da7301812690b'),
                  ('src/main/java/com/rsmaxwell/diaries/web/projection/ProjectionSnapshot.java',
                   '709974533a660c74f64b8253c445637e8d90d226d449bbbf01b30eebcd57cce5'),
                  ('src/main/resources/templates/month-reader.peb',
                   '276dca5208a6b188557131f6f0606822c63f3638d0ba7c2747fcd1d6fdd1b0b7'),
                  ('src/test/java/com/rsmaxwell/diaries/web/mqtt/RetainedContractTest.java',
                   'a056c71da59c6bd122a857b3e675b47131d6572875ba477a9e61897c1596f40d'),
                  ('src/test/java/com/rsmaxwell/diaries/web/projection/ProjectionServiceTest.java',
                   '12ccaa0e4ad62fb7c8e879b6522975254a85a41d0458d81452509365db2b97b1'),
                  ('src/test/java/com/rsmaxwell/diaries/web/rendering/RenderingSafetyTest.java',
                   'cd413c6aa5225aebe753356e5d9a70dd84e37082a88731f5e9d037711f53460c')])}

def git(path,*args,check=True):
    r=subprocess.run(['git','-C',str(path),*args],text=True,capture_output=True)
    if check and r.returncode:
        raise RuntimeError(f'git {args} failed in {path}: {r.stderr.strip()}')
    return r.stdout.strip()

# First check ALL repositories and files; no partial commits due to a late validation failure.
problems=[]
for name,(expected,entries) in data.items():
    folder=root/name
    head=git(folder,'rev-parse','HEAD')
    if head != expected: problems.append(f'{name}: HEAD changed: {head} != {expected}')
    branch=git(folder,'branch','--show-current')
    if branch!='main':problems.append(f'{name}: expected branch main, got {branch}')
    staged=git(folder,'diff','--cached','--name-only')
    if staged: problems.append(f'{name}: index already has staged changes; do not overwrite: {staged}')
    expected_names={p for p,h in entries}
    # Do not accidentally exclude unexpected modified/untracked source changes.
    tracked=git(folder,'diff','--name-only').splitlines()
    untracked=git(folder,'ls-files','--others','--exclude-standard').splitlines()
    extras=[x for x in tracked+untracked if x not in expected_names]
    if extras: problems.append(f'{name}: unreviewed files present: {extras}')
    for rel,hash_value in entries:
        path=folder/rel
        if not path.is_file():problems.append(f'{name}: missing {rel}');continue
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != hash_value:problems.append(f'{name}: SHA mismatch for {rel}: {actual}')
    print(f'{name}: HEAD={head}, branch={branch}, reviewed files={len(entries)}, unrelated unstaged files={len(extras)}')
if problems:
    print('FAIL: release-source checks did not pass:',file=sys.stderr)
    for p in problems:print(' - '+p,file=sys.stderr)
    sys.exit(1)
print('PASS: all three submodules match the 2026-11-26 14:02 source manifest.')
if mode=='--plan':
    print('PLAN ONLY: no git add/commit/push performed.')
    sys.exit(0)
for name,(_,entries) in data.items():
    folder=root/name
    paths=[p for p,h in entries]
    # subprocess avoids shell wildcard expansion and Windows/Cygwin quoting hazards
    subprocess.run(['git','-C',str(folder),'add','--',*paths],check=True)
    subprocess.run(['git','-C',str(folder),'diff','--cached','--check'],check=True)
    actual=set(git(folder,'diff','--cached','--name-only').splitlines())
    if actual!=set(paths):
        print(f'FAIL: staged files differ in {name}; review with git diff --cached; no commit executed for this repository.',file=sys.stderr)
        sys.exit(1)
    subprocess.run(['git','-C',str(folder),'commit','-m','0029-FEAT: hybrid Fragment ownership and Marquee page retirement'],check=True)
    print(f'COMMITTED {name}: {git(folder,"rev-parse","HEAD")}')
print('PASS: application submodule commits created; no pushes and no parent commit.')
print('NEXT: inspect parent submodule pointers, stage 0029 docs selectively, then commit parent.')
PYINNER
