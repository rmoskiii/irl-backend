'use strict';
const { g, pyFloat } = require('./num');

/** LOCKED treatment: rounded balloon + tail (variant 1). Ported from
 *  build_bubbles(). Geometry lives in the contract, not here. */
function wrap(text, width) {
    // textwrap.wrap semantics for the shapes the scenario actually contains:
    // greedy fill on whitespace, no hyphen splitting, collapse runs of spaces.
    const words = String(text).split(/\s+/).filter(Boolean);
    if (!words.length) return [''];
    const lines = [];
    let cur = '';
    for (const w of words) {
        if (!cur) { cur = w; continue; }
        if ((cur + ' ' + w).length <= width) cur += ' ' + w;
        else { lines.push(cur); cur = w; }
    }
    if (cur) lines.push(cur);
    return lines;
}

function composeBubbles(plan, contract) {
    const spec = plan.layers.find(l => l.layer === 'bubbles');
    if (!spec) return null;
    const A = contract.anchors;
    const cfg = A.bubbles;
    const scene = A.scenes[plan.scene];
    const w = cfg.maxWidth, r = cfg.cornerRadius;
    const cc = A.character;

    // NOTE a real asymmetry in the signed-off composer, reproduced deliberately:
    // the BODY is placed with the generic A.character metrics, but the tail aims
    // at a head computed from the PER-BASE A.characters[base] metrics. figure_b's
    // headSocket sits 14px above figure_a's, so using the generic figure here
    // moves every Alex tail apex by ~1.5px. Parity issue, not a redesign - if the
    // asymmetry is wrong it is a 2B.7 question, not a 2C one.
    const headTargetFor = castMember => {
        const m = (A.characters && A.characters[castMember.base]) || cc;
        const s = scene.slots[castMember.slot];
        const hx = s.x + (m.headSocket.x - m.basePoint.x);
        const hy = s.y - (m.basePoint.y - m.headSocket.y);
        return { tx: hx + cfg.tailTarget.dx, ty: hy + cfg.tailTarget.dy };
    };
    const speakerOf = i => {
        const sid = spec.speakers[i];
        if (sid) { const hit = plan.cast.find(c => c.id === sid); if (hit) return hit; }
        return plan.cast[0] || null;
    };

    const parts = [];
    let y = spec.origin.y;
    for (let i = 0; i < spec.texts.length; i++) {
        const lines = wrap(spec.texts[i], cfg.charsPerLine);
        const h = cfg.lineHeight * lines.length + cfg.paddingY;
        const x = spec.origin.x;
        const inner = [];
        inner.push(`<path d="M${x} ${y + r} q0 -${r} ${r} -${r} h${w - 2 * r} q${r} 0 ${r} ${r} ` +
            `v${h - 2 * r} q0 ${r} -${r} ${r} h-${w - 2 * r} q-${r} 0 -${r} -${r} z" ` +
            `fill="var(--irx-cloth-inner)" stroke="var(--irx-line)" ` +
            `stroke-width="${cfg.strokeWidth}" stroke-linejoin="round" />`);

        // an exit beat has no tail: the speaker has left. a remote block has an
        // empty cast: voice, not presence. a tail in either case reads as a bug.
        if (i === spec.texts.length - 1 && !spec.exitBeat && !spec.remote) {
            const tspk = speakerOf(i) || plan.cast[0];
            const { tx, ty } = headTargetFor(tspk);
            const nearRight = tx > x + w / 2;
            const bx = nearRight ? x + w : x;
            const by = y + h - cfg.tailInset;
            const hw = cfg.tail.baseWidth / 2;
            const dx = tx - bx, dy = ty - by;
            const m = Math.max(1e-6, Math.hypot(dx, dy));
            const L = cfg.tail.length;
            const ax = bx + dx / m * L, ay = by + dy / m * L;
            inner.push(`<path d="M${bx} ${g(by - hw)} L${g(ax)} ${g(ay)} L${bx} ${g(by + hw)} z" ` +
                `fill="var(--irx-cloth-inner)" stroke="var(--irx-line)" ` +
                `stroke-width="${cfg.strokeWidth}" stroke-linejoin="round" />`);
            inner.push(`<path d="M${bx} ${g(by - hw)} v${g(2 * hw)}" stroke="var(--irx-cloth-inner)" ` +
                `stroke-width="${pyFloat(cfg.strokeWidth + 1.6)}" fill="none" />`);
        }
        lines.forEach((ln, j) => {
            inner.push(`<text x="${x + cfg.padding}" y="${y + cfg.firstBaseline + j * cfg.lineHeight}" ` +
                `font-family="Zilla Slab, Georgia, serif" font-size="${cfg.fontSize}" ` +
                `fill="var(--irx-line)">${esc(ln)}</text>`);
        });
        parts.push(`<g>${inner.join('')}</g>`);
        y += h + cfg.gap;
    }
    return `<g data-layer="bubbles" data-exit-beat="${spec.exitBeat}">${parts.join('')}</g>`;
}

function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
module.exports = { composeBubbles, wrap };