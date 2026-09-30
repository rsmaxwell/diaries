'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const http=require('node:http');
const {setPublishedPort,startMutableProxy}=require('./step13-proxy-routing.cjs');

function listen(body){
  const server=http.createServer((req,res)=>res.end(body+':'+req.url));
  return new Promise(resolve=>server.listen(0,'127.0.0.1',()=>resolve(server)));
}
function close(server){return new Promise(resolve=>server.close(resolve));}

test('reverse proxy follows new Docker host mapping after responder restart',async()=>{
  const old=await listen('old');const next=await listen('new');const web=await listen('web');
  const upstreamPorts={};
  let proxy;
  try{
    setPublishedPort(upstreamPorts,'responder',old.address().port);
    setPublishedPort(upstreamPorts,'web',web.address().port);
    proxy=await startMutableProxy(0,upstreamPorts);
    const root=`http://127.0.0.1:${proxy.address().port}`;
    assert.equal(await (await fetch(root+'/diaries-responder/files/a.png')).text(),'old:/files/a.png');
    assert.equal(await (await fetch(root+'/reader/a')).text(),'web:/reader/a');
    const newUrl=setPublishedPort(upstreamPorts,'responder',next.address().port);
    assert.equal(newUrl,`http://127.0.0.1:${next.address().port}`);
    await close(old);
    assert.equal(await (await fetch(root+'/diaries-responder/files/a.png')).text(),'new:/files/a.png');
    assert.equal((await fetch(root+'/unknown')).status,404);
  }finally{if(proxy)await close(proxy);await close(next);await close(web);}
});

test('reverse proxy follows new web published port after restart',async()=>{
  const oldWeb=await listen('web-old'),newWeb=await listen('web-new');
  const ports={};let proxy;
  try{
    setPublishedPort(ports,'web',oldWeb.address().port);
    proxy=await startMutableProxy(0,ports);
    const root=`http://127.0.0.1:${proxy.address().port}`;
    assert.equal(await (await fetch(root+'/reader/health/ready')).text(),'web-old:/reader/health/ready');
    setPublishedPort(ports,'web',newWeb.address().port);
    await close(oldWeb);
    assert.equal(await (await fetch(root+'/reader/health/ready')).text(),'web-new:/reader/health/ready');
  }finally{if(proxy)await close(proxy);await close(newWeb);}
});

test('published-port update rejects missing/malformed ports',()=>{
  const ports={};
  assert.throws(()=>setPublishedPort(ports,'responder',undefined));
  assert.throws(()=>setPublishedPort(ports,'responder',-1));
  assert.throws(()=>setPublishedPort(ports,'missing',8081));
});
