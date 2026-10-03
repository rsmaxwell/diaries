/* Fixture-only catalogue Image byte preflight, independent of the browser. */
'use strict';
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const sha256 = bytes => crypto.createHash('sha256').update(bytes).digest('hex');

function cataloguePublicPath(relativePath) {
  assert.equal(typeof relativePath, 'string', 'Uploaded Image must have a relativePath');
  const segments = relativePath.split('/');
  assert(segments.every(segment => segment && segment !== '.' && segment !== '..' &&
    !segment.includes('\\') && !segment.includes(':')),
  'Uploaded Image relativePath must contain canonical, non-empty path segments');
  return '/diaries-responder/files/' + segments.map(encodeURIComponent).join('/');
}

/**
 * Evidence is returned even when an HTTP endpoint is unavailable or returns
 * incorrect bytes. The caller writes it before asserting, so failures remain
 * actionable after the disposable containers have been removed.
 */
async function inspectImageBytes({label, relativePath, expectedBytes, containerSha256,
  containerError, publicOrigin, responderDirectUrl, fetchImpl = fetch}) {
  const expectedSha256 = sha256(expectedBytes);
  const publicPath = cataloguePublicPath(relativePath);
  const directUrl = new URL(publicPath.slice('/diaries-responder'.length), responderDirectUrl).href;
  const publicUrl = new URL(publicPath, publicOrigin).href;
  const result = { label, relativePath, publicPath, expectedSha256,
    containerSha256: containerSha256 || null,
    containerError: containerError || null };
  for (const [name, url] of [['direct', directUrl], ['public', publicUrl]]) {
    try {
      const response = await fetchImpl(url);
      const bytes = Buffer.from(await response.arrayBuffer());
      result[name] = {url, status: response.status, contentType: response.headers.get('content-type'),
        sha256: response.ok ? sha256(bytes) : null,
        errorBody: response.ok ? null : bytes.toString('utf8').slice(0, 400)};
    } catch (error) {
      result[name] = {url, error: String(error && (error.cause?.message || error.message || error))};
    }
  }
  result.ok = result.containerSha256 === expectedSha256 &&
    result.direct?.status === 200 && result.direct.sha256 === expectedSha256 &&
    result.public?.status === 200 && result.public.sha256 === expectedSha256;
  return result;
}
module.exports = {cataloguePublicPath, inspectImageBytes};
