const express = require("express");
const { getRootView, listScenarios } = require("../services/personaService");
const { resolveChoice } = require("../services/evaluationService");
const { logResult } = require("../services/resultsLog");

const router = express.Router();

// Default when no scenarioId is requested at all. This is the ONLY thing
// that matters for a real "daily scenario" later - for now it's just a
// fallback, since the dev picker (GET /list) is the normal way to reach
// anything other than the default.
const DEFAULT_SCENARIO_ID = "the_prince";

// Dev/testing: lists every scenario on disk so a picker UI can jump
// straight into any of them without editing code each time one is added.
router.get("/list", (req, res) => {
  res.json(listScenarios());
});

router.get("/today", (req, res) => {
  const requestedId = req.query.scenarioId;
  const scenarioId = typeof requestedId === "string" && requestedId.length > 0
      ? requestedId
      : DEFAULT_SCENARIO_ID;

  const view = getRootView(scenarioId);
  if (!view) return res.status(404).json({ error: `Unknown scenario: ${scenarioId}` });
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