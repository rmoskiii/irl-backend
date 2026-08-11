# IRL backend (v0)

Tiny Express API for the IRL MVP. Deliberately minimal: no database, no auth,
no live LLM calls yet. Every scenario is a scripted branching decision tree —
each choice has a pre-written persona reaction and a fixed rubric score, so
the whole loop runs for $0 and with zero latency while we validate whether
the core "one situation, what do you do" experience is actually fun.

## Setup

```bash
npm install
cp .env.example .env
npm run dev
```

Server runs on http://localhost:4000 by default.

## Endpoints

- `GET /api/scenarios/today` — returns today's scenario (currently always
  `the_prince`), stripped of scores/reactions, ready for Flutter to render.
- `POST /api/scenarios/respond` — body `{ scenarioId, choiceId, testerId }`.
  Looks up the choice, returns the persona's reaction line, the score deltas,
  and the outcome explanation. Also appends a line to
  `data/results.log.jsonl` so we can answer the only question that matters
  right now: did this tester come back tomorrow?

## Swapping in a real LLM later

All persona/evaluation logic lives behind `src/services/personaService.js`
and `src/services/evaluationService.js`. Both currently do a plain lookup
against the scenario JSON. When you want live-generated persona variety,
replace the body of `getReaction()` in `personaService.js` with an Anthropic
API call (Haiku 4.5 is plenty for this) — nothing in the routes layer needs
to change.

## Adding a new scenario

Drop a new JSON file in `src/data/scenarios/`, following the shape of
`the_prince.json`, and add its id to `SCENARIO_ROTATION` in
`src/routes/scenarios.js`.

## Rate limiting

`src/middleware/rateLimiter.js` is a bare in-memory per-IP limiter. It does
nothing useful yet since there's no LLM cost to protect — it's there so the
hook already exists on the day you do add live calls.
