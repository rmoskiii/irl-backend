const fs = require("fs");
const path = require("path");

const SCENARIOS_DIR = path.join(__dirname, "..", "data", "scenarios");

function loadScenario(scenarioId) {
  const filePath = path.join(SCENARIOS_DIR, `${scenarioId}.json`);
  if (!fs.existsSync(filePath)) return null;
  return JSON.parse(fs.readFileSync(filePath, "utf-8"));
}

// Strips a node down to what the client is allowed to see - message,
// choice labels, and (if present) the presentation block that tells the
// client how to render this beat visually. Never scores/consequence/
// next/terminal.
function publicNode(nodeId, node) {
  return {
    nodeId,
    message: node.message,
    presentation: node.presentation || null,
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

// Dev/testing convenience: every scenario JSON file on disk, summarised.
// This is what powers the debug-only scenario picker so you don't have to
// hand-edit a rotation array every time a new scenario is added.
function listScenarios() {
  const files = fs.readdirSync(SCENARIOS_DIR).filter((f) => f.endsWith(".json"));
  return files
      .map((file) => {
        const scenario = JSON.parse(fs.readFileSync(path.join(SCENARIOS_DIR, file), "utf-8"));
        return {
          id: scenario.id,
          title: scenario.title,
          district: scenario.district,
          difficulty: scenario.difficulty,
        };
      })
      .sort((a, b) => a.difficulty - b.difficulty);
}

module.exports = { loadScenario, getRootView, publicNode, listScenarios };