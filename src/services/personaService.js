const fs = require("fs");
const path = require("path");

const SCENARIOS_DIR = path.join(__dirname, "..", "data", "scenarios");

function loadScenario(scenarioId) {
  const filePath = path.join(SCENARIOS_DIR, `${scenarioId}.json`);
  if (!fs.existsSync(filePath)) return null;
  return JSON.parse(fs.readFileSync(filePath, "utf-8"));
}

// Weighted pick over [{ value, weight }]. Weights need not sum to anything
// in particular. Absent/zero weights are treated as 1 so an author can
// write a plain uniform list without ceremony.
function weightedPick(options) {
  const entries = (options || []).map((o) => ({
    value: o.value,
    weight: typeof o.weight === "number" && o.weight > 0 ? o.weight : 1,
  }));
  if (entries.length === 0) return undefined;

  const total = entries.reduce((sum, e) => sum + e.weight, 0);
  let roll = Math.random() * total;

  for (const entry of entries) {
    roll -= entry.weight;
    if (roll <= 0) return entry.value;
  }
  return entries[entries.length - 1].value;
}

// Walk stateSchema once at scenario start, then apply the optional `seed`
// block on top. The client hands the resulting map back on every /respond,
// so the backend stays stateless.
//
// `seed` exists for keys whose value is decided when a playthrough BEGINS
// rather than by anything the player does — The Prince's `truthTrack` is
// the motivating case. Because it lands in ordinary state, every `when`,
// nextRule and variant reads it with no special handling, and the client
// never sees it as anything other than another opaque key.
//
//   "seed": {
//     "truthTrack": { "weighted": [
//       { "value": "C", "weight": 40 },
//       { "value": "B", "weight": 35 },
//       { "value": "A", "weight": 25 }
//     ] }
//   }
//
// Seeding happens ONLY here. A key seeded at root is then carried by the
// courier like any other, so it can't be re-rolled mid-playthrough.
function initialState(scenario) {
  const schema = scenario.stateSchema || {};
  const state = {};

  for (const [key, field] of Object.entries(schema)) {
    state[key] = field.initial;
  }

  for (const [key, spec] of Object.entries(scenario.seed || {})) {
    if (!(key in schema)) continue;

    const picked = Array.isArray(spec.weighted)
        ? weightedPick(spec.weighted)
        : spec.value;

    if (picked !== undefined) state[key] = picked;
  }

  return state;
}

// All key/value pairs must match. Missing key on state = non-match.
// Used by messageVariants/threadVariants (each `when` block) and by
// nextRules (each rule's `when`).
function matchesAll(when, state) {
  if (!when) return true;
  for (const [key, value] of Object.entries(when)) {
    if (!(key in state)) return false;
    if (state[key] !== value) return false;
  }
  return true;
}

// Array of when objects, OR'd. Used by `requires` on a choice only.
// Deliberately different combining rule from matchesAll — kept as a
// separate helper so nobody normalises them together by mistake.
function matchesAny(whenArray, state) {
  if (!whenArray || whenArray.length === 0) return true;
  return whenArray.some((w) => matchesAll(w, state));
}

// Picks the right message/thread for a node given current state. Walks
// variants in declaration order; first `when` that fully matches wins.
// Falls back to base message/thread if none match.
function resolveNodeContent(node, state) {
  const resolved = {};

  if (Array.isArray(node.messageVariants)) {
    const match = node.messageVariants.find((v) => matchesAll(v.when, state));
    resolved.message = match ? match.message : node.message;
  } else if (node.message !== undefined) {
    resolved.message = node.message;
  }

  if (Array.isArray(node.threadVariants)) {
    const match = node.threadVariants.find((v) => matchesAll(v.when, state));
    resolved.thread = match ? match.thread : node.thread;
  } else if (node.thread !== undefined) {
    resolved.thread = node.thread;
  }

  return resolved;
}

// Strips a node to what the client is allowed to see. Choices whose
// `requires` doesn't match current state are filtered out here rather
// than sent-and-hidden — keeps state opaque to the client.
function publicNode(nodeId, node, state, content) {
  const resolved = content || resolveNodeContent(node, state || {});
  const currentState = state || {};

  const visibleChoices = node.choices.filter(
      (c) => !c.requires || matchesAny(c.requires, currentState)
  );

  return {
    nodeId,
    message: resolved.message ?? null,
    thread: resolved.thread ?? null,
    presentation: node.presentation || null,
    reactionDelay: node.reactionDelay || null,
    interstitial: node.interstitial || null,
    choices: visibleChoices.map((c) => ({ id: c.id, label: c.label })),
  };
}

// `revealTiming` moves out of the client's district check and into the
// scenario. Digital used to imply "show per-turn reasons immediately" by
// virtue of not being Neighbourhood; The Prince is Digital but must hide
// them, because visible deltas let a player shop the verification choices
// — which is the exact skill under test. The outcome ledger is unaffected.
//
// "immediate" (default) | "end_only"
function revealTimingFor(scenario) {
  return scenario.scoring?.revealTiming === "end_only"
      ? "end_only"
      : "immediate";
}

function getRootView(scenarioId) {
  const scenario = loadScenario(scenarioId);
  if (!scenario) return null;

  const rootNode = scenario.nodes[scenario.rootNode];
  const state = initialState(scenario);

  return {
    scenarioId: scenario.id,
    title: scenario.title,
    district: scenario.district,
    difficulty: scenario.difficulty,
    persona: scenario.persona,
    revealTiming: revealTimingFor(scenario),
    state,
    node: publicNode(scenario.rootNode, rootNode, state),
  };
}

function listScenarios() {
  const files = fs.readdirSync(SCENARIOS_DIR).filter((f) => f.endsWith(".json"));
  return files
      .map((file) => {
        const s = JSON.parse(
            fs.readFileSync(path.join(SCENARIOS_DIR, file), "utf-8")
        );
        return {
          id: s.id,
          title: s.title,
          district: s.district,
          difficulty: s.difficulty,
        };
      })
      .sort((a, b) => a.difficulty - b.difficulty);
}

module.exports = {
  loadScenario,
  getRootView,
  publicNode,
  listScenarios,
  initialState,
  matchesAll,
  matchesAny,
  resolveNodeContent,
  revealTimingFor,
};