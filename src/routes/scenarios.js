const express = require("express");
const { getRootView, listScenarios, readNode } = require("../services/personaService");
const { resolveChoice } = require("../services/evaluationService");
const { logResult } = require("../services/resultsLog");

const router = express.Router();

// The Secret is the anchor scenario for IRX. Digital-district scenarios
// (The Prince, The Bank) predate the v3 stateful contract and won't
// resolve correctly under this engine until re-authored — they're
// intentionally unreachable from /today for now.
const DEFAULT_SCENARIO = "the_secret";

router.get("/today", (req, res) => {
  const scenarioId = req.query.scenarioId || DEFAULT_SCENARIO;
  const view = getRootView(scenarioId);
  if (!view) return res.status(404).json({ error: "No scenario available." });
  res.json(view);
});

router.get("/list", (req, res) => {
  res.json(listScenarios());
});

// Boot check: confirms the 45 assets and the render blocks actually loaded in
// the deployed environment, and exposes the cache hit rate.
router.get("/render/health", (req, res) => {
  const { renderHealth } = require("../services/personaService");
  res.json(renderHealth());
});

/* Resume. Stateless: the client owns the run, the server owns the content.
 * Takes the raw state a client stored at a day boundary and returns the same
 * publicNode payload /today returns, with derived bands recomputed rather than
 * trusted. SPEC-08. */
router.post("/node", (req, res) => {
  const { scenarioId, nodeId, state } = req.body;

  if (!scenarioId || !nodeId) {
    return res.status(400).json({ error: "scenarioId and nodeId are required." });
  }

  const view = readNode(scenarioId, nodeId, state);
  if (!view) {
    return res.status(404).json({ error: "Unknown scenario or node." });
  }

  res.json(view);
});

router.post("/respond", (req, res) => {
  const { scenarioId, nodeId, choiceId, runningTotal, state, testerId } = req.body;

  if (!scenarioId || !nodeId || !choiceId) {
    return res.status(400).json({ error: "scenarioId, nodeId and choiceId are required." });
  }

  const result = resolveChoice({ scenarioId, nodeId, choiceId, runningTotal, state });
  if (!result) {
    return res.status(404).json({ error: "Unknown scenario, node or choice." });
  }
  if (result.error) {
    return res.status(400).json({ error: result.error });
  }

  logResult({
    testerId,
    scenarioId,
    nodeId,
    choiceId,
    scores: result.scores,
    terminal: result.terminal,
  });

  res.json(result);
});

module.exports = router;