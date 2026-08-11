const { loadScenario } = require("./personaService");

// v0: pure lookup against the developer-authored rubric baked into the
// scenario JSON. No AI judgment call involved - this stays deterministic
// even after personaService starts using a live model for reaction text.
function scoreChoice(scenarioId, choiceId) {
  const scenario = loadScenario(scenarioId);
  if (!scenario) return null;
  const choice = scenario.choices.find((c) => c.id === choiceId);
  if (!choice) return null;
  return {
    scores: choice.scores,
    outcomeExplanation: scenario.outcome.explanation,
  };
}

module.exports = { scoreChoice };
