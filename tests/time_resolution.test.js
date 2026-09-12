'use strict';
/**
 * Phase 1 — D1 / D9 / D10 unit and negative tests.
 *
 * Harness assumption: node --test with node:assert, matching the existing
 * tests/render suite. If that suite uses a different runner or a different
 * fixture-loading helper, port the three describe blocks rather than adopting
 * this file wholesale — the assertions are the deliverable, not the scaffolding.
 *
 * These cover the Node side. The Python resolver's equivalents (undeclared time
 * raises, unknown nodeProps token raises, scene override short-circuits the
 * location match) belong beside tools/visual/resolve.py in whatever harness
 * validate_assets.py already uses.
 */
const test = require('node:test');
const assert = require('node:assert');
const { resolvePlan } = require('../../src/services/render/resolvePlan');

// ---------------------------------------------------------------- fixtures

const anchors = {
    canvas: { viewBox: '0 0 1600 900', width: 1600, height: 900 },
    // the deprecated global: figure_a's contract
    character: { basePoint: { x: 210, y: 800 }, headSocket: { x: 210, y: 210 } },
    characters: {
        figure_a: { basePoint: { x: 210, y: 800 }, headSocket: { x: 210, y: 210 } },
        figure_b: { basePoint: { x: 210, y: 800 }, headSocket: { x: 210, y: 196 } },
    },
    scenes: {
        'scene.block': {
            slots: { centre: { x: 800, y: 900 } },
            propAnchors: { wall_left: { x: 470, y: 604 } },
        },
    },
    props: { 'prop.note': { basePoint: { x: 90, y: 130 },
            defaultAnchor: { 'scene.block': 'wall_left' } } },
    bubbles: { maxPerNode: 3, placement: { centre: { x: 48, y: 104 } },
        fontSize: 47, lineHeight: 57, charsPerLine: 19, maxWidth: 580,
        cornerRadius: 30, gap: 20, padding: 28, paddingY: 41, firstBaseline: 55,
        tailInset: 40, strokeWidth: 4.4 },
};

const registries = {
    characters: {
        'char.bola': { base: 'figure_a', turned: null },
        'char.jay': { base: 'figure_b', turned: 'figure_b_rear' },
    },
};

const contract = { anchors, registries };

const block = (over = {}) => ({
    mode: 'scene', framing: 'direct',
    scene: { id: 'scene.block', time: 'night' },
    props: [], cast: [], ...over,
});

const withCast = id => block({ cast: [{ id, slot: 'centre',
        presence: 'present', register: 'off', wardrobe: 'day' }] });

// --------------------------------------------------------------- D8: anchor

test('D8 — headAnchor uses the per-base contract, not the deprecated global', () => {
    const a = resolvePlan(withCast('char.bola'), contract).cast[0];
    const b = resolvePlan(withCast('char.jay'), contract).cast[0];

    // figure_a: socket y=210, basePoint y=800 -> 900 - (800-210) = 310
    assert.strictEqual(a.headAnchor.y, 310);
    // figure_b: socket y=196 -> 900 - (800-196) = 296. Pre-D8 this returned 310.
    assert.strictEqual(b.headAnchor.y, 296);
    assert.strictEqual(b.headAnchor.y, a.headAnchor.y - 14,
        'figure_b sits 14px higher; that difference is the whole defect');

    // basePoint is identical on every figure, so transform must NOT have moved
    assert.strictEqual(a.transform, b.transform);
});

test('D8 — a base with no anchors.characters entry falls back to the global', () => {
    const c = { anchors: { ...anchors, characters: {} }, registries };
    const p = resolvePlan(withCast('char.jay'), c).cast[0];
    assert.strictEqual(p.headAnchor.y, 310, 'pre-D8 behaviour preserved');
});

// ----------------------------------------------------------------- D1: time

test('D1 — the plan carries the resolved time at the root', () => {
    const p = resolvePlan(block(), contract);
    assert.strictEqual(p.time, 'night');
});

test('D1 — every environment layer carries the same time; nothing else does', () => {
    const p = resolvePlan(withCast('char.bola'), contract);
    const env = p.layers.filter(l => l.source && l.source.startsWith('environments/'));
    assert.strictEqual(env.length, 5, 'background, architecture, detail, furniture, foreground');
    for (const l of env) assert.strictEqual(l.time, 'night');

    const castLayers = p.layers.filter(l => l.cast);
    for (const l of castLayers)
        assert.strictEqual(l.time, undefined, 'a figure is not time-varying');
});

test('D1 — time is passed through, never defaulted in the plan', () => {
    // the resolver owns the default; resolvePlan must not silently substitute one
    const p = resolvePlan(block({ scene: { id: 'scene.block', time: 'day' } }), contract);
    assert.strictEqual(p.time, 'day');
    assert.ok(p.layers.filter(l => l.time === 'day').length === 5);
});

// ------------------------------------------------------------ D1: filtering

/** Mirrors filter_time() in compose_frame.py. Kept here so the two
 *  implementations are asserted against one set of cases; if the client grows
 *  its own filter it must satisfy these too. */
function filterByTime(nodes, time) {
    return nodes.filter(n => n.dataTime === undefined || n.dataTime === time);
}

test('D1 filter — untagged always survives, tagged is mutually exclusive', () => {
    const nodes = [
        { id: 'parapet' },
        { id: 'lamppool', dataTime: 'night' },
        { id: 'shopfront_open', dataTime: 'day' },
    ];
    const night = filterByTime(nodes, 'night').map(n => n.id);
    const day = filterByTime(nodes, 'day').map(n => n.id);

    assert.deepStrictEqual(night, ['parapet', 'lamppool']);
    assert.deepStrictEqual(day, ['parapet', 'shopfront_open']);
    assert.ok(night.includes('parapet') && day.includes('parapet'));
    assert.ok(!night.includes('shopfront_open') && !day.includes('lamppool'));
});

test('D1 filter — an existing asset carries no data-time, so filtering is a no-op', () => {
    const nodes = [{ id: 'a' }, { id: 'b' }, { id: 'c' }];
    assert.deepStrictEqual(filterByTime(nodes, 'evening'), nodes);
    assert.deepStrictEqual(filterByTime(nodes, 'day'), nodes);
});

// --------------------------------------------------------------- D10: props

test('D10 — nodeProps reach the plan through the existing block.props path', () => {
    const p = resolvePlan(block({ props: ['prop.note'] }), contract);
    assert.strictEqual(p.props.length, 1);
    assert.strictEqual(p.props[0].id, 'prop.note');
    assert.strictEqual(p.props[0].anchor, 'wall_left');
    assert.strictEqual(p.unplaceableProps.length, 0);
});

test('D10 — a prop with no anchor for this scene is omitted, never silently', () => {
    const c = { anchors: { ...anchors,
            props: { 'prop.note': { basePoint: { x: 90, y: 130 }, defaultAnchor: {} } } },
        registries };
    const p = resolvePlan(block({ props: ['prop.note'] }), c);
    assert.strictEqual(p.props.length, 0);
    assert.strictEqual(p.unplaceableProps.length, 1);
    assert.strictEqual(p.unplaceableProps[0].id, 'prop.note');
});

// ------------------------------------------------------------- regression

test('regression — the plan gains time and nothing else', () => {
    const p = resolvePlan(withCast('char.bola'), contract);
    assert.deepStrictEqual(Object.keys(p).sort(), [
        'canvas', 'cast', 'framing', 'layers', 'mode', 'props', 'scene', 'time',
        'unplaceableProps',
    ].sort());
});

test('regression — montage plans are untouched by D1', () => {
    const p = resolvePlan({ mode: 'montage', panels: [{ vignette: 'vig.bus_window' }] }, contract);
    assert.strictEqual(p.time, undefined, 'a montage has no scene and no time');
    assert.strictEqual(p.mode, 'montage');
});