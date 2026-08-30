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

function matchesAll(when, state) {
  if (!when) return true;
  for (const [key, value] of Object.entries(when)) {
    if (!(key in state)) return false;
    if (state[key] !== value) return false;
  }
  return true;
}

function matchesAny(whenArray, state) {
  if (!whenArray || whenArray.length === 0) return true;
  return whenArray.some((w) => matchesAll(w, state));
}

function resolveNodeContent(node, state) {
  const resolved = {};

  // The INDEX matters, not just the text: the visual layer resolves its own
  // block per variant, and the picture has to agree with the prose. Without
  // this, jessica_reacts_hold renders Jessica open-faced on the judgedFirst
  // path — the exact beat the variant exists to carry.
  resolved.variantIndex = null;

  if (Array.isArray(node.messageVariants)) {
    const idx = node.messageVariants.findIndex((v) => matchesAll(v.when, state));
    resolved.variantIndex = idx >= 0 ? idx : null;
    resolved.message = idx >= 0 ? node.messageVariants[idx].message : node.message;
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

let _render = null;
let _blocks = null;
function renderer() {
  if (_render === null) {
    const { RenderService } = require("./renderService");
    const { RenderBlocks } = require("./render/renderBlocks");
    // IRX_SCENE_BUBBLES=1 puts the dialogue inside the artwork instead.
    // Default off: the client already renders the prose natively, and drawing
    // it twice is worse than either option on its own.
    _render = new RenderService({
      includeBubbles: process.env.IRX_SCENE_BUBBLES === '1',
    });
    _blocks = new RenderBlocks();
  }
  return { render: _render, blocks: _blocks };
}

/** Composed artwork for a node, or null when it has none.
 *
 *  Lives here because publicNode is already the one place a node is reduced to
 *  what the client may see, and a picture is presentation. The client receives
 *  an SVG and head coordinates - never state, never the variant index that
 *  chose them. */
function renderFor(nodeId, variantIndex) {
  try {
    const { render, blocks } = renderer();
    const block = blocks.blockFor(nodeId, variantIndex);
    if (!block) return null;                 // messages mode, or another scenario
    return render.render(block, { nodeId });
  } catch (e) {
    // A node the visual contract refuses to compose must not take the prose
    // down with it. act3b_alex_processes resolves 4 bubbles against a cap of 3
    // and is a known Phase 3 content issue.
    console.warn(`[render] ${nodeId}: ${e.code || e.name} - ${e.message}`);
    return null;
  }
}

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
    render: renderFor(nodeId, resolved.variantIndex),
  };
}

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

/** Boot/health check for the render layer. */
function renderHealth() {
  const { render, blocks } = renderer();
  return { ...render.stats, renderBlocks: blocks.stats };
}

module.exports = {
  renderHealth,
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