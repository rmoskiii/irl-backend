const { loadScenario, publicNode } = require("./personaService");

function sumScores(delta) {
  return (delta.savvy || 0) + (delta.streetSmarts || 0) + (delta.integrity || 0);
}

function pickOutcomeText(scenario, finalTotal) {
  // outcomeTiers is ordered highest minTotal first - first match wins.
  const tier = scenario.outcomeTiers.find((t) => finalTotal >= t.minTotal);
  return tier ? tier.explanation : scenario.outcomeTiers[scenario.outcomeTiers.length - 1].explanation;
}

// v0: pure lookup + arithmetic against the developer-authored node graph.
// No AI judgment call involved anywhere in scoring - stays deterministic
// even after personaService starts generating persona text live.
//
// runningTotal is what the client has accumulated so far THIS playthrough
// (each stat, unclamped). The backend stays stateless: it never remembers
// where a player is between requests.
function resolveChoice({ scenarioId, nodeId, choiceId, runningTotal }) {
  const scenario = loadScenario(scenarioId);
  if (!scenario) return null;

  const node = scenario.nodes[nodeId];
  if (!node) return null;

  const choice = node.choices.find((c) => c.id === choiceId);
  if (!choice) return null;

  const delta = choice.scores;

  if (choice.terminal) {
    const priorTotal = sumScores(runningTotal || { savvy: 0, streetSmarts: 0, integrity: 0 });
    const finalTotal = priorTotal + sumScores(delta);
    return {
      scores: delta,
      terminal: true,
      consequence: choice.consequence,
      outcomeExplanation: pickOutcomeText(scenario, finalTotal),
    };
  }

  const nextNode = scenario.nodes[choice.next];
  return {
    scores: delta,
    terminal: false,
    node: publicNode(choice.next, nextNode),
  };
}

module.exports = { resolveChoice };