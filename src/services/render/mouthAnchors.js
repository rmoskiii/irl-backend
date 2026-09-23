'use strict';
const { headPlacement, projectRegisterPoint } = require('./composeFrame');
const { contractFor } = require('./resolvePlan');

/** Where each speaking figure's mouth ends up on the canvas.
 *
 *  A native speech bubble is drawn by the client, so the tail needs a point in
 *  canvas coordinates. headAnchor cannot serve: it is the neck join, which is
 *  the ONE point a register rotation leaves fixed, and a tail that lands on the
 *  neck reads as pointing at the chest. The mouth moves with the tilt, so it has
 *  to be projected through the same placement the composer used.
 *
 *  Optional by construction. A figure with no mouthAnchor in the contract -
 *  every rear register, every figure that predates The Streets - is simply
 *  absent from the map, and the client falls back to the head. Absent is a
 *  normal state here, never an error.
 */
function mouthAnchorsFor(plan, contract, store) {
    const A = contract.anchors;
    const out = {};
    for (const c of plan.cast || []) {
        const cc = contractFor(A, c.base);
        const mouth = cc && cc.mouthAnchor;
        if (!mouth) continue;
        let reg;
        try {
            reg = store.get(c.assets.register);
        } catch {
            continue;   // a missing register is the composer's error to report, not ours
        }
        const place = headPlacement(A, reg);
        const p = projectRegisterPoint({ x: mouth.x, y: mouth.y }, place, c.transform);
        out[c.id] = { x: round(p.x), y: round(p.y) };
    }
    return out;
}

// one decimal: the canvas is 1600x900 and a phone shows it at roughly a
// quarter of that, so anything finer is noise in the payload.
const round = n => Math.round(n * 10) / 10;

module.exports = { mouthAnchorsFor };