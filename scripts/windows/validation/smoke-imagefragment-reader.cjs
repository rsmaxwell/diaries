/* Controlled cross-component ImageFragment reader verification. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const net = require('node:net');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const { execFile } = require('node:child_process');
const { promisify } = require('node:util');
const run = promisify(execFile);
const { makeRetainedSnapshot } = require('./imagefragment-retained-snapshot.cjs');
const { inspectImageBytes } = require('./imagefragment-image-http.cjs');
const { startMutableProxy, setPublishedPort } = require('./imagefragment-proxy-routing.cjs');
const root = path.resolve(__dirname, '../../..');
let playwright;
try { playwright = require('playwright'); } catch (first) {
  try { playwright = require(path.join(root, 'diaries-client/node_modules/playwright')); }
  catch { throw new Error('Playwright is required. Install it or expose it through NODE_PATH.', { cause: first }); }
}
const { chromium } = playwright;
const mqtt = require(path.join(root, 'diaries-client/node_modules/mqtt'));
const [backupArg, outputArg] = process.argv.slice(2);
if (!backupArg || !outputArg) throw Error('Usage: node smoke-imagefragment-reader.cjs BACKUP NEW_OUTPUT');
const backup = fs.realpathSync(backupArg);
const output = path.resolve(outputArg);
assert(!fs.existsSync(output), 'Output must be new');
fs.mkdirSync(output, { recursive: true });
const evidence = path.join(output, 'evidence');
fs.mkdirSync(evidence);
const prefix = 'diaries-0026-step13-' + crypto.randomUUID().slice(0, 8);
const db = prefix + '-db', broker = prefix + '-mqtt', responder = prefix + '-responder', web = prefix + '-web';
const owned = [], connections = [], checks = [];
let browser, proxyServer, networkCreated = false;
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const write = (name, value) => fs.writeFileSync(path.join(evidence, name), typeof value === 'string' ? value : JSON.stringify(value, null, 2));
function expectRpcStatus(reply, expected, label) {
  assert.equal(reply?.status?.code, expected, `${label}: expected HTTP-style RPC status ${expected}; response: ${JSON.stringify(reply)}`);
}
const summary = {
  step: 13,
  startedAtUtc: new Date().toISOString(),
  status: 'RUNNING',
  checks,
  backupFilename: path.basename(backup),
  backupSha256: sha(fs.readFileSync(backup)),
  liveDevelopmentDatabaseModified: false,
  productionDatabaseModified: false,
  liveNasModified: false,
  imageFragmentWritesEnabledInitially: false
};
async function docker(...args) { return (await run('docker', args, { maxBuffer: 64 * 1024 * 1024 })).stdout.trim(); }
async function container(name, args) { await docker('run', '-d', '--name', name, '--network', prefix, ...args); owned.push(name); }
async function unusedPort() {
  const probe = net.createServer();
  await new Promise(resolve => probe.listen(0, '127.0.0.1', resolve));
  const port = probe.address().port;
  await new Promise(resolve => probe.close(resolve));
  return port;
}
async function waitFor(label, action, timeout = 120000) {
  const end = Date.now() + timeout; let error;
  while (Date.now() < end) {
    try { const value = await action(); if (value) return value; } catch (e) { error = e; }
    await new Promise(resolve => setTimeout(resolve, 300));
  }
  throw Error(`${label} timed out: ${error?.message || 'condition not satisfied'}`);
}
async function sql(query) { return docker('exec', db, 'psql', '-XAt', '-U', 'diaries', '-d', 'step13', '-v', 'ON_ERROR_STOP=1', '-c', query); }
async function rows(query) { return JSON.parse(await sql(`SELECT coalesce(json_agg(t),'[]') FROM (${query}) t`)); }
function manifest(directory) {
  const result = [];
  if (!fs.existsSync(directory)) return result;
  function visit(dir) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const file = path.join(dir, entry.name);
      if (entry.isSymbolicLink()) throw Error('Evidence may not contain symlinks');
      if (entry.isDirectory()) visit(file);
      else result.push({ path: path.relative(directory, file).replaceAll('\\', '/'), bytes: fs.statSync(file).size, sha256: sha(fs.readFileSync(file)) });
    }
  }
  visit(directory); return result.sort((a,b) => a.path.localeCompare(b.path));
}
async function connect(username = 'diaries-responder') {
  const client = await mqtt.connectAsync(summary.mqttUrl, { protocolVersion: 5, username, password: 'step13-fixture', clientId: 'step13-' + crypto.randomUUID(), clean: true, reconnectPeriod: 0 });
  connections.push(client); return client;
}
const captureRetainedSnapshot = makeRetainedSnapshot({connect, sha, write});
async function retainedSnapshot(label) {
  console.log(`Step 13 ${label}: reading retained Fragment/Image metadata and waiting for independent MQTT barrier...`);
  const result = await captureRetainedSnapshot(label);
  console.log(`Step 13 ${label}: ${Object.keys(result).filter(t => t.startsWith('diaries/fragments/')).length} Fragments, ${Object.keys(result).filter(t => t.startsWith('diaries/images/')).length} Images; barrier received.`);
  return result;
}
async function restoreBackup() {
  await docker('cp', backup, db + ':/tmp/baseline');
  if (backup.toLowerCase().endsWith('.sql')) {
    await docker('exec', db, 'psql', '-X', '-U', 'diaries', '-d', 'step13', '-v', 'ON_ERROR_STOP=1', '-f', '/tmp/baseline');
  } else {
    await docker('exec', db, 'pg_restore', '-U', 'diaries', '-d', 'step13', '--no-owner', '--no-privileges', '/tmp/baseline');
  }
}
async function applyFixtureSchema() {
  const pageId = (await sql("SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='fragment' AND column_name='page_id'")) === '1';
  const type = (await sql("SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='fragment' AND column_name='type'")) === '1';
  if (!pageId || !type) throw Error('Backup must already contain the 0022 Page/type Fragment schema');
  const hasImage = (await sql("SELECT to_regclass('public.image') IS NOT NULL")) === 't';
  if (!hasImage) {
    const schema = path.join(root, 'change-control/complete/0024-FEAT - introduce reusable persistent Image catalogue/migration/schema.sql');
    await docker('cp', schema, db + ':/tmp/0024-schema.sql');
    await docker('exec', db, 'psql', '-X', '-U', 'diaries', '-d', 'step13', '-v', 'ON_ERROR_STOP=1', '-f', '/tmp/0024-schema.sql');
  }
  const hasImageId = (await sql("SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='fragment' AND column_name='image_id'")) === '1';
  const migration = path.join(root, 'change-control/complete/0025-FEAT - add responder ImageFragment persistence and RPC/migration');
  if (!hasImageId) {
    await docker('cp', migration, db + ':/tmp/0025');
    write('schema-action.txt', 'Applied 0025 migration to restored disposable database.\n');
    await docker('exec', db, 'psql', '-X', '-U', 'diaries', '-d', 'step13', '-v', 'ON_ERROR_STOP=1', '-f', '/tmp/0025/001-preflight.sql', '-f', '/tmp/0025/002-add-fragment-image-reference.sql', '-f', '/tmp/0025/003-postflight.sql');
  } else {
    await docker('cp', path.join(migration, 'assert-schema.sql'), db + ':/tmp/0025-assert.sql');
    write('schema-action.txt', 'Restored database already had 0025 schema; ran assert-schema.sql.\n');
    await docker('exec', db, 'psql', '-X', '-U', 'diaries', '-d', 'step13', '-v', 'ON_ERROR_STOP=1', '-f', '/tmp/0025-assert.sql');
  }
}
function pageFilename(page) {
  // The fixture SQL explicitly aliases page.name as page_name.
  // Reading page.name silently generated 'undefined.jpg', allowing the fixture
  // copy and direct-HTTP preflight to pass against the wrong filename.
  assert.equal(typeof page.page_name, 'string', 'Fixture SQL must provide page_name');
  assert(page.page_name.trim().length > 0, 'Fixture Page name must not be blank');
  assert.equal(typeof page.extension, 'string', 'Fixture SQL must provide Page extension');
  const ext = page.extension.startsWith('.') ? page.extension : '.' + page.extension;
  return page.page_name + ext;
}
function readerArticleHasState(html,id,state) { return new RegExp(`data-reader-fragment=\"${id}\"[^>]*data-media-state=\"${state}\"`).test(html); }
async function createImagesAndPages(pages) {
  const python = process.env.STEP13_PYTHON || 'python';
  fs.mkdirSync(path.join(output, 'inputs'), { recursive: true }); fs.mkdirSync(path.join(output, 'diaries'), { recursive: true });
  for (let i = 0; i < pages.length; i++) {
    const p = pages[i]; const dir = path.join(output, 'diaries', p.diary_name); fs.mkdirSync(dir, { recursive: true });
    await run(python, ['-c', 'from PIL import Image,ImageDraw; import sys; w=int(sys.argv[1]); h=int(sys.argv[2]); im=Image.new("RGB",(w,h),"white"); d=ImageDraw.Draw(im); d.rectangle((max(10,w//10),max(10,h//10),max(100,w*7//10),max(100,h*5//10)),outline="black",width=max(2,min(w,h)//200)); d.text((max(20,w//12),max(20,h//12)),sys.argv[3],fill="black"); im.save(sys.argv[4],quality=80)', String(p.width), String(p.height), `0026 Step 13 disposable page ${i+1}`, path.join(dir, pageFilename(p))]);
  }
  const specs = [
    ['selected.png', 900, 560, 'Step 13 selected catalogue image'],
    ['shared.png', 820, 620, 'Step 13 shared catalogue image'],
    ['missing.png', 760, 540, 'Step 13 missing-file image'],
    ['metadata.png', 720, 500, 'Step 13 metadata-fault image']
  ];
  for (const [name,w,h,label] of specs) await run(python, ['-c', 'from PIL import Image,ImageDraw; import sys; im=Image.new("RGB",(int(sys.argv[1]),int(sys.argv[2])),"white"); d=ImageDraw.Draw(im); d.rectangle((20,20,int(sys.argv[1])-20,int(sys.argv[2])-20),outline="black",width=4); d.text((40,50),sys.argv[3],fill="black"); im.save(sys.argv[4])', String(w), String(h), label, path.join(output, 'inputs', name)]);
}
async function main() {
  const responderJars = fs.readdirSync(path.join(root, 'diaries-responder/build/libs')).filter(x => x.endsWith('-fat.jar'));
  const webJars = fs.readdirSync(path.join(root, 'diaries-web/build/libs')).filter(x => x.endsWith('-fat.jar'));
  assert.equal(responderJars.length,1,'Expected exactly one freshly built responder fat JAR');
  assert.equal(webJars.length,1,'Expected exactly one freshly built web fat JAR');
  const responderJarName=responderJars[0], webJarName=webJars[0];
  fs.copyFileSync(path.join(root,'diaries-responder/build/libs',responderJarName), path.join(output,'responder.jar'));
  fs.copyFileSync(path.join(root,'diaries-web/build/libs',webJarName), path.join(output,'web.jar'));
  write('candidate-artifacts.json', {
    responder:{filename:responderJarName,sha256:sha(fs.readFileSync(path.join(output,'responder.jar')))},
    web:{filename:webJarName,sha256:sha(fs.readFileSync(path.join(output,'web.jar')))},
    runnerSha256:sha(fs.readFileSync(__filename))
  });
  await docker('network','create',prefix); networkCreated=true;
  await container(db, ['--tmpfs','/var/lib/postgresql','-e','POSTGRES_USER=diaries','-e','POSTGRES_DB=step13','-e','POSTGRES_HOST_AUTH_METHOD=trust','postgres:18-alpine']);
  await waitFor('PostgreSQL', async()=>{ await docker('exec',db,'pg_isready','-U','diaries','-d','step13'); return true; });
  await restoreBackup(); await applyFixtureSchema();
  await sql("CREATE EXTENSION IF NOT EXISTS pgcrypto; UPDATE person SET username='step13-smoke', passwordhash=crypt('step13-fixture',gen_salt('bf')), status='ACTIVE', role='ADMIN' WHERE id=(SELECT min(id) FROM person)");
  const candidates = await rows("SELECT DISTINCT p.id AS page_id,p.name AS page_name,p.extension,p.width,p.height,d.id AS diary_id,d.name AS diary_name,f.year,f.month,f.day FROM fragment f JOIN page p ON p.id=f.page_id JOIN diary d ON d.id=p.diary_id WHERE f.type='MARQUEE' AND f.year IS NOT NULL AND f.month IS NOT NULL AND f.day IS NOT NULL AND p.width>0 AND p.height>0 AND p.extension IS NOT NULL ORDER BY p.id,f.year,f.month,f.day");
  assert(candidates.length >= 2, 'Restored fixture needs at least two Page-owned MARQUEE dates');
  const first=candidates[0];
  const second=candidates.find(x => x.page_id!==first.page_id && x.diary_id===first.diary_id && (x.year!==first.year || x.month!==first.month || x.day!==first.day))
    || candidates.find(x => x.page_id!==first.page_id && (x.year!==first.year || x.month!==first.month || x.day!==first.day));
  assert(second, 'Restored fixture needs a second Page on a different diary date'); const pages=[first,second];
  await createImagesAndPages(pages); write('selected-pages.json', pages);
  fs.writeFileSync(path.join(output,'mosquitto.conf'),'listener 1883\nlistener 9001\nprotocol websockets\nallow_anonymous false\npassword_file /tmp/passwords\nacl_file /fixture/aclfile.txt\nmax_inflight_messages 20\nmax_queued_messages 10000\n');
  fs.copyFileSync(path.join(root,'config/mosquitto/aclfile.txt'), path.join(output,'aclfile.txt'));
  await container(broker, ['-p','127.0.0.1::1883','--mount',`type=bind,source=${output},target=/fixture,readonly`,'--entrypoint','sh','eclipse-mosquitto:2.0.22','-c','for u in diaries-responder diaries-client diaries-web diaries-health; do touch /tmp/passwords; mosquitto_passwd -b /tmp/passwords "$u" step13-fixture; done; chmod 644 /tmp/passwords; exec mosquitto -c /fixture/mosquitto.conf']);
  const port = async(name,internal)=>Number((await docker('port',name,String(internal))).split(':').at(-1));
  summary.mqttUrl='mqtt://127.0.0.1:'+await port(broker,1883);
  await waitFor('Mosquitto', async()=>{ try { const probe=await connect('diaries-health'); await probe.endAsync(); return true; } catch { return false; } });
  const proxyPort=await unusedPort(); summary.publicOrigin='http://127.0.0.1:'+proxyPort;
  const responderConfig = enabled => ({
    db:{jdbc:{dbms:'postgresql',driver:'org.postgresql.Driver'},host:db,port:5432,database:'step13',admin:{username:'diaries',password:''},users:[{username:'diaries',password:''}],additionalConnectionProperties:{'hibernate.hbm2ddl.auto':'validate'}},
    diaries:{root:'/data',files:'files',diaries:'diaries',baseUrl:'http://localhost:8081'},mqtt:{host:broker,port:1883,user:{username:'diaries-responder',password:'step13-fixture'}},
    refreshPeriod:'30m',refreshExpiration:'2h',normaliseOnStartup:false,imageFragmentWritesEnabled:enabled,
    secret:Buffer.from('step13-disposable-signing-key-01234567890123456789').toString('base64')
  });
  fs.writeFileSync(path.join(output,'responder.json'),JSON.stringify(responderConfig(false),null,2));
  const javaImage=process.env.STEP13_JAVA_IMAGE || 'diaries-responder:local';
  // These are disposable containers, so always populate both fixture trees. Checking
  // only for /data/files could accidentally skip copying the synthetic Page files
  // when a custom Java runtime image pre-creates that directory.
  await container(responder, ['-p','127.0.0.1::8081','--mount',`type=bind,source=${output},target=/fixture`,'--entrypoint','sh',javaImage,'-c','mkdir -p /data/files/.image-staging /data/diaries; cp -a /fixture/diaries/. /data/diaries/; chmod 700 /data/files/.image-staging; exec java -jar /fixture/responder.jar --config /fixture/responder.json']);
  // Docker Desktop can change an automatically published host port when a
  // disposable container is restarted. The proxy must read these ports at
  // request time rather than retaining values from initial container startup.
  const upstreamPorts = {responder:null, web:null};
  const responderPort=await port(responder,8081);
  summary.responderDirectUrl=setPublishedPort(upstreamPorts,'responder',responderPort);
  async function responderReady(since=summary.startedAtUtc){ await waitFor('responder RPC subscription', async()=>(await docker('logs','--since',since,'--tail','120',responder)).includes("Connected, subscribing to: 'diaries/rpc/request'")); }
  await responderReady();

  // Confirm the fixture file was copied byte-for-byte AND that the responder's
  // static-file handler can serve it. This separates copy/path/policy problems
  // from failures in the browser-visible reverse proxy and web templates.
  const sourceProbes = [];
  for (const p of pages) {
    const filename = pageFilename(p);
    const relativeUrl = '/diaries/' + encodeURIComponent(p.diary_name) + '/' + encodeURIComponent(filename);
    const hostFile = path.join(output, 'diaries', p.diary_name, filename);
    const containerFile = '/data/diaries/' + p.diary_name + '/' + filename;
    const expectedSha256 = sha(fs.readFileSync(hostFile));
    const probe = {pageId:p.page_id, diaryId:p.diary_id, relativeUrl, containerFile, expectedSha256};
    try { probe.containerSha256 = (await docker('exec',responder,'sha256sum',containerFile)).split(/\s+/)[0]; }
    catch(e) { probe.containerError = e.stderr || e.message; }
    const response = await fetch(summary.responderDirectUrl + relativeUrl);
    const bytes = Buffer.from(await response.arrayBuffer());
    probe.directHttpStatus = response.status;
    probe.directContentType = response.headers.get('content-type');
    if (response.ok) probe.directSha256 = sha(bytes);
    else probe.directResponseText = bytes.toString('utf8').slice(0,400);
    sourceProbes.push(probe);
    write('source-page-preflight.json',sourceProbes);
    assert.equal(probe.containerSha256,expectedSha256,
      `Synthetic Page ${p.page_id} not copied byte-for-byte into the disposable responder; see source-page-preflight.json`);
    assert.equal(probe.directHttpStatus,200,
      `Synthetic Page ${p.page_id} not served directly by responder (HTTP ${probe.directHttpStatus}); see source-page-preflight.json`);
    assert.equal(probe.directSha256,expectedSha256,
      `Synthetic Page ${p.page_id} served different bytes by responder; see source-page-preflight.json`);
  }
  const webConfig=JSON.parse(fs.readFileSync(path.join(root,'diaries-web/config/diaries-web.docker.json')));
  webConfig.http.basePath='/reader'; webConfig.http.publicBaseUrl=summary.publicOrigin+'/reader'; webConfig.mqtt.host=broker; webConfig.content.responderBaseUrl=`http://${responder}:8081`; webConfig.content.publicResponderBaseUrl='/diaries-responder';
  fs.writeFileSync(path.join(output,'web.json'),JSON.stringify(webConfig,null,2));
  await container(web, ['-p','127.0.0.1::8082','-e','DIARIES_WEB_MQTT_USERNAME=diaries-web','-e','DIARIES_WEB_MQTT_PASSWORD=step13-fixture','--mount',`type=bind,source=${output},target=/fixture,readonly`,'--entrypoint','java',javaImage,'-jar','/fixture/web.jar','--config','/fixture/web.json']);
  const webPort=await port(web,8082);
  summary.webDirectUrl=setPublishedPort(upstreamPorts,'web',webPort);
  await waitFor('web ready baseline', async()=> (await fetch(summary.webDirectUrl+'/reader/health/ready')).ok);
  proxyServer=await startMutableProxy(proxyPort,upstreamPorts);
  summary.readerUrl=summary.publicOrigin+'/reader';

  // Capture which host port Docker actually publishes after a restart. An
  // MQTT subscription is NOT proof that the responder's static HTTP endpoint
  // or its host-side published port is usable. Persist every failed attempt
  // so a future preflight failure has its immediate cause in the evidence.
  async function refreshResponderHttpAfterRestart(label, previousPort) {
    const diagnostic={label,previousPort,attempts:[],ready:false};
    try {
      await waitFor(label + ' responder HTTP readiness', async()=>{
        const attempt={timestamp:new Date().toISOString()};
        try {
          const published=await port(responder,8081);
          attempt.publishedPort=published;
          summary.responderDirectUrl=setPublishedPort(upstreamPorts,'responder',published);
          attempt.directUrl=summary.responderDirectUrl+sourceProbes[0].relativeUrl;
          const response=await fetch(attempt.directUrl,{signal:AbortSignal.timeout(2500)});
          attempt.status=response.status;
          // Require real Page bytes, not just a TCP listener or MQTT ready.
          if(response.ok){
            const bytes=Buffer.from(await response.arrayBuffer());
            attempt.sha256=sha(bytes);
            diagnostic.ready=attempt.sha256===sourceProbes[0].expectedSha256;
          }
        }catch(error){attempt.error=String(error.cause?.message||error.message||error);}
        diagnostic.attempts.push(attempt);
        // Keep the evidence bounded in an unusually long retry loop.
        if(diagnostic.attempts.length>50)diagnostic.attempts.shift();
        return diagnostic.ready;
      },45000);
    }finally{
      diagnostic.currentPort=upstreamPorts.responder;
      diagnostic.publishedPortChanged=previousPort!==upstreamPorts.responder;
      try{diagnostic.containerState=await docker('inspect','--format','{{.State.Status}} (exit={{.State.ExitCode}}; restarting={{.State.Restarting}})',responder);}
      catch(error){diagnostic.inspectError=String(error.message||error);}
      write(label+'-responder-port.json',diagnostic);
    }
  }

  async function refreshWebHttpAfterRestart(label, previousPort) {
    const diagnostic={label,previousPort,attempts:[],ready:false};
    try {
      await waitFor(label + ' web HTTP readiness',async()=>{
        const attempt={timestamp:new Date().toISOString()};
        try{
          const published=await port(web,8082);
          attempt.publishedPort=published;
          summary.webDirectUrl=setPublishedPort(upstreamPorts,'web',published);
          attempt.url=summary.webDirectUrl+'/reader/health/ready';
          const response=await fetch(attempt.url,{signal:AbortSignal.timeout(2500)});
          attempt.status=response.status;
          diagnostic.ready=response.ok;
        }catch(error){attempt.error=String(error.cause?.message||error.message||error);}
        diagnostic.attempts.push(attempt);
        if(diagnostic.attempts.length>50)diagnostic.attempts.shift();
        return diagnostic.ready;
      },45000);
    }finally{
      diagnostic.currentPort=upstreamPorts.web;
      diagnostic.publishedPortChanged=previousPort!==upstreamPorts.web;
      write(label+'-web-port.json',diagnostic);
    }
  }
  const rpcClient=await connect('diaries-client'), responseTopic=`diaries/rpc/${rpcClient.options.clientId}/response`; await rpcClient.subscribeAsync(responseTopic,{qos:1});
  const pending=new Map(); rpcClient.on('message',(topic,bytes,packet)=>{ const id=packet.properties?.correlationData?.toString(); if(topic!==responseTopic||!pending.has(id))return; const raw=packet.properties.userProperties?.status; const status=JSON.parse(Array.isArray(raw)?raw[0]:raw); const p=pending.get(id);pending.delete(id);clearTimeout(p.timer);p.resolve({status,payload:bytes.length?JSON.parse(bytes):null}); });
  let accessToken; async function rpc(fn,args){ const id=crypto.randomUUID(); const reply=new Promise((resolve,reject)=>pending.set(id,{resolve,timer:setTimeout(()=>{pending.delete(id);reject(Error(fn+' timeout'));},20000)})); await rpcClient.publishAsync('diaries/rpc/request',JSON.stringify({function:fn,args}),{qos:1,properties:{responseTopic,correlationData:Buffer.from(id),...(accessToken?{userProperties:{accessToken}}:{})}}); return reply; }
  const signin=await rpc('signin',{username:'step13-smoke',password:'step13-fixture',sessionId:crypto.randomUUID()}); expectRpcStatus(signin,200,'signin'); accessToken=signin.payload.accessToken;
  async function nextSequence(p,offset){ const max=Number(await sql(`SELECT coalesce(max(sequence),0) FROM fragment WHERE year=${p.year} AND month=${p.month} AND day=${p.day}`)); return Number((max+offset).toFixed(4)); }
  const marqueeArgs={pageId:first.page_id,year:first.year,month:first.month,day:first.day,sequence:await nextSequence(first,10),text:'Step 13 fixture MARQUEE',x:Math.max(10,first.width*.12),y:Math.max(10,first.height*.12),width:Math.max(80,first.width*.30),height:Math.max(80,first.height*.20)};
  write('marquee-fixture-request.json', marqueeArgs);
  const marquee=await rpc('addFragment',marqueeArgs); expectRpcStatus(marquee,200,`addFragment ${JSON.stringify(marqueeArgs)}`); const marqueeId=marquee.payload.id;
  const blocked=await rpc('addImageFragment',{pageId:first.page_id,year:first.year,month:first.month,day:first.day,sequence:await nextSequence(first,20),text:'Step 13 gate-disabled IMAGE'}); expectRpcStatus(blocked,403,'gate-disabled addImageFragment'); write('gate-disabled.json',blocked);
  checks.push('MARQUEE creation succeeds while IMAGE authoring gate is disabled; addImageFragment is rejected with 403');
  const baselineRoute=`/reader/diaries/${first.diary_id}/${first.year}/${String(first.month).padStart(2,'0')}?fragment=${marqueeId}#fragment-${marqueeId}`;
  await waitFor('web live MARQUEE', async()=> (await (await fetch(summary.publicOrigin+baselineRoute)).text()).includes(`data-reader-fragment="${marqueeId}"`));
  const baselineHtml=await (await fetch(summary.publicOrigin+baselineRoute)).text();
  const pageUrlMatch=baselineHtml.match(new RegExp(`data-reader-fragment="${marqueeId}"[^>]*data-image-url="([^"]+)"`));
  assert(pageUrlMatch,'MARQUEE page URL missing');
  const pageUrl=pageUrlMatch[1];
  assert(pageUrl.startsWith('/diaries-responder/'),'MARQUEE Page bytes must use the browser-visible /diaries-responder prefix');
  const expectedPageUrl='/diaries-responder'+sourceProbes[0].relativeUrl;
  const pageBytesResponse=await fetch(new URL(pageUrl,summary.publicOrigin));
  const pageBytes=Buffer.from(await pageBytesResponse.arrayBuffer());
  const browserPrefixProbe={url:pageBytesResponse.url,renderedPageUrl:pageUrl,expectedPageUrl,
    status:pageBytesResponse.status,contentType:pageBytesResponse.headers.get('content-type'),
    responseSha256:pageBytesResponse.ok?sha(pageBytes):null,
    expectedSha256:sourceProbes[0].expectedSha256,
    errorBody:pageBytesResponse.ok?null:pageBytes.toString('utf8').slice(0,400)};
  write('gate-disabled-page-http.json',browserPrefixProbe);
  assert.equal(decodeURIComponent(pageUrl),decodeURIComponent(expectedPageUrl),
    'Web reader emitted an unexpected synthetic Page URL; see gate-disabled-page-http.json');
  assert.equal(pageBytesResponse.status,200,
    `Synthetic Page bytes unavailable through /diaries-responder (HTTP ${pageBytesResponse.status}); see gate-disabled-page-http.json`);
  assert.equal(browserPrefixProbe.responseSha256,browserPrefixProbe.expectedSha256,
    'Reverse proxy served incorrect synthetic Page bytes; see gate-disabled-page-http.json');
  const chrome=process.env.CHROME_BIN || ['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(x=>fs.existsSync(x)); assert(chrome&&fs.existsSync(chrome),'Set CHROME_BIN or install Chrome/Edge');
  browser=await chromium.launch({executablePath:chrome,headless:true});
  const gateContext=await browser.newContext({viewport:{width:1440,height:1050}}); const gatePage=await gateContext.newPage(); gatePage.setDefaultTimeout(25000);
  await gatePage.goto(summary.publicOrigin+baselineRoute); await gatePage.locator(`[data-reader-fragment="${marqueeId}"]`).waitFor();
  assert.equal(await gatePage.locator(`[data-reader-fragment="${marqueeId}"]`).getAttribute('data-has-marquee'),'true');
  assert.equal(await gatePage.locator('[data-viewer-action="fit-selection"]').isEnabled(),true);
  await waitFor('gate-disabled MARQUEE source page', async()=> (await gatePage.locator('[data-viewer-message]').textContent()) !== 'The source image could not be loaded.');
  await gatePage.screenshot({path:path.join(evidence,'gate-disabled-marquee.png'),fullPage:true}); await gateContext.close();
  checks.push('Browser MARQUEE selection/source rendering is healthy while Image authoring remains disabled');
  fs.writeFileSync(path.join(output,'responder.json'),JSON.stringify(responderConfig(true),null,2));
  summary.imageFragmentWritesEnabledFixture=true;
  const gateRestart=new Date().toISOString(), beforeGatePort=upstreamPorts.responder;
  await docker('restart',responder);
  await responderReady(gateRestart);
  await refreshResponderHttpAfterRestart('gate-enabled',beforeGatePort);
  await waitFor('web ready after gated responder restart',async()=>
    (await fetch(summary.webDirectUrl+'/reader/health/ready',{signal:AbortSignal.timeout(2500)})).ok);
  async function upload(name,subdir,filename){ const bytes=fs.readFileSync(path.join(output,'inputs',filename)); const result=await rpc('uploadFile',{name,subdir,bytes:bytes.toString('base64'),size:bytes.length,contentType:'image/png'}); expectRpcStatus(result,200,`uploadFile ${name} in ${subdir}`); assert(result.payload.imageId); return result.payload; }
  const selectedImage=await upload('selected image ü.png','step13/maps/nested','selected.png');
  const sharedImage=await upload('shared image.png','step13/maps/shared','shared.png');
  const missingImage=await upload('missing file.png','step13/maps/faults','missing.png');
  const metadataImage=await upload('metadata fault.png','step13/maps/faults','metadata.png');
  write('uploaded-images.json',{selectedImage,sharedImage,missingImage,metadataImage});
  // Check the actual uploaded bytes through all three layers BEFORE asking a
  // browser to load lazy <img> elements. Metadata presence alone proves nothing
  // about the physical file or the public /diaries-responder route.
  const imageByteProbes=[];
  for (const [label, uploaded, inputName] of [
    ['selected',selectedImage,'selected.png'],['shared',sharedImage,'shared.png'],
    ['missing',missingImage,'missing.png'],['metadata',metadataImage,'metadata.png']]) {
    const relativePath=uploaded.image?.relativePath;
    assert(relativePath,`uploadFile ${label} returned no catalogue Image relativePath`);
    let containerSha256,containerError;
    try { containerSha256=(await docker('exec',responder,'sha256sum','/data/files/'+relativePath)).split(/\s+/)[0]; }
    catch(error) { containerError=error.stderr || error.message; }
    const probe=await inspectImageBytes({label,relativePath,
      expectedBytes:fs.readFileSync(path.join(output,'inputs',inputName)),
      containerSha256,containerError, publicOrigin:summary.publicOrigin,
      responderDirectUrl:summary.responderDirectUrl});
    imageByteProbes.push(probe);
    write('catalogue-image-http-preflight.json',imageByteProbes);
    assert(probe.ok,`${label} Image bytes failed container/direct/public HTTP preflight; inspect catalogue-image-http-preflight.json`);
  }
  checks.push('Every synthetic catalogued Image matches source bytes on disposable filesystem, direct responder HTTP and public reverse-proxy HTTP');
  async function addImage(p,seq,text,imageId){ const args={pageId:p.page_id,year:p.year,month:p.month,day:p.day,sequence:seq,text}; if(imageId!==undefined)args.imageId=imageId; const result=await rpc('addImageFragment',args); expectRpcStatus(result,200,`addImageFragment ${JSON.stringify(args)}`); return result.payload; }
  let off=30; const selectedFrag=await addImage(first,await nextSequence(first,off++),'Step 13 IMAGE with selection',selectedImage.imageId);
  const noSelectionFrag=await addImage(first,await nextSequence(first,off++),'Step 13 IMAGE without selection');
  const sharedFrag1=await addImage(first,await nextSequence(first,off++),'Step 13 shared IMAGE first',sharedImage.imageId);
  const sharedFrag2=await addImage(second,await nextSequence(second,30),'Step 13 shared IMAGE second page/date',sharedImage.imageId);
  const missingFrag=await addImage(first,await nextSequence(first,off++),'Step 13 missing-file IMAGE',missingImage.imageId);
  const metadataFrag=await addImage(first,await nextSequence(first,off++),'Step 13 unavailable-metadata IMAGE',metadataImage.imageId);
  const ids={marqueeId,selectedFragmentId:selectedFrag.id,noSelectionFragmentId:noSelectionFrag.id,sharedFragmentIds:[sharedFrag1.id,sharedFrag2.id],missingFragmentId:missingFrag.id,metadataFragmentId:metadataFrag.id}; write('fixture-ids.json',ids);
  const beforeFaults=await retainedSnapshot('retained-before-faults');
  for(const id of [selectedFrag.id,noSelectionFrag.id,sharedFrag1.id,sharedFrag2.id,missingFrag.id,metadataFrag.id]) assert(beforeFaults[`diaries/fragments/${id}`]);
  for(const id of [selectedImage.imageId,sharedImage.imageId,missingImage.imageId,metadataImage.imageId]) assert(beforeFaults[`diaries/images/${id}`]);
  checks.push('Fixture IMAGE metadata is published by responder; shared Image has two Page/date Fragment references; nested paths use real HTTP bytes');
  const desktop=await browser.newContext({viewport:{width:1440,height:1050}}); const page=await desktop.newPage(); page.setDefaultTimeout(25000);
  const monthUrl=(p,id)=>`${summary.readerUrl}/diaries/${p.diary_id}/${p.year}/${String(p.month).padStart(2,'0')}?fragment=${id}#fragment-${id}`;
  const monthBase=`${summary.readerUrl}/diaries/${first.diary_id}/${first.year}/${String(first.month).padStart(2,'0')}`;
  const selectedRoute=monthUrl(first,selectedFrag.id);
  async function browserImageState(targetPage,p,fragmentId,label,expectedPublicPath){
    const route=monthUrl(p,fragmentId);
    const slug=label.toLowerCase().replace(/[^a-z0-9]+/g,'-');
    const requests=[],consoleErrors=[];
    const onResponse=response=>{
      if(response.url().includes('/diaries-responder/files/'))
        requests.push({url:response.url(),status:response.status(),contentType:response.headers()['content-type'] || null});
    };
    const onRequestFailed=request=>{
      if(request.url().includes('/diaries-responder/files/'))
        requests.push({url:request.url(),failure:request.failure() || 'request failed'});
    };
    const onConsole=message=>{if(message.type()==='error')consoleErrors.push(message.text().slice(0,500));};
    targetPage.on('response',onResponse);
    targetPage.on('requestfailed',onRequestFailed);
    targetPage.on('console',onConsole);
    try {
      await targetPage.goto(route);
      const article=targetPage.locator(`[data-reader-fragment="${fragmentId}"]`);
      await article.waitFor();
      assert.equal(await article.getAttribute('data-media-state'),'AVAILABLE',`${label} must expose AVAILABLE retained metadata`);
      const image=article.locator('img.fragment-media__image');
      await image.waitFor({state:'attached'});
      // The production template intentionally uses loading="lazy". A DOM
      // selector is not enough to trigger an off-screen browser fetch.
      // Behave like a reader scrolling the selected fragment into view.
      await image.scrollIntoViewIfNeeded();
      await waitFor(label+' bytes',()=>image.evaluate(img=>img.complete && img.naturalWidth>0),30000);
      const src=await image.getAttribute('src');
      assert.equal(src,expectedPublicPath,`${label} must render the exact canonical public catalogue URL`);
      return {route,src,naturalWidth:await image.evaluate(img=>img.naturalWidth),
        naturalHeight:await image.evaluate(img=>img.naturalHeight)};
    } catch(error) {
      const article=targetPage.locator(`[data-reader-fragment="${fragmentId}"]`);
      let imageState=null,mediaState=null;
      try {mediaState=await article.getAttribute('data-media-state',{timeout:2000});}catch{}
      try {
        const diagnosticImage=article.locator('img.fragment-media__image');
        if(await diagnosticImage.count()) imageState=await diagnosticImage.evaluate(img=>({
          srcAttribute:img.getAttribute('src'),currentSrc:img.currentSrc,
          loading:img.loading,complete:img.complete,naturalWidth:img.naturalWidth,
          naturalHeight:img.naturalHeight,hidden:img.hidden,
          fileState:img.closest('[data-fragment-media]')?.dataset.mediaFileState || null
        }));
      }catch{}
      write(slug+'-browser-image-diagnostics.json',{label,route,fragmentId,
        expectedPublicPath, mediaState,imageState,requests,consoleErrors,
        error:error.message});
      try {await targetPage.screenshot({path:path.join(evidence,slug+'-failure.png'),timeout:3000});}catch{}
      throw Error(`${label} browser check failed: ${error.message}; see ${slug}-browser-image-diagnostics.json`,{cause:error});
    } finally {
      targetPage.off('response',onResponse);
      targetPage.off('requestfailed',onRequestFailed);
      targetPage.off('console',onConsole);
    }
  }
  const selectedBrowser=await browserImageState(page,first,selectedFrag.id,'selected Image',imageByteProbes[0].publicPath);
  assert.equal(await page.locator(`[data-reader-fragment="${selectedFrag.id}"]`).getAttribute('data-has-marquee'),'false');
  await page.screenshot({path:path.join(evidence,'desktop-month-image.png'),fullPage:true});
  const sharedBrowserFirst=await browserImageState(page,first,sharedFrag1.id,'shared Image first reference',imageByteProbes[1].publicPath);
  const sharedBrowserSecond=await browserImageState(page,second,sharedFrag2.id,'shared Image second reference',imageByteProbes[1].publicPath);
  assert.equal(sharedBrowserSecond.src,sharedBrowserFirst.src,'Both shared-Image Fragments must resolve the same public catalogue URL');
  write('browser-image-verification.json',{selected:selectedBrowser,sharedFirst:sharedBrowserFirst,sharedSecond:sharedBrowserSecond});
  await page.goto(selectedRoute); await page.locator(`[data-reader-fragment="${selectedFrag.id}"]`).waitFor();
  await page.locator(`[data-reader-fragment="${marqueeId}"] [data-fragment-selector="${marqueeId}"]`).focus(); await page.keyboard.press('Enter'); assert((await page.url()).includes(`fragment=${marqueeId}`));
  await page.locator(`[data-reader-fragment="${selectedFrag.id}"] [data-fragment-selector="${selectedFrag.id}"]`).focus(); await page.keyboard.press('Space'); assert((await page.url()).includes(`fragment=${selectedFrag.id}`)); await page.goBack(); await waitFor('month browser back',()=>page.url().includes(`fragment=${marqueeId}`)); await page.goForward(); await waitFor('month browser forward',()=>page.url().includes(`fragment=${selectedFrag.id}`));
  const sourceRoute=`${summary.readerUrl}/diaries/${first.diary_id}/pages/${first.page_id}#fragment-${selectedFrag.id}`; await page.goto(sourceRoute); await page.locator(`[data-transcript-fragment="${selectedFrag.id}"]`).waitFor();
  const sourceImage=page.locator(`[data-transcript-fragment="${selectedFrag.id}"] img.fragment-media__image`);
  await sourceImage.scrollIntoViewIfNeeded();
  await waitFor('desktop source-page selected Image bytes',()=>sourceImage.evaluate(img=>img.complete&&img.naturalWidth>0),30000);
  await page.screenshot({path:path.join(evidence,'desktop-source-image.png'),fullPage:true});
  await page.locator(`[data-transcript-fragment="${marqueeId}"] [data-fragment-selector="${marqueeId}"]`).click(); await page.locator(`[data-transcript-fragment="${selectedFrag.id}"] [data-fragment-selector="${selectedFrag.id}"]`).click(); await page.goBack(); await waitFor('source browser back',()=>page.url().includes(`#fragment-${marqueeId}`)); await page.goForward(); await waitFor('source browser forward',()=>page.url().includes(`#fragment-${selectedFrag.id}`));
  const mobile=await browser.newContext({viewport:{width:390,height:844}});
  const mobilePage=await mobile.newPage();
  const mobileMonth=await browserImageState(mobilePage,first,selectedFrag.id,'mobile selected Image',imageByteProbes[0].publicPath);
  write('mobile-browser-image-verification.json',mobileMonth);
  await mobilePage.screenshot({path:path.join(evidence,'mobile-month-image.png'),fullPage:true});
  await mobilePage.goto(sourceRoute);
  const mobileSourceImage=mobilePage.locator(`[data-transcript-fragment="${selectedFrag.id}"] img.fragment-media__image`);
  await mobileSourceImage.scrollIntoViewIfNeeded();
  await waitFor('mobile source-page selected Image bytes',()=>mobileSourceImage.evaluate(img=>img.complete&&img.naturalWidth>0),30000);
  await mobilePage.screenshot({path:path.join(evidence,'mobile-source-image.png'),fullPage:true});
  await mobile.close();
  checks.push('Desktop/mobile month and source-page views, keyboard selection, deep links and Back/Forward pass through production-style /reader and /diaries-responder prefixes');
  checks.push('A single catalogued Image renders successfully through both referring Fragments on distinct Pages/dates and resolves to the same public catalogue URL');
  const noSelectionHtml=await (await fetch(monthUrl(first,noSelectionFrag.id))).text(); assert(readerArticleHasState(noSelectionHtml,noSelectionFrag.id,'NO_SELECTION'));
  const faultClient=await connect('diaries-responder'); await faultClient.publishAsync(`diaries/images/${metadataImage.imageId}`,Buffer.alloc(0),{qos:1,retain:true});
  await waitFor('missing retained metadata fallback', async()=>{const body=await (await fetch(monthUrl(first,metadataFrag.id))).text();return readerArticleHasState(body,metadataFrag.id,'MISSING_METADATA');});
  await page.goto(monthUrl(first,metadataFrag.id));
  const metadataArticle=page.locator(`[data-reader-fragment="${metadataFrag.id}"]`); await metadataArticle.waitFor();
  assert.equal(await metadataArticle.getAttribute('data-media-state'),'MISSING_METADATA');
  assert.equal(await metadataArticle.locator('img.fragment-media__image').count(),0);
  await page.screenshot({path:path.join(evidence,'desktop-missing-metadata.png'),fullPage:true});
  write('metadata-fault-injection.txt',`Fixture-only retained tombstone: diaries/images/${metadataImage.imageId}\nDatabase row/file left intact; responder restart later restores authoritative metadata.\n`);
  const missingPath='/data/files/'+missingImage.image.relativePath; await docker('exec',responder,'mv',missingPath,missingPath+'.step13-missing');
  const fileFaultContext=await browser.newContext({viewport:{width:1440,height:1050}}); const fileFaultPage=await fileFaultContext.newPage(); fileFaultPage.setDefaultTimeout(25000);
  await fileFaultPage.goto(monthUrl(first,missingFrag.id));
  // The file is deliberately absent. Trigger the lazy fetch by scrolling its
  // figure into view; otherwise FILE_LOAD_FAILED cannot be exercised.
  await fileFaultPage.locator(`[data-fragment-media="${missingFrag.id}"]`).scrollIntoViewIfNeeded();
  await waitFor('browser FILE_LOAD_FAILED',()=>fileFaultPage.locator(`[data-fragment-media="${missingFrag.id}"]`).evaluate(el=>el.dataset.mediaFileState==='FILE_LOAD_FAILED'));
  assert.equal(await fileFaultPage.locator(`[data-fragment-media="${missingFrag.id}"] img`).evaluate(img=>img.hidden),true);
  await fileFaultPage.screenshot({path:path.join(evidence,'desktop-missing-file.png'),fullPage:true}); await fileFaultContext.close();
  checks.push('Owned fixture proves NO_SELECTION, retained-metadata-unavailable fallback and a cache-independent physical missing-file FILE_LOAD_FAILED without touching NAS content');
  const conflict=await rpc('deleteImage',{subdir:'step13/maps/shared',name:'shared image.png'}); expectRpcStatus(conflict,409,'referenced deleteImage conflict'); write('delete-image-conflict.json',conflict);
  for(const id of [sharedFrag1.id,sharedFrag2.id]) { const deleted=await rpc('deleteFragment',{id}); expectRpcStatus(deleted,200,`deleteFragment ${id}`); }
  const deletedImage=await rpc('deleteImage',{subdir:'step13/maps/shared',name:'shared image.png'}); expectRpcStatus(deletedImage,200,'unreferenced deleteImage'); write('delete-image-success.json',deletedImage);
  assert.equal(await docker('exec',responder,'sh','-c',`test ! -e '/data/files/${sharedImage.image.relativePath}' && echo absent`),'absent');
  const afterDelete=await retainedSnapshot('retained-after-delete'); assert(!afterDelete[`diaries/images/${sharedImage.imageId}`]); assert(!afterDelete[`diaries/fragments/${sharedFrag1.id}`]); assert(!afterDelete[`diaries/fragments/${sharedFrag2.id}`]);
  checks.push('DeleteImage returns 409 while referenced; deleting fixture references through deleteFragment then DeleteImage removes DB/file/retained Image state');
  const surviving=[marqueeId,selectedFrag.id,noSelectionFrag.id,missingFrag.id,metadataFrag.id];
  const orderBefore=(await (await fetch(monthBase)).text()).match(/data-reader-fragment="(\d+)"/g)?.map(x=>Number(x.match(/\d+/)[0])).filter(id=>surviving.includes(id))||[]; assert.deepEqual(orderBefore,surviving,'All surviving fixture Fragments must remain in date/sequence chronology before restart'); write('surviving-order-before-restart.json',orderBefore);
  const restartTime=new Date().toISOString(), beforeFinalResponderPort=upstreamPorts.responder;
  await docker('restart',responder);
  await responderReady(restartTime);
  await refreshResponderHttpAfterRestart('final-restart',beforeFinalResponderPort);
  await waitFor('authoritative metadata restored',async()=>{
    const body=await (await fetch(`${monthBase}?fragment=${metadataFrag.id}#fragment-${metadataFrag.id}`)).text();
    return readerArticleHasState(body,metadataFrag.id,'AVAILABLE');
  });
  const beforeFinalWebPort=upstreamPorts.web;
  await docker('restart',web);
  await refreshWebHttpAfterRestart('final-restart',beforeFinalWebPort);
  const orderAfter=(await (await fetch(monthBase)).text()).match(/data-reader-fragment="(\d+)"/g)?.map(x=>Number(x.match(/\d+/)[0])).filter(id=>surviving.includes(id))||[]; assert.deepEqual(orderAfter,orderBefore); write('surviving-order-after-restart.json',orderAfter);
  const finalRetained=await retainedSnapshot('retained-after-restart'); assert(finalRetained[`diaries/images/${metadataImage.imageId}`]);
  const dbFixture=await rows(`SELECT id,type,image_id,page_id,year,month,day,sequence,text FROM fragment WHERE id IN (${surviving.join(',')}) ORDER BY year,month,day,sequence,id`); write('fixture-database-final.json',dbFixture);
  checks.push('Responder/web restart restores authoritative metadata and deterministic surviving chronology with fresh retained replay');
  const networkRecords=[]; page.on('response',r=>{if(r.url().startsWith(summary.publicOrigin))networkRecords.push({url:r.url(),status:r.status()});});
  await page.goto(selectedRoute); await page.waitForLoadState('networkidle'); write('browser-network-sample.json',networkRecords.slice(-80));
  summary.fixtureIds=ids; summary.counts={survivingFixtureFragments:surviving.length,deletedSharedFragments:2,fixtureImagesUploaded:4,fixtureImageDeleted:1}; summary.status='PASSED';
}
main().catch(error=>{summary.status='FAILED';summary.failure=error.stack;process.exitCode=1;console.error(error);}).finally(async()=>{
  if(browser)await browser.close().catch(()=>{}); if(proxyServer)await new Promise(resolve=>proxyServer.close(resolve));
  for(const c of connections)await c.endAsync(true).catch(()=>{});
  for(const name of [responder,web,broker,db]) if(owned.includes(name)){try{const logs=await run('docker',['logs',name],{maxBuffer:32*1024*1024});const lines=(logs.stdout+logs.stderr).split('\n').filter(line=>/Connected, subscribing|synchronise:|Published replay generation|Subscribed to canonical|Javalin started|Sending status:|Image deletion|Step 13|Outgoing messages are being dropped|not authori[sz]ed|denied|too many|queue full|disconnect|Static server|Exception|\bERROR\b|failed|BindException/i.test(line)).slice(-500);write(name.slice(prefix.length+1)+'.log',lines.join('\n')+'\n');}catch{}}
  const cleanup={containersRemoved:[],networkRemoved:false,failures:[]};
  for(const name of owned.reverse()){try{await docker('rm','-f',name);cleanup.containersRemoved.push(name);}catch{cleanup.failures.push(name);}}
  if(networkCreated){try{await docker('network','rm',prefix);cleanup.networkRemoved=true;}catch{cleanup.failures.push(prefix);}}
  write('cleanup.json',cleanup);
  summary.cleanupFailures=cleanup.failures; if(cleanup.failures.length){summary.status='CLEANUP_FAILED';process.exitCode=1;} summary.finishedAtUtc=new Date().toISOString(); write('summary.json',summary);
  fs.writeFileSync(path.join(evidence,'SHA256SUMS.txt'),manifest(evidence).filter(x=>x.path!=='SHA256SUMS.txt').map(x=>x.sha256+'  '+x.path).join('\n')+'\n');
  console.log(`0026 Step 13: ${summary.status}; evidence: ${evidence}`);
});
