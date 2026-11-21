/* 0051 Step 3 cross-component disposable browser smoke. Adapted from the accepted 0026 Step 13 reader harness; isolated fixture and owned containers only. */
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
const root = path.resolve(__dirname, '../../../..');
const { makeRetainedSnapshot } = require(path.join(root, 'scripts/windows/validation/imagefragment-retained-snapshot.cjs'));
const { inspectImageBytes } = require(path.join(root, 'scripts/windows/validation/imagefragment-image-http.cjs'));
const { startMutableProxy, setPublishedPort } = require(path.join(root, 'scripts/windows/validation/imagefragment-proxy-routing.cjs'));
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
const step4Rehearsal = process.env.STEP4_ROLLOUT_REHEARSAL === '1';
const prefix = (step4Rehearsal ? 'diaries-0051-step4-' : 'diaries-0051-step3-') + crypto.randomUUID().slice(0, 8);
const db = prefix + '-db', broker = prefix + '-mqtt', responder = prefix + '-responder', web = prefix + '-web';
const filesVolume = prefix + '-files'; // Only this Step 4 run may create/remove it.
const owned = [], connections = [], checks = [];
let browser, proxyServer, networkCreated = false, filesVolumeCreated = false;
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const write = (name, value) => fs.writeFileSync(path.join(evidence, name), typeof value === 'string' ? value : JSON.stringify(value, null, 2));
function expectRpcStatus(reply, expected, label) {
  assert.equal(reply?.status?.code, expected, `${label}: expected HTTP-style RPC status ${expected}; response: ${JSON.stringify(reply)}`);
}
const summary = {
  feature: '0051', step: step4Rehearsal ? 4 : 3, inheritedHarness: '0026 Step 13',
  startedAtUtc: new Date().toISOString(),
  status: 'RUNNING',
  checks,
  backupFilename: path.basename(backup),
  backupSha256: sha(fs.readFileSync(backup)),
  liveDevelopmentDatabaseModified: false,
  productionDatabaseModified: false,
  liveNasModified: false,
  imageFragmentWritesEnabledInitially: step4Rehearsal,
  acceptanceMode: step4Rehearsal ? 'rollout-preactivation' : (process.env.STEP3_EDITOR_ONLY === '1' ? 'angular-editor' : 'public-reader')
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

// imagefragment-retained-snapshot.cjs parses the JSON once and returns
// { sha256, payload } for each topic. Never JSON.parse() the envelope again.
function retainedPayload(snapshot, topic) {
  const entry = snapshot[topic];
  assert(entry && typeof entry === 'object', `Expected retained topic ${topic}`);
  assert.match(entry.sha256, /^[0-9a-f]{64}$/, `Missing payload checksum for ${topic}`);
  assert(entry.payload && typeof entry.payload === 'object' && !Array.isArray(entry.payload),
    `Expected decoded JSON object for retained topic ${topic}`);
  return entry.payload;
}

// The shared 0026 retained snapshot deliberately subscribes ONLY to Fragment
// and Image topics. Inspect a specific Marquee topic with its own MQTT QoS-1
// replay + independent barrier, so a deletion check cannot pass vacuously.
async function retainedMarqueeTopic(id) {
  const topic = `diaries/marquees/${id}`;
  const marker = `diaries-sync/0051-marquee-probe/${crypto.randomUUID()}`;
  const subscriber = await connect('diaries-responder');
  const publisher = await connect('diaries-responder');
  let retained = null, markerSeen = false, failure;
  subscriber.on('message', (name, bytes, packet) => {
    if (name === topic && packet?.retain && bytes.length) {
      try { retained = { sha256: sha(bytes), payload: JSON.parse(bytes) }; }
      catch (error) { failure = error; }
    }
    if (name === marker) markerSeen = true;
  });
  subscriber.on('error', error => { failure = error; });
  try {
    for (const name of [topic, marker]) {
      const granted = await subscriber.subscribeAsync(name, { qos: 1 });
      assert(Array.isArray(granted) && granted.some(g => g.topic === name && g.qos === 1),
        `MQTT QoS-1 subscription not granted: ${name}`);
    }
    await publisher.publishAsync(marker, '0051-marquee-barrier', { qos: 1, retain: false });
    await waitFor(`Marquee retained-topic replay barrier ${id}`, () => {
      if (failure) throw failure;
      return markerSeen;
    }, 20000);
    if (failure) throw failure;
    return retained;
  } finally {
    await Promise.allSettled([subscriber.endAsync(true), publisher.endAsync(true)]);
  }
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
  // 0051 additive nullable URL migration, only inside this disposable fixture.
  const migration0051 = path.join(root, 'change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees/migration');
  await docker('cp', migration0051, db + ':/tmp/0051');
  await docker('exec', db, 'psql', '-X', '-U', 'diaries', '-d', 'step13', '-v', 'ON_ERROR_STOP=1', '-f', '/tmp/0051/001-add-image-link-url.sql', '-f', '/tmp/0051/002-assert-image-link-schema.sql');
  write('0051-migration.txt', 'Applied and asserted 0051 URL column to disposable database only.\n');
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
// Generate disposable synthetic Page JPEGs and catalogue PNGs using the same
// Chromium/Edge+Playwright runtime required for the UI smoke. PowerShell must
// not try to run Cygwin's /bin/python as a native Windows executable.
async function createImagesAndPages(pages) {
  fs.mkdirSync(path.join(output, 'inputs'), { recursive: true });
  fs.mkdirSync(path.join(output, 'diaries'), { recursive: true });
  const chrome = process.env.CHROME_BIN;
  assert(chrome && fs.existsSync(chrome), 'Chrome/Edge executable must be provided via CHROME_BIN');
  const drawingBrowser = await chromium.launch({ executablePath: chrome, headless: true });
  try {
    const drawingPage = await drawingBrowser.newPage();
    async function makeImage(destination, width, height, label, mime) {
      assert(Number.isInteger(width) && Number.isInteger(height) && width > 0 && height > 0,
        `Invalid synthetic image dimensions: ${width}x${height}`);
      assert(['image/jpeg', 'image/png'].includes(mime), `Unsupported synthetic image MIME: ${mime}`);
      const dataUrl = await drawingPage.evaluate(({width, height, label, mime}) => {
        const canvas = document.createElement('canvas');
        canvas.width = width; canvas.height = height;
        const context = canvas.getContext('2d');
        if (!context) throw Error('Canvas 2D drawing context unavailable');
        context.fillStyle = '#ffffff';
        context.fillRect(0, 0, width, height);
        context.strokeStyle = '#101010';
        context.lineWidth = Math.max(3, Math.round(Math.min(width, height) / 200));
        context.strokeRect(width / 10, height / 10, width * 0.65, height * 0.42);
        context.fillStyle = '#101010';
        context.font = `${Math.max(16, Math.min(48, Math.floor(Math.min(width, height) / 20)))}px sans-serif`;
        context.fillText(label, Math.max(20, width / 12), Math.max(40, height / 12), width * 0.85);
        return canvas.toDataURL(mime, 0.82);
      }, {width, height, label, mime});
      const prefix = `data:${mime};base64,`;
      assert(dataUrl.startsWith(prefix), `Canvas failed to generate ${mime} image`);
      const contents = Buffer.from(dataUrl.slice(prefix.length), 'base64');
      assert(contents.length > 200, `Synthetic image unexpectedly small: ${destination}`);
      fs.writeFileSync(destination, contents);
    }
    for (let i = 0; i < pages.length; i++) {
      const p = pages[i];
      const dir = path.join(output, 'diaries', p.diary_name);
      fs.mkdirSync(dir, { recursive: true });
      const extension = path.extname(pageFilename(p)).toLowerCase();
      const mime = ['.jpg', '.jpeg'].includes(extension) ? 'image/jpeg'
        : extension === '.png' ? 'image/png' : null;
      assert(mime, `Unexpected Page image extension '${extension}' in frozen fixture`);
      await makeImage(path.join(dir, pageFilename(p)), Number(p.width), Number(p.height),
        `0051 disposable Page ${i + 1}`, mime);
    }
    const specs = [
      ['selected.png', 900, 560, '0051 selected catalogue image'],
      ['shared.png', 820, 620, '0051 shared catalogue image'],
      ['missing.png', 760, 540, '0051 missing-file image'],
      ['metadata.png', 720, 500, '0051 metadata-fault image']
    ];
    for (const [name, width, height, label] of specs) {
      await makeImage(path.join(output, 'inputs', name), width, height, label, 'image/png');
    }
  } finally {
    await drawingBrowser.close();
  }
}
async function main() {
  if (step4Rehearsal) {
    // The Step 4 PowerShell launcher records JAR hashes FROM the actual freshly
    // built Docker images. Do not rebuild or copy local JARs a second time.
    write('candidate-artifacts.json', {
      source:'actual candidate Docker images',
      responderImage:process.env.STEP4_CANDIDATE_RESPONDER_IMAGE,
      webImage:process.env.STEP4_CANDIDATE_WEB_IMAGE,
      runnerSha256:sha(fs.readFileSync(__filename))
    });
  } else {
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
  }
  await docker('network','create',prefix); networkCreated=true;
  if (step4Rehearsal) {
    // Docker's local Linux volume supports the real upload protocol: POSIX mode
    // 0700, flock, hard links and atomic rename. The Windows-hosted bind mount
    // used by the first published-image attempt could not satisfy this gate.
    // A run-unique name, explicit absence check and owned cleanup prevent
    // touching the NAS or a developer's existing Docker volumes.
    try {
      await docker('volume','inspect',filesVolume);
      throw Error(`Refusing to reuse pre-existing Docker volume ${filesVolume}`);
    } catch (error) {
      if (!/no such volume/i.test(error.stderr || error.message || '')) throw error;
    }
    const name = await docker('volume','create',
      '--label','diaries.feature=0051','--label','diaries.purpose=step4-published-fixture',filesVolume);
    assert.equal(name,filesVolume,'Disposable Docker volume was not created as requested');
    filesVolumeCreated=true;
    write('step4-files-volume.json',{name:filesVolume,driver:'local',
      purpose:'private Linux filesystem for 0051 upload / rollback',sharedNas:false});
  }
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
  await container(broker, ['-p','127.0.0.1::1883',...(process.env.STEP3_EDITOR_ONLY === '1' ? ['-p','127.0.0.1::9001'] : []),'--mount',`type=bind,source=${output},target=/fixture,readonly`,'--entrypoint','sh','eclipse-mosquitto:2.0.22','-c','for u in diaries-responder diaries-client diaries-web diaries-health; do touch /tmp/passwords; mosquitto_passwd -b /tmp/passwords "$u" step13-fixture; done; chmod 644 /tmp/passwords; exec mosquitto -c /fixture/mosquitto.conf']);
  const port = async(name,internal)=>Number((await docker('port',name,String(internal))).split(':').at(-1));
  summary.mqttUrl='mqtt://127.0.0.1:'+await port(broker,1883);
  await waitFor('Mosquitto', async()=>{ try { const probe=await connect('diaries-health'); await probe.endAsync(); return true; } catch { return false; } });
  const proxyPort=await unusedPort(); summary.publicOrigin='http://127.0.0.1:'+proxyPort;
  const responderConfig = (imageWritesEnabled, extensionWritesEnabled = imageWritesEnabled) => ({
    db:{jdbc:{dbms:'postgresql',driver:'org.postgresql.Driver'},host:db,port:5432,database:'step13',admin:{username:'diaries',password:''},users:[{username:'diaries',password:''}],additionalConnectionProperties:{'hibernate.hbm2ddl.auto':'validate'}},
    diaries:{root:'/data',files:'files',diaries:'diaries',baseUrl:'http://localhost:8081'},mqtt:{host:broker,port:1883,user:{username:'diaries-responder',password:'step13-fixture'}},
    refreshPeriod:'30m',refreshExpiration:'2h',normaliseOnStartup:false,imageFragmentWritesEnabled:imageWritesEnabled,imageFragmentExtensionsWritesEnabled:extensionWritesEnabled,
    secret:Buffer.from('step13-disposable-signing-key-01234567890123456789').toString('base64')
  });
  fs.writeFileSync(path.join(output,'responder.json'),JSON.stringify(responderConfig(step4Rehearsal, false),null,2));
  const javaImage=process.env.STEP13_JAVA_IMAGE || 'diaries-responder:local';
  // These are disposable containers, so always populate both fixture trees. Checking
  // only for /data/files could accidentally skip copying the synthetic Page files
  // when a custom Java runtime image pre-creates that directory.
  // Step 4 runs the exact Jenkins-published responder image, configured using
  // CONFIG_FILE as required by its /opt/diaries/bin/responder.sh entrypoint.
  // Only synthetic fixture directories are mounted. Step 3 keeps its accepted
  // JAR launch unchanged.
  if (step4Rehearsal) {
    const image = process.env.STEP4_CANDIDATE_RESPONDER_IMAGE;
    assert(image, 'Step 4 candidate responder image not provided');
    // Prepare the private staging directory inside the Linux filesystem before
    // the upload RPC. `ImageCatalogueService` requires rwx------ and verifies
    // file locks, hard links and atomic rename on the mounted filesystem.
    const preflight = await docker('run','--rm',
      '--mount',`type=volume,source=${filesVolume},target=/data/files`,
      '--entrypoint','sh',image,'-c',
      'mkdir -p /data/files/.image-staging && chmod 700 /data/files/.image-staging && test "$(stat -c %a /data/files/.image-staging)" = 700 && f=$(mktemp /data/files/.image-staging/0051-preflight-XXXXXX) && ln "$f" "$f.link" && mv "$f.link" "$f.moved" && rm "$f" "$f.moved" && echo STEP4_FILES_PREFLIGHT_PASS');
    assert.equal(preflight,'STEP4_FILES_PREFLIGHT_PASS','Linux Files volume preflight failed');
    write('step4-files-preflight.txt',preflight+'\n');
    await container(responder, ['-p','127.0.0.1::8081',
      '-e','CONFIG_FILE=/fixture/responder.json',
      '--mount',`type=volume,source=${filesVolume},target=/data/files`,
      '--mount',`type=bind,source=${path.join(output,'diaries')},target=/data/diaries,readonly`,
      '--mount',`type=bind,source=${output},target=/fixture,readonly`,
      image]);
  } else {
    await container(responder, ['-p','127.0.0.1::8081','--mount',`type=bind,source=${output},target=/fixture`,'--entrypoint','sh',javaImage,'-c','mkdir -p /data/files/.image-staging /data/diaries; cp -a /fixture/diaries/. /data/diaries/; chmod 700 /data/files/.image-staging; exec java -jar /fixture/responder.jar --config /fixture/responder.json']);
  }
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
  if (step4Rehearsal) {
    const image = process.env.STEP4_CANDIDATE_WEB_IMAGE;
    assert(image, 'Step 4 candidate web image not provided');
    await container(web, ['-p','127.0.0.1::8082',
      '-e','DIARIES_WEB_MQTT_USERNAME=diaries-web',
      '-e','DIARIES_WEB_MQTT_PASSWORD=step13-fixture',
      '--mount',`type=bind,source=${path.join(output,'web.json')},target=/config/diaries-web.json,readonly`,
      image]);
  } else {
    await container(web, ['-p','127.0.0.1::8082','-e','DIARIES_WEB_MQTT_USERNAME=diaries-web','-e','DIARIES_WEB_MQTT_PASSWORD=step13-fixture','--mount',`type=bind,source=${output},target=/fixture,readonly`,'--entrypoint','java',javaImage,'-jar','/fixture/web.jar','--config','/fixture/web.json']);
  }
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
  // Step 4 is an opt-in, separate pre-activation rollout/rollback rehearsal.
  // Do not execute the already accepted Step 3 scenarios again in this mode.
  if (step4Rehearsal) {
    const { runStep4RolloutChecks } = require('./step4-rollout-rehearsal-checks.cjs');
    await runStep4RolloutChecks({root,output,evidence,summary,checks,first,
      responder,web,db,broker,prefix,owned,filesVolume,docker,container,port,sql,rows,rpc,
      waitFor,write,retainedSnapshot,retainedPayload,expectRpcStatus,
      responderConfig,upstreamPorts,
      relogin:async()=>{
        accessToken=undefined;
        const response=await rpc('signin',{username:'step13-smoke',password:'step13-fixture',sessionId:crypto.randomUUID()});
        expectRpcStatus(response,200,'signin after component swap');
        accessToken=response.payload.accessToken;
      }
    });
    summary.status='PASSED';
    return;
  }
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
  // Only one synthetic catalogued image is needed for 0051; the already-accepted
  // 0026 missing-media and shared-image lifecycle suites are NOT rerun here.
  const selectedImage=await upload('0051 selected image.png','step3/maps/nested','selected.png');
  write('uploaded-images.json',{selectedImage});
  const path0051=selectedImage.image?.relativePath;
  assert(path0051,'0051 uploaded Image must have retained relativePath');
  const bytes0051=fs.readFileSync(path.join(output,'inputs','selected.png'));
  const containerHash0051=(await docker('exec',responder,'sha256sum','/data/files/'+path0051)).split(/\s+/)[0];
  const byteProbe0051=await inspectImageBytes({label:'0051-selected',relativePath:path0051,
    expectedBytes:bytes0051,containerSha256:containerHash0051,
    publicOrigin:summary.publicOrigin,responderDirectUrl:summary.responderDirectUrl});
  write('0051-image-byte-preflight.json',byteProbe0051);
  assert(byteProbe0051.ok,'0051 catalogue Image byte preflight failed');
  const legacyPlain=await rpc('addImageFragment',{pageId:first.page_id,year:first.year,month:first.month,
    day:first.day,sequence:await nextSequence(first,50),text:'0051 plain IMAGE',imageId:selectedImage.imageId});
  expectRpcStatus(legacyPlain,200,'0051 plain Image authoring without link');
  const selectedFrag=legacyPlain.payload;
  // The editor-only acceptance mode reuses the proven, disposable setup and
  // deliberately SKIPS the previously accepted public-reader scenario suite.
  if (process.env.STEP3_EDITOR_ONLY === '1') {
    const { runAngularEditorChecks } = require('./step3-angular-editor-checks.cjs');
    const mqttWsPort = await port(broker, 9001);
    await runAngularEditorChecks({
      browser, root, evidence, summary, checks, first, selectedFrag, selectedImage,
      mqttWsPort, responderPort: () => upstreamPorts.responder, sql, rows, write,
    });
    summary.status='PASSED';
    return;
  }
  const desktop=await browser.newContext({viewport:{width:1440,height:1050}});
  const page=await desktop.newPage();page.setDefaultTimeout(25000);
  const monthUrl=(p,id)=>`${summary.readerUrl}/diaries/${p.diary_id}/${p.year}/${String(p.month).padStart(2,'0')}?fragment=${id}#fragment-${id}`;
  checks.push('0051 synthetic catalogue Image byte-for-byte matches disposable filesystem, responder HTTP and browser proxy; old unrelated 0026 suites are not repeated');
  // 0051 cross-component acceptance: real RPC mutations -> PostgreSQL -> retained
  // state -> web projection -> Chrome/Edge month and source-page rendering.
  const imageLinkDestination='https://example.org/maps/0051%20photo.png?part=1%2F2#map';
  async function create0051(label, link) {
    const args={pageId:first.page_id,year:first.year,month:first.month,day:first.day,
      sequence:1,text:'0051 '+label,
      imageId:selectedImage.imageId};
    if(link)args.imageLinkUrl=imageLinkDestination;
    // Unique generated date sequence, without colliding with the historic fixture:
    const serial=++create0051.serial;
    args.sequence=await nextSequence(first,100+serial);
    const result=await rpc('addImageFragment',args);
    expectRpcStatus(result,200,'0051 '+label+' create');
    return result.payload.id;
  }
  create0051.serial=0;
  async function fragmentRow(id) {
    // Keep the PostgreSQL NUMERIC column numeric in the JSON row. PostgreSQL
    // json_agg() serialises NUMERIC as a JSON number; ::text would instead
    // send a String to the responder's Utilities.getBigDecimal RPC adapter.
    const list=await rows(`SELECT id,version,page_id AS "pageId",year,month,day,sequence,text,
      type,image_id AS "imageId",image_link_url AS "imageLinkUrl" FROM fragment WHERE id=${Number(id)}`);
    assert.equal(list.length,1,`0051 fragment ${id} must have one authoritative row`);
    assert.equal(typeof list[0].sequence,'number',`0051 Fragment ${id} sequence must remain numeric for MQTT-RPC`);
    assert(Number.isFinite(list[0].sequence),`0051 Fragment ${id} sequence must be finite`);
    return list[0];
  }
  async function marqueeRow(id) {
    const list=await rows(`SELECT id,version,fragment_id AS "fragmentId",page_id AS "pageId",x,y,width,height FROM marquee WHERE id=${Number(id)}`);
    assert.equal(list.length,1,`0051 marquee ${id} must have one authoritative row`);
    return list[0];
  }
  async function attach0051(fragmentId,label) {
    expectRpcStatus(await rpc('lockFragment',{id:fragmentId}),200,label+' lock before attach');
    const row=await fragmentRow(fragmentId);
    const reply=await rpc('addMarquee',{fragmentId,pageId:first.page_id,fragmentVersion:row.version,
      x:Math.max(10,first.width*.18),y:Math.max(10,first.height*.21),width:Math.max(80,first.width*.25),height:Math.max(80,first.height*.23)});
    expectRpcStatus(reply,200,label+' attach marquee');
    return reply.payload.id;
  }
  async function edit0051(id,fields) {
    expectRpcStatus(await rpc('lockFragment',{id}),200,'0051 lock before fragment update');
    const f=await fragmentRow(id);
    const args={id:f.id,version:f.version,year:f.year,month:f.month,day:f.day,
      sequence:f.sequence,text:f.text,...fields};
    const result=await rpc('updateFragment',args);
    expectRpcStatus(result,200,'0051 updateFragment');
  }
  const noLinkNoMarquee=selectedFrag.id; // already exercised by the accepted source-image fixture
  const linkOnly=await create0051('link only',true);
  const marqueeOnly=await create0051('marquee only',false);
  const both=await create0051('link and marquee',true);
  const marqueeOnlyId=await attach0051(marqueeOnly,'marquee only');
  const bothMarqueeId=await attach0051(both,'link and marquee');
  summary.step3Ids={noLinkNoMarquee,linkOnly,marqueeOnly,both,marqueeOnlyId,bothMarqueeId};
  write('0051-fixture-ids.json',summary.step3Ids);
  for(const [id,link,marqueeId] of [
    [noLinkNoMarquee,false,null],[linkOnly,true,null],
    [marqueeOnly,false,marqueeOnlyId],[both,true,bothMarqueeId]]) {
    const f=await fragmentRow(id);
    assert.equal(f.type,'IMAGE');
    assert.equal(f.imageId,selectedImage.imageId);
    assert.equal(f.imageLinkUrl,link?imageLinkDestination:null);
    const joined=await rows(`SELECT id FROM marquee WHERE fragment_id=${Number(id)}`);
    assert.deepEqual(joined.map(m=>m.id),marqueeId?[marqueeId]:[]);
  }
  async function awaitPublished(id,hasLink,hasMarquee) {
    await waitFor('0051 published '+id,async()=>{
      const html=await (await fetch(monthUrl(first,id))).text();
      const fragmentRe=new RegExp(`data-reader-fragment="${id}"[^>]*data-has-marquee="${hasMarquee}"`);
      if(!fragmentRe.test(html))return false;
      const chunk=html.split(`data-reader-fragment="${id}"`)[1]?.split('</article>')[0]||'';
      return (chunk.includes('fragment-media__link')===hasLink);
    },45000);
  }
  for(const [id,link,hasMarquee] of [[noLinkNoMarquee,false,false],[linkOnly,true,false],
    [marqueeOnly,false,true],[both,true,true]]) await awaitPublished(id,link,hasMarquee);
  async function check0051Browser(targetPage,id,hasLink,hasMarquee,suffix) {
    await targetPage.goto(monthUrl(first,id));
    const card=targetPage.locator(`[data-reader-fragment="${id}"]`);
    await card.waitFor();
    assert.equal(await card.getAttribute('data-fragment-type'),'IMAGE');
    assert.equal(await card.getAttribute('data-has-marquee'),String(hasMarquee));
    const links=card.locator('a.fragment-media__link');
    assert.equal(await links.count(),hasLink?1:0);
    if(hasLink)assert.equal(await links.first().getAttribute('href'),imageLinkDestination);
    const source=card.locator('a.fragment-media__source-link, .fragment-media__source a');
    assert.equal(await source.count(),1,'0051 source-page action is independent of external image link');
    const sourceHref=await source.first().getAttribute('href');
    assert(sourceHref&&!sourceHref.startsWith('https://example.org'), '0051 source navigation must not follow external link');
    assert.equal(await targetPage.locator('[data-viewer-action="fit-selection"]').isEnabled(),hasMarquee);
    await card.locator('img.fragment-media__image').scrollIntoViewIfNeeded();
    await waitFor('0051 '+suffix+' media image bytes',()=>card.locator('img.fragment-media__image').evaluate(img=>img.complete&&img.naturalWidth>0),30000);
    await targetPage.screenshot({path:path.join(evidence,`0051-${suffix}-month.png`),fullPage:true});
    await targetPage.goto(new URL(sourceHref,summary.publicOrigin).toString());
    const transcript=targetPage.locator(`[data-transcript-fragment="${id}"]`);
    await transcript.waitFor();
    assert.equal(await transcript.locator('a.fragment-media__link').count(),hasLink?1:0);
    assert.equal(await targetPage.locator(`[data-marquee-fragment="${id}"]`).count(),hasMarquee?1:0);
    if(hasMarquee)assert.equal(await transcript.locator('button[data-fragment-selector]').textContent().then(t=>t.trim()),'Show on source page');
    await targetPage.screenshot({path:path.join(evidence,`0051-${suffix}-source.png`),fullPage:true});
  }
  for(const [id,link,marquee,suffix] of [[noLinkNoMarquee,false,false,'plain'],[linkOnly,true,false,'link'],
    [marqueeOnly,false,true,'marquee'],[both,true,true,'both']]) {
    await check0051Browser(page,id,link,marquee,'desktop-'+suffix);
  }
  const uiMobile=await browser.newContext({viewport:{width:390,height:844}});
  const mobile0051=await uiMobile.newPage();
  await check0051Browser(mobile0051,both,true,true,'mobile-both');
  await uiMobile.close();
  checks.push('0051 all four IMAGE variants render desktop month/source, independent external/source links, and appropriate Marquee selection; combined IMAGE tested on mobile');
  const topics0051=await retainedSnapshot('0051-four-variants');
  for(const [id,link,marqueeId] of [[noLinkNoMarquee,false,null],[linkOnly,true,null],
      [marqueeOnly,false,marqueeOnlyId],[both,true,bothMarqueeId]]) {
    const payload=retainedPayload(topics0051,`diaries/fragments/${id}`);
    assert.equal(payload.type,'IMAGE');
    assert.equal(payload.imageId,selectedImage.imageId);
    assert.equal(payload.imageLinkUrl,link?imageLinkDestination:null);
    assert.equal(payload.marqueeId,marqueeId);
  }
  const retainedMarquee = await retainedMarqueeTopic(bothMarqueeId);
  assert(retainedMarquee, 'IMAGE Marquee must have a retained MQTT topic before removal');
  assert.equal(retainedMarquee.payload.id,bothMarqueeId);
  assert.equal(retainedMarquee.payload.fragmentId,both);
  checks.push('0051 retained Fragment/Image envelopes are decoded once; Marquee topic exists before deletion');
  // Existing writer compatibility: an edit which omits imageLinkUrl preserves it.
  await edit0051(linkOnly,{text:'0051 text-only edit preserves external link'});
  assert.equal((await fragmentRow(linkOnly)).imageLinkUrl,imageLinkDestination);
  expectRpcStatus(await rpc('lockFragment',{id:linkOnly}),200,'0051 unsafe URL lock');
  const beforeBad=await fragmentRow(linkOnly);
  const unsafe=await rpc('updateFragment',{id:linkOnly,version:beforeBad.version,year:beforeBad.year,
    month:beforeBad.month,day:beforeBad.day,sequence:beforeBad.sequence,text:beforeBad.text,
    imageLinkUrl:'javascript:alert(1)'});
  expectRpcStatus(unsafe,400,'0051 unsafe javascript URL is rejected');
  assert.equal((await fragmentRow(linkOnly)).imageLinkUrl,imageLinkDestination);
  expectRpcStatus(await rpc('unlockFragment',{id:linkOnly}),200,'0051 release lock after rejected URL');
  // Marquee edits cannot mutate IMAGE identity or its destination.
  expectRpcStatus(await rpc('lockFragment',{id:both}),200,'0051 lock before marquee edit');
  const b=await marqueeRow(bothMarqueeId);
  expectRpcStatus(await rpc('updateMarquee',{id:b.id,version:b.version,pageId:b.pageId,fragmentId:both,
    x:b.x+7,y:b.y+9,width:b.width,height:b.height}),200,'0051 edit Marquee geometry');
  assert.equal((await fragmentRow(both)).imageLinkUrl,imageLinkDestination);
  assert.equal((await fragmentRow(both)).type,'IMAGE');
  checks.push('0051 ordinary edits preserve the external destination; unsafe writes reject; Marquee geometry updates preserve IMAGE identity/link');
  const step3Restart=new Date().toISOString(), priorStep3ResponderPort=upstreamPorts.responder;
  await docker('restart',responder);
  await responderReady(step3Restart);
  await refreshResponderHttpAfterRestart('0051-restart',priorStep3ResponderPort);
  const priorStep3WebPort=upstreamPorts.web;
  await docker('restart',web);
  await refreshWebHttpAfterRestart('0051-restart',priorStep3WebPort);
  const replay0051=await retainedSnapshot('0051-after-restart');
  assert.equal(retainedPayload(replay0051,`diaries/fragments/${both}`).imageLinkUrl,imageLinkDestination);
  assert.equal(retainedPayload(replay0051,`diaries/fragments/${both}`).marqueeId,bothMarqueeId);
  await awaitPublished(both,true,true);
  await check0051Browser(page,both,true,true,'desktop-both-after-restart');
  checks.push('0051 responder/web restart preserves committed IMAGE URL and optional Marquee in both retained state and browser');
  // Explicit CLEAR and Marquee removal preserve a functioning IMAGE with source link.
  await edit0051(linkOnly,{clearImageLinkUrl:true});
  assert.equal((await fragmentRow(linkOnly)).imageLinkUrl,null);
  await awaitPublished(linkOnly,false,false);
  expectRpcStatus(await rpc('lockFragment',{id:both}),200,'0051 lock before Marquee removal');
  const removing=await marqueeRow(bothMarqueeId);
  expectRpcStatus(await rpc('deleteMarquee',{id:bothMarqueeId,version:removing.version}),200,'0051 remove Marquee');
  assert.equal((await fragmentRow(both)).type,'IMAGE');
  assert.equal((await fragmentRow(both)).imageId,selectedImage.imageId);
  await awaitPublished(both,true,false);
  const afterRemoval=await retainedSnapshot('0051-after-clear-and-removal');
  assert.equal(await retainedMarqueeTopic(bothMarqueeId),null,
    'Deleted Marquee must not have a retained MQTT topic');
  assert.equal(retainedPayload(afterRemoval,`diaries/fragments/${both}`).marqueeId,null);
  assert.equal(retainedPayload(afterRemoval,`diaries/fragments/${linkOnly}`).imageLinkUrl,null);
  checks.push('0051 explicit link clearing and optional Marquee deletion update DB, retained topics and reader without deleting the catalogued Image');
  summary.fixtureIds=summary.step3Ids;
  summary.status='PASSED';
}
main().catch(error=>{summary.status='FAILED';summary.failure=error.stack;process.exitCode=1;console.error(error);}).finally(async()=>{
  if(browser)await browser.close().catch(()=>{}); if(proxyServer)await new Promise(resolve=>proxyServer.close(resolve));
  for(const c of connections)await c.endAsync(true).catch(()=>{});
  for(const name of [responder,web,broker,db]) if(owned.includes(name)){try{const logs=await run('docker',['logs',name],{maxBuffer:32*1024*1024});const lines=(logs.stdout+logs.stderr).split('\n').filter(line=>/Connected, subscribing|synchronise:|Published replay generation|Subscribed to canonical|Javalin started|Sending status:|Image deletion|Step 13|Outgoing messages are being dropped|not authori[sz]ed|denied|too many|queue full|disconnect|Static server|Exception|\bERROR\b|failed|BindException/i.test(line)).slice(-500);write(name.slice(prefix.length+1)+'.log',lines.join('\n')+'\n');}catch{}}
  const cleanup={containersRemoved:[],networkRemoved:false,
    filesVolume:step4Rehearsal ? filesVolume : null,filesVolumeRemoved:false,failures:[]};
  for(const name of owned.reverse()){try{await docker('rm','-f',name);cleanup.containersRemoved.push(name);}catch{cleanup.failures.push(name);}}
  if(filesVolumeCreated){
    try { await docker('volume','rm',filesVolume); cleanup.filesVolumeRemoved=true; }
    catch(error){cleanup.failures.push(`files-volume:${filesVolume}: ${error.message}`);}
  }
  if(networkCreated){try{await docker('network','rm',prefix);cleanup.networkRemoved=true;}catch{cleanup.failures.push(prefix);}}
  write('cleanup.json',cleanup);
  summary.cleanupFailures=cleanup.failures; if(cleanup.failures.length){summary.status='CLEANUP_FAILED';process.exitCode=1;} summary.finishedAtUtc=new Date().toISOString(); write('summary.json',summary);
  fs.writeFileSync(path.join(evidence,'SHA256SUMS.txt'),manifest(evidence).filter(x=>x.path!=='SHA256SUMS.txt').map(x=>x.sha256+'  '+x.path).join('\n')+'\n');
  console.log(`0051 Step ${summary.step}: ${summary.status}; evidence: ${evidence}`);
});
