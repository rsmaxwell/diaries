/* 0024 Phase 10: packaged applications, real MQTT RPC and browser UI on owned fixtures. */
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
const { chromium } = require('playwright');
const root = path.resolve(__dirname, '../../..');
const mqtt = require(path.join(root, 'diaries-client/node_modules/mqtt'));
const [backupArg, filesArg, outputArg] = process.argv.slice(2);
if (!backupArg || !filesArg || !outputArg) throw Error('Usage: node smoke-image-catalogue.cjs BACKUP FILES_COPY_SOURCE NEW_OUTPUT');
const backup = fs.realpathSync(backupArg), source = fs.realpathSync(filesArg), output = path.resolve(outputArg);
assert(!fs.existsSync(output), 'Output must be new');
assert(!output.startsWith(source + path.sep), 'Output cannot be inside the copy source');
fs.mkdirSync(output, { recursive: true });
const evidence = path.join(output, 'evidence');
fs.mkdirSync(evidence);
const prefix = 'diaries-0024-phase10-' + crypto.randomUUID().slice(0, 8);
const db = prefix + '-db', broker = prefix + '-mqtt', responder = prefix + '-responder', web = prefix + '-web';
const owned = [], connections = [], checks = [];
let browser, server, networkCreated = false;
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const write = (name, value) => fs.writeFileSync(path.join(evidence, name), typeof value === 'string' ? value : JSON.stringify(value, null, 2));
const summary = { phase: 10, startedAtUtc: new Date().toISOString(), status: 'RUNNING', checks,
  backupFilename: path.basename(backup), backupSha256: sha(fs.readFileSync(backup)), liveDataModified: false };
async function docker(...args) { return (await run('docker', args, { maxBuffer: 32 * 1024 * 1024 })).stdout.trim(); }
async function container(name, args) { await docker('run', '-d', '--name', name, '--network', prefix, ...args); owned.push(name); }
async function unusedPort() {
  const probe = net.createServer();
  await new Promise(resolve => probe.listen(0, '127.0.0.1', resolve));
  const port = probe.address().port;
  await new Promise(resolve => probe.close(resolve));
  return port;
}
async function waitFor(label, action, timeout = 120000) {
  const end = Date.now() + timeout;
  let error;
  while (Date.now() < end) {
    try { const value = await action(); if (value) return value; } catch (e) { error = e; }
    await new Promise(resolve => setTimeout(resolve, 300));
  }
  throw Error(`${label} timed out: ${error?.message || 'condition not satisfied'}`);
}
async function sql(query) { return docker('exec', db, 'psql', '-XAt', '-U', 'diaries', '-d', 'image_smoke_test', '-v', 'ON_ERROR_STOP=1', '-c', query); }
async function rows(query) { return JSON.parse(await sql(`SELECT coalesce(json_agg(t),'[]') FROM (${query}) t`)); }
function manifest(directory) {
  const result = [];
  function visit(dir) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      assert(!entry.isSymbolicLink(), 'Smoke copies cannot follow symlinks');
      const file = path.join(dir, entry.name);
      if (entry.isDirectory()) visit(file);
      else result.push({ path: path.relative(directory, file).replaceAll('\\', '/'), bytes: fs.statSync(file).size, sha256: sha(fs.readFileSync(file)) });
    }
  }
  visit(directory);
  return result.sort((a, b) => a.path.localeCompare(b.path));
}
async function connect(username = 'diaries-responder') {
  const client = await mqtt.connectAsync(summary.mqttUrl, { protocolVersion: 5, username, password: 'phase10-fixture',
    clientId: 'smoke-' + crypto.randomUUID(), clean: true, reconnectPeriod: 0 });
  connections.push(client);
  return client;
}
async function snapshot(label) {
  const chronology = await rows(['diary', 'page', 'fragment', 'marquee'].map(table =>
    `SELECT '${table}' AS name,count(*)::int AS count,md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]')) AS hash FROM ${table} t`).join(' UNION ALL '));
  const images = await rows('SELECT * FROM image ORDER BY id');
  const client = await connect();
  const retained = {};
  const marker = 'diaries/diaries/_sync/smoke/' + crypto.randomUUID();
  let drained = false;
  client.on('message', (topic, bytes, packet) => { if (topic === marker) drained = true; else if (packet.retain && bytes.length) retained[topic] = sha(bytes); });
  await client.subscribeAsync('diaries/#', { qos: 0 });
  await client.publishAsync(marker, '1', { qos: 1, retain: false });
  await waitFor('retained snapshot', () => drained);
  await client.endAsync();
  // Hash in Linux: copying back to Windows would collapse deliberately case-colliding names.
  const sizes = new Map((await docker('exec', responder, 'find', '/data/files', '-type', 'f', '-exec', 'stat', '-c', '%s %n', '{}', ';')).split('\n').filter(Boolean).map(line => {
    const match = line.match(/^(\d+) (.*)$/); assert(match); return [match[2], Number(match[1])];
  }));
  const files = (await docker('exec', responder, 'find', '/data/files', '-type', 'f', '-exec', 'sha256sum', '{}', ';')).split('\n').filter(Boolean).map(line => {
    const match = line.match(/^([a-f0-9]{64})  (.*)$/); assert(match);
    return { path: match[2].slice('/data/files/'.length), bytes: sizes.get(match[2]), sha256: match[1] };
  }).filter(file => !file.path.startsWith('.image-staging/')).sort((a, b) => a.path.localeCompare(b.path));
  const value = { chronology, images, files, retained };
  write(label + '.json', value);
  return value;
}
function sameChronology(a, b) { assert.deepEqual(b.chronology, a.chronology); }
async function main() {
  console.log('Copying Files and creating synthetic smoke inputs.');
  const sourceManifest = manifest(source);
  fs.cpSync(source, path.join(output, 'files'), { recursive: true, errorOnExist: true });
  assert.deepEqual(manifest(path.join(output, 'files')), sourceManifest);
  write('source-copy-sha256.json', sourceManifest);
  fs.mkdirSync(path.join(output, 'inputs'));
  fs.mkdirSync(path.join(output, 'diaries'));
  const python = process.env.SMOKE_PYTHON || 'python';
  await run(python, ['-c', 'from PIL import Image,ImageDraw; import sys,pathlib; p=pathlib.Path(sys.argv[1]); im=Image.new("RGB",(1200,1600),"wheat"); d=ImageDraw.Draw(im); d.rectangle((90,110,900,650),outline="black",width=8); d.text((100,150),"0024 disposable source page",fill="black"); im.save(p/"smoke-ui.jpg"); im.save(p/"smoke-octet.png")', path.join(output, 'inputs')]);
  const jpeg = fs.readFileSync(path.join(output, 'inputs/smoke-ui.jpg'));
  const png = fs.readFileSync(path.join(output, 'inputs/smoke-octet.png'));
  fs.writeFileSync(path.join(output, 'files/smoke-pre-existing.png'), png);
  fs.writeFileSync(path.join(output, 'files/smoke-corrupt.png'), Buffer.from([137,80,78,71,13,10,26,10,0]));
  const responderJar = fs.readdirSync(path.join(root, 'diaries-responder/build/libs')).find(x => x.endsWith('-fat.jar'));
  const webJar = fs.readdirSync(path.join(root, 'diaries-web/build/libs')).find(x => x.endsWith('-fat.jar'));
  fs.copyFileSync(path.join(root, 'diaries-responder/build/libs', responderJar), path.join(output, 'responder.jar'));
  fs.copyFileSync(path.join(root, 'diaries-web/build/libs', webJar), path.join(output, 'web.jar'));
  write('artifacts.json', { responder: { filename: responderJar, sha256: sha(fs.readFileSync(path.join(output, 'responder.jar'))) },
    web: { filename: webJar, sha256: sha(fs.readFileSync(path.join(output, 'web.jar'))) },
    client: manifest(path.join(root, 'diaries-client/dist/diaries-client/browser')), runnerSha256: sha(fs.readFileSync(__filename)) });
  await docker('network', 'create', prefix); networkCreated = true;
  await container(db, ['--tmpfs', '/var/lib/postgresql', '-e', 'POSTGRES_USER=diaries', '-e', 'POSTGRES_DB=image_smoke_test', '-e', 'POSTGRES_HOST_AUTH_METHOD=trust', 'postgres:18-alpine']);
  await waitFor('PostgreSQL', async () => { await docker('exec', db, 'pg_isready', '-U', 'diaries'); return true; });
  await docker('cp', backup, db + ':/tmp/baseline.dump');
  await docker('exec', db, 'pg_restore', '-U', 'diaries', '-d', 'image_smoke_test', '--no-owner', '--no-privileges', '/tmp/baseline.dump');
  const migration = path.join(root, 'change-control/complete/0024-FEAT - introduce reusable persistent Image catalogue/migration');
  await docker('cp', path.join(migration, 'schema.sql'), db + ':/tmp/schema.sql');
  await docker('exec', db, 'psql', '-X', '-U', 'diaries', '-d', 'image_smoke_test', '-v', 'ON_ERROR_STOP=1', '-f', '/tmp/schema.sql');
  // Only the restored fixture's login is changed; diary content is never edited.
  await sql("CREATE EXTENSION IF NOT EXISTS pgcrypto; UPDATE person SET username='phase10-smoke', passwordhash=crypt('phase10-fixture',gen_salt('bf')), status='ACTIVE', role='ADMIN' WHERE id=(SELECT min(id) FROM person)");
  const selected = (await rows('SELECT f.id AS fragment_id,f.page_id,f.year,f.month,d.id AS diary_id,d.name AS diary_name,p.name AS page_name,p.extension,p.width AS page_width,p.height AS page_height,m.x,m.y,m.width AS marquee_width,m.height AS marquee_height FROM fragment f JOIN page p ON p.id=f.page_id JOIN diary d ON d.id=p.diary_id JOIN marquee m ON m.fragment_id=f.id WHERE f.type=\'MARQUEE\' ORDER BY f.id LIMIT 1'))[0];
  assert(selected, 'Backup must contain a MARQUEE fragment');
  const pageDirectory = path.join(output, 'diaries', selected.diary_name);
  fs.mkdirSync(pageDirectory, { recursive: true });
  const pageFilename = selected.page_name + (selected.extension.startsWith('.') ? '' : '.') + selected.extension;
  await run(python, ['-c', 'from PIL import Image,ImageDraw,ImageFont; import sys,json; r=json.loads(sys.argv[1]); im=Image.new("RGB",(r["page_width"],r["page_height"]),"wheat"); d=ImageDraw.Draw(im); x,y,w,h=(r[k] for k in ("x","y","marquee_width","marquee_height")); d.rectangle((x,y,x+w,y+h),outline="navy",width=10); d.text((x+35,y+35),"0024 disposable MARQUEE source",fill="navy",font=ImageFont.load_default(size=45)); im.save(sys.argv[2])', JSON.stringify(selected), path.join(pageDirectory, pageFilename)]);
  write('ui-fixture.json', { ...selected, pageImage: 'Synthetic page image; database page/fragment/marquee metadata unchanged' });
  fs.writeFileSync(path.join(output, 'mosquitto.conf'), 'listener 1883\nlistener 9001\nprotocol websockets\nallow_anonymous false\npassword_file /tmp/passwords\nacl_file /fixture/aclfile.txt\nmax_queued_messages 10000\n');
  fs.copyFileSync(path.join(root, 'config/mosquitto/aclfile.txt'), path.join(output, 'aclfile.txt'));
  await container(broker, ['-p', '127.0.0.1::1883', '-p', '127.0.0.1::9001', '--mount', `type=bind,source=${output},target=/fixture,readonly`, '--entrypoint', 'sh', 'eclipse-mosquitto:2.0.22', '-c',
    'for u in diaries-responder diaries-client diaries-web diaries-health; do touch /tmp/passwords; mosquitto_passwd -b /tmp/passwords "$u" phase10-fixture; done; chmod 644 /tmp/passwords; exec mosquitto -c /fixture/mosquitto.conf']);
  const port = async (name, internal) => Number((await docker('port', name, String(internal))).split(':').at(-1));
  summary.mqttUrl = 'mqtt://127.0.0.1:' + await port(broker, 1883);
  const wsPort = await port(broker, 9001);
  const config = { db: { jdbc: { dbms: 'postgresql', driver: 'org.postgresql.Driver' }, host: db, port: 5432, database: 'image_smoke_test', admin: { username: 'diaries', password: '' }, users: [{ username: 'diaries', password: '' }], additionalConnectionProperties: { 'hibernate.hbm2ddl.auto': 'validate' } },
    diaries: { root: '/data', files: 'files', diaries: 'diaries', baseUrl: 'http://localhost:8081' },
    mqtt: { host: broker, port: 1883, user: { username: 'diaries-responder', password: 'phase10-fixture' } }, refreshPeriod: '30m', refreshExpiration: '2h', normaliseOnStartup: false,
    secret: Buffer.from('phase10-disposable-signing-key-01234567890123456789').toString('base64') };
  fs.writeFileSync(path.join(output, 'responder.json'), JSON.stringify(config));
  const javaImage = process.env.SMOKE_JAVA_IMAGE || 'diaries-responder:local';
  const responderPort = await unusedPort();
  await container(responder, ['-p', `127.0.0.1:${responderPort}:8081`, '--mount', `type=bind,source=${output},target=/fixture`, '--entrypoint', 'sh', javaImage, '-c',
    'mkdir -p /data; if [ ! -d /data/files ]; then cp -a /fixture/files /data/files; cp -a /fixture/diaries /data/diaries; mkdir -p /data/files/.image-staging; chmod 700 /data/files/.image-staging; fi; exec java -jar /fixture/responder.jar --config /fixture/responder.json']);
  summary.responderUrl = 'http://127.0.0.1:' + await port(responder, 8081);
  await waitFor('responder HTTP', async () => (await fetch(summary.responderUrl + '/diaries/' + encodeURIComponent(selected.diary_name) + '/' + encodeURIComponent(pageFilename))).ok);
  async function responderReady(since = summary.startedAtUtc) {
    await waitFor('responder RPC subscription', async () => (await docker('logs', '--since', since, '--tail', '30', responder)).includes("Connected, subscribing to: 'diaries/rpc/request'"));
  }
  await responderReady();
  await docker('exec', responder, 'sh', '-c', 'mkdir -p /data/files/smoke-case; cp /fixture/inputs/smoke-octet.png /data/files/smoke-case/Photo.png; cp /fixture/inputs/smoke-octet.png /data/files/smoke-case/photo.png');
  const webConfig = JSON.parse(fs.readFileSync(path.join(root, 'diaries-web/config/diaries-web.docker.json')));
  webConfig.mqtt.host = broker; webConfig.content.responderBaseUrl = `http://${responder}:8081`;
  webConfig.content.publicResponderBaseUrl = summary.responderUrl;
  fs.writeFileSync(path.join(output, 'web.json'), JSON.stringify(webConfig));
  await container(web, ['-p', '127.0.0.1::8082', '-e', 'DIARIES_WEB_MQTT_USERNAME=diaries-web', '-e', 'DIARIES_WEB_MQTT_PASSWORD=phase10-fixture', '--mount', `type=bind,source=${output},target=/fixture,readonly`, '--entrypoint', 'java', javaImage, '-jar', '/fixture/web.jar', '--config', '/fixture/web.json']);
  summary.webUrl = 'http://127.0.0.1:' + await port(web, 8082);
  await waitFor('web ready', async () => (await fetch(summary.webUrl + '/health/ready')).ok);
  console.log('Packaged responder/web ready; exercising authenticated MQTT and browser upload.');
  const rpcClient = await connect('diaries-client'), responseTopic = `diaries/rpc/${rpcClient.options.clientId}/response`;
  await rpcClient.subscribeAsync(responseTopic, { qos: 1 });
  const pending = new Map();
  rpcClient.on('message', (topic, bytes, packet) => {
    const id = packet.properties?.correlationData?.toString();
    if (topic !== responseTopic || !pending.has(id)) return;
    const status = JSON.parse(packet.properties.userProperties.status);
    const entry = pending.get(id); pending.delete(id); clearTimeout(entry.timer);
    entry.resolve({ status, payload: bytes.length ? JSON.parse(bytes) : null });
  });
  let accessToken;
  async function rpc(fn, args) {
    const id = crypto.randomUUID();
    const reply = new Promise((resolve, reject) => pending.set(id, { resolve, timer: setTimeout(() => { pending.delete(id); reject(Error(fn + ' timeout')); }, 15000) }));
    await rpcClient.publishAsync('diaries/rpc/request', JSON.stringify({ function: fn, args }), { qos: 1,
      properties: { responseTopic, correlationData: Buffer.from(id), ...(accessToken ? { userProperties: { accessToken } } : {}) } });
    return reply;
  }
  const signedIn = await rpc('signin', { username: 'phase10-smoke', password: 'phase10-fixture', sessionId: crypto.randomUUID() });
  assert.equal(signedIn.status.code, 200); accessToken = signedIn.payload.accessToken;
  const initial = await snapshot('01-before');
  assert.equal(initial.images.length, 0);
  const webCounts = { diary: 'diaries', page: 'pages', fragment: 'fragments', marquee: 'marquees' };
  await waitFor('complete web projection', async () => {
    const health = await (await fetch(summary.webUrl + '/health/ready')).json();
    return initial.chronology.every(table => health[webCounts[table.name]] === table.count);
  });
  write('web-before-health.json', await (await fetch(summary.webUrl + '/health/ready')).json());
  const observer = await connect();
  const publishedImages = [];
  observer.on('message', (topic, bytes, packet) => publishedImages.push({ topic, qos: packet.qos, retained: packet.retain, payload: JSON.parse(bytes) }));
  await observer.subscribeAsync('diaries/images/+', { qos: 1 });
  const clientConfig = JSON.parse(fs.readFileSync(path.join(root, 'diaries-client/public/assets/config.json')));
  clientConfig.brokerDirectUrl = 'ws://127.0.0.1:' + wsPort; clientConfig.password = 'phase10-fixture';
  clientConfig.responderBaseUrlMode = 'explicit'; clientConfig.responderBaseUrl = summary.responderUrl;
  const clientDist = path.join(root, 'diaries-client/dist/diaries-client/browser');
  server = http.createServer((req, res) => {
    const url = new URL(req.url, 'http://localhost');
    if (url.pathname.endsWith('/assets/config.json')) { res.setHeader('Content-Type', 'application/json'); return res.end(JSON.stringify(clientConfig)); }
    let file = path.resolve(clientDist, '.' + decodeURIComponent(url.pathname.replace(/^\/diaries/, '')));
    if (!file.startsWith(clientDist + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) file = path.join(clientDist, 'index.html');
    const mime = { '.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html', '.json': 'application/json', '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };
    res.setHeader('Content-Type', mime[path.extname(file)] || 'application/octet-stream'); fs.createReadStream(file).pipe(res);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  summary.clientUrl = 'http://127.0.0.1:' + server.address().port + '/diaries';
  browser = await chromium.launch({ executablePath: process.env.CHROME_BIN || 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1050 } });
  const page = await context.newPage(); page.setDefaultTimeout(20000);
  await page.goto(summary.clientUrl + '/signin');
  await page.getByLabel('Username', { exact: true }).fill('phase10-smoke');
  await page.getByLabel('Password', { exact: true }).fill('phase10-fixture');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.waitForURL('**/diaries/diaries');
  const selectedRoute = `/diary/${selected.diary_id}/${selected.page_id}/${selected.fragment_id}`;
  await page.goto(summary.clientUrl + selectedRoute);
  await page.getByRole('button', { name: 'Fit selection', exact: true }).waitFor();
  await waitFor('selected client marquee', () => page.locator('#rect-selected').count());
  await page.getByRole('button', { name: 'Fit selection', exact: true }).click();
  await page.getByRole('button', { name: 'Zoom in', exact: true }).click();
  await page.screenshot({ path: path.join(evidence, 'client-marquee.png'), fullPage: true });
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Upload file', exact: true }).click();
  await (await chooser).setFiles(path.join(output, 'inputs/smoke-ui.jpg'));
  await page.locator('.file-name').filter({ hasText: /^smoke-ui.jpg$/ }).waitFor();
  await waitFor('uploaded JPEG preview', () => page.locator('img[alt="smoke-ui.jpg"]').evaluateAll(imgs => imgs.some(img => img.complete && img.naturalWidth > 0)));
  await page.screenshot({ path: path.join(evidence, 'client-upload-preview.png'), fullPage: true });
  await page.getByRole('button', { name: 'Close', exact: true }).click();
  const uiImage = (await rows("SELECT * FROM image WHERE relative_path='smoke-ui.jpg'"))[0];
  assert.equal(uiImage.mime_type, 'image/jpeg');
  checks.push('Actual client sign-in, MARQUEE selection/zoom, JPEG upload, file listing and decoded thumbnail');
  const responses = [];
  async function upload(name, bytes, contentType, extra = {}) { const value = await rpc('uploadFile', { name, bytes: bytes.toString('base64'), size: bytes.length, contentType, ...extra }); responses.push({ operation: 'uploadFile', name, ...value }); return value; }
  const twin = await upload('smoke-twin.jpg', jpeg, 'image/jpeg');
  const octet = await upload('smoke-octet.png', png, 'application/octet-stream');
  for (const value of [twin, octet]) { assert.equal(value.status.code, 200); assert(value.payload.imageId); assert(value.payload.image); }
  assert.equal(twin.payload.image.checksum, uiImage.checksum);
  assert.notEqual(twin.payload.imageId, uiImage.id);
  assert.equal(octet.payload.image.mimeType, 'image/png');
  const generic = await upload('smoke-generic.bin', Buffer.from('generic phase10 data'), 'application/octet-stream');
  assert.equal(generic.status.code, 200); assert(!generic.payload.imageId);
  const protectedBefore = await snapshot('02-before-guards');
  assert.equal(protectedBefore.images.length, 3);
  assert.equal(new Set(publishedImages.map(message => message.topic)).size, 3);
  assert(publishedImages.every(message => message.qos === 1 && message.topic === 'diaries/images/' + message.payload.id));
  write('upload-image-publications.json', publishedImages);
  for (const extra of [{}, { overwrite: true }]) assert.equal((await upload('smoke-ui.jpg', jpeg, 'image/jpeg', extra)).status.code, 409);
  assert.equal((await upload('SMOKE-UI.JPG', jpeg, 'image/jpeg')).status.code, 409);
  const deletion = await rpc('deleteFile', { name: 'smoke-ui.jpg' }); responses.push({ operation: 'deleteFile', ...deletion }); assert.equal(deletion.status.code, 409);
  const corrupt = await upload('smoke-bad-upload.png', fs.readFileSync(path.join(output, 'files/smoke-corrupt.png')), 'image/png'); assert.equal(corrupt.status.code, 400);
  const protectedAfter = await snapshot('03-after-guards');
  assert.deepEqual(protectedAfter.images, protectedBefore.images); assert.deepEqual(protectedAfter.files, protectedBefore.files); sameChronology(initial, protectedAfter);
  write('rpc-responses.json', responses);
  checks.push('Content-detected octet-stream PNG, distinct same-checksum Images, generic uncatalogued upload, immutable conflict/delete/corrupt rejection');
  const webPage = await context.newPage();
  const webRoute = `/diaries/${selected.diary_id}/${selected.year}/${String(selected.month).padStart(2, '0')}?fragment=${selected.fragment_id}`;
  const webBefore = await (await fetch(summary.webUrl + webRoute)).text();
  assert(webBefore.includes('data-viewer-marquee'));
  await webPage.goto(summary.webUrl + webRoute);
  await webPage.getByRole('button', { name: 'Fit selection', exact: true }).click();
  await webPage.getByRole('button', { name: 'Zoom in', exact: true }).click();
  await webPage.screenshot({ path: path.join(evidence, 'web-marquee.png'), fullPage: true });
  await sql(`INSERT INTO image(relative_path,mime_type,original_filename,width,height,checksum) VALUES('smoke-absent.png','image/png','smoke-absent.png',1200,1600,'${sha(png)}')`);
  const absentDelete = await rpc('deleteFile', { name: 'smoke-absent.png' });
  assert.equal(absentDelete.status.code, 409);
  responses.push({ operation: 'deleteFile', name: 'smoke-absent.png', ...absentDelete });
  write('rpc-responses.json', responses);
  // Quiesce every test writer. The CLI also holds the production catalogue/file locks.
  await page.goto('about:blank'); await webPage.goto('about:blank'); await rpcClient.endAsync();
  console.log('Running reviewed reconciliation, repeat apply, then responder restart.');
  async function reconcile(name, mode = 'dry-run', plan) {
    const args = ['exec', responder, 'java',
      '-cp', '/fixture/responder.jar', 'com.rsmaxwell.diaries.responder.migration.migration0024.Migration0024ImageCatalogue', '--config', '/fixture/responder.json', '--output', '/fixture/evidence/' + name, '--mode', mode];
    if (plan) args.push('--plan', '/fixture/evidence/' + plan + '/0024-create-plan.json');
    write(name + '.log', await docker(...args));
    return JSON.parse(fs.readFileSync(path.join(evidence, name, '0024-summary.json')));
  }
  const dry = await reconcile('reconciliation-dry-run');
  assert(dry.counts.CREATE_MISSING > 0); assert(dry.counts.DATABASE_ROW_MISSING_FILE > 0); assert(dry.counts.UNREADABLE > 0); assert(dry.counts.UNSUPPORTED > 0);
  assert.equal(dry.counts.CASE_COLLISION, 2);
  const apply = await reconcile('reconciliation-apply', 'apply', 'reconciliation-dry-run');
  assert.equal(apply.insertedRows, dry.counts.CREATE_MISSING);
  const repeat = await reconcile('reconciliation-repeat-apply', 'apply', 'reconciliation-dry-run');
  assert.equal(repeat.insertedRows, 0);
  const post = await reconcile('reconciliation-post-dry-run'); assert(!post.counts.CREATE_MISSING);
  let restartTime = new Date().toISOString();
  await docker('restart', responder);
  await waitFor('responder restarted', async () => (await fetch(summary.responderUrl + '/diaries/' + selected.diary_name + '/' + pageFilename)).ok);
  await responderReady(restartTime);
  const final = await snapshot('04-after-reconciliation-restart'); sameChronology(initial, final);
  assert.deepEqual(final.files, protectedAfter.files);
  const imageTopics = Object.keys(final.retained).filter(topic => /^diaries\/images\/\d+$/.test(topic));
  assert.equal(imageTopics.length, final.images.length);
  restartTime = new Date().toISOString();
  await docker('restart', responder);
  await waitFor('second responder restart', async () => (await fetch(summary.responderUrl + '/diaries/' + selected.diary_name + '/' + pageFilename)).ok);
  await responderReady(restartTime);
  const restarted = await snapshot('05-second-restart');
  assert.deepEqual(restarted, final);
  assert.equal(await (await fetch(summary.webUrl + webRoute)).text(), webBefore);
  write('web-after-health.json', await (await fetch(summary.webUrl + '/health/ready')).json());
  await page.goto(summary.clientUrl + selectedRoute);
  await page.getByRole('button', { name: 'List files', exact: true }).click();
  await waitFor('PNG thumbnail after restart', () => page.locator('img[alt="smoke-octet.png"]').evaluateAll(imgs => imgs.some(img => img.complete && img.naturalWidth > 0)));
  await page.screenshot({ path: path.join(evidence, 'client-post-restart-list.png'), fullPage: true });
  checks.push('Reconciliation reports missing/corrupt/generic/pre-existing files, reviewed apply and repeat apply are idempotent');
  checks.push('Two responder restarts reproduce database Images and retained state; chronology and all file hashes unchanged by guards/reconciliation/restarts');
  checks.push('Client and web MARQUEE behavior preserved; web HTML identical and client PNG preview works after restart');
  assert.deepEqual(manifest(source), sourceManifest);
  summary.counts = { beforeImages: initial.images.length, uploadedImages: protectedAfter.images.length, finalImages: final.images.length, finalImageTopics: imageTopics.length, beforeFiles: initial.files.length, afterFiles: final.files.length };
  summary.reconciliation = { dry: dry.counts, insertedRows: apply.insertedRows, repeatInsertedRows: repeat.insertedRows, post: post.counts };
  summary.status = 'PASSED';
}
main().catch(error => { summary.status = 'FAILED'; summary.failure = error.stack; process.exitCode = 1; console.error(error); }).finally(async () => {
  if (browser) await browser.close().catch(() => {});
  if (server) server.close();
  for (const client of connections) await client.endAsync(true).catch(() => {});
  for (const name of [responder, web, broker]) if (owned.includes(name)) {
    try {
      const logs = await run('docker', ['logs', name], { maxBuffer: 32 * 1024 * 1024 });
      // Keep operational evidence without copying authentication replies or uploaded bytes.
      const lines = (logs.stdout + logs.stderr).split('\n').filter(line =>
        /Connected, subscribing|synchronise:|sizeof\(|Sending status:|Listening on|Published replay generation|Subscribed to canonical|Connecting diaries-web|Javalin started|Outgoing messages are being dropped/.test(line));
      write(name.slice(prefix.length + 1) + '.log', lines.join('\n') + '\n');
    } catch { /* failure summary still records outcome */ }
  }
  const cleanupFailures = [];
  for (const name of owned.reverse()) { try { await docker('rm', '-f', name); } catch { cleanupFailures.push(name); } }
  if (networkCreated) { try { await docker('network', 'rm', prefix); } catch { cleanupFailures.push(prefix); } }
  summary.cleanupFailures = cleanupFailures;
  if (cleanupFailures.length) { summary.status = 'CLEANUP_FAILED'; process.exitCode = 1; }
  summary.finishedAtUtc = new Date().toISOString(); write('summary.json', summary);
  fs.writeFileSync(path.join(evidence, 'SHA256SUMS.txt'), manifest(evidence).map(file => file.sha256 + '  ' + file.path).join('\n') + '\n');
  console.log('Phase 10: ' + summary.status + '; evidence: ' + evidence);
});
