'use strict';
const fs = require('fs');
const path = require('path');

/** Decides, per node, whether the dialogue is drawn as balloons inside the
 *  artwork or left as prose beneath it — and if it is drawn, removes it from
 *  the prose so the player never reads the same line twice.
 *
 *  This is a product decision per beat, not an engineering one, which is why
 *  the list is data rather than code. `confession` earns the balloons: the
 *  line landing in the room is the beat. `act2_alex_checks_in` does not: it is
 *  mostly narration with one line of dialogue at the end.
 *
 *  De-duplication is exact, never fuzzy. The bubble strings in the render
 *  block were extracted verbatim from the message, so they can be removed by
 *  literal match. Verified across all 20 dialogue-bearing nodes: every bubble
 *  is found in its own message. If a string ever stops matching, this reports
 *  it rather than silently shipping a duplicate.
 */
class BubblePolicy {
    constructor(file) {
        this.file = file || path.join(__dirname, '..', '..', '..',
            'tools', 'visual', 'bubble_nodes.json');
        let cfg = { nodes: [] };
        try {
            cfg = JSON.parse(fs.readFileSync(this.file, 'utf8'));
        } catch {
            // No config is a valid state: it means no node uses balloons.
        }
        this.nodes = new Set(cfg.nodes || []);
        this.delivery = cfg.delivery || {};
    }

    /** Global override wins, so IRX_SCENE_BUBBLES still works for comparing the
     *  two treatments on every node at once.
     *
     *  variantIndex is optional and only narrows: `s1d4_close#1` enables the
     *  dialogue on that message variant alone, while the bare node id enables
     *  every variant, exactly as before. Needed because a node's variants can
     *  carry different lines - `s1d4_close` says nothing in its base message and
     *  two different things in its two variants. */
    wants(nodeId, override, variantIndex) {
        if (override === true || override === false) return override;
        if (variantIndex !== null && variantIndex !== undefined
            && this.nodes.has(`${nodeId}#${variantIndex}`)) return true;
        return this.nodes.has(nodeId);
    }

    /** How this scenario's dialogue reaches the player.
     *
     *  'baked'  - balloons drawn inside the artwork by the renderer. The 2B
     *             treatment, and still what The Secret ships.
     *  'native' - the same lines, stripped from the prose exactly as the baked
     *             path strips them, handed to the client to draw at the mouth.
     *             The artwork stays text-free, so the line reflows, scales with
     *             the OS text size and survives a camera that crops the canvas.
     *
     *  Per scenario rather than global because it is a presentation decision per
     *  district, and because it lets The Streets move without touching a single
     *  frame of the other two. */
    deliveryFor(scenarioId) {
        return this.delivery[scenarioId] === 'native' ? 'native' : 'baked';
    }

    /** The message with the balloon dialogue taken out.
     *
     *  Returns { message, removed, complete }. `complete` is false if any bubble
     *  string was not found, which means the scenario prose and the render block
     *  have drifted apart — the caller should fall back to prose rather than
     *  ship a half-deduplicated message. */
    stripDialogue(message, bubbles) {
        if (!message || !bubbles || !bubbles.length) {
            return { message, removed: 0, complete: false };
        }
        let out = message;
        let removed = 0;
        for (const b of bubbles) {
            const text = (b && b.text) || '';
            if (!text) continue;
            // quoted form first: the message writes dialogue inside quotation marks
            // and removing the quotes too avoids leaving an orphaned pair
            const quoted = `"${text}"`;
            if (out.includes(quoted)) {
                out = out.replace(quoted, '');
                removed++;
            } else if (out.includes(text)) {
                out = out.replace(text, '');
                removed++;
            }
        }
        const cleaned = out
            .replace(/[ \t]+\n/g, '\n')
            // a line lifted from the FRONT of a paragraph leaves the space that
            // followed it; one lifted from the middle leaves a double space
            .replace(/\n[ \t]+/g, '\n')
            .replace(/[ \t]{2,}/g, ' ')
            .replace(/\n{3,}/g, '\n\n')
            .trim();
        return {
            message: cleaned,
            removed,
            complete: removed === bubbles.filter(b => b && b.text).length,
        };
    }

    get stats() {
        return { bubbleNodes: this.nodes.size, source: this.file };
    }
}

module.exports = { BubblePolicy };