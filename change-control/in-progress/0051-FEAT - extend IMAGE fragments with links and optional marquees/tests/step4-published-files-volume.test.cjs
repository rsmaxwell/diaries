/* Regression: 0051 published upload requires Linux local storage primitives. */
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const main = fs.readFileSync(path.join(__dirname,'step3-isolated-reader-smoke.cjs'),'utf8');
const rollout = fs.readFileSync(path.join(__dirname,'step4-rollout-rehearsal-checks.cjs'),'utf8');
const responderRoot=path.resolve(__dirname,'../../../../diaries-responder/src/main/java/com/rsmaxwell/diaries/responder');
const service=fs.readFileSync(path.join(responderRoot,'utilities/ImageCatalogueService.java'),'utf8');
const upload=fs.readFileSync(path.join(responderRoot,'handlers/UploadFile.java'),'utf8');

test('upload RPC checks private POSIX, hardlink, lock, atomic rename capabilities',()=>{
  assert.match(upload,/verifyStorageCapabilities\(\)/);
  for (const s of ['channel.tryLock()','Files.createLink(link, source)','StandardCopyOption.ATOMIC_MOVE','rwx------']) assert(service.includes(s),s);
});
test('Step 4 published-image run creates an owned unique Docker local volume',()=>{
  assert.match(main,/const filesVolume = prefix \+ '-files'/);
  assert.match(main,/if \(step4Rehearsal\) \{\s*\/\/ Docker's local Linux volume/);
  assert.match(main,/await docker\('volume','inspect',filesVolume\)/);
  assert.match(main,/Refusing to reuse pre-existing Docker volume/);
  assert.match(main,/await docker\('volume','create'/);
  assert.match(main,/filesVolumeCreated=true/);
});
test('preflight operates on Linux volume and checks staging permissions and hardlinks before responder startup',()=>{
  assert.match(main,/const preflight = await docker\('run','--rm'/);
  assert.match(main,/stat -c %a \/data\/files\/\.image-staging/);
  assert.match(main,/ln "\$f" "\$f.link"/);
  assert.match(main,/STEP4_FILES_PREFLIGHT_PASS/);
  const preflight=main.indexOf('const preflight = await docker(');
  const responderStart=main.indexOf("await container(responder, ['-p'",preflight);
  assert(preflight>=0 && responderStart>preflight);
});
test('candidate and legacy responders reuse the same Linux volume without Windows Files bind mount',()=>{
  assert.match(main,/`type=volume,source=\$\{filesVolume\},target=\/data\/files`/);
  assert.equal((rollout.match(/`type=volume,source=\$\{filesVolume\},target=\/data\/files`/g)||[]).length,2);
  assert.doesNotMatch(rollout,/type=bind,source=\$\{path.join\(output,'files'\)\},target=\/data\/files/);
  assert.match(main,/owned,filesVolume,/);
  assert.match(rollout,/owned,filesVolume,/);
});
test('volume is removed after containers even on failure; cleanup failure is fatal',()=>{
  assert.match(main,/if\(filesVolumeCreated\)\{[\s\S]*?await docker\('volume','rm',filesVolume\)/);
  assert(main.indexOf("await docker('rm','-f',name)") < main.indexOf("await docker('volume','rm',filesVolume)"));
  assert.match(main,/cleanup\.filesVolumeRemoved=true/);
  assert.match(main,/summary\.cleanupFailures=cleanup\.failures; if\(cleanup\.failures\.length\)/);
});
test('normal Step 3 direct JAR and Windows smoke mode remain unchanged',()=>{
  assert.match(main,/if \(step4Rehearsal\) \{[\s\S]*?\} else \{\s*await container\(responder,/);
  assert.match(main,/exec java -jar \/fixture\/responder\.jar --config \/fixture\/responder\.json/);
  assert.doesNotMatch(main,/nas-photo|data\/database\/common|docker compose down/);
});
