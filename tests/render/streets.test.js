'use strict';
/** The Streets delivers artwork end to end: every resolved render block
 *  composes, and every colour resolves.
 *
 *  Guards the three failures found wiring Streets to the client:
 *   - the XML reader crashed on CDATA, so every scenario shipped render: null;
 *   - figures and scenes were looked up by names the files don't carry
 *     (figure_f.body.svg vs jay.body.svg; scene.jay.balcony vs scene.jay_balcony);
 *   - only the first :root block was read, so Streets figures on the walkway
 *     (scene.block carries a 50-token block) resolved to magenta.
 */
const test = require('node:test');
const assert = require('node:assert');
const path = require('path');
const { RenderService } = require('../../src/services/renderService');
const { RenderBlocks } = require('../../src/services/render/renderBlocks');

const svc = new RenderService({ includeBubbles: false });
const blocks = new RenderBlocks();
const streets = blocks.forScenario('the_streets');
const { publicNode } = require('../../src/services/personaService');
const scenario = require('../../src/data/scenarios/the_streets.json');

test('every Streets render block composes and fully resolves', async t => {
    const entries = Object.entries(streets);
    assert.strictEqual(entries.length, 51, 'one entry per Streets node');
    for (const [nodeId, variants] of entries) {
        for (const [key, block] of Object.entries(variants)) {
            if (!block) continue;   // messages / call / no-picture nodes
            await t.test(`${nodeId}::${key}`, () => {
                const r = svc.render(block, { nodeId });
                assert.ok(r.svg.length > 1000, 'a real frame');
                assert.ok(!r.svg.includes('var(--'), 'no unresolved var()');
                assert.ok(!/#FF00FF/i.test(r.svg), 'no magenta: every token resolved');
                assert.deepStrictEqual(r.warnings, []);
            });
        }
    }
});

test('render blocks are scoped per scenario', () => {
    assert.ok(blocks.blockFor('s1d1_walkway', null, 'the_streets'));
    assert.strictEqual(blocks.blockFor('s1d1_walkway', null, 'the_secret'), null,
        "a Streets node id never resolves under another scenario");
    assert.ok(blocks.blockFor('act2_alex_checks_in', null, 'the_secret'));
});

/* ---------------------------------------------------------------- *
 *  Native dialogue: the mobile shell draws the line, not the frame.
 * ---------------------------------------------------------------- */


/** Every node, and every message variant of it, as the client receives it. */
function* payloads() {
    for (const [nodeId, node] of Object.entries(scenario.nodes)) {
        if (!node || !node.choices) continue;
        const states = [{}, ...(node.messageVariants || []).map(v => v.when || {})];
        for (const state of states)
            yield [nodeId, state, publicNode(nodeId, node, state, null, 'the_streets')];
    }
}

test('a speaking figure reports a mouth, and it is on the face', async t => {
    for (const [nodeId, state, out] of payloads()) {
        const r = out.render;
        if (!r || !r.dialogue) continue;
        await t.test(`${nodeId} ${JSON.stringify(state)}`, () => {
            for (const line of r.dialogue) {
                const mouth = r.mouthAnchors[line.speaker];
                const head = r.headAnchors[line.speaker];
                assert.ok(mouth, `${line.speaker} speaks, so it must report a mouth`);
                // the head joins the body at headAnchor and the face is above it:
                // a mouth below that point is on the chest, one far above is in
                // the hair. Measured range across the six figures is 33..45.
                const above = head.y - mouth.y;
                assert.ok(above > 15 && above < 90,
                    `mouth ${above} above the neck join, expected 15..90`);
                assert.ok(Math.abs(mouth.x - head.x) < 40,
                    'a tilted head moves the mouth sideways, but not off the face');
            }
        });
    }
});

test('a spoken line is never also in the prose', async t => {
    let spoken = 0;
    for (const [nodeId, state, out] of payloads()) {
        const lines = (out.render && out.render.dialogue) || [];
        for (const line of lines) {
            spoken++;
            assert.ok(!out.message.includes(line.text),
                `${nodeId}: "${line.text}" reaches the player twice`);
        }
        // a node that speaks never also bakes the balloons into the artwork
        if (lines.length) assert.strictEqual(out.render.bubbles, false, nodeId);
    }
    assert.strictEqual(spoken, 13, 'The Streets speaks 13 lines, base messages and variants');
});

test('every authored line is delivered, or none of them are', async t => {
    for (const [nodeId, state, out] of payloads()) {
        const block = blocks.blockFor(nodeId, variantIndexFor(nodeId, state), 'the_streets');
        const authored = ((block && block.bubbles) || []).filter(b => b && b.text);
        if (!authored.length) continue;
        await t.test(`${nodeId} ${JSON.stringify(state)}`, () => {
            const delivered = (out.render && out.render.dialogue) || [];
            // Partial delivery is the one outcome the policy must never produce:
            // either the prose keeps every line, or speech takes every line.
            assert.ok(delivered.length === 0 || delivered.length === authored.length,
                `${delivered.length} of ${authored.length} delivered`);
            if (delivered.length)
                assert.deepStrictEqual(delivered.map(d => d.text), authored.map(b => b.text));
        });
    }
});

function variantIndexFor(nodeId, state) {
    const node = scenario.nodes[nodeId];
    if (!Array.isArray(node.messageVariants) || !Object.keys(state).length) return null;
    const idx = node.messageVariants.findIndex(v =>
        Object.entries(v.when || {}).every(([k, val]) => state[k] === val));
    return idx >= 0 ? idx : null;
}

test('a montage reports where its panels are', () => {
    const montages = [...payloads()]
        .filter(([, , out]) => out.render && out.render.montage);
    assert.ok(montages.length >= 3, 'The Streets runs three montages');
    for (const [nodeId, , out] of montages) {
        const panels = out.render.montage.panels;
        assert.strictEqual(panels.length, 3, nodeId);
        assert.deepStrictEqual(panels.map(p => p.x), [92, 580, 1068], nodeId);
        for (const p of panels) {
            assert.strictEqual(p.width, 440);
            assert.strictEqual(p.height, 550);
            assert.ok(p.x >= 0 && p.x + p.width <= 1600, 'inside the canvas');
            assert.ok(p.y >= 0 && p.y + p.height <= 900, 'inside the canvas');
        }
    }
});

test('The Secret still bakes its balloons and ships no native dialogue', () => {
    const secret = require('../../src/data/scenarios/the_secret.json');
    const out = publicNode('act2_alex_reveal', secret.nodes['act2_alex_reveal'],
        {}, null, 'the_secret');
    assert.strictEqual(out.render.bubbles, true, 'baked, exactly as before');
    assert.strictEqual(out.render.dialogue, undefined, 'nothing native leaks in');
});