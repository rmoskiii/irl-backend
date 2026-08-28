'use strict';
const { NoPlacementForSlot, NoSpeakerTarget, MaxPerNodeExceeded } = require('./errors');

/** Pure: resolved render block in, ordered composition plan out. No I/O, no SVG.
 *
 *  This is the module that replaces the hand-authored frame declarations in
 *  anchors.json. Those declarations were transcriptions of render blocks made
 *  for the 2B audit; at runtime there are no declarations, so everything they
 *  carried - asset base, register, wardrobe, prop anchor - has to be derived
 *  from the block plus the contract. Level 1 fixtures assert exactly this.
 */
function resolvePlan(block, contract, opts = {}) {
    const { anchors: A, registries: R } = contract;
    if (block.mode === 'montage') return montagePlan(block, A);

    const sceneId = block.scene.id;
    const scene = A.scenes[sceneId];
    const turned = block.framing === 'turned';

    const cast = (block.cast || [])
        .filter(c => !c.presence || c.presence === 'present')
        .map(c => {
            const reg = R.characters[c.id];
            const base = turned ? reg.turned : reg.base;
            const register = turned ? 'rear' : c.register;
            const slot = scene.slots[c.slot];
            const cc = A.character;
            return {
                id: c.id, base, slot: c.slot, register, wardrobe: c.wardrobe,
                transform: `translate(${slot.x - cc.basePoint.x},${slot.y - cc.basePoint.y})`,
                assets: {
                    body: `characters/${base}.body.svg`,
                    register: `characters/${base}.register.${register}.svg`,
                    wardrobe: `characters/${base}.wardrobe.${c.wardrobe}.svg`,
                },
                // emitted so the client never has to re-derive where a head is
                headAnchor: {
                    x: slot.x + (cc.headSocket.x - cc.basePoint.x),
                    y: slot.y - (cc.basePoint.y - cc.headSocket.y),
                },
            };
        });

    // A block may list a prop the scene has no anchor for - `prop.door_closed`
    // appears in act4_avoidant_outside (street) and act4_late_disclosure (party)
    // but declares a defaultAnchor only for the kitchen. The signed-off 2B frames
    // omit it, so the renderer must omit it too or it stops reproducing them.
    // Omitted, never silently: it surfaces on the plan and in the node response.
    const unplaceableProps = [];
    const props = [];
    for (const id of block.props || []) {
        const meta = A.props[id];
        const anchorName = (meta.defaultAnchor || {})[sceneId];
        if (!anchorName) {
            unplaceableProps.push({ id, scene: sceneId,
                reason: 'no defaultAnchor declared for this scene' });
            continue;
        }
        const anc = scene.propAnchors[anchorName];
        props.push({
            id, anchor: anchorName, source: `props/${id}.svg`,
            transform: `translate(${anc.x - meta.basePoint.x},${anc.y - meta.basePoint.y})`,
        });
    }

    const layers = [];
    for (const l of ['background', 'architecture', 'environmental_detail'])
        layers.push({ layer: l, source: `environments/${sceneId}.svg`, group: l });
    for (const l of ['character_back', 'character_body', 'character_clothing', 'character_head'])
        for (const c of cast) layers.push({ layer: l, cast: c.id, transform: c.transform });
    layers.push({ layer: 'furniture', source: `environments/${sceneId}.svg`, group: 'furniture' });
    for (const p of props)
        layers.push({ layer: 'prop', id: p.id, anchor: p.anchor, source: p.source, transform: p.transform });
    for (const l of ['character_contact', 'character_front'])
        for (const c of cast) layers.push({ layer: l, cast: c.id, transform: c.transform });
    layers.push({ layer: 'foreground', source: `environments/${sceneId}.svg`, group: 'foreground' });

    const bubbles = resolveBubbles(block, cast, scene, A, opts.nodeId);
    if (bubbles) layers.push(bubbles);

    return { canvas: A.canvas, scene: sceneId, mode: block.mode,
        framing: block.framing, cast, props, layers, unplaceableProps };
}

function resolveBubbles(block, cast, scene, A, nodeId) {
    let list = (block.bubbles || []).slice();
    let exitBeat = false;
    if (!list.length && block.exitBeat) { list = [block.exitBeat]; exitBeat = true; }
    if (!list.length) return null;

    const cfg = A.bubbles;
    if (cfg.maxPerNode && list.length > cfg.maxPerNode)
        throw new MaxPerNodeExceeded(nodeId || '(render block)', list.length, cfg.maxPerNode);

    const speakerOf = b => {
        const sid = b && b.speaker;
        if (sid) { const hit = cast.find(c => c.id === sid); if (hit) return hit; }
        return cast[0] || block.bubbleSpeaker || null;
    };
    const first = speakerOf(list[0]);
    if (!first && !exitBeat && cast.length) throw new NoSpeakerTarget(block.nodeId);

    // an absent/remote block has no cast: the stack still needs an origin slot
    const slot = first ? first.slot : (block.bubbleSpeaker && block.bubbleSpeaker.slot) || 'centre';
    const origin = (scene.bubblePlacement || {})[slot] || cfg.placement[slot];
    if (!origin) throw new NoPlacementForSlot(slot);

    return {
        layer: 'bubbles', origin, count: list.length, exitBeat, remote: cast.length === 0,
        speakers: list.map(b => b.speaker || null),
        texts: list.map(b => b.text),
        config: Object.fromEntries(['fontSize', 'lineHeight', 'charsPerLine', 'maxWidth',
            'cornerRadius', 'gap', 'padding', 'paddingY', 'firstBaseline', 'tailInset',
            'strokeWidth', 'maxPerNode'].map(k => [k, cfg[k]])),
    };
}

function montagePlan(block, A) {
    return {
        canvas: A.canvas, mode: 'montage',
        panels: (block.panels || []).map(p => ({ vignette: p.vignette, caption: p.caption || null })),
        layers: (block.panels || []).map((p, i) => ({
            layer: 'montage_panel', index: i, source: `vignettes/${p.vignette}.svg` })),
    };
}

module.exports = { resolvePlan };