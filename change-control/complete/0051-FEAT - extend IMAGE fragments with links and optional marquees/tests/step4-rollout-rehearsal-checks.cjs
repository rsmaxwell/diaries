/* 0051 Step 4: opt-in pre-activation rollback rehearsal. All state is disposable. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

function verifyRepositoryDigest(inspected, expected, label) {
  assert.equal(inspected.architecture,'amd64',`${label} must be linux/amd64`);
  const found=(inspected.digests||[]).map(d=>d.replace(/^docker\.io\//,''));
  assert(found.includes(expected),`${label} repository digest mismatch: expected ${expected}; found ${found.join(', ')}`);
  return true;
}

async function runStep4RolloutChecks(ctx) {
  const {root,output,summary,checks,first,responder,web,broker,prefix,owned,filesVolume,
    docker,container,port,sql,rows,rpc,waitFor,write,retainedSnapshot,
    retainedPayload,expectRpcStatus,responderConfig,relogin} = ctx;
  const env = process.env;
  const images = {
    candidate: {
      responder:env.STEP4_CANDIDATE_RESPONDER_IMAGE,
      web:env.STEP4_CANDIDATE_WEB_IMAGE,
      client:env.STEP4_CANDIDATE_CLIENT_IMAGE,
    },
    legacy: {
      responder:env.STEP4_LEGACY_RESPONDER_IMAGE,
      web:env.STEP4_LEGACY_WEB_IMAGE,
      client:env.STEP4_LEGACY_CLIENT_IMAGE,
    }
  };
  for (const [kind,items] of Object.entries(images))
    for (const [component,ref] of Object.entries(items))
      assert(ref && !/\s/.test(ref),`Missing ${kind} ${component} Docker reference`);
  summary.testedImages=images;
  summary.rollbackBoundary='BEFORE first 0051 extension write only';
  summary.extensionWritePerformed=false;
  summary.olderBinariesRestartedAfterExtensionWrite=false;
  const identity={};
  for (const [kind,items] of Object.entries(images)) {
    identity[kind]={};
    for(const [part,ref] of Object.entries(items)) {
      const inspect=JSON.parse(await docker('image','inspect',ref));
      assert.equal(inspect.length,1,`Image missing: ${ref}`);
      identity[kind][part]={reference:ref,id:inspect[0].Id,
        digests:inspect[0].RepoDigests||[],architecture:inspect[0].Architecture,
        entrypoint:inspect[0].Config.Entrypoint};
    }
  }
  write('step4-image-identities.json',identity);
  // Verify the actual published repository digests measured on pluto, NOT the
  // daemon-local image IDs. OCI and Docker daemons may expose different IDs
  // for the exact same published platform image. All refs are digest-pinned.
  const requiredLegacyDigests={
    responder:'rsmaxwell/diaries-responder@sha256:d0f9224d759e06cabf26eb19722b3b417b170f7c6e3919c481acbe64db507695',
    client:'rsmaxwell/diaries-client@sha256:9b510d4611792bb37907ec45c0400f11cdc7baa7e7dfaecd007a8e7ec9427edd',
    web:'rsmaxwell/diaries-web@sha256:063e5296f9b49f40f43bf89cc2d5ce4fcdc63a98efe211a57ae884a30981254b'
  };
  for(const [part, required] of Object.entries(requiredLegacyDigests)) {
    assert.equal(images.legacy[part].replace(/^docker\.io\//,''),required,
      `Legacy ${part} Docker reference must be pinned to the observed production digest`);
    verifyRepositoryDigest(identity.legacy[part],required,`Legacy ${part}`);
  }
  for(const [part,ref] of Object.entries(images.candidate)) {
    const expected=ref.replace(/^docker\.io\//,'');
    assert.match(expected,new RegExp('^rsmaxwell/diaries-'+part+'@sha256:[a-f0-9]{64}$'),
      `Candidate ${part} reference must be digest-pinned to the published image`);
    verifyRepositoryDigest(identity.candidate[part],expected,`Candidate ${part}`);
    assert.notEqual(expected,requiredLegacyDigests[part],
      `Candidate ${part} unexpectedly matches the pre-0051 production digest`);
  }
  checks.push('All six Docker images identified by published digests and linux/amd64; local image IDs recorded, not compared across daemons');

  const seq = async(offset)=> Number((Number(await sql(`SELECT coalesce(max(sequence),0) FROM fragment WHERE year=${first.year} AND month=${first.month} AND day=${first.day}`))+offset).toFixed(4));
  const common={pageId:first.page_id,year:first.year,month:first.month,day:first.day};
  const imageBytes=fs.readFileSync(path.join(output,'inputs','selected.png'));
  const upload=await rpc('uploadFile',{name:'0051 step4 plain image',subdir:'0051/step4',
    bytes:imageBytes.toString('base64'),size:imageBytes.length,contentType:'image/png'});
  expectRpcStatus(upload,200,'upload synthetic Image while extension gate false');
  const imageId=upload.payload.imageId;
  const plainArgs={...common,sequence:await seq(100),text:'0051 pre-activation plain IMAGE',imageId};
  const added=await rpc('addImageFragment',plainArgs);
  expectRpcStatus(added,200,'existing IMAGE authoring gate remains true');
  const imageFragmentId=added.payload.id;
  const fragment=async id => (await rows(`SELECT id,version,type,image_id AS "imageId",image_link_url AS "imageLinkUrl",page_id AS "pageId" FROM fragment WHERE id=${Number(id)}`))[0];
  const before=await fragment(imageFragmentId);
  assert.equal(before.type,'IMAGE'); assert.equal(before.imageId,imageId);
  assert.equal(before.imageLinkUrl,null);
  const link='https://example.org/0051/rollback?x=1%2F2#map';
  const blockedCreate=await rpc('addImageFragment',{...common,sequence:await seq(100),text:'must be blocked',imageId,imageLinkUrl:link});
  expectRpcStatus(blockedCreate,403,'extension link creation denied while gate false');
  // Versioned update is also gated; a rejected update must not clear the URL
  // or change the saved Fragment. Release its lock after the failed request.
  expectRpcStatus(await rpc('lockFragment',{id:imageFragmentId}),200,'lock plain IMAGE before denied link update');
  const beforeVersioned=await rows(`SELECT id,version,year,month,day,sequence::float8 AS sequence,text FROM fragment WHERE id=${imageFragmentId}`);
  const rejectedUpdate=await rpc('updateFragment',{...beforeVersioned[0],imageLinkUrl:link});
  expectRpcStatus(rejectedUpdate,403,'extension link update denied while gate false');
  expectRpcStatus(await rpc('unlockFragment',{id:imageFragmentId}),200,'unlock after denied link update');
  const afterRejectedUpdate=await fragment(imageFragmentId);
  assert.equal(afterRejectedUpdate.imageLinkUrl,null,'Rejected extension update changed link');
  const blockedMarquee=await rpc('addMarquee',{fragmentId:imageFragmentId,pageId:first.page_id,
    fragmentVersion:afterRejectedUpdate.version,x:30,y:40,width:100,height:120});
  expectRpcStatus(blockedMarquee,403,'extension Marquee attachment denied while gate false');
  assert.deepEqual(await fragment(imageFragmentId),afterRejectedUpdate,'Denied Marquee creation changed Fragment');
  assert.equal(Number(await sql(`SELECT count(*) FROM marquee WHERE fragment_id=${imageFragmentId}`)),0);
  assert.equal(Number(await sql('SELECT count(*) FROM fragment WHERE image_link_url IS NOT NULL')),0,
    'Historical fixture unexpectedly contains extension links');
  write('step4-gate-disabled.json',{imageFragmentId,imageId,plainFragment:before,
    blockedLinkStatus:blockedCreate.status,blockedUpdateStatus:rejectedUpdate.status,blockedMarqueeStatus:blockedMarquee.status});
  checks.push('Gate false: ordinary IMAGE write succeeds, new URL and IMAGE Marquee writes reject with 403 without mutation');

  const legacyMarquee=await rpc('addFragment',{...common,sequence:await seq(100),text:'0051 Step4 original MARQUEE',
    x:20,y:30,width:150,height:100});
  expectRpcStatus(legacyMarquee,200,'original MARQUEE authoring under disabled extension gate');
  const originalMarqueeId=legacyMarquee.payload.id;
  const monthPath=`/reader/diaries/${first.diary_id}/${first.year}/${String(first.month).padStart(2,'0')}?fragment=${originalMarqueeId}`;
  const readyWeb = async name=>{
    const p=await port(web,8082); const base=`http://127.0.0.1:${p}`;
    await waitFor(name+' HTTP ready',async()=>
      (await fetch(base+'/reader/health/ready',{signal:AbortSignal.timeout(3000)})).ok,60000);
    await waitFor(name+' retained old-fragment rendering',async()=>{
      const response=await fetch(base+monthPath,{signal:AbortSignal.timeout(10000)});
      if(!response.ok)return false;
      const html=await response.text();
      return html.includes(`data-reader-fragment="${originalMarqueeId}"`) &&
        html.includes(`data-reader-fragment="${imageFragmentId}"`);
    },60000);
    return {port:p,status:200,legacyMarqueeVisible:true,plainImageVisible:true};
  };
  const newReader=await readyWeb('candidate reader');
  const beforeRetained=await retainedSnapshot('step4-gate-disabled-before-rollback');
  assert.equal(retainedPayload(beforeRetained,`diaries/fragments/${imageFragmentId}`).imageLinkUrl,null);
  assert.equal(retainedPayload(beforeRetained,`diaries/fragments/${imageFragmentId}`).type,'IMAGE');

  // Run each client as a short-lived HTTP-only candidate/legacy binary check.
  // Its config is synthetic, and there are NO NAS or persistent DB mounts.
  async function clientHttp(name,ref) {
    // Never copy a developer's ignored local client config into test evidence.
    // The probe fetches static HTML/config only; it does not open a writer session.
    const clientConfig={brokerMode:'direct',brokerDirectUrl:'ws://127.0.0.1:1',
      responderBaseUrlMode:'same-host-port',responderBaseUrlPort:8081,
      username:'diaries-client',password:'step13-fixture',diaries:'diaries',files:'files',
      clientId:'0051-rollout',keepalive:60,reconnectPeriod:1000,connectTimeout:30000,
      protocolVersion:5,clean:false,fragmentLockTtlSeconds:900};
    const cfg=path.join(output,'step4-client-config.json');
    fs.writeFileSync(cfg,JSON.stringify(clientConfig));
    const containerName=`${prefix}-${name}-client`;
    await container(containerName,['-p','127.0.0.1::8080','--mount',`type=bind,source=${cfg},target=/usr/share/nginx/html/diaries/assets/config.json,readonly`,ref]);
    try {
      const p=await port(containerName,8080);
      await waitFor(`${name} Angular HTTP`,async()=>{
        const response=await fetch(`http://127.0.0.1:${p}/diaries/`,{signal:AbortSignal.timeout(2500)});
        return response.ok;
      },45000);
      const r=await fetch(`http://127.0.0.1:${p}/diaries/`);
      const html=await r.text();
      assert(html.includes('<app-root'),`${name} client HTML missing Angular root`);
      const cr=await fetch(`http://127.0.0.1:${p}/diaries/assets/config.json`);
      assert(cr.ok,`${name} client config unavailable`);
      return {image:ref,status:r.status,configStatus:cr.status,port:p};
    } finally {
      await docker('rm','-f',containerName);
      const i=owned.indexOf(containerName);if(i>=0)owned.splice(i,1);
    }
  }
  const candidateClient=await clientHttp('candidate',images.candidate.client);
  checks.push('New reader and client HTTP entry points render with extension gate false');

  // Remove only containers created by this script; do not call Docker Compose
  // or touch development/production container names or volumes.
  let swapNumber=0;
  const retired=[];
  async function removeOwned(name){
    assert(owned.includes(name),`Refusing to remove unowned container ${name}`);
    const ordinal=++swapNumber;
    const record={ordinal,name};
    try {
      const inspection=JSON.parse(await docker('inspect',name))[0];
      record.id=inspection.Id;
      record.image=inspection.Image;
      record.running=inspection.State.Running;
      record.exitCode=inspection.State.ExitCode;
    } catch(error) { record.inspectError=error.message; }
    try { write(`step4-retired-${ordinal}-${name}.log`,await docker('logs','--tail','250',name)); }
    catch(error) {record.logError=error.message;}
    await docker('stop',name);await docker('rm',name);
    owned.splice(owned.indexOf(name),1);
    retired.push(record);
    write('step4-retired-containers.json',retired);
  }
  const newResponderArgs=['-p','127.0.0.1::8081',
    '-e','CONFIG_FILE=/fixture/responder.json',
    '--mount',`type=volume,source=${filesVolume},target=/data/files`,
    '--mount',`type=bind,source=${path.join(output,'diaries')},target=/data/diaries,readonly`,
    '--mount',`type=bind,source=${output},target=/fixture,readonly`];
  const legacyResponderArgs=['-p','127.0.0.1::8081',
    '-e','CONFIG_FILE=/config/responder.json',
    '--mount',`type=volume,source=${filesVolume},target=/data/files`,
    '--mount',`type=bind,source=${path.join(output,'diaries')},target=/data/diaries,readonly`,
    '--mount',`type=bind,source=${path.join(output,'step4-legacy-responder.json')},target=/config/responder.json,readonly`];
  const webEnv=['-e','DIARIES_WEB_MQTT_USERNAME=diaries-web',
    '-e','DIARIES_WEB_MQTT_PASSWORD=step13-fixture'];
  const webArgs=['-p','127.0.0.1::8082',...webEnv,
    '--mount',`type=bind,source=${path.join(output,'web.json')},target=/config/diaries-web.json,readonly`];
  const legacyConfig=responderConfig(true,false);
  delete legacyConfig.imageFragmentExtensionsWritesEnabled;
  fs.writeFileSync(path.join(output,'step4-legacy-responder.json'),JSON.stringify(legacyConfig,null,2));
  // No new-format record has been written: this is the ONLY safe rollback window.
  await removeOwned(web);await removeOwned(responder);
  await container(responder,[...legacyResponderArgs,images.legacy.responder]);
  await waitFor('old responder subscription',async()=>
    (await docker('logs','--tail','120',responder)).includes("diaries/rpc/request"),90000);
  await container(web,[...webArgs,images.legacy.web]);
  const oldReader=await readyWeb('legacy reader');
  await relogin();
  const oldPlain=await rpc('addImageFragment',{...common,sequence:await seq(100),text:'0051 old-writer plain IMAGE',imageId});
  expectRpcStatus(oldPlain,200,'old writer pre-activation plain IMAGE');
  const oldPlainId=oldPlain.payload.id;
  assert.equal((await fragment(oldPlainId)).imageLinkUrl,null);
  const oldClient=await clientHttp('legacy',images.legacy.client);
  assert.deepEqual(await fragment(imageFragmentId),afterRejectedUpdate,
    'Legacy rollback modified an existing candidate plain IMAGE');
  write('step4-preactivation-rollback.json',{candidateClient,newReader,oldReader,oldClient,
    preactivationRollback:'PASS',oldWriterCreatedPlainImageId:oldPlainId,
    preservedFragmentId:imageFragmentId,linkCount:Number(await sql('SELECT count(*) FROM fragment WHERE image_link_url IS NOT NULL'))});
  checks.push('Before extension write: deployed old responder/web/client IDs start; old writer creates plain IMAGE; reader renders MARQUEE; existing IMAGE unchanged');

  // Re-upgrade, still gate false. Confirm existing state and retained replay.
  await removeOwned(web);await removeOwned(responder);
  fs.writeFileSync(path.join(output,'responder.json'),JSON.stringify(responderConfig(true,false),null,2));
  await container(responder,[...newResponderArgs,images.candidate.responder]);
  await waitFor('re-upgraded responder subscription',async()=>
    (await docker('logs','--tail','120',responder)).includes('diaries/rpc/request'),90000);
  await container(web,[...webArgs,images.candidate.web]);
  const upgradedReader=await readyWeb('re-upgraded reader');
  await relogin();
  assert.equal((await fragment(imageFragmentId)).imageLinkUrl,null);
  assert.equal((await fragment(oldPlainId)).imageLinkUrl,null);
  const disabledAfterRollback=await rpc('addImageFragment',{...common,sequence:await seq(100),text:'still disabled',imageId,imageLinkUrl:link});
  expectRpcStatus(disabledAfterRollback,403,'gate still disabled after re-upgrade');
  checks.push('Re-upgrade without extension writes preserves plain records and keeps independent extension gate disabled');

  // Cross the rollback boundary only after old containers are gone.
  await removeOwned(responder);
  fs.writeFileSync(path.join(output,'responder.json'),JSON.stringify(responderConfig(true,true),null,2));
  await container(responder,[...newResponderArgs,images.candidate.responder]);
  await waitFor('activated candidate responder subscription',async()=>
    (await docker('logs','--tail','120',responder)).includes('diaries/rpc/request'),90000);
  await relogin();
  const activated=await rpc('addImageFragment',{...common,sequence:await seq(100),text:'0051 extension activation boundary',imageId,imageLinkUrl:link});
  expectRpcStatus(activated,200,'extension write allowed after coordinated activation');
  summary.extensionWritePerformed=true;
  const activatedId=activated.payload.id;
  assert.equal((await fragment(activatedId)).imageLinkUrl,link);
  const activatedRetained=await retainedSnapshot('step4-after-activation');
  assert.equal(retainedPayload(activatedRetained,`diaries/fragments/${activatedId}`).imageLinkUrl,link);
  const activePort=await port(web,8082);
  await waitFor('candidate reader renders newly activated URL',async()=>{
    const resp=await fetch(`http://127.0.0.1:${activePort}${monthPath}`);
    const html=await resp.text();
    return resp.ok && html.includes(`data-reader-fragment="${activatedId}"`) &&
      html.includes('fragment-media__link');
  },60000);
  summary.oldBinariesSafeRollbackTarget=false;
  summary.olderBinariesRestartedAfterExtensionWrite=false;
  write('step4-rollout-receipt.json',{status:'PASSED',imageIdentities:identity,
    beforeActivation:{plainImageId:imageFragmentId,legacyCreatedId:oldPlainId,
      legacyClient:oldClient,legacyReader:oldReader,candidateClient,candidateReader:newReader},
    reupgrade:{reader:upgradedReader,extensionGate:false},
    afterActivation:{extensionWriteId:activatedId,linkPersisted:true,retainedLinkConfirmed:true,
      oldBinariesSafeRollbackTarget:false,olderBinariesRestarted:false},
    productionModified:false,fixtureOnly:true});
  checks.push('After coordinated activation: new URL retained; OLD BINARIES NOT RESTARTED and explicitly unsafe rollback targets');
}
module.exports={runStep4RolloutChecks,verifyRepositoryDigest};
