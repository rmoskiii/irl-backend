const fs = require("fs");
const path = require("path");

const LOG_PATH = path.join(__dirname, "..", "data", "results.log.jsonl");

// v0: append-only flat file. This is the one piece of persistence we allow
// before validation - it's what lets us answer "did they come back
// tomorrow" without standing up a real database.
function logResult({ testerId, scenarioId, choiceId, scores }) {
  const entry = {
    testerId: testerId || "anonymous",
    scenarioId,
    choiceId,
    scores,
    timestamp: new Date().toISOString(),
  };
  fs.appendFileSync(LOG_PATH, JSON.stringify(entry) + "\n");
}

module.exports = { logResult };
