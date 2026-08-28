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
    constructor(file) {
        this.file = file || path.join(__dirname, '..', '..', '..',
            'tools', 'visual', 'render_blocks.json');
        this.blocks = JSON.parse(fs.readFileSync(this.file, 'utf8'));
    }

    /** variantIndex: integer index of the matched messageVariant, or null/undefined
     *  when the node rendered its default `message`. Returns null for nodes with
     *  no artwork (messages mode) and for anything unknown - the caller treats a
     *  null block as "this node has no picture", which is a legitimate state. */
    blockFor(nodeId, variantIndex) {
        const node = this.blocks[nodeId];
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