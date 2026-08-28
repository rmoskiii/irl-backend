'use strict';
const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');

const { loadContract } = require('../../src/services/render/anchors');
const { AssetStore } = require('../../src/services/render/assetStore');
const { resolvePlan } = require('../../src/services/render/resolvePlan');
const { composeFrame } = require('../../src/services/render/composeFrame');
const { cacheKey } = require('../../src/services/render/cacheKey');
const { RenderService, errors } = require('../../src/services/renderService');
const { canonicalSvg } = require('./canonical');

// repo-relative by default: tests/render/ -> ../../tools/visual
const VISUAL = process.env.IRX_VISUAL || path.join(__dirname, '..', '..', 'tools', 'visual');
const FIX = process.env.IRX_FIXTURES || path.join(__dirname, 'fixtures');
const LOCKED = path.join(VISUAL, 'assets', 'frames');

const contract = loadContract(path.join(VISUAL, 'assets'), path.join(VISUAL, 'registries.json'));
const store = new AssetStore(path.join(VISUAL, 'assets')).loadAll();
const index = JSON.parse(fs.readFileSync(path.join(FIX, 'index.json'), 'utf8'));
const fixture = k => JSON.parse(fs.readFileSync(path.join(FIX, `${k.slice(0, 16)}.plan.json`), 'utf8'));

test('cache key is the sha256 of the canonicalised render block', async t => {
    for (const f of index.fixtures) {
        await t.test(f.renderKey, () => {
            assert.strictEqual(cacheKey(fixture(f.cacheKey).renderBlock), f.cacheKey);
        });
    }
});

test('cache key collapses states that resolve to the same visual', () => {
    const b = fixture(index.fixtures[0].cacheKey).renderBlock;
    const reordered = JSON.parse(JSON.stringify(b));
    assert.strictEqual(cacheKey(b), cacheKey(reordered), 'same block, same key');
    const changed = { ...b, framing: b.framing === 'direct' ? 'turned' : 'direct' };
    assert.notStrictEqual(cacheKey(b), cacheKey(changed), 'different visual, different key');
});

test('LEVEL 1 — resolved plan matches the fixture plan', async t => {
    for (const f of index.fixtures) {
        await t.test(f.renderKey, () => {
            const fx = fixture(f.cacheKey);
            const plan = resolvePlan(fx.renderBlock, contract);
            const shape = l => [l.layer, l.cast || l.id || l.group || '', l.transform || ''].join('|');
            assert.deepStrictEqual(plan.layers.map(shape), fx.plan.layers.map(shape));
        });
    }
});

test('LEVEL 2 — composed SVG matches the signed-off 2B composition', async t => {
    for (const f of index.fixtures) {
        await t.test(f.renderKey, () => {
            const fx = fixture(f.cacheKey);
            const locked = fs.readFileSync(path.join(LOCKED, `${fx.sourceFrame}.svg`), 'utf8');
            const mine = composeFrame(resolvePlan(fx.renderBlock, contract), contract, store);
            assert.strictEqual(
                canonicalSvg(mine, { ignoreProvenance: true }),
                canonicalSvg(locked, { ignoreProvenance: true }));
        });
    }
});

test('maxPerNode is enforced, not advisory', () => {
    const blocks = JSON.parse(fs.readFileSync(path.join(VISUAL, 'render_blocks.json'), 'utf8'));
    const over = blocks['act3b_alex_processes']['default'];
    assert.throws(() => resolvePlan(over, contract, { nodeId: 'act3b_alex_processes' }),
        e => e instanceof errors.MaxPerNodeExceeded && /Phase 3 content/.test(e.message));
});

test('renderService returns presentation only, and caches by block hash', () => {
    const svc = new RenderService({ assetsDir: path.join(VISUAL, 'assets'),
        registriesPath: path.join(VISUAL, 'registries.json') });
    const blocks = JSON.parse(fs.readFileSync(path.join(VISUAL, 'render_blocks.json'), 'utf8'));
    const out = svc.render(blocks['act2_alex_reveal']['default']);
    assert.match(out.svg, /^<svg /);
    assert.strictEqual(out.aspect, '16:9');
    assert.ok(out.headAnchors['char.alex'], 'head anchors emitted');
    for (const k of ['state', 'derivedState', 'scoring', 'variantIndex'])
        assert.strictEqual(out[k], undefined, `${k} must not reach the client`);
    svc.render(blocks['act2_alex_reveal']['default']);
    assert.strictEqual(svc.stats.cache.hits, 1);
});

test('a prop with no anchor in this scene is surfaced, never silently dropped', () => {
    const svc = new RenderService({ assetsDir: path.join(VISUAL, 'assets'),
        registriesPath: path.join(VISUAL, 'registries.json') });
    const blocks = JSON.parse(fs.readFileSync(path.join(VISUAL, 'render_blocks.json'), 'utf8'));
    const out = svc.render(blocks['act4_avoidant_outside']['default']);
    assert.strictEqual(out.warnings.length, 1);
    assert.strictEqual(out.warnings[0].id, 'prop.door_closed');
});