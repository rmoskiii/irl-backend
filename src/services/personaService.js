const fs = require("fs");
const path = require("path");

const SCENARIOS_DIR = path.join(__dirname, "..", "data", "scenarios");

function loadScenario(scenarioId) {
  const filePath = path.join(SCENARIOS_DIR, `${scenarioId}.json`);
  if (!fs.existsSync(filePath)) return null;
  return JSON.parse(fs.readFileSync(filePath, "utf-8"));
}

// Strips a node down to what the client is allowed to see - message + choice
// labels, never scores/consequence/next/terminal.
function publicNode(nodeId, node) {
  return {
    nodeId,
    message: node.message,
    choices: node.choices.map((c) => ({ id: c.id, label: c.label })),
  };
}

function getRootView(scenarioId) {
  const scenario = loadScenario(scenarioId);
  if (!scenario) return null;
  const rootNode = scenario.nodes[scenario.rootNode];
  return {
    scenarioId: scenario.id,
    title: scenario.title,
    district: scenario.district,
    difficulty: scenario.difficulty,
    persona: scenario.persona,
    node: publicNode(scenario.rootNode, rootNode),
  };
}

module.exports = { loadScenario, getRootView, publicNode };