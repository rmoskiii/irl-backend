'use strict';
const { outerXml } = require('./xml');
const { mergeStyles, mergeDefs, svgRoot } = require('./svgBuilder');
const { composeBubbles } = require('./composeBubbles');
const { g } = require('./num');

/** Where a register lands inside its figure, as the composer places it.
 *
 *  Extracted rather than duplicated because a native speech bubble aims at a
 *  point ON the register (the mouth), and a point derived from a second copy of
 *  this maths would drift from the drawing the moment either copy changed. The
 *  composer and the mouth emitter read the same function, so the tail lands on
 *  the mouth that was actually drawn.
 *
 *  Returns the two parts separately: the translate that seats the register in
 *  the figure, and the rotation the register declares about its own neck
 *  anchor. Applied in that written order - `translate(...) rotate(...)` - which
 *  means a point is rotated first, then translated. */
function headPlacement(A, reg) {
    const [nx, ny] = String(reg.attrs['data-neck-anchor']).split(',').map(Number);
    const cc = A.character;
    return {
        nx, ny,
        dx: cc.headSocket.x - nx,
        dy: cc.headSocket.y - ny,
        rotate: parseFloat(reg.attrs['data-register-rotate'] || '0') || 0,
    };
}

/** A register-local point as it ends up on the canvas: rotate about the neck
 *  anchor, seat the register in the figure, then place the figure in its slot.
 *  `slot` is the plan's cast transform, `translate(x,y)`. */
function projectRegisterPoint(pt, place, slotTransform) {
    const m = /translate\((-?[\d.]+),\s*(-?[\d.]+)\)/.exec(slotTransform || '');
    const sx = m ? Number(m[1]) : 0;
    const sy = m ? Number(m[2]) : 0;
    const t = (place.rotate * Math.PI) / 180;
    const cos = Math.cos(t), sin = Math.sin(t);
    const rx = place.nx + (pt.x - place.nx) * cos - (pt.y - place.ny) * sin;
    const ry = place.ny + (pt.x - place.nx) * sin + (pt.y - place.ny) * cos;
    return { x: rx + place.dx + sx, y: ry + place.dy + sy };
}

/** Plan in, SVG string out. Never reads the scenario, never sees state. */
function composeFrame(plan, contract, store, opts = {}) {
    const A = contract.anchors;
    if (plan.mode === 'montage') return composeMontage(plan, contract, store, opts);

    const envRel = `environments/${plan.scene}.svg`;
    const styles = [...store.get(envRel).styles];
    const defs = [...store.get(envRel).defs];
    const layers = new Map();
    const push = (name, xml) => {
        if (!layers.has(name)) layers.set(name, []);
        layers.get(name).push(xml);
    };

    for (const name of ['background', 'architecture', 'environmental_detail', 'furniture', 'foreground'])
        push(name, store.group(envRel, name));

    for (const c of plan.cast) {
        const body = store.get(c.assets.body);
        const ward = store.get(c.assets.wardrobe);
        const reg = store.get(c.assets.register);
        styles.push(...body.styles, ...ward.styles, ...reg.styles);
        defs.push(...body.defs, ...ward.defs, ...reg.defs);

        const place = headPlacement(A, reg);
        let headTf = `translate(${g(place.dx)},${g(place.dy)})`;
        if (place.rotate) headTf += ` rotate(${g(place.rotate)},${g(place.nx)},${g(place.ny)})`;

        const slotLayer = (inner, extra) => extra
            ? `<g transform="${c.transform}"><g transform="${extra}">${inner}</g></g>`
            : `<g transform="${c.transform}">${inner}</g>`;

        const opt = (rel, id) => { try { return store.group(rel, id); } catch { return null; } };
        const back = opt(c.assets.body, 'character_back');
        const contact = opt(c.assets.body, 'character_contact');
        const front = opt(c.assets.body, 'character_front');
        if (back) push('character_back', slotLayer(back));
        push('character_body', slotLayer(store.group(c.assets.body, 'character_body')));
        push('character_clothing', slotLayer(store.group(c.assets.wardrobe, 'character_clothing')));
        push('character_head', slotLayer(store.group(c.assets.register, 'character_head'), headTf));
        if (contact) push('character_contact', slotLayer(contact));
        if (front) push('character_front', slotLayer(front));
    }

    for (const p of plan.props) {
        const a = store.get(p.source);
        styles.push(...a.styles);
        defs.push(...a.defs);
        push('prop', `<g id="${p.id.replace(/\./g, '_')}" transform="${p.transform}">` +
            `${store.group(p.source, 'prop')}</g>`);
    }

    let body = `<defs><style>${mergeStyles(styles)}</style>${mergeDefs(defs, outerXml)}</defs>`;
    for (const name of A.layerOrder)
        for (const xml of layers.get(name) || [])
            body += `<g data-layer="${name}">${xml}</g>`;

    if (opts.bubbles !== false) {
        const b = composeBubbles(plan, contract);
        if (b) body += b;
    }
    // provenance at runtime is the render key, not the 2B frame declaration name
    const attrs = { viewBox: A.canvas.viewBox };
    if (opts.renderKey) attrs['data-render-key'] = opts.renderKey;
    return svgRoot(attrs, body);
}

function composeMontage(plan, contract, store) {
    const A = contract.anchors;
    const cfg = A.montage;
    const styles = [], defs = [];
    const pw = cfg.panelWidth, ph = cfg.panelHeight;
    let inner = `<rect x="0" y="0" width="${A.canvas.width}" height="${A.canvas.height}" ` +
        `fill="var(${cfg.matte})" />`;
    // the plan owns the rectangles: the client is told the same geometry the
    // composer draws, so a phone showing one panel frames exactly this panel
    plan.panels.forEach((p) => {
        const rel = `vignettes/${p.vignette}.svg`;
        const a = store.get(rel);
        styles.push(...a.styles); defs.push(...a.defs);
        const x = p.x;
        inner += `<g transform="translate(${g(x)},${cfg.top}) scale(${g(pw / cfg.sourceWidth)})">` +
            `${store.group(rel, 'vignette')}</g>`;
        inner += `<rect x="${g(x)}" y="${cfg.top}" width="${pw}" height="${ph}" fill="none" ` +
            `stroke="var(${cfg.frame})" stroke-width="${cfg.frameWidth}" />`;
        if (p.caption)
            inner += `<text x="${g(x + pw / 2)}" y="${cfg.top + ph + cfg.captionGap}" ` +
                `text-anchor="middle" font-family="monospace" font-size="${cfg.captionSize}" ` +
                `letter-spacing="1.6" fill="var(${cfg.frame})">${String(p.caption).toUpperCase()}</text>`;
    });
    const body = `<defs><style>${mergeStyles(styles)}</style>${mergeDefs(defs, outerXml)}</defs>` +
        `<g data-layer="montage">${inner}</g>`;
    const attrs = { viewBox: A.canvas.viewBox, 'data-mode': 'montage' };
    return svgRoot(attrs, body);
}

module.exports = { composeFrame, headPlacement, projectRegisterPoint };