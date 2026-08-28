'use strict';
/** Throwaway route-layer stand-in so the port is curl-able before any Flutter
 *  work. Not part of the port - delete once wired into the real Express app. */
const http = require('http');
const fs = require('fs');
const { RenderService, errors } = require('./src/services/renderService');

const V = process.env.IRX_VISUAL || '/home/claude/irx/irx_handoff/tools/visual';
const svc = new RenderService({ assetsDir: `${V}/assets`, registriesPath: `${V}/registries.json` });
const blocks = JSON.parse(fs.readFileSync(`${V}/render_blocks.json`, 'utf8'));

http.createServer((req, res) => {
    const [, nodeId, variant = 'default'] = req.url.split('/').filter(Boolean).length
        ? ['', ...req.url.replace(/^\/node\//, '').split('/')] : ['', '', ''];
    const block = (blocks[nodeId] || {})[variant];
    const send = (code, body) => {
        res.writeHead(code, { 'content-type': 'application/json' });
        res.end(JSON.stringify(body, null, 2));
    };
    if (!block) return send(404, { error: 'no render block', nodeId, variant });
    try {
        send(200, svc.attachTo({ nodeId, prose: '(prose omitted)', choices: [] }, block));
    } catch (e) {
        if (e instanceof errors.MaxPerNodeExceeded)
            return send(422, { error: e.code, message: e.message, nodeId });
        send(500, { error: 'RENDER_FAILED', message: e.message });
    }
}).listen(8731, () => console.log('render demo on :8731'));