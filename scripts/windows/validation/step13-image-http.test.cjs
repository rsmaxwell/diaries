'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const {cataloguePublicPath, inspectImageBytes} = require('./step13-image-http.cjs');
const sha256 = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const fixtureBytes = Buffer.from('owned fixture-only image bytes');
const base = {
  label: 'synthetic selected Image', relativePath: 'step13/maps/nested/selected image ü.png',
  expectedBytes: fixtureBytes, containerSha256: sha256(fixtureBytes),
  publicOrigin: 'http://127.0.0.1:12345', responderDirectUrl: 'http://127.0.0.1:23456'
};
test('encodes each Unicode path segment without encoding the path separators', () => {
  assert.equal(cataloguePublicPath(base.relativePath),
    '/diaries-responder/files/step13/maps/nested/selected%20image%20%C3%BC.png');
  for (const invalid of ['', 'a//b', '../x', 'a\\b', 'C:/x']) {
    assert.throws(() => cataloguePublicPath(invalid));
  }
});
test('successful byte preflight checks container, responder and public proxy hashes', async () => {
  const calls = [];
  const result = await inspectImageBytes({...base, fetchImpl: async url => {
    calls.push(url);
    return new Response(fixtureBytes, {status:200, headers:{'content-type':'image/png'}});
  }});
  assert.equal(result.ok, true);
  assert.equal(calls.length,2);
  assert.equal(new URL(calls[0]).pathname,'/files/step13/maps/nested/selected%20image%20%C3%BC.png');
  assert.equal(new URL(calls[1]).pathname,'/diaries-responder/files/step13/maps/nested/selected%20image%20%C3%BC.png');
});
test('preflight retains HTTP status/body when public prefix returns 404', async () => {
  const result = await inspectImageBytes({...base, fetchImpl: async url =>
    new Response(url.includes('/diaries-responder/') ? 'not found' : fixtureBytes,
      {status: url.includes('/diaries-responder/') ? 404 : 200})});
  assert.equal(result.ok,false);
  assert.equal(result.direct.sha256,sha256(fixtureBytes));
  assert.equal(result.public.status,404);
  assert.equal(result.public.errorBody,'not found');
});
test('preflight retains mismatched bytes, missing container and network errors', async () => {
  const result = await inspectImageBytes({...base, containerSha256:null,
    containerError:'missing file', fetchImpl: async url => {
      if (url.includes('/diaries-responder/')) throw Error('connection reset');
      return new Response('wrong image', {status:200});
    }});
  assert.equal(result.ok,false);
  assert.equal(result.containerError,'missing file');
  assert.notEqual(result.direct.sha256,result.expectedSha256);
  assert.match(result.public.error,/connection reset/);
});
