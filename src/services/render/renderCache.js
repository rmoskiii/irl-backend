'use strict';

/** LRU keyed by the resolved render-block hash. Two scenario states that
 *  resolve to the same visual share one entry - that is the whole point of
 *  hashing the block rather than nodeId+variantIndex. */
class RenderCache {
    constructor(max = 256) { this.max = max; this.map = new Map(); this.hits = 0; this.misses = 0; }
    get(k) {
        if (!this.map.has(k)) { this.misses++; return undefined; }
        const v = this.map.get(k);
        this.map.delete(k); this.map.set(k, v);   // refresh recency
        this.hits++;
        return v;
    }
    set(k, v) {
        if (this.map.has(k)) this.map.delete(k);
        this.map.set(k, v);
        if (this.map.size > this.max) this.map.delete(this.map.keys().next().value);
        return v;
    }
    get stats() { return { size: this.map.size, hits: this.hits, misses: this.misses }; }
}
module.exports = { RenderCache };