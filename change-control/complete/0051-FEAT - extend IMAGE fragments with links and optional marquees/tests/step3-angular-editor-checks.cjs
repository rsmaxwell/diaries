/* 0051 Step 3: signed-in Angular editor browser acceptance in disposable fixture. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');

const mime = new Map([
  ['.html','text/html; charset=utf-8'], ['.js','text/javascript; charset=utf-8'],
  ['.css','text/css; charset=utf-8'], ['.json','application/json; charset=utf-8'],
  ['.svg','image/svg+xml'], ['.png','image/png'], ['.jpg','image/jpeg'],
  ['.jpeg','image/jpeg'], ['.ico','image/x-icon'], ['.woff','font/woff'],
  ['.woff2','font/woff2'], ['.txt','text/plain; charset=utf-8']
]);

// HTTPS content is never fetched. Test only the resulting href attributes.
const IMAGE_URL = 'https://example.org/0051/editor-photo.png?part=1%2F2#selection';
const unsafeUrl = 'javascript:alert(1)';

function createEditorServer(staticDir, mqttWsPort, responderPort) {
  const root = path.resolve(staticDir);
  const config = {
    brokerMode:'direct', brokerDirectUrl:`ws://127.0.0.1:${mqttWsPort}`,
    responderBaseUrlMode:'same-origin', username:'diaries-client',
    password:'step13-fixture', diaries:'diaries', files:'files',
    clientId:'step3-editor', keepalive:60, reconnectPeriod:1000,
    connectTimeout:30000, protocolVersion:5, clean:false,
    fragmentLockTtlSeconds:900
  };
  const server=http.createServer((req,res)=>{
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      res.writeHead(405); res.end(); return;
    }
    let url;
    try { url = new URL(req.url, 'http://127.0.0.1'); }
    catch { res.writeHead(400); res.end(); return; }
    if(url.pathname === '/assets/config.json'){
      res.writeHead(200,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});
      res.end(JSON.stringify(config));return;
    }
    if(url.pathname === '/diaries-responder' || url.pathname.startsWith('/diaries-responder/')){
      const upstream=responderPort();
      if(!Number.isInteger(upstream)){res.writeHead(503);res.end('responder unavailable');return;}
      const upstreamPath=url.pathname.slice('/diaries-responder'.length)||'/';
      const p=http.request({hostname:'127.0.0.1',port:upstream,
        path:upstreamPath+url.search,method:req.method,
        headers:{...req.headers,host:`127.0.0.1:${upstream}`}},reply=>{
          res.writeHead(reply.statusCode,reply.headers);reply.pipe(res);
        });
      p.on('error',err=>{if(!res.headersSent){res.writeHead(502);res.end(err.message);}else res.destroy(err);});
      p.end();return;
    }
    let decoded;
    try { decoded=decodeURIComponent(url.pathname); }
    catch {res.writeHead(400);res.end();return;}
    if(decoded.includes('\\') || decoded.includes('\0') || decoded.split('/').includes('..')){
      res.writeHead(403);res.end();return;
    }
    const candidate=path.resolve(root, '.'+decoded);
    if(candidate!==root && !candidate.startsWith(root+path.sep)){
      res.writeHead(403);res.end();return;
    }
    let file=candidate;
    let stat;
    try {stat=fs.statSync(file);}catch{}
    if(stat?.isDirectory()){file=path.join(file,'index.html');stat=fs.existsSync(file)?fs.statSync(file):undefined;}
    // Angular deep links are handled by the client router. Don't rewrite
    // missing static assets (which should instead give 404).
    if(!stat?.isFile() && !path.extname(decoded)) {
      file=path.join(root,'index.html');stat=fs.existsSync(file)?fs.statSync(file):undefined;
    }
    if(!stat?.isFile()){res.writeHead(404);res.end('not found');return;}
    res.writeHead(200,{'Content-Type':mime.get(path.extname(file).toLowerCase())||'application/octet-stream',
      'Cache-Control':'no-store','Content-Length':stat.size});
    if(req.method==='HEAD'){res.end();return;}
    fs.createReadStream(file).pipe(res);
  });
  return new Promise((resolve,reject)=>{
    server.once('error',reject);
    server.listen(0,'127.0.0.1',()=>{
      server.removeListener('error',reject);
      resolve({server,origin:`http://127.0.0.1:${server.address().port}`});
    });
  });
}

async function runAngularEditorChecks({browser,root,evidence,summary,checks,first,selectedFrag,selectedImage,
  mqttWsPort,responderPort,rows,write}) {
  const dist=path.join(root,'diaries-client','dist','diaries-client','browser');
  assert(fs.existsSync(path.join(dist,'index.html')),
    'Angular development build missing. Run verify-step3-angular-editor.ps1');
  const {server,origin}=await createEditorServer(dist,mqttWsPort,responderPort);
  let context=null, mobile=null;
  const browserErrors=[];
  const diaryId=Number(first.diary_id), pageId=Number(first.page_id), fragmentId=Number(selectedFrag.id);
  const imageId=Number(selectedImage.imageId);
  const target=`/diary/${diaryId}/${pageId}/${fragmentId}`;
  summary.angularEditorOrigin=origin;
  summary.editorFixture={diaryId,pageId,fragmentId,imageId};
  const current=async()=>{
    const fragment=await rows(`SELECT id,type,image_id AS "imageId",image_link_url AS "imageLinkUrl",page_id AS "pageId" FROM fragment WHERE id=${fragmentId}`);
    assert.equal(fragment.length,1,'Exactly one editor IMAGE Fragment expected');
    return fragment[0];
  };
  const marqueeRows=()=>rows(`SELECT id,fragment_id AS "fragmentId",page_id AS "pageId",x,y,width,height FROM marquee WHERE fragment_id=${fragmentId}`);
  const wait=async(label,predicate,timeout=25000)=>{
    const end=Date.now()+timeout;let last;
    while(Date.now()<end){try{const v=await predicate();if(v)return v;}catch(e){last=e;}
      await new Promise(resolve=>setTimeout(resolve,250));}
    throw Error(`${label} not reached${last?': '+last.message:''}`);
  };
  const signIn=async(page)=>{
    await page.goto(origin+'/signin?returnUrl='+encodeURIComponent(target),{waitUntil:'domcontentloaded'});
    await page.locator('input[name="username"]').fill('step13-smoke');
    await page.locator('input[name="password"]').fill('step13-fixture');
    await page.getByRole('button',{name:'Sign in',exact:true}).click();
    await page.locator(`app-image-fragment-reference .identity`).getByText(`IMAGE Fragment ${fragmentId}`).waitFor({timeout:45000});
    assert(new URL(page.url()).pathname.includes(target),'Sign-in did not return to selected IMAGE Fragment');
  };
  try {
    context=await browser.newContext({viewport:{width:1440,height:960},acceptDownloads:false});
    const page=await context.newPage(); page.setDefaultTimeout(30000);
    page.on('pageerror',error=>browserErrors.push(`desktop: ${error.message}`));
    await signIn(page);
    checks.push('Browser signs in through real MQTT-RPC and opens the selected IMAGE Fragment in the Angular editor');
    const editor=page.locator('app-image-fragment-reference');
    const input=editor.locator('#image-fragment-link-url');
    const save=editor.getByRole('button',{name:'Save link'});
    const clear=editor.getByRole('button',{name:'Clear link'});
    assert.equal(await clear.isDisabled(),true,'Clear must be disabled when no URL exists');
    await input.fill(unsafeUrl);
    assert.equal(await save.isDisabled(),true,'Unsafe javascript URL must not be savable');
    await input.fill(IMAGE_URL);
    assert.equal(await save.isEnabled(),true,'Save link should enable for valid, changed URL');
    await save.click();
    await wait('link persisted',async()=>(await current()).imageLinkUrl===IMAGE_URL);
    await wait('safe image anchor',async()=>await editor.locator('a[aria-label^="Open linked Image"]').count()===1);
    assert.equal(await editor.locator('a[aria-label^="Open linked Image"]').getAttribute('href'),IMAGE_URL);
    assert.equal((await current()).imageId,imageId);
    checks.push('IMAGE URL Save rejects unsafe input, persists safe URL and displays the external image anchor without opening it');
    await page.screenshot({path:path.join(evidence,'editor-link-only-desktop.png'),fullPage:true});

    const create=page.getByRole('button',{name:'Add marquee to selected fragment'});
    await wait('create marquee button enabled',async()=>await create.isEnabled());
    await create.click();
    const attached=await wait('Marquee attached',async()=>{
      const list=await marqueeRows();return list.length===1?list[0]:null;
    },30000);
    assert.equal(attached.pageId,pageId); assert.equal(attached.fragmentId,fragmentId);
    assert.equal((await current()).type,'IMAGE');
    assert.equal((await current()).imageLinkUrl,IMAGE_URL,'URL must survive Marquee creation');
    await wait('source highlighting enabled',async()=>
      await page.getByRole('button',{name:'Fit selection'}).isEnabled());
    const show=editor.getByRole('button',{name:/Show on source page/});
    assert.match(await show.textContent(),/highlight selection/);
    await show.click();
    assert.equal((await current()).pageId,pageId,'Source navigation must not mutate page ownership');
    checks.push('Angular Marquee attach preserves IMAGE identity, URL and Page; Show on source page highlights instead of following external link');
    await page.screenshot({path:path.join(evidence,'editor-image-with-marquee-desktop.png'),fullPage:true});

    const edit=page.getByRole('button',{name:'Move or resize selected marquee'});
    await wait('edit marquee button enabled',async()=>await edit.isEnabled());
    await edit.click();
    assert.equal(await edit.getAttribute('aria-pressed'),'true');
    const shape=page.locator('app-image-viewer rect.selected-outline');
    await shape.waitFor();
    const bounding=await shape.boundingBox();
    assert(bounding && bounding.width>30 && bounding.height>30,'Selected Marquee not visible in source viewer');
    const x=bounding.x+bounding.width*.5,y=bounding.y+bounding.height*.5;
    await page.mouse.move(x,y); await page.mouse.down();
    await page.mouse.move(x+24,y+18,{steps:12}); await page.mouse.up();
    await wait('Marquee geometry changed by pointer drag',async()=>{
      const list=await marqueeRows();
      return list.length===1 && (Math.abs(list[0].x-attached.x)>1 || Math.abs(list[0].y-attached.y)>1) ? list[0]:null;
    },30000);
    assert.equal((await current()).imageLinkUrl,IMAGE_URL,'URL must survive geometry edit');
    checks.push('Angular move/resize Marquee interaction persists geometry through MQTT-RPC');
    await page.screenshot({path:path.join(evidence,'editor-marquee-edited-desktop.png'),fullPage:true});

    const tabs=page.locator('.lm_tab').filter({hasText:'Day reader'});
    await wait('Day reader tab',async()=>await tabs.count()>0);
    await tabs.first().click();
    const selectedDayItem=page.locator(`.day-reader .fragment-item[data-fragment-id="${fragmentId}"]`);
    await wait('Image ID label',async()=>await selectedDayItem
      .getByText(`Image ID: ${imageId}`,{exact:true}).count()>0);
    const dayMetadata=await selectedDayItem.locator('.fragment-metadata').innerText();
    assert(dayMetadata.indexOf('Position ')>=0 &&
      dayMetadata.indexOf(`Image ID: ${imageId}`)>dayMetadata.indexOf('Position '),
      'Day reader Image ID must follow Position');
    checks.push('Day reader shows Image ID directly after Position for selected IMAGE Fragment');
    await page.screenshot({path:path.join(evidence,'editor-day-reader-desktop.png'),fullPage:true});

    mobile=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
    const phone=await mobile.newPage();phone.setDefaultTimeout(30000);
    phone.on('pageerror',error=>browserErrors.push(`mobile: ${error.message}`));
    await signIn(phone);
    assert.equal(await phone.locator('#image-fragment-link-url').count(),1);
    await phone.screenshot({path:path.join(evidence,'editor-image-marquee-mobile.png'),fullPage:true});
    checks.push('Mobile signed-in Angular editor renders IMAGE link and selected source without blocking navigation');
    await mobile.close();mobile=null;

    const remove=page.getByRole('button',{name:'Delete marquee from selected fragment'});
    await wait('Delete Marquee enabled',async()=>await remove.isEnabled());
    await remove.click();
    await wait('Marquee removed',async()=>(await marqueeRows()).length===0);
    assert.equal((await current()).imageLinkUrl,IMAGE_URL,'Link must survive Marquee removal');
    await clear.click();
    await wait('URL cleared',async()=>(await current()).imageLinkUrl===null);
    await wait('external anchor removed',async()=>await editor.locator('a[aria-label^="Open linked Image"]').count()===0);
    const final=await current();
    assert.equal(final.type,'IMAGE'); assert.equal(final.imageId,imageId);
    checks.push('Angular Marquee deletion and link clear preserve IMAGE identity and catalogue reference');
    await page.screenshot({path:path.join(evidence,'editor-cleared-desktop.png'),fullPage:true});
    write('editor-browser-errors.json',browserErrors);
    assert.deepEqual(browserErrors,[],'Uncaught browser application exceptions');
    write('angular-editor-acceptance.json',{status:'PASSED',fixture:{diaryId,pageId,fragmentId,imageId},
      checks:checks.filter(x=>x.startsWith('Angular')||x.startsWith('Browser signs')||x.startsWith('IMAGE URL')||x.startsWith('Day reader')||x.startsWith('Mobile signed')),screenshots:6});
  } finally {
    if(mobile) await mobile.close().catch(()=>{});
    if(context) await context.close().catch(()=>{});
    await new Promise(resolve=>server.close(resolve));
    write('editor-browser-errors.json',browserErrors);
  }
}
module.exports={runAngularEditorChecks};
