const {
  loadScenario,
  publicNode,
  matchesAll,
  matchesAny,
  resolveNodeContent,
} = require("./personaService");

function applySetState(state, setState, stateSchema) {
  if (!setState) return state;
  const next = { ...state };
  for (const [key, value] of Object.entries(setState)) {
    const schema = stateSchema[key];
    if (!schema) continue;
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

// Legacy path — score-threshold lookup. Kept only for scenarios that
// haven't been migrated to `reflections` yet (Prince, Bank).
function pickOutcomeText(scenario, finalTotal) {
  const tiers = scenario.outcomeTiers || [];
  const tier = tiers.find((t) => finalTotal >= t.minTotal);
  return tier ? tier.explanation : (tiers[tiers.length - 1]?.explanation || "");
}

// Reflection path — pattern-matched prose instead of a graded number.
// Walks `reflections` in declaration order, first fully-matching `when`
// wins, same semantics as messageVariants/threadVariants. Falls back to
// `defaultReflection` if nothing matches (shouldn't happen in practice
// since trajectory is always set, but the engine never leaves a terminal
// turn with no reflection at all).
function pickReflection(scenario, state) {
  const reflections = scenario.reflections || [];
  const match = reflections.find((r) => matchesAll(r.when, state));
  if (match) return { title: match.title, text: match.text };
  const fallback = scenario.defaultReflection || {};
  return { title: fallback.title || "", text: fallback.text || "" };
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

  if (choice.requires && !matchesAny(choice.requires, currentState)) {
    return { error: "Choice not available in current state." };
  }

  const nextState = applySetState(currentState, choice.setState, stateSchema);

  const delta = choice.scores || { savvy: 0, streetSmarts: 0, integrity: 0 };
  const reasons = choice.reasons || {};
  const beat = choice.beat || null;

  let nextNodeId;
  if (Array.isArray(choice.nextRules)) {
    const rule = choice.nextRules.find((r) => matchesAll(r.when, nextState));
    if (rule) nextNodeId = rule.next;
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

    // scores/reasons still flow back regardless of mode — the client
    // applies these to the cross-scenario home-screen stat pool on every
    // turn, independent of how (or whether) this scenario grades itself.
    const usesReflections =
        Array.isArray(scenario.reflections) && scenario.reflections.length > 0;

    let outcomeFields;
    if (usesReflections) {
      const reflection = pickReflection(scenario, nextState);
      outcomeFields = {
        reflectionTitle: reflection.title,
        reflectionText: reflection.text,
      };
    } else {
      const priorTotal = sumScores(
          runningTotal || { savvy: 0, streetSmarts: 0, integrity: 0 }
      );
      const finalTotal = priorTotal + sumScores(delta);
      outcomeFields = { outcomeExplanation: pickOutcomeText(scenario, finalTotal) };
    }

    return {
      scores: delta,
      reasons,
      beat,
      terminal: true,
      state: nextState,
      consequence: choice.terminal.consequence,
      landing: choice.terminal.landing,
      ...outcomeFields,
    };
  }

  if (!nextNodeId) {
    return { error: `No next node resolved for choice ${choiceId}.` };
  }

  const nextNode = scenario.nodes[nextNodeId];
  if (!nextNode) return { error: `Unknown next node: ${nextNodeId}.` };

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