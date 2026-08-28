'use strict';
const { parse } = require('../../src/services/render/xml');

/** Same canonical form the Python fixture generator uses: sorted attributes,
 *  collapsed whitespace, tree structure only. Byte equality is deliberately NOT
 *  the test - attribute ordering and serialisation differences are irrelevant
 *  and would produce false failures. */
/** Root provenance attributes are audit metadata, not composition: the 2B
 *  frames carry `id`/`data-frame`/`data-render-block` naming the hand-authored
 *  declaration they came from, and the runtime has no declarations. Parity is
 *  asserted on the composition; provenance is asserted separately. */
const PROVENANCE = new Set(['id', 'data-frame', 'data-render-block', 'data-render-key']);

function canonicalSvg(text, { ignoreProvenance = false } = {}) {
    const root = parse(text);
    const svg = root.children.find(c => c.tag === 'svg');
    const n = norm(svg);
    if (ignoreProvenance) for (const k of PROVENANCE) delete n.attrs[k];
    return stable(n);
}

/** json.dumps(sort_keys=True, separators=(',',':')) with ASCII escaping. */
function stable(v) {
    if (v === null || typeof v !== 'object') return esc(JSON.stringify(v));
    if (Array.isArray(v)) return `[${v.map(stable).join(',')}]`;
    return `{${Object.keys(v).sort().map(k => `${esc(JSON.stringify(k))}:${stable(v[k])}`).join(',')}}`;
}
function esc(s) {
    return s.replace(/[\u0080-\uFFFF]/g, c => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0'));
}
function norm(el) {
    const attrs = {};
    for (const k of Object.keys(el.attrs).sort()) {
        if (k === 'xmlns') continue;
        attrs[k] = String(el.attrs[k]).replace(/\s+/g, ' ').trim();
    }
    const text = (el.text || '').trim();
    // key order must match the Python generator's dict literal, since both sides
    // compare serialised JSON strings
    return { tag: el.tag, attrs, text: text || null, children: el.children.map(norm) };
}
module.exports = { canonicalSvg };