'use strict';
const path = require('path');
const { loadContract } = require('./render/anchors');
const { AssetStore } = require('./render/assetStore');
const { resolvePlan } = require('./render/resolvePlan');
const { composeFrame } = require('./render/composeFrame');
const { cacheKey } = require('./render/cacheKey');
const { RenderCache } = require('./render/renderCache');
const { flattenTokens } = require('./render/flattenTokens');
const errors = require('./render/errors');

/** The only composition module the route layer touches.
 *
 *  render(renderBlock) -> { svg, cacheKey, aspect, headAnchors, warnings }
 *
 *  The firewall holds by construction: the input is a RESOLVED render block -
 *  presentation data the resolver has already produced - and the output is a
 *  picture plus head coordinates. No scenario, no state map, no scoring keys,
 *  no variant indices ever pass through here.
 */
class RenderService {
    /** flattenForClient: resolve var(--irx-*) to literal colours before sending.
     *  On by default because flutter_svg cannot resolve CSS custom properties.
     *  Turn it off to inspect the composition exactly as the fixtures assert it. */
    constructor({ assetsDir, registriesPath, cacheSize = 256,
                    flattenForClient = true } = {}) {
        this.flattenForClient = flattenForClient;
        // single source of truth: the same assets the 2B.6 gate signed off. A copy
        // under src/ would be free to drift from the audited set.
        const visual = path.join(__dirname, '..', '..', 'tools', 'visual');
        this.assetsDir = assetsDir || process.env.IRX_ASSETS_DIR || path.join(visual, 'assets');
        this.registriesPath = registriesPath || path.join(visual, 'registries.json');
        this.contract = loadContract(this.assetsDir, this.registriesPath);
        this.store = new AssetStore(this.assetsDir).loadAll();
        this.cache = new RenderCache(cacheSize);
    }

    render(renderBlock, { nodeId } = {}) {
        const key = cacheKey(renderBlock);
        const hit = this.cache.get(key);
        if (hit) return hit;

        const plan = resolvePlan(renderBlock, this.contract, { nodeId });
        const composed = composeFrame(plan, this.contract, this.store, { renderKey: key });
        const svg = this.flattenForClient ? flattenTokens(composed) : composed;

        const headAnchors = {};
        for (const c of plan.cast || []) headAnchors[c.id] = c.headAnchor;

        const warnings = (plan.unplaceableProps || []).map(u => ({
            code: 'PROP_NOT_PLACEABLE_IN_SCENE', ...u }));

        return this.cache.set(key, {
            svg, cacheKey: key, aspect: '16:9',
            canvas: this.contract.anchors.canvas.viewBox,
            headAnchors, warnings,
        });
    }

    /** For the route layer: attach presentation to a node response without
     *  letting anything else leak into it. */
    attachTo(nodeResponse, renderBlock) {
        if (!renderBlock) return nodeResponse;
        return { ...nodeResponse, render: this.render(renderBlock, { nodeId: nodeResponse.nodeId }) };
    }

    get stats() { return { assets: this.store.count, cache: this.cache.stats }; }
}
module.exports = { RenderService, errors };