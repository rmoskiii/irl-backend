const express = require("express");
const { getPublicScenario, getReaction } = require("../services/personaService");
const { scoreChoice } = require("../services/evaluationService");
const { logResult } = require("../services/resultsLog");

const router = express.Router();

// Hardcoded to one scenario for now. Add ids here as new scenario JSON
// files land in data/scenarios/ - a real "daily scenario" rotation is a
// post-validation feature, not a v0 one.
const SCENARIO_ROTATION = ["the_prince"];

router.get("/today", (req, res) => {
  const scenarioId = SCENARIO_ROTATION[0];
  const scenario = getPublicScenario(scenarioId);
  if (!scenario) return res.status(404).json({ error: "No scenario available." });
  res.json(scenario);
});

router.post("/respond", (req, res) => {
  const { scenarioId, choiceId, testerId } = req.body;
  if (!scenarioId || !choiceId) {
    return res.status(400).json({ error: "scenarioId and choiceId are required." });
  }

  const reaction = getReaction(scenarioId, choiceId);
  const evaluation = scoreChoice(scenarioId, choiceId);

  if (!reaction || !evaluation) {
    return res.status(404).json({ error: "Unknown scenario or choice." });
  }

  logResult({ testerId, scenarioId, choiceId, scores: evaluation.scores });

  res.json({
    reaction,
    scores: evaluation.scores,
    outcomeExplanation: evaluation.outcomeExplanation,
  });
});

module.exports = router;
