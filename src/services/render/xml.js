'use strict';

/** Minimal XML reader for the asset set: well-formed SVG, no CDATA outside
 *  <style>, no DTD. Deliberately NOT a general parser - it exists so the
 *  composer can lift a named <g> subtree verbatim, exactly as ElementTree does,
 *  without a re-serialisation round trip that could perturb the output. */
function parse(src) {
    let i = 0;
    const root = { tag: '#root', attrs: {}, children: [], text: '' };
    const stack = [root];
    while (i < src.length) {
        const lt = src.indexOf('<', i);
        if (lt === -1) break;
        if (lt > i) {
            const text = src.slice(i, lt);
            const top = stack[stack.length - 1];
            if (text.trim()) top.text = (top.text || '') + decode(text);
        }
        if (src.startsWith('<!--', lt)) { i = src.indexOf('-->', lt) + 3; continue; }
        if (src.startsWith('<?', lt)) { i = src.indexOf('?>', lt) + 2; continue; }
        if (src.startsWith('</', lt)) {
            const gt = src.indexOf('>', lt);
            stack.pop(); i = gt + 1; continue;
        }
        const gt = findTagEnd(src, lt);
        const raw = src.slice(lt + 1, gt).replace(/\/$/, '').trim();
        const selfClosing = src[gt - 1] === '/';
        const sp = raw.search(/\s/);
        const tag = sp === -1 ? raw : raw.slice(0, sp);
        const attrs = {};
        if (sp !== -1) {
            const re = /([\w:.-]+)\s*=\s*"([^"]*)"/g;
            let m;
            while ((m = re.exec(raw.slice(sp)))) attrs[m[1]] = decode(m[2]);
        }
        const node = { tag: strip(tag), attrs, children: [], text: '',
            start: lt, end: -1, src };
        stack[stack.length - 1].children.push(node);
        i = gt + 1;
        if (selfClosing) { node.end = gt + 1; continue; }
        stack.push(node);
        node._openEnd = gt + 1;
        // find matching close to record the verbatim span
        node.end = matchingClose(src, node.tag, gt + 1);
    }
    return root;
}

function strip(tag) { return tag.includes(':') ? tag.split(':').pop() : tag; }

/** ElementTree resolves entities when it reads; the canonical comparison is
 *  against its output, so the reader has to resolve them too. */
function decode(s) {
    return s.replace(/&#(\d+);/g, (_, d) => String.fromCharCode(+d))
        .replace(/&#x([0-9a-fA-F]+);/g, (_, h) => String.fromCharCode(parseInt(h, 16)))
        .replace(/&lt;/g, '<').replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"').replace(/&apos;/g, "'")
        .replace(/&amp;/g, '&');
}

function findTagEnd(src, lt) {
    let inQ = false;
    for (let j = lt + 1; j < src.length; j++) {
        const c = src[j];
        if (c === '"') inQ = !inQ;
        else if (c === '>' && !inQ) return j;
    }
    return src.length;
}

function matchingClose(src, tag, from) {
    let depth = 1, i = from;
    const open = new RegExp(`<${tag}(\\s|>|/>)`, 'g');
    while (depth > 0 && i < src.length) {
        const nextOpen = src.indexOf(`<${tag}`, i);
        const nextClose = src.indexOf(`</${tag}`, i);
        if (nextClose === -1) return src.length;
        if (nextOpen !== -1 && nextOpen < nextClose) {
            const e = findTagEnd(src, nextOpen);
            if (src[e - 1] !== '/') depth++;
            i = e + 1;
        } else {
            depth--;
            i = src.indexOf('>', nextClose) + 1;
            if (depth === 0) return i;
        }
    }
    return i;
}

/** Depth-first search for an element by tag+id. */
function findById(node, tag, id) {
    for (const c of node.children || []) {
        if (c.tag === tag && c.attrs.id === id) return c;
        const hit = findById(c, tag, id);
        if (hit) return hit;
    }
    return null;
}

function findAll(node, tag, out = []) {
    for (const c of node.children || []) {
        if (c.tag === tag) out.push(c);
        findAll(c, tag, out);
    }
    return out;
}

/** The element's exact source text, so a lifted subtree is byte-preserved. */
function outerXml(node) { return node.src.slice(node.start, node.end); }

function innerText(node) {
    return node.src.slice(node._openEnd, node.end - `</${node.tag}>`.length);
}

module.exports = { parse, findById, findAll, outerXml, innerText };