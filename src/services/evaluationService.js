const {
  loadScenario,
  publicNode,
  matchesAll,
  matchesAny,
  resolveNodeContent,
} = require("./personaService");

function applySetState(state, setState, stateSchema) {
  if (!setState) return state;

  const next = { ...state };

  for (const [key, value] of Object.entries(setState)) {
    const schema = stateSchema[key];
    if (!schema) continue;

    if (schema.type === "int") {
      next[key] = (next[key] || 0) + value;

      if (Array.isArray(schema.range)) {
        const [min, max] = schema.range;
        next[key] = Math.max(min, Math.min(max, next[key]));
      }
    } else {
      next[key] = value;
    }
  }

  return next;
}

// Derived keys computed from real state after every setState, merged before
// any `when` is evaluated.
//
// `from` identifies the source numeric state key.
// `minus` optionally subtracts another numeric state key.
// `bands` are evaluated in declaration order and the first band whose
// minimum is satisfied wins.
//
// This lets authored conditions work with simple enum-like values such as:
//   "assuranceGap": "false_confidence"
// rather than requiring numeric operators inside `when`.
function applyDerived(state, derivedSchema) {
  if (!derivedSchema) return state;

  const next = { ...state };

  for (const [key, spec] of Object.entries(derivedSchema)) {
    let source = next[spec.from] || 0;

    if (spec.minus) {
      source -= next[spec.minus] || 0;
    }

    const band = (spec.bands || []).find((b) => source >= b.min);

    next[key] = band ? band.value : null;
  }

  return next;
}

// Only evaluated at terminal time.
//
// Rules are declaration-order / first-match-wins, using the same matchesAll
// semantics as messageVariants, threadVariants, etc.
//
// The result is written into state under the scenario's own `outcomeKey`
// BEFORE aftermath and final-message variants are resolved, so those
// variants can condition on the world's fate as well as the player's
// behaviour. The Secret calls it `coupleOutcome`; The Prince calls it
// `resolution`. The engine doesn't care which.
function resolveOutcome(scenario, state) {
  const rules = scenario.outcomeRules || [];
  const hit = rules.find((r) => matchesAll(r.when, state));
  return hit ? hit.value : (scenario.outcomeDefault || null);
}

// Picks the first matching variant from a declaration-ordered list.
//
// If no variant matches and a fallback is supplied, the fallback's `text`
// is returned. Otherwise null is returned.
function pickVariant(list, state, fallback) {
  const hit = (list || []).find((v) => matchesAll(v.when, state));
  return hit ? hit.text : (fallback ? fallback.text : null);
}

// Aftermath is a scenario-declared map of named slots, each holding its own
// declaration-ordered variant list:
//
//   "aftermath": {
//     "jessica": [ { "when": {...}, "text": "..." }, ... ],
//     "alex":    [ ... ]
//   }
//
// Slots used to be hardcoded fields (jessicaAftermath / alexAftermath),
// which meant every new scenario added two more named fields to this
// service, the Dart model, and the outcome screen. They're now data. The
// Prince declares money / data / others; nothing in the engine changes.
//
// Returns null rather than {} when a scenario authors no aftermath at all,
// so the client can distinguish "no aftermath" from "aftermath resolved to
// nothing".
function resolveAftermath(scenario, state) {
  const slots = scenario.aftermath;
  if (!slots) return null;

  const resolved = {};

  for (const [slot, variants] of Object.entries(slots)) {
    const text = pickVariant(variants, state);
    if (text) resolved[slot] = text;
  }

  return Object.keys(resolved).length > 0 ? resolved : null;
}

function sumScores(delta) {
  return (delta.savvy || 0) + (delta.streetSmarts || 0) + (delta.integrity || 0);
}

// Score-threshold lookup. No longer mutually exclusive with reflections —
// a scenario may author both, and Digital scenarios do: a graded outcome
// AND a named pattern.
function pickOutcomeText(scenario, finalTotal) {
  const tiers = scenario.outcomeTiers || [];
  const tier = tiers.find((t) => finalTotal >= t.minTotal);

  return tier
      ? tier.explanation
      : (tiers[tiers.length - 1]?.explanation || "");
}

// Reflection path — pattern-matched prose instead of (or alongside) a
// graded number.
//
// Walks `reflections` in declaration order, first fully-matching `when`
// wins, same semantics as messageVariants/threadVariants.
//
// Falls back to `defaultReflection` if nothing matches.
function pickReflection(scenario, state) {
  const reflections = scenario.reflections || [];
  const match = reflections.find((r) => matchesAll(r.when, state));

  if (match) {
    return { title: match.title, text: match.text };
  }

  const fallback = scenario.defaultReflection || {};

  return {
    title: fallback.title || "",
    text: fallback.text || "",
  };
}

function resolveChoice({ scenarioId, nodeId, choiceId, runningTotal, state }) {
  const scenario = loadScenario(scenarioId);
  if (!scenario) return null;

  const node = scenario.nodes[nodeId];
  if (!node) return null;

  const choice = node.choices.find((c) => c.id === choiceId);
  if (!choice) return null;

  const stateSchema = scenario.stateSchema || {};
  const currentState = state || {};

  if (choice.requires && !matchesAny(choice.requires, currentState)) {
    return { error: "Choice not available in current state." };
  }

  // Apply the authored state changes first, then derive the banded / helper
  // state from the resulting real state.
  //
  // This means every subsequent `when` evaluation sees both:
  //   - the actual accumulated state
  //   - the latest derived state
  const nextState = applyDerived(
      applySetState(currentState, choice.setState, stateSchema),
      scenario.derivedState
  );

  const delta = choice.scores || { savvy: 0, streetSmarts: 0, integrity: 0 };
  const reasons = choice.reasons || {};
  const beat = choice.beat || null;

  let nextNodeId;

  // nextRules are evaluated against the state AFTER setState + derivedState.
  if (Array.isArray(choice.nextRules)) {
    const rule = choice.nextRules.find((r) => matchesAll(r.when, nextState));
    if (rule) nextNodeId = rule.next;
  }

  if (nextNodeId === undefined && choice.next) {
    nextNodeId = choice.next;
  }

  const isTerminal =
      nextNodeId === null || (nextNodeId === undefined && choice.terminal);

  if (isTerminal) {
    if (!choice.terminal) {
      return {
        error: `Rule matched null-next but choice ${choiceId} has no terminal block.`,
      };
    }

    // scores/reasons still flow back regardless of mode — the client
    // applies these to the cross-scenario home-screen stat pool on every
    // turn, independent of how (or whether) this scenario grades itself.
    //
    // Reflections and tiers are no longer either/or. A scenario that
    // authors both gets both: the tier answers "how did that go", the
    // reflection answers "what pattern were you running". Digital wants
    // both; Neighbourhood authors reflections only and the tier fields
    // simply come back absent.
    const outcomeFields = {};

    if (Array.isArray(scenario.reflections) && scenario.reflections.length > 0) {
      const reflection = pickReflection(scenario, nextState);
      outcomeFields.reflectionTitle = reflection.title;
      outcomeFields.reflectionText = reflection.text;
    }

    if (Array.isArray(scenario.outcomeTiers) && scenario.outcomeTiers.length > 0) {
      const priorTotal = sumScores(
          runningTotal || { savvy: 0, streetSmarts: 0, integrity: 0 }
      );
      const finalTotal = priorTotal + sumScores(delta);
      outcomeFields.outcomeExplanation = pickOutcomeText(scenario, finalTotal);
    }

    // The world's fate is resolved only once the scenario reaches a
    // terminal, from the complete accumulated state including derived
    // values — and written into state under the scenario's own key before
    // aftermath and final-message variants are evaluated.
    const outcomeKey = scenario.outcomeKey || "outcome";

    const finalState = {
      ...nextState,
      [outcomeKey]: resolveOutcome(scenario, nextState),
    };

    return {
      scores: delta,
      reasons,
      beat,
      terminal: true,

      state: finalState,

      consequence: choice.terminal.consequence,
      landing: choice.terminal.landing,

      // Slot-keyed aftermath. Each slot resolves independently against the
      // same final state, which is what lets one world-outcome produce
      // asymmetric consequences across the parties involved.
      aftermath: resolveAftermath(scenario, finalState),

      // Names the pattern the player may not have known they were forming.
      finalMessage: pickVariant(
          scenario.finalMessage,
          finalState,
          scenario.defaultFinalMessage
      ),

      ...outcomeFields,
    };
  }

  if (!nextNodeId) {
    return { error: `No next node resolved for choice ${choiceId}.` };
  }

  const nextNode = scenario.nodes[nextNodeId];
  if (!nextNode) {
    return { error: `Unknown next node: ${nextNodeId}.` };
  }

  const content = resolveNodeContent(nextNode, nextState);

  return {
    scores: delta,
    reasons,
    beat,
    terminal: false,
    state: nextState,
    node: publicNode(nextNodeId, nextNode, nextState, content, scenario.id),
  };
}

module.exports = {
  resolveChoice,
  // Exported for the resume endpoint only. Bands are recomputed from raw
  // state on every read; they are never treated as an authoritative
  // persisted value. SPEC-08 invariant 8.
  applyDerived,
};