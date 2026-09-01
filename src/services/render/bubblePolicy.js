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
    }

    /** Global override wins, so IRX_SCENE_BUBBLES still works for comparing the
     *  two treatments on every node at once. */
    wants(nodeId, override) {
        if (override === true || override === false) return override;
        return this.nodes.has(nodeId);
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