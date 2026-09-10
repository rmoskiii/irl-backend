# THE STREETS — V5 AUDIT
## Story Bible V5 and Spec V5 assessed against the closed v1.1 contracts

**Read-only. No files modified. Nothing authored.**

Assessed: V5 Story Bible (canonical creative), V5 Spec (canonical content-authoring), against
`IRX_THE_STREETS_SPEC_V1.1.md`, the authored skeleton `the_streets.json` (63 nodes, 33 keys), the
creative-gate documents, and the running code.

---

## Verdict

**V5 is a better story than the one it replaces, and it is not yet safe to author from.**

Six blocking contradictions, three expressibility gaps, and one direct conflict with shipped client
behaviour. Four of the six are cases where **the V5 Spec carries forward text from my earlier
documents that the V5 Bible has since overruled** — the Spec was built by merging into v1.1 rather
than by rewriting from the Bible, so it contains dead story statements that now contradict the
canonical creative source.

None of this requires an engine change. Most of it is one editing pass on the Spec plus five
decisions. But authoring against V5 as it currently stands would produce a scenario that fails its
own validator on trajectory rules and displays a labelled INTEGRITY score to a player in a product
whose bible says there is no morality score.

---

## What V5 improves, and should be protected

**The financial spine is the biggest gain.** *Legitimate need → internal pressure → temptation of
speed → choice → consequence*, with Bola under real mortgage pressure and explicitly never directing
him toward illegality, is a stronger and more honest engine than anything in the earlier documents.
It also makes `money` — the one visible number — load-bearing from Day 1 without a meter.

**The response-density contract is the best single addition.** Linear response / narrative
acknowledgement / meaningful choice, with the explicit instruction not to manufacture alternatives,
is the correct answer to the failure mode the skeleton was heading toward. My 63-node skeleton has
102 choices; under V5 a substantial number of those are fake and should collapse to single-choice
beats.

**Two Dee routes (Day 3 opportunity, Day 5 cousin) is better than one.** It separates "speed and
ambiguity" from "clean trust," which is what stops Dee reading as a recruiter far more reliably than
the single-offer version did.

**The character knowledge rule** — state is not automatically character knowledge, transmission must
be authored — is a genuine safeguard against the "the game remembered my flag" failure and should be
treated as a hard rule, not guidance.

**Day 6 as a sequence of calls** fits the existing `remote` and `messages` modes and needs almost no
artwork. That is a real budget win nobody has counted yet.

---

## Blocking contradictions

### B1 — Trajectory definitions contradict the trajectory rules *(most serious)*

The V5 Spec retains the v1.1 outcome-rule table verbatim while the V5 Bible redefines what the
trajectories mean. On two of nine the definitions are opposites.

| Trajectory | v1.1 rule (retained in V5 Spec) | V5 Bible §9 definition | Status |
|---|---|---|---|
| `carrying_it` | `daySixAct: "fronted"` — took someone else's consequence | "repeatedly concealed, postponed or made promises he could not honour" | **Opposite** |
| `holding` | `outcomeDefault` — nothing resolved | "told at least one costly truth, returned responsibility or held a credible boundary" | **Opposite.** A default cannot require positive evidence. |
| `kept_both` | `disciplineBand: held` AND `jayBand: tight` | "followed through for Jay **and Tunde**" | Misaligned — rule reads discipline, definition reads Tunde |
| `on_your_own` | `jayBand: broken` AND `tundeBand: broken` | "clear boundaries and accepted the loneliness" | Misaligned — rule reads burned bridges, definition reads chosen limits |
| `in_it`, `useful`, `the_one_they_call`, `moving`, `invisible` | — | — | Compatible |

**`holding` is the sharp one.** It is currently reachable only through `outcomeDefault`, which fires
when nothing else matches. V5 defines it as an earned position requiring a costly truth or a held
boundary. Those cannot both be true. Either `holding` gets rules and something else becomes the
default, or the V5 definition is rewritten as the residual it mechanically is.

### B2 — "No single choice determines a trajectory" is violated by the rules V5 retains

V5 Bible §9: *"No single choice determines a trajectory"* and *"at least three distinct authored
evidence points from different moments in the week."*

Retained rule 3 is `{daySixAct: "fronted"}` — one Day 6 choice, one key, determines `carrying_it`
outright. Retained rule 2 is `{heatBand: "burnt"}` — one accumulated axis.

This is not a wording problem. **Satisfying the three-evidence rule requires rewriting the outcome
rule table**, and multi-evidence rules are harder to make reachable — the Phase 2 work already
showed three of nine trajectories were unreachable on the first attempt with *simpler* rules.

### B3 — The V5 Spec's Day 1 contradicts the V5 Bible's Day 1

- **Spec:** *"Day 1 — THE ASK … The hook is that Jay did not turn up and tomorrow the player must go to his house."*
- **Bible:** Day 1 is Bola at home, the Jay/Tunde split, an Amara text, and a closing message from an **unknown number** asking him to hold something till morning. The day *"should end on uncertainty, not a reveal."* There is no handover, no no-show, and no going to Jay's house.

The Spec line is carried over from my creative-gate document, which V5 supersedes. Per the authority
order, the Bible wins and the Spec sentence is dead.

**This matters beyond a stray sentence:** the whole Day-1 hook has changed. It is no longer *"he
didn't turn up and I have to see him tomorrow."* It is *"I said yes to something I can't see."* The
retention hook needs re-deciding, not just re-wording.

### B4 — "THE PLATE" now means two different things

- **Creative gate:** Jay's mum puts a plate in front of the player at her own table — the debt made physical, the scene that passed the bag-deletion test.
- **V5 Bible Day 2:** *"A relative has left a plate of food that must be collected before closing; Jay needs the player to make the run with him."* The plate is an errand McGuffin at a third location.

Same title, different scene, different location, different emotional content. Anyone holding both
documents will conflate them. **The V5 version is locked and I am not arguing against it** — but two
consequences need recording: the debt-at-the-table image is gone unless deliberately re-added, and
**Day 2 may no longer take place at Jay's flat.**

### B5 — Jay's flat is not in the environment inventory, and the Day 2/Day 4 asset economy is gone

SPEC-13's table lists ten tokens: `block_walkway` ×2, `chicken_shop` ×2, `bedroom`, `home_kitchen`,
`corridor`, `cage`, `stairwell`, `bus_stop`. **`jay_flat` is not among them**, and Day 4 takes place
entirely inside it.

Worse: I registered `scene.jay_flat` in `mapping.the_streets.json` last pass with
`usedBy: ["day 2 - the plate", "day 4 - the birthday"]`, justified by both days sharing one evening
interior — one token, one asset. Under V5, Day 2 is a run to a relative's before closing time, so
**that justification no longer holds and the entry is already stale.**

Net: the inventory is either eleven tokens, or one of the existing ten gets cut. Under V5's day
anchors, `cage` and `bus_stop` are the weakest — but SPEC-13 explicitly says not to remove tokens
merely because Day 4 stopped routing through them, which was written before anyone checked whether
they were used elsewhere.

### B6 — Two state keys are named that do not exist

V5 Bible §5 lists evidence booleans including **`asked_jay`** and **`kept_cousin_commitment`**.
Verified against the authored schema: neither exists. The twelve that do are `helped_jay`,
`refused_the_offer`, `stop_was_filmed`, `missed_training`, `told_jay_about_dee`, `lied_to_mum`,
`answered_mum`, `stayed_out`, `paid_it_back`, `walked_away`, `apologised_to_kai`,
`kept_the_receipt`.

The same section says *"No new state field is approved in this bible."* **V5 names two fields it
does not authorise.** Per V5's own rule this must be raised, not solved.

---

## OPEN CREATIVE DECISION — REVIEW BEFORE CLAUDE

### OCD-1 — `asked_jay`: reuse or authorise?

V5 Day 1 Movement 2 makes asking Jay what's wrong the information gate: *"If the player does not ask,
Jay says he is fine and information is lost."* That needs a flag and there is no clean spare.

**Candidate reuse: `kept_the_receipt`.** Its stated meaning is "the small, boring, unglamorous act
that turns out to matter" — currently "set a condition on Friday." V5 Day 1's closing offers
*"accept, ask one careful question or refuse,"* which is the same shape. But it cannot carry both
*asked Jay about his sister* and *asked the careful question at the handoff* — those are different
moments with different consequences.

**Options:** (a) `kept_the_receipt` carries the handoff question and `asked_jay` is authorised as a
13th flag; (b) `kept_the_receipt` is repurposed to Jay and the handoff question is expressed through
`heat`/`stayed_out` instead; (c) the Jay information gate is expressed structurally through
`nextRules` and a jay-trust delta with no flag. **(c) is the only option requiring no new key**, and
it works — but the information is then unavailable to Day 6 matchers, which V5 Day 6 wants.

### OCD-2 — `kept_cousin_commitment`: the Day 5 enum cannot hold Day 6 behaviour

V5 Day 5 lists five responses: accept fully, accept with a time limit, arrange a responsible
handover, decline honestly, **or abandon the commitment when a higher-status opportunity appears.**

`dayFive` has four values (`none/took/took_limited/declined`) and — more importantly — **abandonment
happens on Day 6, not Day 5.** A Day 5 enum structurally cannot record a Day 6 event.

**Candidate reuse: `missed_training`.** It is literally about not turning up to training, and Day 5's
responsibility is Tuesday/Thursday training. This is a clean fit and needs no new key. It costs the
key's current meaning (Tunde's sessions), which under V5 is arguably subsumed anyway.

**Also unresolved:** `dayFive` has four slots for five outcomes. "Responsible handover" and "decline
honestly" are meaningfully different to Dee and currently collapse to `declined`.

### OCD-3 — The shipped client displays a labelled INTEGRITY score

**This is the conflict with the highest blast radius, and it is with running code, not a document.**

V5 Bible §2 rules 11 and 15: *"No choice is labelled good, bad, moral, immoral, savvy or
street-smart"* and *"There is no morality score."*

`outcome_screen.dart` renders `SAVVY`, `INTEGRITY` and `STREETSMARTS` as labelled totals (lines
321–326) and iterates per-turn `TurnBreakdown` deltas with a staged reveal (line 294). Every existing
scenario supplies `choice.scores` in those three dimensions, and v1.1 retains
`scoring.dimensions` with `revealTiming: "end_only"`.

So a Streets player finishes the week and is shown a number labelled INTEGRITY. That is a morality
score by any reading of the bible.

**Three options, none free:**

| Option | Cost |
|---|---|
| **Zero all Streets scores**, keep the field for schema compatibility | Outcome screen shows three zeros and a flat breakdown. Probably reads as broken. Cross-scenario `AppState` never moves for Streets players. **No client change, no engine change.** |
| **Omit `reasons` only**, keep scores as neutral magnitudes | The moralising surface (per-choice justification text) disappears; the labelled totals remain. My skeleton already omits `reasons`. Partial compliance only. |
| **Client change** — suppress the stat panel per district | Forbidden by V5's own implementation boundary. Would be a real change to shipped behaviour. |

**Nothing here is authorable until this is decided**, because every choice in the file carries a
`scores` block.

---

## Consequences for the existing skeleton

| Item | Status under V5 |
|---|---|
| 63 nodes | **Ceiling, not target.** V5 explicitly accepts fewer. Day 4's 12 nodes are likely too many; V5 wants Day 6 dense and Days 1 and 7 shortest. |
| 102 choices | **Substantially too many.** The response-density contract collapses fake choices into single-choice beats. Expect a meaningful reduction. |
| `stop_was_filmed` | **Moves to Day 3, not Day 1.** V5 places the filmed stop in Day 3 as social interpretation. My last pass named it for Friday and left the write on Day 4. It is now wrong on both counts. |
| `refused_the_offer` | **Ambiguous again.** V5 has two Dee offers — Day 3 opportunity and Day 5 cousin. This is the same class of bug as `refused_the_bag`, one rename later. Needs to name which offer. |
| `dayFourWent` = `amara/tunde/kai/nowhere` | Survives. V5 Day 4's braided encounters map cleanly. |
| `walked_away` | Maps to V5 Day 3 Kai stop, "or leave." Good. |
| `helped_jay`, `lied_to_mum`, `answered_mum`, `paid_it_back`, `told_jay_about_dee` | All map cleanly. |
| `apologised_to_kai` | Maps to Day 4 "answer Kai calmly and let the moment pass." |
| `stayed_out` | **Orphaned.** Its Day 1 meaning (waiting outside the shop) has no V5 equivalent. |
| `plannedScenes` entry for `scene.jay_flat` | **Stale.** `usedBy` names Day 2, which no longer happens there. |
| "Flag count is 11, not 12" (V5 Spec, SPEC-03) | **Wrong, and it is my error propagated into a canonical document.** The list is 12 and always was. |

---

## Structural risks V5 introduces

**R-A — The Day 3 stop invites a causal reading the story refuses.** A police stop two days after a
bag storyline will be read as connected. V5 forbids the connection and forbids resolving it. That is
defensible ambiguity in principle, but the failure mode is a player concluding the game is
withholding rather than that life is ambiguous. **The mitigation is that the player is carrying
nothing on Day 3** — the stop genuinely finds nothing, because there is nothing. That has to be
legible in the prose or the ambiguity curdles.

**R-B — Two unexplained things is one more than one.** The bag is never explained. The unknown
number is never identified. Dee's connection stays suggestive and unconfirmed. Three deliberate
unresolveds in seven days risks reading as evasion rather than restraint. The bible's own warning
about "authorial vagueness" applies to itself here.

**R-C — The response-density contract has no representation in JSON.** Linear response and narrative
acknowledgement are both single-choice nodes and are structurally identical. Only *meaningful choice*
(≥2 choices) is distinguishable. V5 says the JSON "must preserve the distinction" and also forbids
unsupported metadata. **Resolution: the distinction is an authoring discipline recorded in the
generator, not a JSON field.** Cheap, but it needs saying, because otherwise someone adds a
`responseType` field and the validator rejects it.

**R-D — The three-evidence trajectory requirement is not validator-expressible.** V5 says so itself
("not a new validator requirement unless existing tooling already supports it"). It does not. Layer B
proves trajectories are *reachable*; it cannot prove each is reachable *only* through three distinct
evidence points. That stays a human review gate, and it should be named as one rather than assumed.

---

## Recommended edits to the V5 Spec

The Spec was merged into v1.1 rather than rewritten from the Bible. That is the root cause of B1–B5.

1. **Delete the story restatements from the Spec.** The "V5 creative authoring constraints →
   Day-specific creative constraints" section duplicates the Bible and has already drifted from it
   (B3). One canonical story source. The Spec should state contracts and point at the Bible.
2. **Rewrite the outcome-rule table** to match Bible §9, or rewrite Bible §9 to match the rules.
   Resolve `carrying_it` and `holding` explicitly (B1).
3. **Decide whether "no single choice determines a trajectory" binds the rule table** (B2). If it
   does, the table needs multi-evidence rules and a reachability re-proof.
4. **Add `jay_flat` to SPEC-13's environment inventory** and re-derive the count (B5).
5. **Correct "Flag count is 11, not 12"** in SPEC-03.
6. **Record OCD-1, OCD-2 and OCD-3** in the Spec as open, not resolved. Currently the Spec says
   "No unresolved creative decision remains," which is not true once B6 is noticed.

---

## What I would do before authoring

**In order, and none of it is asset work:**

1. **Resolve OCD-3 (the score display).** Highest blast radius, touches every choice in the file, and
   it is a conflict with shipped code rather than with a document. Nothing is authorable until it is
   settled.
2. **Resolve B1 and B2 (trajectories).** These determine the shape of every day's consequences.
   Authoring days against a trajectory table that will change is wasted work — and the Phase 2
   experience says reachability is the part that bites.
3. **Resolve OCD-1 and OCD-2 (the two named keys).** Small, but they decide Day 1 Movement 2 and
   Day 5/6, and V5's own rules forbid me deciding them.
4. **Settle B3 (the Day 1 hook) and B4/B5 (Day 2's location and the environment count).**
5. **Then** re-author the generator against the Bible, day by day, with the response-density
   classification recorded in comments and the choice count falling substantially from 102.
6. **Then** validate, and only then look at assets.

**Asset work should not start.** The environment inventory is wrong by at least one token, Day 2's
location is undetermined, and Day 4's single-gathering decision has not been reconciled with a scene
list written before it.

---

**V5 AUDIT COMPLETE — NO FILES MODIFIED.**