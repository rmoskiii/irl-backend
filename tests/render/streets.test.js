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