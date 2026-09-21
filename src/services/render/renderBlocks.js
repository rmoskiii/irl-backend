'use strict';
const fs = require('fs');
const path = require('path');

/** Loads the resolved render blocks once at boot and answers
 *  "which visual state does this node, in this variant, resolve to?"
 *
 *  The file is produced by tools/visual/dump_render.py from the scenario plus
 *  the mapping. It is generated, not authored - regenerate it whenever the
 *  scenario or the mapping changes, and regenerate the fixtures after that.
 *
 *  Keyed node -> variantKey -> block, where variantKey is "default" or
 *  "variant[N]" and N is the index of the messageVariants entry the ENGINE
 *  matched. The client never picks: that would let presentation diverge from
 *  the prose, and would put variant selection on the wrong side of the firewall.
 */
class RenderBlocks {
    /** Blocks are scoped per scenario: tools/visual/render_blocks.<scenarioId>.json,
     *  exactly as dump_render.py writes them. Node ids are only unique WITHIN a
     *  scenario, so a single flat map keyed by node id is one shared id away from
     *  serving one scenario's picture in another. The flat render_blocks.json is
     *  still read as the fallback for a scenario with no file of its own. */
    constructor(file, dir) {
        this.dir = dir || path.join(__dirname, '..', '..', '..', 'tools', 'visual');
        this.file = file || path.join(this.dir, 'render_blocks.json');
        this.blocks = fs.existsSync(this.file)
            ? JSON.parse(fs.readFileSync(this.file, 'utf8')) : {};
        this.byScenario = new Map();
    }

    forScenario(scenarioId) {
        if (!scenarioId) return this.blocks;
        if (!this.byScenario.has(scenarioId)) {
            const f = path.join(this.dir, `render_blocks.${scenarioId}.json`);
            this.byScenario.set(scenarioId, fs.existsSync(f)
                ? JSON.parse(fs.readFileSync(f, 'utf8')) : this.blocks);
        }
        return this.byScenario.get(scenarioId);
    }

    /** variantIndex: integer index of the matched messageVariant, or null/undefined
     *  when the node rendered its default `message`. Returns null for nodes with
     *  no artwork (messages mode) and for anything unknown - the caller treats a
     *  null block as "this node has no picture", which is a legitimate state. */
    blockFor(nodeId, variantIndex, scenarioId) {
        const node = this.forScenario(scenarioId)[nodeId];
        if (!node) return null;
        const key = (variantIndex === null || variantIndex === undefined)
            ? 'default'
            : `variant[${variantIndex}]`;
        // A variant may exist in the scenario without changing the visual state, in
        // which case dump_render emits no key for it. Falling back to default is
        // correct: the picture genuinely is the default one.
        return node[key] || node.default || null;
    }

    get stats() {
        const nodes = Object.keys(this.blocks).length;
        const states = Object.values(this.blocks)
            .reduce((n, v) => n + Object.keys(v).length, 0);
        const renderable = Object.values(this.blocks)
            .reduce((n, v) => n + Object.values(v).filter(Boolean).length, 0);
        return { nodes, states, renderable };
    }
}
module.exports = { RenderBlocks };