'use strict';

/** Thrown when a node resolves more bubbles than the bubble contract allows.
 *  Deliberately fatal: a silently overflowing stack is worse than a build error,
 *  and the fix belongs in Phase 3 content, not in the renderer. */
class MaxPerNodeExceeded extends Error {
    constructor(nodeId, count, cap) {
        super(`node '${nodeId}' resolves ${count} bubbles; maxPerNode is ${cap}. ` +
            `Phase 3 content issue - split or compress the dialogue in the scenario. ` +
            `Do not raise maxPerNode to make it compose.`);
        this.name = 'MaxPerNodeExceeded';
        this.code = 'MAX_PER_NODE_EXCEEDED';
        this.nodeId = nodeId; this.count = count; this.cap = cap;
    }
}
class MissingAsset extends Error {
    constructor(path) { super(`missing asset: ${path}`); this.name = 'MissingAsset'; this.code = 'MISSING_ASSET'; }
}
class MissingLayerGroup extends Error {
    constructor(asset, group) {
        super(`${asset}: missing layer group '${group}'`);
        this.name = 'MissingLayerGroup'; this.code = 'MISSING_LAYER_GROUP';
    }
}
class NoPlacementForSlot extends Error {
    constructor(slot) { super(`bubbles: no placement defined for slot '${slot}'`); this.name = 'NoPlacementForSlot'; this.code = 'NO_PLACEMENT_FOR_SLOT'; }
}
class NoSpeakerTarget extends Error {
    constructor(nodeId) {
        super(`bubbles: node '${nodeId}' has no cast and no bubbleSpeaker, so the tail has no target`);
        this.name = 'NoSpeakerTarget'; this.code = 'NO_SPEAKER_TARGET';
    }
}
module.exports = { MaxPerNodeExceeded, MissingAsset, MissingLayerGroup, NoPlacementForSlot, NoSpeakerTarget };