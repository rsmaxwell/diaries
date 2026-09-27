const fs = require('node:fs');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const {createRequire} = require('node:module');
const path = require('node:path');

const [root, out, phase, mqttPort, httpPort, container] = process.argv.slice(2);
const mqtt = createRequire(path.join(root, 'diaries-client/package.json'))('mqtt');
const client = mqtt.connect(`mqtt://127.0.0.1:${mqttPort}`, {protocolVersion: 5, reconnectPeriod: 0});
const pause = ms => new Promise(r => setTimeout(r, ms));
const reply = `fixture/step15/reply/${phase}/${process.pid}/${Date.now()}`;
const httpBase = `http://127.0.0.1:${httpPort}`;
let token;
let counter = 0;
const records = [];

function sql(query) {
  return execFileSync('docker', ['exec', container, 'psql', '-X', '-U', 'diaries', '-d', 'image_wiring_test', '-At', '-v', 'ON_ERROR_STOP=1', '-c', query], {encoding: 'utf8'}).trim();
}
function row(table, id) {
  assert(Number.isInteger(id));
  return JSON.parse(sql(`select to_jsonb(t) from ${table} t where id=${id}`));
}
async function rpc(fn, args = {}, expected = 200, timeout = 15000) {
  const correlation = String(++counter);
  return await new Promise((resolve, reject) => {
    let settled = false;
    const cleanup = () => { clearTimeout(timer); client.off('message', receive); };
    const fail = error => { if (settled) return; settled = true; cleanup(); reject(error); };
    const timer = setTimeout(() => fail(Error(`${fn} timeout after ${timeout}ms`)), timeout);
    function receive(topic, payload, packet) {
      if (topic !== reply || packet.properties?.correlationData?.toString() !== correlation) return;
      if (settled) return;
      settled = true; cleanup();
      try {
        const rawStatus = packet.properties?.userProperties?.status;
        if (!rawStatus) throw Error(`${fn}: response status user property missing`);
        const status = JSON.parse(Array.isArray(rawStatus) ? rawStatus[0] : rawStatus);
        const value = payload.length ? JSON.parse(payload.toString()) : null;
        records.push({function: fn, status: status.code, payload: fn === 'signin' ? {authenticated: status.code === 200} : value});
        console.log(`[rpc] <- ${fn} correlation=${correlation} status=${status.code}`);
        assert.equal(status.code, expected, `${fn}: ${JSON.stringify(status)}`);
        resolve(value);
      } catch (e) { reject(e); }
    }
    client.on('message', receive);
    const properties = {responseTopic: reply, correlationData: Buffer.from(correlation)};
    if (token) properties.userProperties = {accessToken: token};
    console.log(`[rpc] -> ${fn} correlation=${correlation}`);
    client.publish('diaries/rpc/request', JSON.stringify({function: fn, args}), {qos: 1, properties}, err => {
      if (err) return fail(Error(`${fn} publish failed: ${err.message}`));
      console.log(`[rpc] publish acknowledged ${fn} correlation=${correlation}`);
    });
  });
}
async function snapshot(topics) {
  const observer = mqtt.connect(`mqtt://127.0.0.1:${mqttPort}`, {protocolVersion: 5, reconnectPeriod: 0});
  const values = {};
  observer.on('message', (t, p) => { if (p.length) values[t] = JSON.parse(p.toString()); });
  await new Promise((r, j) => { observer.once('connect', r); observer.once('error', j); });
  await observer.subscribeAsync(topics, {qos: 1});
  await pause(700);
  observer.end(true);
  return values;
}
const fragmentTopic = id => `diaries/fragments/${id}`;
const alias = f => `diaries/dates/${f.year}/${f.month}/${f.day}/${f.id}`;
async function checkFragment(id) {
  const db = row('fragment', id);
  const values = await snapshot([fragmentTopic(id), alias(db)]);
  assert.equal(values[fragmentTopic(id)].imageId, db.image_id);
  assert.equal(values[fragmentTopic(id)].text, db.text);
  assert.deepEqual(values[fragmentTopic(id)], values[alias(db)]);
  return values;
}
async function update(id, extra = {}) {
  await rpc('lockFragment', {id});
  const f = row('fragment', id);
  await rpc('updateFragment', {id, version: f.version, year: f.year, month: f.month, day: f.day, sequence: f.sequence, text: f.text, ...extra});
  return row('fragment', id);
}
const file = {name: 'step15.png', subdir: 'step15/images'};
async function upload() {
  const bytes = fs.readFileSync(path.join(root, 'diaries-responder/src/test/resources/image-inspection/sample.png'));
  const result = await rpc('uploadFile', {...file, contentType: 'image/png', bytes: bytes.toString('base64'), size: bytes.length});
  assert(result.imageId > 0);
  const res = await fetch(`${httpBase}/files/step15/images/step15.png`);
  assert.equal(res.status, 200);
  assert.deepEqual(Buffer.from(await res.arrayBuffer()), bytes);
  return result.imageId;
}

(async () => {
  try {
    await new Promise((r, j) => { client.once('connect', r); client.once('error', j); });
    await client.subscribeAsync(reply, {qos: 1});
    console.log(`[phase] ${phase}: subscribed to ${reply}`);

    if (phase === 'corrupt') {
      const state = JSON.parse(fs.readFileSync(path.join(out, 'state.json')));
      await client.publishAsync(fragmentTopic(state.id), '', {qos: 1, retain: true});
      await client.publishAsync(alias(state.fragment), JSON.stringify({...state.fragment, text: 'stale fixture'}), {qos: 1, retain: true});
      records.push({removedCanonical: true, corruptedDateAlias: true});
      return;
    }

    console.log(`[phase] ${phase}: MQTT client connected; responder readiness was already verified by the Java health-check client`);
    const signed = await rpc('signin', {username: 'step15', password: 'Step15-only', sessionId: 'step15'}, 200, 10000);
    token = signed.accessToken;
    assert(token);
    await rpc('getVersion');

    const page = JSON.parse(sql('select to_jsonb(p) from page p order by id limit 1'));
    const base = {pageId: page.id, year: 2096, month: 1, day: 1, sequence: 1000, text: 'Step 15 controlled fixture'};

    if (phase === 'disabled') {
      const old = JSON.parse(sql('select to_jsonb(f) from fragment f order by id limit 1'));
      const reads = await snapshot([`diaries/pages/${page.id}`, fragmentTopic(old.id), alias(old)]);
      assert(reads[`diaries/pages/${page.id}`]);
      assert(reads[alias(old)]);
      assert(reads[fragmentTopic(old.id)]);
      fs.writeFileSync(path.join(out, 'existing-read-summary.json'), JSON.stringify({pageId: page.id, fragmentId: old.id, topics: Object.keys(reads), passed: true}, null, 2));

      await rpc('addImageFragment', base, 403);
      const f = await rpc('addFragment', {...base, x: 1, y: 2, width: 100, height: 100});
      assert.equal(f.type, 'MARQUEE');
      assert.equal(f.imageId, null);
      await update(f.id, {text: 'MARQUEE edited'});
      await checkFragment(f.id);
      const m = JSON.parse(sql(`select to_jsonb(m) from marquee m where fragment_id=${f.id}`));
      await rpc('lockFragment', {id: f.id});
      await rpc('updateMarquee', {id: m.id, version: m.version, pageId: page.id, fragmentId: f.id, x: 5, y: 6, width: 120, height: 130});
      assert.equal(row('marquee', m.id).x, 5);
      await rpc('deleteFragment', {id: f.id});
      assert.equal(sql(`select count(*) from fragment where id=${f.id}`), '0');
      assert.equal(sql(`select count(*) from marquee where id=${m.id}`), '0');

      const imageId = await upload();
      await rpc('listFiles', {subdir: file.subdir});
      await rpc('deleteFile', file, 409);
      await rpc('deleteImage', file);
      assert.equal(sql(`select count(*) from image where id=${imageId}`), '0');
      assert.equal((await fetch(`${httpBase}/files/step15/images/step15.png`)).status, 404);
      records.push({gateDisabledVerified: true, marqueeLifecycleVerified: true, uploadCatalogueVerified: true, deleteFileProtectionVerified: true, unreferencedDeleteImageVerified: true});
    } else if (phase === 'enabled') {
      const imageId = await upload();
      const f = await rpc('addImageFragment', {...base, imageId});
      assert.equal(f.type, 'IMAGE');
      assert.equal(f.marqueeId, null);
      await update(f.id, {text: 'IMAGE edited', day: 2, sequence: 2000});
      await update(f.id, {imageId: null});
      assert.equal(row('fragment', f.id).image_id, null);
      await update(f.id, {imageId});
      await rpc('normaliseFragments', {year: 2096, month: 1, day: 2});
      await rpc('deleteImage', file, 409);
      await rpc('deleteFile', file, 409);

      const fragment = row('fragment', f.id);
      const image = row('image', imageId);
      const marquees = Number(sql(`select count(*) from marquee where fragment_id=${f.id}`));
      assert.equal(marquees, 0);
      const retained = await checkFragment(f.id);
      Object.assign(retained, await snapshot([`diaries/images/${imageId}`]));
      assert.equal(retained[`diaries/images/${imageId}`].id, imageId);
      assert.deepEqual(await snapshot([alias(f)]), {}); // old date alias was tombstoned
      fs.writeFileSync(path.join(out, 'state.json'), JSON.stringify({id: f.id, imageId, fragment, image, marquees, retained}, null, 2));
      records.push({imageFragmentCreated: true, imageSelectionClearedAndReattached: true, noMarquee: true, retainedFragmentAndImageVerified: true, referencedDeleteImageConflictVerified: true, deleteFileProtectionVerified: true});
    } else if (phase === 'replay-delete') {
      const s = JSON.parse(fs.readFileSync(path.join(out, 'state.json')));
      const retained = await checkFragment(s.id);
      Object.assign(retained, await snapshot([`diaries/images/${s.imageId}`]));
      assert.deepEqual(retained, s.retained);
      fs.writeFileSync(path.join(out, 'replayed-retained.json'), JSON.stringify(retained, null, 2));

      await rpc('deleteImage', file, 409);
      await rpc('deleteFragment', {id: s.id});
      await rpc('deleteImage', file);
      assert.equal(sql(`select count(*) from fragment where id=${s.id}`), '0');
      assert.equal(sql(`select count(*) from image where id=${s.imageId}`), '0');
      assert.deepEqual(await snapshot([fragmentTopic(s.id), alias(s.fragment), `diaries/images/${s.imageId}`]), {});
      assert.equal((await fetch(`${httpBase}/files/step15/images/step15.png`)).status, 404);
      records.push({startupReplayVerified: true, referenceConflictRechecked: true, databaseRowsRemoved: true, retainedTombstonesVerified: true, physicalFileAbsent: true});
    } else {
      throw Error(`Unknown phase: ${phase}`);
    }
  } finally {
    fs.writeFileSync(path.join(out, `${phase}-rpc.json`), JSON.stringify(records, null, 2));
    try { client.end(true); } catch {}
  }
})().catch(e => { console.error(e && e.stack ? e.stack : e); process.exitCode = 1; });
