const fs = require('node:fs');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const bundle = fs.readFileSync(process.argv[2], 'utf8');
const fixture = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
assert.equal(fixture.type, 'MARQUEE');
assert.equal(fixture.imageId, null);
const regions = [
 ['canonical', bundle.match(/getLiveFragment\$\([a-zA-Z_$]+\)\{.*?(?=getLivePage\$)/s)?.[0]],
 ['date alias', bundle.match(/this\.fragments\$=this\.selectedFragment\$.*?(?=this\.selectFragmentsForDate\$)/s)?.[0]]
];
for (const [label, region] of regions) {
 assert.ok(region, `${label} decoder region missing`);
 const callback = region.match(/[a-zA-Z_$]+=>JSON\.parse\([a-zA-Z_$]+\.toString\(\)\)/)?.[0];
 assert.ok(callback, `${label} JSON decoder missing`);
 // Evaluate only the extracted JSON.parse callback, not application startup code.
 const decode = Function(`return (${callback})`)();
 const withNull = decode(Buffer.from(JSON.stringify(fixture)));
 const legacy = {...fixture}; delete legacy.imageId;
 assert.deepEqual(withNull, fixture);
 assert.deepEqual(decode(Buffer.from(JSON.stringify(legacy))), legacy);
 delete withNull.imageId; assert.deepEqual(withNull, legacy);
 console.log(`PASS: deployed client ${label} decoder tolerates imageId:null; callback=${callback}`);
}
console.log('bundle SHA256=' + crypto.createHash('sha256').update(bundle).digest('hex'));
