'use strict';

/** Merges <style> rules and <defs> children the way the Python composer does:
 *  rule-level dedup preserving first-seen order, id-level dedup for defs. */
function mergeStyles(blocks) {
    const seen = new Set(), out = [];
    for (const b of blocks) {
        for (const rule of String(b).match(/[^{}]+\{[^{}]*\}/g) || []) {
            const k = rule.trim();
            if (!seen.has(k)) { seen.add(k); out.push(k); }
        }
    }
    return '\n' + out.join('\n') + '\n';
}

function mergeDefs(nodes, outerXml) {
    const seen = new Set(), out = [];
    for (const n of nodes) {
        const id = n.attrs && n.attrs.id;
        if (id && seen.has(id)) continue;
        if (id) seen.add(id);
        out.push(outerXml(n));
    }
    return out.join('');
}

function svgRoot(attrs, body) {
    const a = Object.entries(attrs).map(([k, v]) => `${k}="${escAttr(v)}"`).join(' ');
    return `<svg xmlns="http://www.w3.org/2000/svg" ${a}>${body}</svg>`;
}

function escAttr(v) {
    return String(v).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
}
module.exports = { mergeStyles, mergeDefs, svgRoot };