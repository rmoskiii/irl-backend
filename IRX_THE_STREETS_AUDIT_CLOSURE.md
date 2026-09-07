# THE STREETS — ARCHITECTURE AUDIT: CLOSURE
## All unknowns resolved against `irl-backend` source

**Status: diagnosis complete. No files modified. Read-only.**

Supersedes the UNVERIFIED sections of `IRX_THE_STREETS_ARCHITECTURE_AUDIT.md`. Everything below is
cited to source. **U-01 through U-05 are closed. U-06 remains open** (it lives in `irx-flutter`).

**Suggested destination:** `irl-backend/IRX_THE_STREETS_AUDIT_CLOSURE.md`

**What was inspected:** 25 JS modules / 1,721 lines across `src/`, `package.json`, `tests/render/`,
and 7 config files in `tools/visual/`. `tools/visual/assets/anchors.json` was not in the upload
(the `-x "*.json"` exclusion caught it) — its shape is inferred from `resolvePlan.js`, which reads
every field it uses. This affects nothing in the verdict.

---

## 1. THE HEADLINE, REVISED

The previous audit said **NO, BUT** and could not size the BUT. It can now.

> **The engine is smaller and cleaner than its documentation implies, and it is entirely
> district-agnostic. The Streets is content and config — with exactly one behavioural addition.**
>
> **There is no server-side persistence of any kind.** Not a thin one. None. `package.json`
> declares three dependencies — `express`, `cors`, `dotenv` — and the only write to disk in the
> entire service is an append-only analytics log whose own comment reads: *"Still the only
> persistence we allow before validation."* (`src/services/resultsLog.js:8`)

And the consequence nobody would predict from the outside:

> **Because the server is stateless and the client already owns the state map, seven-day resume is
> a Flutter-only change with zero backend work.**

`POST /api/scenarios/respond` receives `state` in the request body
(`src/routes/scenarios.js:33`) and every response returns the full `state` back
(`src/services/evaluationService.js:254, 291`). The client is already the custodian of the run. To
resume on Day 2, Flutter persists `{scenarioId, nodeId, state}` locally and replays it. **No new
endpoint, no database, no schema change, no engine change.**

That reclassifies the single item that was blocking the whole programme, and it moves the Day 1 →
Day 7 vertical slice forward by however long a persistence tier would have taken.

---

## 2. UNKNOWNS — CLOSED

### U-01 — Does `requires` use the shared `when` matcher? **YES. PASS.**

`src/services/personaService.js:53–66`:

```js
function matchesAll(when, state) {          // AND: every pair must match
  for (const [key, value] of Object.entries(when)) {
    if (!(key in state)) return false;
    if (state[key] !== value) return false;
  }
  return true;
}
function matchesAny(whenArray, state) {     // OR: any clause matches
  if (!whenArray || whenArray.length === 0) return true;
  return whenArray.some((w) => matchesAll(w, state));
}
```

Applied at `personaService.js:162–163` and again at `evaluationService.js:171`.

**Disjunctive normal form is confirmed in code.** `requires: [{A,B},{C}]` is `(A AND B) OR C`, and
multi-pair clauses work today. The same `matchesAll` serves `messageVariants`, `threadVariants`,
`nextRules`, `outcomeRules`, `reflections`, `aftermath` and `finalMessage` — one matcher, six
call sites, no divergence. **SPEC-01 stands as a documentation fix only.**

Two details worth authoring against:

- **Key existence is required.** `if (!(key in state)) return false`. A typo'd key doesn't error —
  it makes the clause permanently false. Silent dead branch. See RF-10.
- **`requires: []` matches everything.** An empty array is not "impossible", it is "unrestricted".

### U-02 — Persistence and the state boundary. **NO SERVER PERSISTENCE. CONFIRMED.**

| Question | Answer | Evidence |
|---|---|---|
| Server run store? | **None** | No DB dep; `package.json` = express, cors, dotenv |
| Session/auth? | **None** | `src/index.js` — cors, json, rateLimiter, routes. 30 lines. |
| Who owns state? | **The client** | `routes/scenarios.js:33` reads `state` from `req.body` |
| Does the server return state? | **The whole map, every turn** | `evaluationService.js:291` `state: nextState`; `:254` `state: finalState` |
| Does the client see hidden state? | **Yes, all of it** | `getRootView` returns `state` at `personaService.js:200`; includes every `stateSchema` key and every `derivedState` band |
| Is `requires` server-enforced? | **Re-checked server-side** — but against client-supplied state | `evaluationService.js:171` |
| Cursor / run ID / completion flag? | **None** | client sends `nodeId` per request |

**`publicNode` is a genuine projection — of the node, not the state.** `personaService.js:158–178`
returns `nodeId, message, thread, presentation, reactionDelay, interstitial, choices, render`, with
choices reduced to `{id, label}` (`:175`). It strips `scores`, `setState`, `requires`, `reasons`,
`next`, `nextRules`, `beat`, `terminal` and the unmatched `messageVariants`. That is real and well
built. It simply sits alongside a full state map that ships regardless.

**Three consequences.**

1. **`visible: true` is not merely unnecessary — it is unimplementable as specified.** The client
   must return the state map for the engine to work. There is no version of the current
   architecture in which the client holds the map and cannot read it. **Withdraw the field.** The
   HUD reads `state.money` directly.
2. **v1.0 §D.2 — *"The Streets should not rely on the client hiding secret state"* — is
   incompatible with the current architecture.** Not "at risk". Incompatible. Satisfying it
   requires inverting state ownership, which is the D-sized change. **SPEC-12.**
3. **Gating is server-*evaluated* but not server-*authoritative*.** A modified client can send any
   state and pass any `requires`. For a single-player narrative game the exploit is spoiling your
   own story, which is a tolerable MVP position — but it should be a decision, not a discovery.

**Sizing, split properly:**

| Capability | Class | Where | Cost |
|---|---|---|---|
| 7 days in one sitting | **A** | — | zero |
| **Resume across days, one device** | **C** | **`irx-flutter` only** | **zero backend** |
| Multiple concurrent runs, one device | **C** | `irx-flutter` | client keys |
| Multi-device, accounts, anti-tamper, server-authoritative outcomes | **D** | new backend tier | DB + auth + migration, none of which exist |

**The MVP needs row 2. Row 4 is a real product, not a change.**

### U-03 — Does the loader branch on `schemaVersion`? **NO. Don't bump.**

`personaService.js:6–10`:

```js
function loadScenario(scenarioId) {
  const filePath = path.join(SCENARIOS_DIR, `${scenarioId}.json`);
  if (!fs.existsSync(filePath)) return null;
  return JSON.parse(fs.readFileSync(filePath, "utf-8"));
}
```

`schemaVersion` is **read nowhere in `src/`**. There is no validator, no migration, no version
gate. **SPEC-07 closes: author The Streets as `schemaVersion: 3`.**

The corollary is less comfortable: **there is no runtime scenario validation at all.** A malformed
95-node file fails at whatever node first touches the defect, mid-playtest. See RF-10.

### U-04 — Scenario registration. **Directory listing. Pure content.**

`personaService.js:206`: `fs.readdirSync(SCENARIOS_DIR).filter(f => f.endsWith(".json"))`.

**Dropping `the_streets.json` into `src/data/scenarios/` registers it.** `district` is passed
through untouched as a string.

**SPEC-06 closes: the district registry is not needed and should be withdrawn.** Two caveats:

- `DEFAULT_SCENARIO = "the_secret"` is hard-coded at `routes/scenarios.js:14`, but
  `/today?scenarioId=the_streets` already works.
- `listScenarios()` lists **everything** in the directory, including The Prince and The Bank, which
  the code comment says *"predate the v3 stateful contract and won't resolve correctly under this
  engine."* Pre-existing, not Streets-caused, but it means the list endpoint advertises broken
  scenarios.

### U-05 — Cache key. **Already exactly the model v1.0 proposed.**

`src/services/render/cacheKey.js:22–26`:

```js
/** ... sha256 of the canonicalised resolved render block. Never nodeId+variantIndex —
 *  variant indices are a server-side resolution detail, and two different states can
 *  resolve to one visual. */
function cacheKey(renderBlock) {
  return crypto.createHash('sha256').update(canonical(renderBlock)).digest('hex');
}
```

**v1.0 §K.7's render-block identity model is not a proposal. It is shipped, tested and documented,
and the comment rejects the nodeId alternative in the same words.** `parity.test.js` asserts both
directions: identical blocks collapse, a changed `framing` diverges. Classification **A**.

### U-06 — Does Flutter hold and return state? **OPEN**, but now near-certain.

`/respond` cannot function unless the client returns `state`. The remaining question is only
*where* Flutter keeps it and whether it survives app restart today. **This is now the single most
important file to look at**, because it determines whether seven-day resume is a few hours of work
or a few days. Needed: the API client and the `ScenarioNode`/state model in `irx-flutter`.

---

## 3. CORRECTIONS TO THE STREETS v1.0

Found by reading the repo. Four are material; the first is the largest error in the document.

### C-1 — Time variants are not free. **Asset budget understated.**

`tools/visual/registries.json`, `scenesNote`:

> *"resolve.py reads `scene_def['default_time']` and offers no per-node override, so **a room seen
> at two times is two scene tokens and two assets**. `desk_evening` carries Act 1 and `desk_day`
> carries the Friday afternoon reply."*

Career already paid this: `scene.desk_evening` and `scene.desk_day` are two full environments for
one room. `registries.json` declares each scene with a single-element `times` array and a
`default_time`.

**v1.0 §I.3 claimed *"Eight environments × three times ≈ 24 apparent locations for eight
environments' cost."* That is wrong.** Lighting is not an overlay in this pipeline; it is a scene
token.

Recount against v1.0 §I.3's own table: `block_walkway` (dusk, night) 2 · `chicken_shop` (day,
night) 2 · `bedroom` 1 · `home_kitchen` (day, night) 2 · `corridor` 1 · `cage` (dusk, night) 2 ·
`stairwell` 1 · `bus_stop` (dusk, night) 2 = **13 full environments, not 8 plus 6 cheap overlays.**

| | v1.0 | Corrected |
|---|---|---|
| Environments | 8 | **13** |
| "Lighting overlays" | 6 (cheap) | **0 — the category does not exist** |
| Environment subtotal | 14 assets, 6 cheap | **13 assets, all full cost** |
| Total SVG | ~96 | **~95, but ~5 more full environments** |

Total barely moves; **cost and schedule move a lot**, because environments are the most expensive
asset class and each needs its own occlusion design and alpha test.

**Three options, all content/config, all needing a decision (SPEC-13):**
- **Accept 13 environments.** Honest, most expensive.
- **Cut time variants to one per location.** Back to 8. Cheapest; loses the dusk/night contrast the
  district leans on hardest.
- **Add per-node time override to `resolve.py`.** Tooling change in `tools/visual/` (not shipped in
  the upload, so unsized). Only worth it if the same room genuinely repeats at two times often
  enough to beat drawing it twice — Career decided it wasn't.

### C-2 — There are six render modes, not five. `none` exists and matters.

`registries.json → modes`: `scene · montage · remote · absent · messages · none`, with:

> *"'none' is an INTENTIONAL blank: the node is a scene by presentation type but deliberately
> carries no artwork. It resolves to a null render block … set only through an explicit
> `modeOverrides` entry — never inferred from a missing visual block."*

The Instruction uses it four times (`mapping.the_instruction.json → modeOverrides`).

**This is the exact mechanism The Streets' safety rule needs.** "Camera cuts before method" has a
first-class, auditable representation: `mode: "none"` is a *positive assertion of intentional
absence*, distinguishable from an asset that failed to resolve. v1.0 §Q.3 described the principle;
the engine already has the primitive. Upgrade §13/§Q from **B** to **A**.

### C-3 — Character tiers are already native. Withdraw as an invention.

v1.0 §G.2 proposed "character tiers" as a new asset-cost lever. `registries.json` already does it:
`char.dana` has **two** registers, with the note *"Two registers because she appears in two nodes …
a third would be an orphan under validator rule 8."* And `char.ray` and `char.dana` both carry
`turned: null` — **rear figures are optional per character.**

Register count per character is content, decided by frame count, and validator rule 8 (no orphaned
assets) already enforces the discipline from the other direction. **Withdraw §G.2 as a new concept;
keep it as an authoring convention.** Also: v1.0's asset table budgeted 6 rear figures; several
can be dropped, partly offsetting C-1.

### C-4 — The geometry contract is global, and reuse is proven twice.

`resolvePlan.js:35` reads `const cc = A.character` — **one** `basePoint`, `headSocket` and
`neckSpan` for all figures, not per-figure as the scope document describes. And both Career figures
were built on it:

> *"figure_c reuses figure_a's geometry contract only — basePoint, headSocket, neckSpan. Face,
> hair, proportion and wardrobe are drawn fresh."* — and figure_d likewise from figure_b.

**Good news and a hard constraint.** The Streets' six figures inherit the neck contract, the slot
system and the register-swap test for free — but they must be built on one of the two existing
geometry contracts. Character variety comes from face, hair, proportion, wardrobe and palette, not
from body geometry. **Design the cast to that constraint rather than discovering it at figure four.**

### C-5 — `render_blocks` per-scenario is already solved. Withdraw Change 3.

The upload contains `render_blocks.json`, `render_blocks.the_secret.json` and
`render_blocks.the_instruction.json`. Verified mechanically: the merged file is the **exact union**
— 30 + 23 = 53 nodes, **zero ID collisions**.

The documented "single-file loader" limitation was resolved by the build-time concatenation the
scope document floated. Adding a third scenario is: run `dump_render.py` for The Streets, append.
**Config, not engine. Withdraw Change 3.**

**But the node-ID namespace is global** (`renderBlocks.js` keys by `nodeId` alone, with no scenario
prefix). At 53 nodes there are no collisions; at 148 with The Streets, a duplicate ID would
silently render another scenario's artwork. v1.0's `d<n>_<name>` convention is distinctive enough.
**Add a collision assertion to the concatenation step** — cheap, and it is exactly the silent-no-op
failure class already on the standing-practices list.

### C-6 — `textLayer: "native"` exists and changes the bubble constraints

`mapping.the_instruction.json`:

> `"textLayer": "native"` — *"Bubbles are OFF for the whole Career scenario. Dialogue and choices
> are carried by the native Flutter layer below the contained 16:9 artwork. Without this flag the
> resolver extracts quoted spans into bubbles, and `ask2_qa` variant[0] emits four — over
> `anchors.bubbles.maxPerNode` — which the composer throws on."*

Corroborated at `personaService.js:128` (`IRX_SCENE_BUBBLES` defaults **off**: *"the client already
renders the prose natively, and drawing it twice is worse than either option"*) and by
`bubble_nodes.json`, which opts in **6 nodes total**.

**So the shipped default is native text, not balloons.** v1.0 §I.1 treats `maxPerNode: 3` and the
120-character ceiling as hard composer constraints on all authoring. Under `textLayer: "native"`
they bind only the opted-in nodes.

**SPEC-14 — decide this before authoring, not after.** It changes the prose budget for 95 nodes. The
Instruction chose native and gave a specific reason. Balloons are the stronger read on the beats
that earn them, which is why the per-node opt-in exists.

### C-7 — Two engine features exist that v1.0 didn't know about

- **`seed` + `weightedPick`** (`personaService.js:14–48`): a scenario may declare randomised initial
  state, weighted. Neither shipped scenario uses it. Available to The Streets — and a **hard
  constraint on persistence**: a resumed run must store the seeded values, never re-derive them.
- **`outcomeTiers`** (`evaluationService.js`, `pickOutcomeText`): score-threshold outcomes,
  co-existing with reflections. Unused by both scenarios. The Streets should continue to ignore it —
  `scoring.note` in The Instruction argues correctly that a summed threshold cannot separate two
  legitimate landings.

---

## 4. WHAT THE CODE CONFIRMS ABOUT THE STREETS' CORE MECHANICS

Everything the previous audit inferred from the `engineContract` text is implemented as described.

| Mechanic | Implementation | Verdict |
|---|---|---|
| Additive ints, clamped | `applySetState` — `(next[key] \|\| 0) + value`, then `Math.max(min, Math.min(max, …))` | **A** |
| Enum/bool assignment | same function, `else` branch | **A** |
| Derived bands after every mutation | `applyDerived(applySetState(...), scenario.derivedState)` — `evaluationService.js` | **A** |
| `minus` differentials | `if (spec.minus) source -= next[spec.minus] \|\| 0` | **A** |
| Band ordering | `bands.find(b => source >= b.min)` — first match; **declare descending** | **A** |
| No band match | yields `null`, key still present | **A** |
| `nextRules` on post-derived state | `choice.nextRules.find(r => matchesAll(r.when, nextState))` | **A** |
| Terminal detection | `next === null` or absent `next` with a `terminal` block | **A** |
| Outcome at terminal only | `resolveOutcome(scenario, nextState)`, written under `outcomeKey` | **A** |
| Reflections cannot read outcome | `pickReflection(scenario, nextState)` — **`nextState`, not `finalState`** | **A** |
| Aftermath per slot | `resolveAftermath` iterates authored slots; slots are data | **A** |
| Variant index reaches the renderer | `findIndex`, carried into `blockFor(nodeId, variantIndex)` | **A** |
| Render pipeline is scenario-blind | `resolvePlan.js` reads only `anchors` + `registries` | **A** |
| Multi-district registry | `registries.json`: *"one registry, two districts"* | **A** |
| Firewall banned list | `registries.json → scoring_keys_forbidden`, 24 keys | **A** (add Streets keys) |

**Every state, branching, gating, outcome and render mechanic The Streets needs is implemented and
in production. None of it is a proposal.**

---

## 5. REVISED MINIMAL CHANGE SET

Down from five to **two**, one of which is client-only.

### CHANGE 1 — Client-side run persistence *(blocking, `irx-flutter` only)*

| | |
|---|---|
| **File** | `irx-flutter` — API client / scenario state model (**pending U-06**) |
| **Why** | Seven days needs resume. The server is stateless and the client already owns the map. |
| **Responsibility** | Persist `{scenarioId, nodeId, state, runningTotal, startedAt}` locally; restore on launch; clear on terminal. |
| **Layer** | **CLIENT** |
| **Backend change** | **None.** |
| **Regression risk** | **Very low.** Existing scenarios are unaffected if persistence is scoped by `scenarioId` and cleared at terminal. |
| **Testing** | Kill and relaunch mid-run → resume at the same node with identical state. Terminal → cleared. Seeded state persisted, not re-derived (C-7). |

### CHANGE 2 — `lockedLabel` *(recommended, ~3 lines + one client style)*

| | |
|---|---|
| **File** | `src/services/personaService.js:162–175` (`publicNode`) + a Flutter disabled-choice style |
| **Why** | `requires` removes the choice entirely; the player never learns the door existed. |
| **Change** | Stop filtering; map all choices, emitting `available: matchesAny(...)` and substituting `lockedLabel` where present and failing. Keep `evaluationService.js:171` unchanged — it already rejects unavailable choices server-side. |
| **Layer** | **ENGINE** (3 lines) + **CONTRACT** (one optional field) + **CLIENT** (one style) |
| **Regression risk** | **Low, and bounded.** The Instruction has 6 `requires` blocks and The Secret none. Absent `lockedLabel`, keep the current filter — behaviour byte-identical. |
| **Testing** | Failing `requires` + `lockedLabel` → present, `available:false`. Without the field → absent. Re-run the parity fixtures: render blocks are untouched, so all must be identical. |

### WITHDRAWN

| Proposal | Reason |
|---|---|
| Server run persistence | Not needed for MVP. Client-held state already supports resume. Row 4 of §2/U-02 is a product, not a change. |
| `visible: true` | **Unimplementable as specified.** The client must hold the map. |
| `render_blocks` per-scenario loader | Already solved by build-time merge (C-5). Add a collision assertion instead. |
| District registry | `readdirSync` (U-04). |
| `structure` block | Day is content, proven earlier and unchanged. |
| `schemaVersion: 4` | Nothing reads it (U-03). |
| Character tiers as an engine concept | Already native (C-3). |
| Slot scale factors | Still deferred. `registries.json` declares 7 slots; only 3 are used and depth is unscaled. |

---

## 6. SPECIFICATION ISSUES — UPDATED

| ID | Issue | Status |
|---|---|---|
| SPEC-01 | `requires` documented as ANY only | **Confirmed by code.** Restate as DNF. |
| SPEC-02 | Band count: 10 named, 11 stated, 12 needed | **Open.** Declare exhaustively. |
| SPEC-03 | `carrying_it` unreachable | **Open.** Author the rule or delete. |
| SPEC-04 | `{kaiStrain: 3}` violates own rule 10 | **Open.** Fix the example. |
| SPEC-05 | `structure` block | **Closed — withdraw.** |
| SPEC-06 | District registry | **Closed — withdraw** (U-04). |
| SPEC-07 | `schemaVersion: 4` | **Closed — stay on 3** (U-03). |
| SPEC-08 | Run cardinality | **Open**, now client-side: how many local saves? |
| SPEC-09 | Multi-device | **Closed for MVP:** single-device only. Revisit with accounts. |
| SPEC-10 | Snapshot vs event log | **Closed:** snapshot. The engine is snapshot-based throughout. |
| SPEC-11 | `visible` semantics | **Closed — withdraw the field** (U-02). |
| **SPEC-12** | v1.0 §D.2 "must not rely on the client hiding secret state" is **incompatible** with client-held state | **NEW, decision required.** Accept for MVP, or commit to server-authoritative runs (D). **Recommend accept** — it is single-player, and the only exploit is spoiling your own story. |
| **SPEC-13** | Time variants cost a full environment each (C-1) | **NEW, decision required.** 13 environments / cut variants / extend `resolve.py`. |
| **SPEC-14** | `textLayer: native` vs balloons | **NEW, decision required before authoring.** Sets the prose budget for 95 nodes. |

---

## 7. RED FLAGS — UPDATED

**Cleared:** RF-1 (persistence sizing — now known, and the MVP path avoids the backend entirely),
RF-4 (multi-pair `requires` — confirmed in code), RF-7 (`render_blocks` — already merged).

**Downgraded:** RF-3 (client breakage from state projection) — no longer applicable, since the
projection is withdrawn.

**Standing:**

**RF-2 (PERSISTENCE)** — migration debt still arrives, just on the client. A locally-saved run must
survive a scenario edit. Version the saved snapshot from the first commit; a mid-week `stateSchema`
change would otherwise resume runs against a stale schema. **Not retrofittable.**

**RF-5 (CONTENT)** — no NOT operator; complements must be enumerated as OR clauses.

**RF-6 (CONTENT)** — `messageVariants` growth. Cap at 3/node before authoring.

**RF-8 (VISUAL)** — exterior occlusion at y=600. Unchanged, and **worse under C-1**: 13
environments to occlusion-test rather than 8, and most are exteriors.

**RF-10 (ENGINE / AUTHORING) — NEW, and the most dangerous finding in this pass.**
`evaluationService.js:16`:

```js
const schema = stateSchema[key];
if (!schema) continue;          // setState key not in stateSchema — silently dropped
```

**A `setState` key absent from `stateSchema` is silently discarded.** Paired with
`matchesAll`'s `if (!(key in state)) return false`, a single typo produces a mutation that never
happens and a condition that never fires — with **no error, no warning, and no runtime validation
anywhere in the service** (U-03). At 12 keys and 23 nodes The Instruction survives this. At 34 keys
and 95 nodes it is a matter of when.

**This is precisely the silent-no-op failure class already on the standing-practices list, sitting
in the engine's hot path.** Mitigation is cheap and must exist before authoring: a build-time
scenario validator asserting every `setState` and every `when` key resolves against `stateSchema` +
`derivedState`. That is v1.0's proposed rules 10 and 16, and they should be built **first**.

**RF-11 (VISUAL) — NEW.** Node IDs are a global namespace across scenarios (`renderBlocks.js`).
Zero collisions today; a collision at 148 nodes silently renders another scenario's artwork. Assert
at concatenation.

---

## 8. FINAL VERDICT

### DOES THE STREETS REQUIRE A NEW ENGINE?

# NO.

Not "no, but" any more. **No.**

The backend requires **one three-line change** (`lockedLabel` in `publicNode`), and that is
optional — a replay-quality improvement, not a blocker. Everything else The Streets needs from the
server is implemented, in production, and district-agnostic by construction: `resolvePlan.js` reads
only `anchors.json` and `registries.json` and has never heard of a scenario; `registries.json`
carries two districts in one file and says so; `readdirSync` registers a third scenario by dropping
a file in a folder; the cache key is already the render-block hash v1.0 asked for.

The seven-day requirement — the one thing that looked like a new architectural tier — turns out to
be satisfied by the architecture already in place. **The server is stateless and the client already
owns the run.** Persistence is a Flutter change with no backend counterpart.

**The real cost of The Streets is content, config and ~95 pristine SVGs.** That was the thesis of
the v1.0 document and the repository supports it more strongly than the document claimed.

### A. WHAT WE CAN BUILD TODAY, ZERO CHANGES

The full 7-day graph; every branch, rejoin and delayed consequence; DNF gating; all bands including
differentials; all 9 trajectories with aftermath, reflections and final messages; days as
`day` metadata plus `interstitial`; all six render modes including the `none` blank that the
safety rule wants; 13 environments, 6 characters on the two existing geometry contracts, registers,
wardrobes, props, vignettes; two-figure composition; Day-4 divergence. **Played in one sitting, The
Streets ships on today's engine.**

### B. CONTENT / CONFIG ONLY

`src/data/scenarios/the_streets.json` · `tools/visual/mapping.the_streets.json` ·
`registries.json` additions (6 characters, 13 scenes, 18 props, 6 vignettes, Streets keys appended
to `scoring_keys_forbidden`) · `anchors.json` additions (scene slots, prop anchors, bubble
placement) · `render_blocks.the_streets.json` concatenated into `render_blocks.json` ·
`bubble_nodes.json` or a `textLayer` decision (SPEC-14) · ~95 SVGs · the new validator checks.

### C. ENGINE / CONTRACT / CLIENT WORK

1. **Client-side run persistence** — `irx-flutter` only, blocking, **pending U-06**
2. **`lockedLabel`** — 3 lines in `publicNode` + one Flutter style, optional
3. **A build-time scenario validator** — not in the original change set, promoted by **RF-10**.
   Tooling, not runtime. **Build it before authoring node one.**

### D. PRODUCT / SPEC DECISIONS

SPEC-02, 03, 04 block skeleton authoring. **SPEC-13** (13 environments vs cut variants) blocks the
asset budget. **SPEC-14** (native text vs balloons) blocks the prose budget. **SPEC-12**
(client-visible hidden state) needs an explicit accept for MVP. SPEC-08 sets local save cardinality.

### E. RECOMMENDED IMPLEMENTATION ORDER

| # | Step | Gate |
|---|---|---|
| 1 | **Close U-06** — the Flutter API client and state model | Change 1 sized |
| 2 | **Resolve SPEC-02, 03, 04, 12, 13, 14** → v1.1 | Signed off. Asset and prose budgets fixed. |
| 3 | **Build the scenario validator** (RF-10) — `setState`/`when` keys, band references, variant cap, node-ID collision | Runs green against `the_secret` and `the_instruction` **unmodified**. If it flags a real defect in either, that is the check working. |
| 4 | **Author the 7-day skeleton** — no prose, no assets | Validator green; exhaustive path simulation; `carrying_it` reachable; multi-pair `requires` asserted |
| 5 | **Day 1 prose + ~18 assets + one environment through the full gate** | Occlusion alpha test; 390pt readability |
| 6 | **Day 1 playable — current engine, zero changes, no persistence** | **Does it feel like a game?** Playtest 14–24s. |
| 7 | **Change 1 (client persistence) + Change 2 (`lockedLabel`)** | Kill/relaunch resumes; parity fixtures unchanged |
| 8 | **Days 2–3, retention gate** | Day-1 → Day-2 return rate |
| 9 | **Days 4–7, full visual audit, integration** | Flutter work ≈ one disabled-choice style |

**Step 6 still precedes every change.** That was the right sequencing when persistence looked like a
new backend tier; it is more obviously right now that Day 1 needs no engine work whatsoever.

---

**AUDIT CLOSED — NO FILES MODIFIED.**

U-01 to U-05 resolved against source. U-06 open pending `irx-flutter`.