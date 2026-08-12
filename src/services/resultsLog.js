const fs = require("fs");
const path = require("path");

const LOG_PATH = path.join(__dirname, "..", "data", "results.log.jsonl");

// v0: append-only flat file, one line per turn (not just per finished
// playthrough) - so drop-off mid-conversation is visible, not just
// completions. Still the only persistence we allow before validation.
function logResult({ testerId, scenarioId, nodeId, choiceId, scores, terminal }) {
  const entry = {
    testerId: testerId || "anonymous",
    scenarioId,
    nodeId,
    choiceId,
    scores,
    terminal,
    timestamp: new Date().toISOString(),
  };
  fs.appendFileSync(LOG_PATH, JSON.stringify(entry) + "\n");
}

module.exports = { logResult };