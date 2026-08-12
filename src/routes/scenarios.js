const express = require("express");
const { getRootView } = require("../services/personaService");
const { resolveChoice } = require("../services/evaluationService");
const { logResult } = require("../services/resultsLog");

const router = express.Router();

// Hardcoded to one scenario for now. Add ids here as new scenario JSON
// files land in data/scenarios/ - a real "daily scenario" rotation is a
// post-validation feature, not a v0 one.
const SCENARIO_ROTATION = ["the_prince"];

router.get("/today", (req, res) => {
  const scenarioId = SCENARIO_ROTATION[0];
  const view = getRootView(scenarioId);
  if (!view) return res.status(404).json({ error: "No scenario available." });
  res.json(view);
});

router.post("/respond", (req, res) => {
  const { scenarioId, nodeId, choiceId, runningTotal, testerId } = req.body;

  if (!scenarioId || !nodeId || !choiceId) {
    return res.status(400).json({ error: "scenarioId, nodeId and choiceId are required." });
  }

  const result = resolveChoice({ scenarioId, nodeId, choiceId, runningTotal });
  if (!result) {
    return res.status(404).json({ error: "Unknown scenario, node or choice." });
  }

  logResult({ testerId, scenarioId, nodeId, choiceId, scores: result.scores, terminal: result.terminal });

  res.json(result);
});

module.exports = router;