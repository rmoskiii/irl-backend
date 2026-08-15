const {
  loadScenario,
  publicNode,
  matchesAll,
  matchesAny,
  resolveNodeContent,
} = require("./personaService");

// Integer keys in the schema are additive deltas (clamped to `range` if
// declared). Enum and bool keys are assignments. Reading the type off the
// schema — rather than sniffing the value — keeps `jordanTrust: 0` in a
// setState block from being mistaken for a bool assignment.
function applySetState(state, setState, stateSchema) {
  if (!setState) return state;
  const next = { ...state };
  for (const [key, value] of Object.entries(setState)) {
    const schema = stateSchema[key];
    if (!schema) continue; // forgiving of authoring typos
    if (schema.type === "int") {
      next[key] = (next[key] || 0) + value;
      if (Array.isArray(schema.range)) {
        const [min, max] = schema.range;
        next[key] = Math.max(min, Math.min(max, next[key]));
      }
    } else {
      next[key] = value;
    }
  }
  return next;
}

function sumScores(delta) {
  return (delta.savvy || 0) + (delta.streetSmarts || 0) + (delta.integrity || 0);
}

function pickOutcomeText(scenario, finalTotal) {
  const tier = scenario.outcomeTiers.find((t) => finalTotal >= t.minTotal);
  return tier
      ? tier.explanation
      : scenario.outcomeTiers[scenario.outcomeTiers.length - 1].explanation;
}

function resolveChoice({ scenarioId, nodeId, choiceId, runningTotal, state }) {
  const scenario = loadScenario(scenarioId);
  if (!scenario) return null;

  const node = scenario.nodes[nodeId];
  if (!node) return null;

  const choice = node.choices.find((c) => c.id === choiceId);
  if (!choice) return null;

  const stateSchema = scenario.stateSchema || {};
  const currentState = state || {};

  // If the choice has `requires` and none of its when-blocks match, it
  // should never have been offered. Reject rather than silently proceed.
  if (choice.requires && !matchesAny(choice.requires, currentState)) {
    return { error: "Choice not available in current state." };
  }

  // 1. setState first. Everything downstream — variants, next-node
  //    rendering — sees the updated state.
  const nextState = applySetState(currentState, choice.setState, stateSchema);

  const delta = choice.scores || { savvy: 0, streetSmarts: 0, integrity: 0 };
  const reasons = choice.reasons || {};
  const beat = choice.beat || null;

  // 2. Resolve navigation. nextRules in declaration order, first match
  //    wins. A matched rule with `next: null` means "resolve terminal".
  //    If no rule matches, fall back to choice.next. If neither exists,
  //    fall through to terminal.
  let nextNodeId; // undefined = unresolved; null = "use terminal"; string = navigate
  if (Array.isArray(choice.nextRules)) {
    const rule = choice.nextRules.find((r) => matchesAll(r.when, nextState));
    if (rule) nextNodeId = rule.next; // could be null
  }
  if (nextNodeId === undefined && choice.next) {
    nextNodeId = choice.next;
  }

  const isTerminal =
      nextNodeId === null || (nextNodeId === undefined && choice.terminal);

  if (isTerminal) {
    if (!choice.terminal) {
      return { error: `Rule matched null-next but choice ${choiceId} has no terminal block.` };
    }
    const priorTotal = sumScores(
        runningTotal || { savvy: 0, streetSmarts: 0, integrity: 0 }
    );
    const finalTotal = priorTotal + sumScores(delta);
    return {
      scores: delta,
      reasons,
      beat,
      terminal: true,
      state: nextState,
      consequence: choice.terminal.consequence,
      landing: choice.terminal.landing,
      outcomeExplanation: pickOutcomeText(scenario, finalTotal),
    };
  }

  if (!nextNodeId) {
    return { error: `No next node resolved for choice ${choiceId}.` };
  }

  const nextNode = scenario.nodes[nextNodeId];
  if (!nextNode) return { error: `Unknown next node: ${nextNodeId}.` };

  // 3. Variants on the destination node resolve against the new state.
  //    This is the ordering the whole scenario depends on: get this
  //    wrong and act2_probe_response:hold_line silently renders Act 3's
  //    default text instead of the "Alex is suspicious" version.
  const content = resolveNodeContent(nextNode, nextState);

  return {
    scores: delta,
    reasons,
    beat,
    terminal: false,
    state: nextState,
    node: publicNode(nextNodeId, nextNode, nextState, content),
  };
}

module.exports = { resolveChoice };