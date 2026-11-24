'use strict';
// An isolated MQTT WebSocket framing bridge, not an MQTT broker.
// It forwards raw MQTT binary packets to the already running rehearsal broker.
const http = require('node:http');
const net = require('node:net');
const { WebSocket, WebSocketServer } = require('ws');
const HOST = 'diaries-0028-replay-broker';
const PORT = 1883;
const MAX_CONNECTIONS = 12;
let connections = 0;
const server = http.createServer((_req, res) => {
  res.writeHead(404, { 'Content-Type': 'text/plain', 'Cache-Control': 'no-store' });
  res.end('Not found\n');
});
const sockets = new WebSocketServer({
  noServer: true,
  perMessageDeflate: false,
  maxPayload: 16 * 1024 * 1024,
  handleProtocols: (protocols) => protocols.has('mqtt') ? 'mqtt' : false
});
server.on('upgrade', (req, socket, head) => {
  const path = (req.url || '').split('?')[0];
  const offered = (req.headers['sec-websocket-protocol'] || '').split(',').map(x => x.trim());
  if (path !== '/mosquitto/' || !offered.includes('mqtt') || connections >= MAX_CONNECTIONS) {
    socket.write('HTTP/1.1 403 Forbidden\r\nConnection: close\r\nContent-Length: 0\r\n\r\n');
    socket.destroy();
    return;
  }
  sockets.handleUpgrade(req, socket, head, ws => sockets.emit('connection', ws, req));
});
sockets.on('connection', ws => {
  connections += 1;
  const tcp = net.createConnection({ host: HOST, port: PORT });
  let closed = false;
  function closeBoth() {
    if (closed) return;
    closed = true;
    connections -= 1;
    tcp.destroy();
    if (ws.readyState === WebSocket.OPEN) ws.close();
    else if (ws.readyState !== WebSocket.CLOSED) ws.terminate();
  }
  ws.on('message', (message, isBinary) => {
    if (!isBinary || closed) { closeBoth(); return; }
    // Pause WebSocket reads when the TCP broker cannot consume quickly enough.
    if (!tcp.write(message)) {
      ws._socket?.pause();
    }
  });
  tcp.on('drain', () => ws._socket?.resume());
  tcp.on('data', chunk => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(chunk, { binary: true }, err => { if (err) closeBoth(); });
    }
  });
  tcp.on('error', closeBoth);
  tcp.on('end', closeBoth);
  tcp.on('close', closeBoth);
  ws.on('error', closeBoth);
  ws.on('close', closeBoth);
});
server.listen(9001, '0.0.0.0', () => console.log('0028 isolated MQTT WebSocket framing bridge ready on 9001'));
