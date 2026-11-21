/* Read-only source checks; NOT a replacement for the Docker rehearsal. */
'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'../../../..');
const current=fs.readFileSync(path.join(__dirname,'step3-isolated-reader-smoke.cjs'),'utf8');
const rollout=fs.readFileSync(path.join(__dirname,'step4-rollout-rehearsal-checks.cjs'),'utf8');
const ps=fs.readFileSync(path.join(__dirname,'../tools/verify-step4-disposable-rollout.ps1'),'utf8');
const ignore=fs.readFileSync(path.join(root,'diaries-client/scripts/files/Dockerfile.dockerignore'),'utf8');
test('Step 3 implementation remains available when Step 4 opt-in is absent',()=>{
  assert.match(current,/const step4Rehearsal = process\.env\.STEP4_ROLLOUT_REHEARSAL === '1'/);
  assert.match(current,/if \(step4Rehearsal\) \{/);
  assert.match(current,/if \(process\.env\.STEP3_EDITOR_ONLY === '1'\)/);
});
test('Writer and extension flags remain independent',()=>{
  assert.match(current,/const responderConfig = \(imageWritesEnabled, extensionWritesEnabled = imageWritesEnabled\)/);
  assert.match(current,/JSON\.stringify\(responderConfig\(step4Rehearsal, false\)/);
  assert.match(rollout,/responderConfig\(true,false\)/);
  assert.match(rollout,/responderConfig\(true,true\)/);
});
test('Old images cannot be started after activating new URL state',()=>{
  const boundary=rollout.indexOf('summary.extensionWritePerformed=true');
  const legacy=rollout.indexOf('await container(responder,[...legacyResponderArgs');
  const reupgrade=rollout.indexOf('await container(responder,[...newResponderArgs');
  assert(legacy>0&&reupgrade>legacy&&boundary>reupgrade);
  assert.match(rollout,/olderBinariesRestartedAfterExtensionWrite=false/);
  assert.match(rollout,/oldBinariesSafeRollbackTarget=false/);
});
test('Gated operations, preserved data and old-client checks are explicit',()=>{
  for (const s of ['blockedCreate,403','rejectedUpdate,403','blockedMarquee,403',
                   "oldPlain,200",'candidateClient=await clientHttp',"oldClient=await clientHttp",
                   'retainedPayload(activatedRetained']) assert(rollout.includes(s),s);
});
test('No NAS, production Compose or destructive DB scripts in rehearsal',()=>{
  for(const source of [rollout,ps]){
    assert.doesNotMatch(source,/await\s+docker\(['"](?:compose|push)['"]|Run-Logged\s+['"]docker['"]\s+@\(['"](?:compose|push)['"]/i);
    assert.doesNotMatch(source,/\bNAS_HOST\b|nas-photo|\/mnt\/nas/i);
  }
  assert.match(ps,/Get-FileHash/);
  assert.match(ps,/STEP4_ROLLOUT_REHEARSAL/);
});
test('Client image build excludes Windows dependencies and outputs',()=>{
  assert.match(ignore,/node_modules\//);
  assert.match(ignore,/\.angular\//);
});

// Regression: PowerShell treats "$part:" as an invalid scoped variable reference.
test('Candidate identity output uses valid PowerShell interpolation before Docker starts',()=>{
  assert.match(ps,/Write-Host "Candidate \$\{part\}: \$\(\$details\.Id\)"/);
  assert.doesNotMatch(ps,/Candidate \$part:/);
});

// 0051 Step 4 regression: image IDs are daemon-specific. Verify the measured
// production RepoDigests (and architecture), never compare a local .Id to
// the production .Id as if they were identical content-addressing schemes.
test('Published legacy images require exact production digests and platform',()=>{
  for(const sha of [
    'd0f9224d759e06cabf26eb19722b3b417b170f7c6e3919c481acbe64db507695',
    '9b510d4611792bb37907ec45c0400f11cdc7baa7e7dfaecd007a8e7ec9427edd',
    '063e5296f9b49f40f43bf89cc2d5ce4fcdc63a98efe211a57ae884a30981254b']){
    assert(ps.includes(sha),`expected published digest missing: ${sha}`);
  }
  for(const pattern of [
    /\$localDigests\s*=\s*@\(\$details\.RepoDigests/,
    /\$localDigests -ccontains \$expectedDigest/,
    /\$platform -cne 'linux\/amd64'/,
    /throw "Legacy \$part repository digest mismatch:/,
    /throw "Legacy \$part platform mismatch:/,
    /baseline-image-identities\.json/,
    /productionImageId=\$productionImageIds\[\$part\]/]) assert.match(ps,pattern);
  assert.doesNotMatch(ps,/\$details\.Id -ne \$oldIds\[\$part\]/);
});
