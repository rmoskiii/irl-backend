'use strict';
const fs = require('fs');
const path = require('path');
const { parse, findById, findAll, outerXml } = require('./xml');
const { MissingAsset, MissingLayerGroup } = require('./errors');

/** Loads and parses the 45 source SVGs once at boot. 388 KB total - there is no
 *  reason to touch disk per request. Everything downstream reads from here. */
class AssetStore {
    constructor(assetsDir) {
        this.dir = assetsDir;
        this.cache = new Map();
        this.count = 0;
    }
    loadAll() {
        for (const sub of ['characters', 'environments', 'props', 'vignettes']) {
            const d = path.join(this.dir, sub);
            if (!fs.existsSync(d)) continue;
            for (const f of fs.readdirSync(d)) {
                if (f.endsWith('.svg')) { this.get(`${sub}/${f}`); this.count++; }
            }
        }
        return this;
    }
    get(rel) {
        if (this.cache.has(rel)) return this.cache.get(rel);
        const p = path.join(this.dir, rel);
        if (!fs.existsSync(p)) throw new MissingAsset(rel);
        const src = fs.readFileSync(p, 'utf8');
        const root = parse(src);
        const entry = {
            rel, src, root,
            styles: findAll(root, 'style').map(s => s.src.slice(s._openEnd, s.end - '</style>'.length)),
            defs: findAll(root, 'defs').flatMap(d => d.children.filter(c => c.tag !== 'style')),
            attrs: (findAll(root, 'svg')[0] || { attrs: {} }).attrs,
        };
        this.cache.set(rel, entry);
        return entry;
    }
    /** Verbatim source of a named layer group - the same subtree lift the Python
     *  composer does with ElementTree, without a re-serialisation round trip. */
    group(rel, id) {
        const a = this.get(rel);
        const g = findById(a.root, 'g', id);
        if (!g) throw new MissingLayerGroup(rel, id);
        return outerXml(g);
    }
}
module.exports = { AssetStore };