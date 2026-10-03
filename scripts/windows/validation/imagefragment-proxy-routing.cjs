/* Dynamic public routes for disposable containers with ephemeral published ports. */
'use strict';
const assert = require('node:assert/strict');
const http = require('node:http');

function setPublishedPort(upstreamPorts, service, port) {
  assert(['responder','web'].includes(service), 'Unknown ImageFragment reader upstream');
  assert(Number.isInteger(port) && port>=1 && port<=65535, 'Invalid published Docker port');
  upstreamPorts[service]=port;
  return `http://127.0.0.1:${port}`;
}

function startMutableProxy(port, upstreamPorts) {
  const server=http.createServer((req,res)=>{
    // Read the current value on EVERY request: Docker Desktop may reallocate a
    // '-p 127.0.0.1::PORT' host port after 'docker restart'.
    const target=req.url.startsWith('/reader')?
      {port:upstreamPorts.web,path:req.url}:
      req.url.startsWith('/diaries-responder')?
      {port:upstreamPorts.responder,path:req.url.slice('/diaries-responder'.length)||'/'}:null;
    if(!target){res.statusCode=404;return res.end('not found');}
    if(!Number.isInteger(target.port)){
      res.statusCode=503;return res.end('upstream not ready');
    }
    const proxy=http.request({host:'127.0.0.1',port:target.port,method:req.method,
      path:target.path,headers:{...req.headers,host:`127.0.0.1:${target.port}`}},upstream=>{
      res.writeHead(upstream.statusCode,upstream.headers);upstream.pipe(res);
    });
    proxy.on('error',error=>{
      if(res.headersSent){res.destroy(error);return;}
      res.statusCode=502;res.end(error.message);
    });
    req.pipe(proxy);
  });
  return new Promise((resolve,reject)=>{
    server.once('error',reject);
    server.listen(port,'127.0.0.1',()=>{server.removeListener('error',reject);resolve(server);});
  });
}
module.exports={setPublishedPort,startMutableProxy};
