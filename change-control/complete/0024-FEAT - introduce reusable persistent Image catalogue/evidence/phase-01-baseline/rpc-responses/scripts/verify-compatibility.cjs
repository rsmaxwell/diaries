'use strict';
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

// Existing values, types and collection order are stable. Object additions are allowed.
function containsBaseline(expected, actual, location = 'reply') {
  if (Array.isArray(expected)) {
    assert.ok(Array.isArray(actual), `${location}: expected array`);
    assert.equal(actual.length, expected.length, `${location}: array length`);
    expected.forEach((value, index) => containsBaseline(value, actual[index], `${location}[${index}]`));
  } else if (expected !== null && typeof expected === 'object') {
    assert.ok(actual !== null && typeof actual === 'object' && !Array.isArray(actual), `${location}: expected object`);
    for (const key of Object.keys(expected)) {
      assert.ok(Object.hasOwn(actual, key), `${location}.${key}: missing existing field`);
      containsBaseline(expected[key], actual[key], `${location}.${key}`);
    }
  } else {
    assert.equal(actual, expected, `${location}: existing value/type changed`);
  }
}
function checkOmissions(reply) {
  if (reply.function !== 'listFiles' || reply.status.code !== 200) return;
  for (const item of reply.payload.items) {
    if (item.dir) assert.ok(!Object.hasOwn(item, 'url'), 'directory url must remain omitted');
    if (item.dir || item.name.endsWith('.png')) {
      assert.ok(!Object.hasOwn(item, 'dateTaken'), 'absent dateTaken must remain omitted, not null');
    }
  }
}
function selfTest() {
  const original = { name: 'test.png', size: 68, items: [{ dir: false }] };
  containsBaseline(original, { ...original, imageId: 7, items: [{ dir: false, image: { id: 7 } }] });
  assert.throws(() => containsBaseline(original, { size: 68, items: original.items }));
  assert.throws(() => containsBaseline(original, { ...original, size: '68' }));
  assert.throws(() => containsBaseline(original, { ...original, name: null }));
  assert.throws(() => containsBaseline(original, { ...original, items: [] }));
  assert.throws(() => containsBaseline({ items: [1, 2] }, { items: [2, 1] }));
  assert.throws(() => checkOmissions({ function: 'listFiles', status: { code: 200 }, payload: { items: [{ dir: true, url: null }] } }));
}
function verifyCapture(directory) {
  const cases = JSON.parse(fs.readFileSync(path.join(directory, 'cases.json'), 'utf8'));
  assert.equal(cases.length, 33, 'complete baseline case count');
  assert.equal(new Set(cases.map(c => c.caseId)).size, cases.length, 'unique case IDs');
  const root = JSON.parse(fs.readFileSync(path.join(directory, 'environment.json'), 'utf8')).filesRoot;
  const normalize = text => text.replaceAll(JSON.stringify(root).slice(1, -1), '<FILES_ROOT>');
  for (const entry of cases) {
    const raw = JSON.parse(fs.readFileSync(path.join(directory, 'raw', entry.caseId + '.json'), 'utf8'));
    const normalized = JSON.parse(fs.readFileSync(path.join(directory, 'normalized', entry.caseId + '.json'), 'utf8'));
    assert.deepEqual(normalized, entry);
    assert.equal(Buffer.from(raw.payloadBase64, 'base64').toString('utf8'), raw.payloadUtf8);
    assert.equal(raw.responseTopic, 'diaries/rpc/0024-baseline/response');
    assert.equal(raw.responseProperties.correlationData, raw.correlationDataBase64);
    const statuses = raw.responseUserProperties.filter(p => p.key === 'status');
    assert.equal(statuses.length, 1);
    assert.deepEqual(JSON.parse(statuses[0].value), entry.status);
    assert.equal(raw.responseQos, 1); assert.equal(raw.responseRetain, false);
    assert.deepEqual(JSON.parse(normalize(raw.payloadUtf8)), entry.payload);
    assert.ok(!raw.responseUserProperties.some(p => p.key === 'accessToken'));
    checkOmissions(entry);
  }
  const byId = Object.fromEntries(cases.map(c => [c.caseId, c]));
  const items = byId['list-populated-root'].payload.items;
  assert.deepEqual(items.map(i => i.name), ['alpha', 'empty', 'zeta', 'dated.jpg', 'plain.png']);
  assert.equal(items[3].dateTaken, 1577934245000);
  assert.equal(items[3].mtime, 1704164646000);
  assert.equal(byId['list-populated-nested'].payload.items[0].url, '/files/alpha/nested%20space/image%20space.png');
  assert.deepEqual(byId['delete-generic-existing'].payload, byId['delete-generic-missing'].payload);
  assert.equal(byId['upload-duplicate'].status.code, 409);
  for (const op of ['upload', 'list', 'delete']) {
    assert.equal(byId[`${op}-auth-missing`].status.code, 401);
    assert.equal(byId[`${op}-auth-reader`].status.code, 401);
    assert.equal(byId[`${op}-auth-invalid`].status.code, 500); // Observation, not a desired future API rule.
  }
  return cases;
}
if (require.main === module) {
  const baseline = process.argv[2];
  if (!baseline) throw new Error('Usage: node verify-compatibility.cjs <capture-directory> [candidate-cases.json]');
  selfTest();
  const expected = verifyCapture(baseline);
  const actual = process.argv[3] ? JSON.parse(fs.readFileSync(process.argv[3], 'utf8')) : expected;
  assert.equal(actual.length, expected.length, 'candidate case count');
  assert.equal(new Set(actual.map(c => c.caseId)).size, actual.length, 'candidate IDs unique');
  for (const row of expected) {
    const candidate = actual.find(c => c.caseId === row.caseId);
    assert.ok(candidate, `missing case ${row.caseId}`);
    containsBaseline(row, candidate, row.caseId); checkOmissions(candidate);
  }
  console.log(`PASS: ${expected.length} captured cases; raw/normalized integrity, wire metadata, listing semantics, omitted fields and additive comparison; 7 comparator self-checks.`);
}
module.exports = { containsBaseline, checkOmissions, verifyCapture };
