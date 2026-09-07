/* Layer B - graph and state simulation.
 *
 * Drives evaluationService.resolveChoice, the same entry point the /respond
 * route uses. Nothing here models setState, derivedState, nextRules ordering or
 * terminal detection: it asks the engine and records what came back. A
 * validator that reimplements the engine is a second engine, and the day they
 * disagree is the day the validator starts lying.
 *
 * Exploration is breadth-first over (nodeId, canonical state). Two paths that
 * arrive at the same node carrying the same state are the same situation, so
 * the frontier collapses instead of exploding.
 */

const path = require("path");

const ROOT = path.join(__dirname, "..");

// personaService FIRST, and memoise loadScenario before evaluationService is
// loaded. evaluationService destructures loadScenario at require time, so the
// wrapper has to be in place before that happens.
//
// Why: loadScenario is readFileSync + JSON.parse, and resolveChoice calls it on
// every single turn. That is correct for a stateless service handling one
// request; for a walk of half a million turns it is the entire runtime. A
// 67 KB scenario re-parsed per step measured at 0.7 ms/step - 275 seconds to
// get four days in. Memoising by scenarioId changes no semantics: scenario
// files do not change mid-walk. Production is untouched.
const persona = require(path.join(ROOT, "src", "services", "personaService"));

const _scenarioCache = new Map();
const _loadScenario = persona.loadScenario;
persona.loadScenario = function cachedLoadScenario(scenarioId) {
    if (!_scenarioCache.has(scenarioId)) _scenarioCache.set(scenarioId, _loadScenario(scenarioId));
    return _scenarioCache.get(scenarioId);
};

const { resolveChoice } = require(path.join(ROOT, "src", "services", "evaluationService"));

const { eachWhen, LIMITS } = require("./validate_scenario");

const ZERO = { savvy: 0, streetSmarts: 0, integrity: 0 };
const DEFAULT_CAP = 250000;

function canonical(state) {
    return JSON.stringify(Object.keys(state).sort().map((k) => [k, state[k]]));
}

/** Walk every reachable (node, state) pair.
 *
 *  Returns the raw observations. Deciding what is wrong is the caller's job -
 *  this function only reports what the engine actually did.
 */
function explore(scenario, cap = DEFAULT_CAP) {
    const scenarioId = scenario.id;
    const start = persona.initialState(scenario);

    const seen = new Set();
    const queue = [{ nodeId: scenario.rootNode, state: start, depth: 0 }];
    seen.add(scenario.rootNode + "|" + canonical(start));

    const reachedNodes = new Set([scenario.rootNode]);
    const takenChoices = new Set();
    const offeredChoices = new Set();
    const statesByNode = new Map();
    const allStates = [];
    const trajectories = new Set();
    const terminals = new Set();
    const dayEdges = new Map(); // day -> Set of opening node ids on the next day
    const daysSeen = new Set();

    let steps = 0;
    let capped = false;
    let maxDepth = 0;

    // The composer will try to load assets that may not be present in a checkout
    // without them, and warns on every miss. renderFor catches, so the walk is
    // correct either way; the noise just drowns the report.
    const warn = console.warn;
    console.warn = () => {};

    try {
        while (queue.length) {
            if (steps++ > cap) {
                capped = true;
                break;
            }
            const { nodeId, state, depth } = queue.shift();
            maxDepth = Math.max(maxDepth, depth);

            const node = scenario.nodes[nodeId];
            if (!node) continue;
            if (typeof node.day === "number") daysSeen.add(node.day);

            if (!statesByNode.has(nodeId)) statesByNode.set(nodeId, []);
            statesByNode.get(nodeId).push(state);
            allStates.push(state);

            // Offered = what publicNode would show. This is the real requires filter.
            const visible = (node.choices || []).filter(
                (c) => !c.requires || persona.matchesAny(c.requires, state)
            );
            for (const choice of visible) offeredChoices.add(`${nodeId}.${choice.id}`);

            for (const choice of visible) {
                const result = resolveChoice({
                    scenarioId,
                    nodeId,
                    choiceId: choice.id,
                    runningTotal: ZERO,
                    state,
                });
                if (!result) continue;
                takenChoices.add(`${nodeId}.${choice.id}`);

                if (result.terminal) {
                    terminals.add(`${nodeId}.${choice.id}`);
                    const key = scenario.outcomeKey;
                    if (key && result.state && result.state[key] !== undefined) {
                        trajectories.add(result.state[key]);
                    }
                    continue;
                }

                const nextId = result.node && result.node.nodeId;
                if (!nextId) continue;
                reachedNodes.add(nextId);

                const nextNode = scenario.nodes[nextId];
                if (
                    typeof node.day === "number" &&
                    typeof nextNode?.day === "number" &&
                    nextNode.day !== node.day
                ) {
                    if (!dayEdges.has(node.day)) dayEdges.set(node.day, new Set());
                    dayEdges.get(node.day).add(nextId);
                }

                const stamp = nextId + "|" + canonical(result.state);
                if (!seen.has(stamp)) {
                    seen.add(stamp);
                    queue.push({ nodeId: nextId, state: result.state, depth: depth + 1 });
                }
            }
        }
    } finally {
        console.warn = warn;
    }

    return {
        reachedNodes,
        offeredChoices,
        takenChoices,
        statesByNode,
        allStates,
        trajectories,
        terminals,
        dayEdges,
        daysSeen,
        steps,
        capped,
        maxDepth,
        distinctStates: seen.size,
    };
}

/** Seeded PRNG. A validator that returns different answers on different runs is
 *  not a validator, so the sampler is deterministic. */
function rng(seed) {
    let x = seed >>> 0;
    return () => ((x = (x * 1664525 + 1013904223) >>> 0) / 4294967296);
}

function emptyWalk() {
    return {
        reachedNodes: new Set(), offeredChoices: new Set(), takenChoices: new Set(),
        allStates: [], trajectories: new Set(), terminals: new Set(),
        dayEdges: new Map(), daysSeen: new Set(), steps: 0, capped: false,
        maxDepth: 0, distinctStates: 0, samples: 0,
    };
}

/** Random complete playthroughs, root to terminal.
 *
 *  Exhaustive BFS proves unreachability but cannot finish: a seven-day graph
 *  with sixteen integer keys reaches half a million distinct states before it
 *  gets out of Day 5. Sampling is the reverse trade - it cannot prove anything
 *  unreachable, but it witnesses reachability cheaply and it gets to Day 7,
 *  which is where the trajectories and terminals live.
 *
 *  The two are combined in layerB, and the distinction is load-bearing:
 *  a witness is proof, an absence after a capped walk is not.
 */
function sample(scenario, runs = 4000, seed = 20260907, maxDepth = 200) {
    const scenarioId = scenario.id;
    const rand = rng(seed);
    const w = emptyWalk();
    w.samples = runs;

    const warn = console.warn;
    console.warn = () => {};
    try {
        for (let run = 0; run < runs; run++) {
            let state = persona.initialState(scenario);
            let nodeId = scenario.rootNode;
            w.reachedNodes.add(nodeId);

            for (let depth = 0; depth < maxDepth; depth++) {
                const node = scenario.nodes[nodeId];
                if (!node) break;
                if (typeof node.day === "number") w.daysSeen.add(node.day);
                w.allStates.push(state);

                const visible = (node.choices || []).filter(
                    (c) => !c.requires || persona.matchesAny(c.requires, state)
                );
                if (!visible.length) break;
                for (const c of visible) w.offeredChoices.add(`${nodeId}.${c.id}`);

                const choice = visible[Math.floor(rand() * visible.length)];
                const result = resolveChoice({
                    scenarioId, nodeId, choiceId: choice.id, runningTotal: ZERO, state,
                });
                if (!result) break;
                w.takenChoices.add(`${nodeId}.${choice.id}`);
                w.steps++;

                if (result.terminal) {
                    w.terminals.add(`${nodeId}.${choice.id}`);
                    const key = scenario.outcomeKey;
                    if (key && result.state && result.state[key] !== undefined) {
                        w.trajectories.add(result.state[key]);
                        w.allStates.push(result.state);
                    }
                    break;
                }
                const nextId = result.node && result.node.nodeId;
                if (!nextId) break;
                const nextNode = scenario.nodes[nextId];
                if (typeof node.day === "number" && typeof nextNode?.day === "number" &&
                    nextNode.day !== node.day) {
                    if (!w.dayEdges.has(node.day)) w.dayEdges.set(node.day, new Set());
                    w.dayEdges.get(node.day).add(nextId);
                }
                w.reachedNodes.add(nextId);
                w.maxDepth = Math.max(w.maxDepth, depth);
                state = result.state;
                nodeId = nextId;
            }
        }
    } finally {
        console.warn = warn;
    }
    return w;
}

function merge(a, b) {
    const out = emptyWalk();
    for (const k of ["reachedNodes", "offeredChoices", "takenChoices", "trajectories",
        "terminals", "daysSeen"]) {
        out[k] = new Set([...a[k], ...b[k]]);
    }
    out.allStates = a.allStates.concat(b.allStates);
    out.dayEdges = new Map();
    for (const src of [a.dayEdges, b.dayEdges]) {
        for (const [day, set] of src) {
            if (!out.dayEdges.has(day)) out.dayEdges.set(day, new Set());
            for (const v of set) out.dayEdges.get(day).add(v);
        }
    }
    out.steps = a.steps + b.steps;
    out.capped = a.capped || b.capped;
    out.maxDepth = Math.max(a.maxDepth, b.maxDepth);
    out.distinctStates = a.distinctStates;
    out.samples = a.samples + b.samples;
    return out;
}

function layerB(scenario, report, ctx) {
    const id = scenario.id;
    const streets = ctx.profile === "streets";
    const bfs = explore(scenario, ctx.cap);
    const sampled = sample(scenario, ctx.samples ?? 4000);
    const walk = merge(bfs, sampled);
    ctx.walks = ctx.walks || {};
    ctx.walks[id] = walk;

    // SOUNDNESS. A capped walk has not searched the whole space, so "never
    // witnessed" stops meaning "impossible". Everything that reports an absence -
    // B01, B02, B04, B07, B08 - is downgraded to a warning in that case. A
    // witness is still proof either way; only the negative claim weakens.
    const partial = bfs.capped;
    const absent = (rule, where, message) => {
        if (partial) {
            report.warn(rule, id, where, `${message} (not witnessed in ${walk.steps} turns ` +
                `across ${sampled.samples} sampled runs and a capped exhaustive walk - ` +
                `unproven, not disproven)`);
        } else {
            report.fail(rule, id, where, message);
        }
    };

    if (partial) {
        report.warn(
            "B00", id, "simulation",
            `exhaustive walk hit the cap of ${ctx.cap} steps at ${bfs.distinctStates} ` +
            `distinct states; absence findings below are warnings, not failures`
        );
    }

    // B09 - at least one path must end
    if (walk.terminals.size === 0) {
        report.fail("B09", id, "simulation", "no reachable path reaches a terminal choice");
    }

    // B01 - unreachable nodes
    for (const nodeId of Object.keys(scenario.nodes || {})) {
        if (!walk.reachedNodes.has(nodeId)) {
            absent("B01", `nodes.${nodeId}`, "node is unreachable from rootNode");
        }
    }

    // B02 - a choice that is never offered in any reachable state is a gate that
    // can never open. Its setState, prose and consequence are all dead.
    for (const [nodeId, node] of Object.entries(scenario.nodes || {})) {
        if (!walk.reachedNodes.has(nodeId)) continue;
        for (const choice of node.choices || []) {
            if (!walk.offeredChoices.has(`${nodeId}.${choice.id}`)) {
                absent("B02", `nodes.${nodeId}.choices.${choice.id}`,
                    "choice is never offered; its requires cannot be satisfied in any reachable state");
            }
        }
    }

    // B08 - the deep one. A `when` that no reachable state satisfies is a variant
    // that never shows, a rule that never fires, a consequence that was authored
    // and then quietly disconnected. Catches typos the static pass cannot, because
    // the key and value are both individually legal.
    //
    // Skipped for outcome-time matchers, which run against terminal state carrying
    // outcomeKey and are covered by B04.
    const terminalScoped = new Set(["outcomeRules", "reflections", "aftermath", "finalMessage"]);
    eachWhen(scenario, (when, where) => {
        const top = where.split(".")[0];
        if (terminalScoped.has(top)) return;
        const satisfiable = walk.allStates.some((state) => persona.matchesAll(when, state));
        if (!satisfiable) {
            absent("B08", where,
                `no reachable state satisfies ${JSON.stringify(when)}; this condition never fires`);
        }
    });

    // B04 - trajectory reachability
    const produced = new Set((scenario.outcomeRules || []).map((r) => r.value));
    if (scenario.outcomeDefault) produced.add(scenario.outcomeDefault);
    for (const t of produced) {
        if (!walk.trajectories.has(t)) {
            absent("B04", `outcome.${t}`, "no reachable path produces this trajectory");
        }
    }

    // B07 - a key written only by choices that can never be taken
    const live = new Set();
    for (const [nodeId, node] of Object.entries(scenario.nodes || {})) {
        for (const choice of node.choices || []) {
            if (!walk.offeredChoices.has(`${nodeId}.${choice.id}`)) continue;
            for (const key of Object.keys(choice.setState || {})) live.add(key);
        }
    }
    for (const [nodeId, node] of Object.entries(scenario.nodes || {})) {
        for (const choice of node.choices || []) {
            for (const key of Object.keys(choice.setState || {})) {
                if (!live.has(key)) {
                    absent("B07", `stateSchema.${key}`,
                        "written only by choices that are never offered; the mutation can never occur");
                    live.add(key); // report once
                }
            }
        }
    }

    if (!streets) return;

    // B05 - canonical day opening. Multiple edges may converge on one opening
    // node; two different openings make the resume checkpoint ambiguous and force
    // both to be authored as cold opens.
    for (const [day, openings] of [...walk.dayEdges].sort((a, b) => a[0] - b[0])) {
        if (openings.size > 1) {
            report.fail(
                "B05",
                id,
                `day ${day}`,
                `resolves to ${openings.size} different day-${day + 1} opening nodes ` +
                `(${[...openings].join(", ")}); exactly one canonical opening is required`
            );
        }
    }

    // B06 - every day must be on every route
    for (let day = 1; day <= LIMITS.finalDay; day++) {
        if (!walk.daysSeen.has(day)) {
            report.fail("B06", id, `day ${day}`, "no reachable node carries this day");
        }
    }
}

module.exports = { explore, sample, merge, layerB, canonical, DEFAULT_CAP };