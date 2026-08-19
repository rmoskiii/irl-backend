#!/usr/bin/env node
// Migrates a schema-v3 scenario from the hardcoded aftermath fields to the
// slot-keyed map, and declares the outcome key.
//
//   node migrate_the_secret.js path/to/the_secret.json
//
// Idempotent. Backs up to <file>.bak before writing.
//
// Why this is a script and not a rewritten file: the copy of the_secret.json
// in the project folder is the earlier Jordan-era version with no aftermath,
// no reflections and no outcomeRules. Run this against your live file.

const fs = require("fs");
const path = process.argv[2];

if (!path) {
  console.error("usage: node migrate_the_secret.js <path-to-the_secret.json>");
  process.exit(1);
}

const raw = fs.readFileSync(path, "utf-8");
const s = JSON.parse(raw);

let changed = false;

if (s.jessicaAftermath || s.alexAftermath) {
  s.aftermath = {};
  if (s.jessicaAftermath) s.aftermath.jessica = s.jessicaAftermath;
  if (s.alexAftermath) s.aftermath.alex = s.alexAftermath;
  delete s.jessicaAftermath;
  delete s.alexAftermath;
  changed = true;
  console.log("• nested aftermath ->", Object.keys(s.aftermath).join(", "));
} else if (s.aftermath) {
  console.log("• aftermath already nested:", Object.keys(s.aftermath).join(", "));
} else {
  console.log("! no aftermath found — is this the right file?");
}

// Without this, outcomeKey defaults to "outcome" and every `coupleOutcome`
// condition in the aftermath and finalMessage blocks silently stops matching.
if (s.outcomeKey !== "coupleOutcome") {
  s.outcomeKey = "coupleOutcome";
  changed = true;
  console.log('• set outcomeKey = "coupleOutcome"');
}

s.engineContract = s.engineContract || {};
s.engineContract.aftermath =
  "A map of named slots, each a declaration-ordered variant list. Composed at " +
  "terminal time so one world outcome yields different consequences per party.";
s.engineContract.outcomeKey =
  "The state key outcomeRules writes into before aftermath and finalMessage " +
  "resolve. Named per scenario: coupleOutcome here, resolution in The Prince.";

// Sanity: count how many conditions depend on the outcome key being right.
const json = JSON.stringify(s);
const hits = (json.match(/"coupleOutcome"/g) || []).length;
console.log(`• ${hits} references to coupleOutcome will now resolve`);

if (changed) {
  fs.writeFileSync(path + ".bak", raw);
  fs.writeFileSync(path, JSON.stringify(s, null, 2));
  console.log("written. backup at " + path + ".bak");
} else {
  console.log("nothing to change.");
}
