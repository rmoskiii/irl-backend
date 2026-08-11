const fs = require("fs");
const path = require("path");

const SCENARIOS_DIR = path.join(__dirname, "..", "data", "scenarios");

function loadScenario(scenarioId) {
  const filePath = path.join(SCENARIOS_DIR, `${scenarioId}.json`);
  if (!fs.existsSync(filePath)) return null;
  return JSON.parse(fs.readFileSync(filePath, "utf-8"));
}

function getPublicScenario(scenarioId) {
  const scenario = loadScenario(scenarioId);
  if (!scenario) return null;
  // Strip scores/reactions/outcome so the client never sees the rubric.
  return {
    id: scenario.id,
    title: scenario.title,
    district: scenario.district,
    difficulty: scenario.difficulty,
    persona: scenario.persona,
    opening: scenario.opening,
    choices: scenario.choices.map((c) => ({ id: c.id, label: c.label })),
  };
}

// v0: scripted lookup, no live model call. Swap this function's body for an
// Anthropic API call (Haiku 4.5 is enough) when you want reaction variety -
// nothing in routes/services.js needs to change, the signature stays the same.
function getReaction(scenarioId, choiceId) {
  const scenario = loadScenario(scenarioId);
  if (!scenario) return null;
  const choice = scenario.choices.find((c) => c.id === choiceId);
  if (!choice) return null;
  return choice.reaction;
}

module.exports = { loadScenario, getPublicScenario, getReaction };
