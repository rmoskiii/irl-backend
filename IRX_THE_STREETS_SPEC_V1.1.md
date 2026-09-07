# THE STREETS — SPEC v1.1 CLOSURE

**Status: specification gate. Read-only. No files modified, no code written.**

**Suggested destination:** `irl-backend/IRX_THE_STREETS_SPEC_V1.1.md`

Closes every open issue from the architecture audit, the U-02/U-05 closure and the U-06 closure.
Supersedes the affected sections of v1.0. Where a decision was verified against source, the file and
line are cited.

---

## Executive decision

- **Twelve derived bands, named and fixed.** All derived, all scenario-scoped, all reading raw
  integer keys. Thresholds live in scenario JSON. No engine change.
- **`carrying_it` stays and is not a state key.** It is a trajectory driven by the existing
  `daySixAct` enum. The rule list becomes nine rules for nine trajectories, with `holding` reachable
  only through `outcomeDefault`.
- **Newly found, and it constrains authoring: derived bands do not exist at the root node.**
  `initialState` (`personaService.js:31–49`) never calls `applyDerived`, and `matchesAll` fails on a
  missing key. The root node may not reference any derived-state key in any matcher or variant
  condition. This has never bitten because The
  Instruction's root node has one `continue` choice and no variants.
- **State visibility is presentation, not security.** `visible: true` is withdrawn. The full state
  map persists in the snapshot and reaches the client, and The Streets is designed so that reading
  it costs the player the experience rather than the game. Explicitly not an anti-tamper boundary.
- **`textLayer: "native"` globally**, with a hard cap of eight bubble-enabled nodes. Native text is
  selectable, reflows, and respects OS text size — on a 95-node prose-led scenario for a 14–24
  audience, that is not a close call.
- **Ten environments, not thirteen and not eight.** One time per location, with exactly two
  locations earning a second. Revised asset budget: **~85 SVG**, down from ~96 despite the
  time-variant correction, because v1.0 over-budgeted rear figures.
- **Unknown state keys become a hard build failure.** `evaluationService.js:16` silently drops
  `setState` keys absent from `stateSchema`; at 34 keys and 95 nodes that is the single most likely
  source of a wasted week.
- **Two additive backend contract items, no new engine machinery:** the node-read endpoint for
  resume, and a `contentRevision` field so a stale snapshot can be retired rather than resumed into
  nonsense.

---

## SPEC-02 — Band count

**v1.0 ambiguity.** Ten bands named, eleven stated, twelve actually required. `mumBand` and `kaiBand`
implied by the §D.4 table but never written. `moneyBand` used in the §E.2 example and declared
nowhere. `kaiBand` structurally impossible as specified, since Kai has no trust axis.

**Verification.** `applyDerived` (`evaluationService.js:44–62`) computes `next[spec.from] || 0`,
optionally subtracts `next[spec.minus] || 0`, then takes the **first** band satisfying
`source >= b.min`. Bands are written into the same accumulating object, so a band *could* name
another band in `from` — but band values are strings, `"tight" >= 3` is `false`, and the source would
fall through to the last band. Silent nonsense. Likewise a boolean source: `true || 0` is `true`, and
`true >= 3` is `false`.

### Decision

**Twelve bands. All derived, all scenario-scoped, all reading raw integer keys only.**

| # | Band | `from` | `minus` | Values, worst → best |
|---|---|---|---|---|
| 1 | `moneyBand` | `money` | — | `short` · `enough` · `flush` |
| 2 | `repBand` | `rep` | — | `nobody` · `quiet` · `solid` · `known` |
| 3 | `heatBand` | `heat` | — | `burnt` · `hot` · `warm` · `clear` |
| 4 | `disciplineBand` | `discipline` | — | `gone` · `slipping` · `held` |
| 5 | `creditBand` | `credit` | — | `owing` · `even` · `owed` |
| 6 | `exposureBand` | `heat` | `credit` | `exposed` · `watched` · `noticed` · `clear` |
| 7 | `jayBand` | `jayTrust` | `jayStrain` | `broken` · `frayed` · `steady` · `tight` |
| 8 | `tundeBand` | `tundeTrust` | `tundeStrain` | as above |
| 9 | `amaraBand` | `amaraTrust` | `amaraStrain` | as above |
| 10 | `deeBand` | `deeTrust` | `deeStrain` | as above |
| 11 | `mumBand` | `mumTrust` | `mumStrain` | as above |
| 12 | `kaiBand` | `kaiStrain` | — | `quiet` · `needled` · `hostile` (**inverted**) |

`kaiBand` reads strain alone, because Kai is friction rather than a relationship the player is
building. Its ordering runs *worst-at-the-top* relative to the others, which is why it is named
distinctly rather than forced into the trust/strain shape.

**Thresholds are scenario config**, declared in `the_streets.json → derivedState`, exactly as The
Instruction declares `exposureBand`. Not global. They are a balance surface and must be tunable
without a deploy.

`amaraBand` uses the shared four-value shape. v1.0 §K.8's `otherDoors` example gates on `"closed"`;
that is corrected to `"broken"`. Amara's arc is described in prose as *interested, distant, or
closed* (v1.0 L576) and that language stays in the writing — per-character band vocabularies are not
introduced, because one character's flavour is not worth a second value set for authors to confuse.

`kaiBand` and `mumBand` are declared but not yet referenced by authored content. This is expected:
both characters land on Days 6–7. Their keys will emit "never read" warnings throughout Phase 2 and
that is the validator working correctly, not a defect to suppress.

**Band usage — required by authored content vs available abstraction:**

| Band | Referenced by | Required? | Evidence |
|---|---|---|---|
| `moneyBand` | Day 7 `lockedLabel` gate | **Yes** | v1.0 L449 |
| `repBand` | outcome rules 8, 9 | **Yes** | SPEC-03 |
| `heatBand` | outcome rules 2, 9 | **Yes** | SPEC-03 |
| `disciplineBand` | outcome rules 5, 6 | **Yes** | SPEC-03 |
| `creditBand` | outcome rules 4, 8 | **Yes** | SPEC-03 |
| `exposureBand` | outcome rule 1 | **Yes** | SPEC-03 |
| `jayBand` | outcome rules 5, 7; Day 2 `requires` | **Yes** | v1.0 L410, L648 |
| `tundeBand` | outcome rule 7 | **Yes** | v1.0 L650 |
| `amaraBand` | `otherDoors` | **Yes** | v1.0 L1106 |
| `deeBand` | Day 5 `messageVariants` | **Yes** | v1.0 L1011 |
| `kaiBand` | SPEC-04 corrected example only | **Available** | SPEC-04 |
| `mumBand` | nowhere | **Available** | none |

**Nothing in the engine changes.** `from`, `minus` and `bands` are all in production use.

### Authoring rule

1. A band's `from` and `minus` **must name integer keys declared in `stateSchema`.** Never another
   band, never a boolean, never an enum.
2. **`bands` must be declared in descending `min` order**, terminating in `{ "min": -999 }`. The
   engine takes the first match; an ascending list silently returns the wrong band for every value.
3. **Content references bands, never the raw integers behind them.** `when: { jayBand: "frayed" }`,
   never `when: { jayTrust: 4 }`. Binds `when`, `requires`, `nextRules`, `outcomeRules`,
   `reflections`, `aftermath` and `finalMessage` alike.
4. **The root node may not reference any derived-state key in any matcher or variant condition.**
   See the Day-boundary contract below.

### Implementation impact

**NONE.** Content and config only.

---

## SPEC-03 — `carrying_it`

**v1.0 ambiguity.** Nine trajectories listed in §H.3; the §H.1 example rules produce eight distinct
values. `carrying_it` — *"fronted something for someone else and are still holding it"* — is
unreachable.

### Decision

**`carrying_it` is kept. It is not a state key.** It is a trajectory value, driven by
`daySixAct: "fronted"`, an enum already declared in v1.0 §D.5 and otherwise read by nothing.

It is kept rather than deleted because it is the district's most distinctive landing: taking someone
else's consequence and still carrying it is not `in_it` (you took it and it landed on you) and not
`on_your_own` (you held the line and burned the people holding it). Deleting it would leave
`daySixAct: "fronted"` as an authored branch with no terminal consequence, which is worse than the
inconsistency it was reported as.

**Final rule list — nine rules, nine trajectories, ordered, first match wins:**

| # | `when` | → |
|---|---|---|
| 1 | `dayFive: "took"`, `exposureBand: "exposed"` | `in_it` |
| 2 | `heatBand: "burnt"` | `in_it` |
| 3 | `daySixAct: "fronted"` | `carrying_it` |
| 4 | `dayFive: "took"`, `creditBand: "owed"` | `useful` |
| 5 | `disciplineBand: "held"`, `jayBand: "tight"` | `kept_both` |
| 6 | `disciplineBand: "held"` | `moving` |
| 7 | `jayBand: "broken"`, `tundeBand: "broken"` | `on_your_own` |
| 8 | `creditBand: "owed"`, `repBand: "known"` | `the_one_they_call` |
| 9 | `repBand: "nobody"`, `heatBand: "clear"` | `invisible` |
| — | `outcomeDefault` | `holding` |

`carrying_it` sits at rule 3: after the two rules where the thing you were carrying has already
detonated, before every rule about what you built. **v1.0's redundant `{exposureBand: "clear"} →
holding` rule is deleted** — `outcomeDefault` covers it, and a rule that duplicates the default is
an invitation to edit one and forget the other.

### Authoring rule

- `daySixAct` is `enum { none, fronted, covered, sat }`, initial `none`, set exactly once, on Day 6.
- **The v1.0 boolean flag `fronted_it` is deleted.** It duplicated `daySixAct: "fronted"`, and two
  keys carrying one fact desync the moment one is edited. `daySixAct` is the single authority.
  Flag count is 11, not 12.
- Rule ordering is load-bearing and must be reproduced verbatim.
- Every trajectory must be reached by at least one `testPlaythrough`. Nine trajectories, minimum
  nine playthroughs, plus one for `holding` via the default. **Ten minimum.**

### Implementation impact

**NONE.** Content only.

---

## SPEC-04 — `kaiStrain`

**v1.0 ambiguity.** `kaiStrain` is a real state variable (§D.4: Kai carries strain only, 0–6). The
defect is that the §E.1 canonical choice example — the most-copied block in the document — writes
`"nextRules": [{ "when": { "kaiStrain": 3 }, ... }]`, a raw integer reference that violates the
document's own validator rule 10.

### Decision

**The variable is kept. The example is wrong and is corrected to `{ "kaiBand": "hostile" }`.**

Two things follow, both closures rather than changes:

- **`kaiBand` is added to the band contract** (SPEC-02, band 12), which is what makes the corrected
  example legal.
- **Validator rule 10 is confirmed to bind `nextRules`**, not only `when` and `requires`. `nextRules`
  uses the same `matchesAll` matcher (`evaluationService.js` — `choice.nextRules.find(r =>
  matchesAll(r.when, nextState))`) and carries identical brittleness. v1.0's rule text named only two
  of the six call sites.

### Authoring rule

Rule 10 restated in full: **no `when` object anywhere in a scenario may reference a raw integer state
key.** That covers `messageVariants`, `threadVariants`, `requires`, `nextRules`, `outcomeRules`,
`reflections`, `aftermath` and `finalMessage`. Enum and boolean keys are referenced directly; integer
keys only ever through their band.

### Implementation impact

**NONE.** Documentation fix plus one band declaration.

---

## SPEC-08 — Local save cardinality and the persistence contract

**v1.0 ambiguity.** Persistence was unspecified. U-06 established that the client owns state, the
server is stateless, `_scenarioState` dies with the widget, and `/today` returns only the root node.

### Decision — the persistence contract

**Storage.** One key per scenario: `run:the_streets`. **Exactly one active snapshot per scenario at
any time.** No save slots, no branching saves. Replay overwrites.

**Snapshot payload:**

```
snapshotVersion    int     format version of this record
contentRevision    int     scenario content revision at write time
scenarioId         string
nodeId             string  the NEXT day's opening node
day                int     the day that node opens
state              map     opaque, verbatim, including derived bands
runningTotal       object  StatDelta
breakdown          array   TurnBreakdown[] for the whole run to date
visitedLocations   array   string[]
startedAt          string  ISO-8601, run creation
updatedAt          string  ISO-8601, last write
phase              enum    "active" | "complete"
```

**When a snapshot is written.** At **day boundaries only**, and at terminal. Never per turn.

A day boundary occurs when `/respond` returns a non-terminal `node` whose `day` differs from the
current node's `day`. On receipt of such a response the client writes the snapshot **immediately, as
the first action after parsing the response and before any interstitial, transition or UI state
change.** That reduces the loss window to milliseconds and is the single most important sequencing
detail in this contract.

**Written after day-close effects.** The response already carries post-`setState`,
post-`derivedState` state (`evaluationService.js:291`). There is no separate day-close mutation to
sequence around.

**Which node is stored: the next day's opening node.** Not the completed day's terminal node. A
resume therefore opens on the new day, which is the only reading that makes "return tomorrow" mean
anything.

**Killed during a choice.** No snapshot was written mid-day, so the run resumes at the start of the
current day and the player replays it. The abandoned turn will have been logged server-side by
`resultsLog` — a single duplicated analytics row, acceptable, and worth knowing about before it shows
up in the funnel.

**Killed during the day-close transition.** Because the write precedes the transition, this is the
same case: resume at the start of the current day. If the process dies between the HTTP response and
the write — a window of milliseconds — the outcome is identical. **The design is deliberately
loss-tolerant in one direction only: a player may lose a day, never gain one.**

**Analytics identity — required, and it lands here rather than later.** `resultsLog.js` writes one
row per `/respond` — `{testerId, scenarioId, nodeId, choiceId, scores, terminal, timestamp}`, fired
unconditionally at `routes/scenarios.js:47` — with no run, session or device identity. Every row in
the current log is `"anonymous"`, and `the_secret`/`establish`/`continue` appears eight times across
40 rows with no way to separate eight players from one player eight times. Replaying a partially
completed day therefore re-emits every turn of that day indistinguishably from a first attempt —
and independently of replay, **the Day-1→Day-2 return rate cannot be computed from the current log
at all.** Since that rate is the Days 2–3 retention gate and "do they want to come back tomorrow"
is the Day 1 gate, the instrument must exist before either.

Four additive client-supplied fields, logged alongside the existing row. No new tier, no
authentication:

- `runId` — generated at run creation, held in the snapshot, sent with every `/respond`
- `installId` — stable per device, persisted beside `AppState`, sent as or with `testerId`
- `turnSeq` — monotonic within a run, so `(runId, nodeId, higher turnSeq)` is identifiably a replay
- Analysis rule: dedupe on `(runId, nodeId)`, keeping the **last** row — the turn that stuck

Player-facing scoring is unaffected either way: `runningTotal` is client-held and restored from the
snapshot, and the log's `scores` field is a per-turn delta that nothing sums.

**Terminal.** On a terminal response the client **replaces** the active snapshot with
`phase: "complete"` plus the terminal payload (consequence, landing, reflection, aftermath, final
message, breakdown), rather than clearing it. On relaunch, `phase: "complete"` routes straight to the
outcome screen. The record is cleared only when the player leaves that screen, at which point a
minimal completed-run record — `{ scenarioId, trajectory, completedAt }` — is appended to a separate
history key for streaks and "you've played this before". **Clearing on receipt of the terminal
response would lose a player's entire seven-day ending to one badly-timed app kill.**

**`startedAt`** is provenance and display only: run age, "started last Tuesday". **It does not gate
day availability.** Whether Day 3 unlocks on a real calendar day is a product decision deliberately
kept out of the persistence contract, so it can be changed without touching saved runs.

**`snapshotVersion`** versions the record format. A snapshot with an unknown version is discarded.

**`contentRevision`** versions the scenario content. The scenario declares it; the server echoes it;
the client stores it at write and compares at read. **On mismatch the run is retired, not resumed** —
the player is told the story has been updated and offered a fresh start. This is RF-2 and it is not
retrofittable: without it, editing a `stateSchema` range mid-week resumes live runs against a schema
that no longer exists, and the failure is silent.

The two versions are orthogonal and both are needed. `snapshotVersion` governs whether the client
can **parse** the record; `contentRevision` governs whether the record is still **meaningful**. A
snapshot can be perfectly parseable and semantically dead.

**Retiring the run on mismatch is a product decision, not an implementation detail**, because it
destroys a player's in-flight seven-day run and they see it happen. Recorded here as Richard's
decision, with alternatives: **retire** (recommended), **resume anyway**, or **soft-migrate**
against a declared key map. Resume-anyway is rejected for MVP specifically because it fails silently
— a removed state key makes every `when` referencing it false, and the player completes a run whose
branches quietly stopped firing, with no error at any layer.

**Cross-scenario `AppState`** (`savvy`/`integrity`/`streetSmarts`) persists **separately**, under its
own key, with its own lifecycle. It is never inside the run snapshot, is not cleared when a run
completes, and **is never readable by `when`** — the moment scenario logic can read the profile, the
scenario becomes unbalanceable and untestable.

### Authoring rule

- Every day has **exactly one** transition to the next day. Multiple day-boundary edges out of one
  day are not permitted — the snapshot would be ambiguous about which node opens tomorrow.
- Every node declares `day`. The boundary is detected from it.
- No node before Day 7 carries a `terminal` block.

### Implementation impact

**REQUIRED — contract only, described, not implemented.**

- **Backend:** a node-read endpoint taking `{scenarioId, nodeId, state}` and returning the same
  `publicNode` payload `/respond` returns. It must recompute `derivedState` from the supplied raw
  state before resolving, so it is idempotent regardless of what the client stored. Server remains
  stateless.
- **Backend:** `contentRevision` on the scenario, echoed in both `/today` and node responses.
- **Client:** a storage dependency, the snapshot read/write, `TurnBreakdown.toJson`/`fromJson`, and
  `AppState` persistence.

---

## SPEC-12 — Hidden state and public state

**v1.0 ambiguity.** §D.2 asserted The Streets "should not rely on the client hiding secret state."
The audit established that the client receives the full state map at `/today`
(`personaService.js:200`) and on every turn (`evaluationService.js:254, 291`), and must return it for
the engine to function. `requires` is re-checked server-side (`evaluationService.js:171`) but against
client-supplied state.

### Decision — **A and B, jointly. Not C.**

**Withdraw `visible: true`** (A) and **state the non-guarantee explicitly** (B).

- **`visible: true` is withdrawn from the schema.** It is not merely unnecessary; it is
  unimplementable. The client must hold the map. A field marking one key visible while thirty-three
  others ship alongside it is a comment pretending to be a mechanism.
- **The HUD reads `state.money` directly.** No projection, no flag.
- **All state may exist in the persisted snapshot**, verbatim, including every band. Filtering it
  would break resume for zero benefit.
- **`publicNode` projects the node, not the state**, and that is correct and stays as-is. It already
  strips `scores`, `setState`, `requires`, `reasons`, `next`, `nextRules`, `terminal` and unmatched
  variants (`personaService.js:158–178`). **That is the projection that matters** — it is what stops
  the client seeing the consequences of choices it hasn't made.
- **No state field is omitted from client payloads.**

**C is explicitly rejected.** Server-authoritative runs would require a store, identity and auth,
none of which exist, to defend a single-player narrative game whose only exploit is spoiling your own
story. The cost is a new architectural tier; the benefit is preventing a player from disappointing
themselves.

**Does The Streets depend on secrecy for gameplay? No.** It depends on **non-display**. The
distinction is the whole answer. A player who never sees `heat` experiences accumulation as dread; a
player who reads it off the wire has traded that for a number. Nothing breaks — they have simply
bought a worse product than the one they were given.

**The recorded position, verbatim, for v1.1:**

> Hidden state in The Streets is a presentation boundary, not a security boundary. The client holds
> the full state map by architectural necessity. Gate evaluation is server-side but not
> server-authoritative against a modified client. This is accepted for MVP and must be revisited
> before any competitive, social, or leaderboard feature — each of which would convert a harmless
> single-player exploit into a real one.

### Authoring rule

- Do not author any beat whose effect depends on the player being unable to discover a state value.
- No mechanic — leaderboard, versus, shared score, tradeable item — may be added to The Streets while
  this position stands.

### Implementation impact

**NONE.** A field is withdrawn and a position is recorded. `publicNode` is unchanged.

---

## SPEC-13 — Time variants

**v1.0 ambiguity.** §I.3 claimed eight environments across three times gave "24 apparent locations
for eight environments' cost." `registries.json → scenesNote` states the opposite: *"a room seen at
two times is two scene tokens and two assets."* Career already paid it — `scene.desk_evening` and
`scene.desk_day` are two full assets for one room.

### Decision

**Ten scene tokens across eight locations. A second time must be earned, and is capped at two
locations.**

| Location | Times | Tokens | Second time earned? |
|---|---|---|---|
| `block_walkway` | dusk, night | **2** | **Yes.** The district's anchor image, and the dusk→night shift is the visual spine of the whole run. |
| `chicken_shop` | day, night | **2** | **Yes.** The only location genuinely used in two social registers — Day 1 daytime and Day 6 night. |
| `bedroom` | night | 1 | private, reflective, night by nature |
| `home_kitchen` | evening | 1 | family scenes are evening |
| `corridor` | day | 1 | college |
| `cage` | dusk | 1 | |
| `stairwell` | night | 1 | the pressure environment |
| `bus_stop` | night | 1 | |
| **Total** | | **10** | |

**A single asset may not represent two times.** `resolve.py` reads one `default_time` per scene and
offers no per-node override; a scene token *is* a time. Attempting to reuse one asset across two
times would mean authoring both beats at one lighting state, which is a craft compromise the visual
contract exists to prevent.

**No tooling solution.** Adding a per-node time override to `resolve.py` would only pay for itself if
rooms repeated across times often — Career evaluated this and drew two assets instead. At two
qualifying locations, so does The Streets.

**Day 4's three-lane divergence needs no new environments.** The three lanes route to `cage`
(Tunde), `chicken_shop` (Amara) and `block_walkway` (Kai) — all already in the library. v1.0 §F.3's
"two extra environments" was double-counting.

### Revised asset budget

The number moved for two reasons pulling in opposite directions: time variants cost more than v1.0
assumed, and rear figures cost less (`registries.json` — Ray and Dana both carry `turned: null`;
rear figures are optional per character).

| Category | v1.0 | v1.1 | Note |
|---|---|---|---|
| Bodies, front | 6 | 6 | |
| Bodies, rear | 6 | **3** | Jay, Tunde, Amara only. Dee is never turned; supporting characters don't need it. |
| Registers, front | 26 | 26 | 4 principals × 5 + 2 supporting × 3 |
| Registers, rear | 6 | **3** | |
| Wardrobes, front | 10 | 10 | |
| Wardrobes, rear | 6 | **3** | |
| Environments | 8 | **10** | scene tokens, all full cost |
| Lighting overlays | 6 | **0** | the category does not exist |
| Props | 18 | 18 | |
| Vignettes | 6 | 6 | |
| **Total** | **~96** | **~85** | |

**~85 SVG is the planning baseline, not a contractual cap.** Nothing in the source documents fixes
the number; it is arithmetic over the current cast, environment and prop decisions, and the skeleton
will move it. Ten of them are environments and each needs its own occlusion design and alpha test,
which is where the schedule actually lives.

**Overage rule:** the baseline may be exceeded when the locked skeleton demonstrates a specific need
— a required frame with no asset to compose it. It may not be exceeded for craft, coverage or
variety. Any increase above **+10% (≈94)** is a budget decision requiring named sign-off, not an
authoring choice, and the count is re-derived from the asset manifest at the end of the skeleton
phase rather than carried forward from this document.

### Authoring rule

- A location is a **scene token**, not a room. `scene.block_walkway_dusk` and
  `scene.block_walkway_night` are two entries in `registries.json` and two assets.
- Adding a third dual-time location requires a named dramatic justification and a budget decision,
  not an authoring choice.

### Implementation impact

**NONE.** Config and assets.

---

## SPEC-14 — Text layer

**v1.0 ambiguity.** §I.1 treated `maxPerNode: 3` and the 120-character bubble ceiling as hard
constraints on all authoring. The audit found `textLayer: "native"` in
`mapping.the_instruction.json`, bubbles defaulting off (`personaService.js:128`,
`IRX_SCENE_BUBBLES` unset → off), and `bubble_nodes.json` opting in six nodes total.

### Decision

**`textLayer: "native"` for The Streets globally, with per-node bubble opt-in capped at eight nodes.**

Native is the default for four reasons, none aesthetic: text stays selectable, it reflows, it honours
OS text size — which for a 14–24 audience on phones is an accessibility floor, not a nicety — and
95 prose-led nodes under a 120-character-per-bubble ceiling would deform the writing rather than
discipline it.

**Bubbles are opt-in, per node, for beats where seeing the line land in the room *is* the beat.**
Reserved for: the Day 5 ask, the Day 6 landing, and no more than six others chosen after the first
composed frames exist. **Cap: eight. Hard.** Beyond that the treatment stops being a signal.

**Mode rules:**

| Mode | Text treatment |
|---|---|
| `scene` | Native by default. Bubbles only if the node is in `bubble_nodes.json`. |
| `montage` | Captions only, ≤40 chars, ≤3 panels. Never bubbles. |
| `remote` | Native. The distinct-bubble styling of v1.0 §I is not available under native and is not needed — the beat is carried by prose and an empty frame. |
| `absent` | `exitBeat`, one line, native. |
| `messages` | No artwork. Native by construction. |
| `none` | No artwork, deliberate blank. Native. |

**Narration is permitted** on native nodes — it is simply prose. The v1.0 rule of zero narration in
`scene` mode was a bubble-mode constraint and does not bind here.

**Prose budget under native.** The 120-character cap binds only bubble-enabled nodes. Native nodes
get a **soft guidance of ~700 characters per node message, warned not failed** by the validator. The
v1.0 thesis — that the visual layer must *absorb* narration rather than accompany it — still holds,
but it is enforced by editorial judgement and the 390pt read, not by a character count that no longer
has a mechanical reason to exist.

**`headAnchors` requires no additional use.** It is already carried
(`scene_render.dart`) and unused, existing so that "native dialogue, if it ever happens, needs no
server change." The Streets does not need speech positioned against heads in the artwork; that is a
future capability, not an MVP one.

### Authoring rule

- `mapping.the_streets.json` declares `"textLayer": "native"`.
- A node gets bubbles only by explicit entry in `bubble_nodes.json`. Maximum eight.
- Bubble-enabled nodes obey ≤3 bubbles and ≤120 characters each, engine-enforced (the composer
  throws).
- Native nodes: ~700 characters soft, warned.

### Implementation impact

**NONE.** Config only. Both mechanisms are in production.

---

## RF-10 — Silent state-key dropping

**Finding.** `evaluationService.js:16` — `const schema = stateSchema[key]; if (!schema) continue;`.
A `setState` key absent from `stateSchema` is silently discarded. Paired with `matchesAll`'s
`if (!(key in state)) return false`, a typo produces a mutation that never happens and a condition
that never fires, with no error. There is no runtime scenario validation anywhere
(`loadScenario` is `JSON.parse(readFileSync)`).

### Decision — validator requirements

| Condition | Verdict |
|---|---|
| `setState` key not in `stateSchema` | **HARD FAILURE** |
| `when` key not in `stateSchema` and not in `derivedState` | **HARD FAILURE** |
| Band referenced in `when` but not declared in `derivedState` | **HARD FAILURE** |
| Band whose `from`/`minus` names a key that is not a declared int | **HARD FAILURE** |
| Band whose `bands` are not in descending `min`, or lack a `-999` terminator | **HARD FAILURE** |
| Raw integer key referenced in any `when` | **HARD FAILURE** (rule 10, all six call sites) |
| `requires` not an array | **HARD FAILURE** |
| `requires` containing an empty clause `{}` | **HARD FAILURE** — matches everything; always an authoring error |
| `requires: []` | **WARNING** — legal and means "unrestricted", but is almost always a deleted condition |
| Band referenced by the **root node**'s `messageVariants` or `requires` | **HARD FAILURE** — see the day-boundary contract |
| State key declared but never written by any choice | **WARNING** |
| State key declared and written but never read by any `when` | **WARNING** |
| `messageVariants` > 3 on a node | **HARD FAILURE** |
| Bubble-enabled node with > 3 bubbles or a bubble > 120 chars | **HARD FAILURE** |
| Native node message > 700 chars | **WARNING** |
| Trajectory with no reaching `testPlaythrough` | **HARD FAILURE** |
| Node unreachable, or choice reachable in no state | **HARD FAILURE** |

**Warnings must be printed and counted, never suppressed.** The distinction is that a failure means
the scenario is provably broken; a warning means it is probably wrong.

### Implementation impact

**REQUIRED — tooling.** A build-time scenario validator. **Not runtime**: the engine stays as it is,
and nothing about this changes `evaluationService`. **It must run green against `the_secret.json` and
`the_instruction.json` unmodified before The Streets uses it** — if it flags a real defect in either,
that is the check working and the defect gets its own decision, not a silent fix.

---

## RF-11 — Global node ID collisions

**Finding.** `renderBlocks.js` keys blocks by `nodeId` alone with no scenario namespace, and
`blockFor(nodeId, variantIndex)` looks up globally. Verified: the merged `render_blocks.json` is the
exact union of the two per-scenario files — 30 + 23 = 53, **zero collisions today**. At 148 nodes
with The Streets, a duplicate would silently render another scenario's artwork.

### Decision

**Node IDs are globally unique across all scenarios. A collision is a hard build failure.**

Scenario-local IDs were considered and rejected: namespacing would change `blockFor`'s signature,
`dump_render.py`'s output shape and every fixture — an engine change, to solve a problem a build-time
assertion solves for free.

**Mandatory prefix convention**, which makes collisions nearly impossible before the check even runs:

| Scenario | Prefix | Status |
|---|---|---|
| `the_secret` | *(none)* | grandfathered, unchanged |
| `the_instruction` | *(none)* | grandfathered, unchanged |
| `the_streets` | `d<n>_` | e.g. `d5_the_ask`, `d5_reaction` |
| future | scenario-distinctive prefix | |

**Existing scenarios are not renamed.** Renaming node IDs would invalidate every render block,
fixture and `testPlaythrough` for zero benefit.

### Implementation impact

**REQUIRED — tooling.** One assertion in the render-block concatenation step. No engine change.

---

## Render-block collision rule

**Decision.**

- **Duplicate render-block keys in the merged `render_blocks.json` are illegal. Hard build failure.**
- **No byte-identical exception.** Two scenarios independently producing the same key is a node-ID
  collision (RF-11) regardless of whether the payloads currently agree. A byte-identical exception
  passes today and silently overrides tomorrow, the first time one of the two is edited.
- **No override behaviour of any kind.** No last-wins, no first-wins, no explicit override key.

Note this is about *block keys*, not *block content*. **Two different nodes resolving to the same
render block is normal and desirable** — the cache key is the sha256 of the canonicalised block
(`cacheKey.js`), and collapsing identical visuals is the point. That is content-level sharing and is
unaffected by this rule.

### Implementation impact

**REQUIRED — tooling.** Same assertion as RF-11. No engine change.

---

## `requires` semantics

**Confirmed as the v1.1 authoring contract**, verified in source at `personaService.js:53–66`.

```
requires: [ {A, B}, {C} ]   ==   (A AND B) OR C
```

`requires` is an **OR of clauses**; each clause is an **AND of pairs**. Disjunctive normal form.
One shared `matchesAll`, six call sites, no divergence. Filtered in `publicNode`
(`personaService.js:162`) and re-checked on submit (`evaluationService.js:171`).

| Case | Behaviour |
|---|---|
| `requires: []` or absent | Matches everything. The choice is unrestricted. |
| Missing state key | The clause is **false**. Not an error at runtime — a hard failure at build time. |
| Missing derived band | Same. **Note the root node**, where no band key exists at all. |
| Invalid operator | There are none. `when` is strict equality only, no nesting. |
| `NOT` | **Does not exist.** |
| Complements | Enumerated as OR clauses: "anything except `sat`" is `[{daySixAct:"none"},{daySixAct:"fronted"},{daySixAct:"covered"}]`. |

**Complement guideline:** if a complement needs more than three clauses, prefer an explicit flag or a
narrower enum. **Warning, not failure.** A hard cap on a legal construction invites the exact
workaround it was meant to prevent — an author who hits a wall invents an inverse boolean, which is
the state explosion the rule was guarding against. The warning surfaces the smell; the author
decides.

### Implementation impact

**NONE.** Documentation of existing, verified behaviour.

---

## Message / variant caps

**Decision — both caps, with mode-specific rules.**

| Limit | Value | Enforcement | Applies to |
|---|---|---|---|
| `messageVariants` per node | **3** | Validator, hard fail | every node |
| Bubbles per node | **3** | Engine — the composer throws | bubble-enabled nodes only |
| Bubble length | **120 chars** | Validator, hard fail | bubble-enabled nodes only |
| `exitBeat` | **1**, 120 chars | Validator, hard fail | `absent` |
| Montage panels | **3** | Validator, hard fail | `montage` |
| Montage caption | **40 chars** | Validator, hard fail | `montage` |
| Native message | **~700 chars** | Validator, **warning** | native nodes |
| Bubble-enabled nodes per scenario | **8** | Validator, hard fail | scenario-wide |

The three-panel montage cap is geometry, not preference: `anchors.montage` sets `panelWidth 440`
and `gap 48`, so four panels span 1904 on a 1600 canvas.

**The variant cap is the real one.** The Instruction runs 24 variants across 23 nodes — 1.04 per
node. The Streets at 95 nodes with 34 state keys extrapolates past 200 uncapped, and variant prose,
not node count, is where content cost actually accumulates.

### Implementation impact

**NONE beyond the validator** already required by RF-10.

---

## Day-boundary / terminal lifecycle contract

**Decision.**

**Day completion.** A day completes when the player selects a choice whose resolved `next` is a node
whose `day` differs from the current node's. Identical for Days 1 through 6. There is no separate
day-close node type, no day-close event, and no engine concept of a day — it is content metadata plus
a client-side comparison.

**Canonical opening rule.** Every reachable path through Day N must resolve to **exactly one
canonical Day N+1 opening node**. Multiple choices and multiple edges may converge on that node —
that is the spine pattern and it is encouraged.

Validator check: for each day N, the set of distinct target node IDs whose `day` differs from N must
have cardinality exactly 1.

The constraint is not about edges. It is that a resumed day opens with an **empty transcript**, so
the day's opening node must be authored as a cold open. Two canonical openings would work
mechanically but doubles that burden and makes it likely one is written as a continuation of a scene
the player can no longer see.

**Day 7 terminal.** A choice with a `terminal` block, or `next: null` resolving to one — the existing
engine detection (`evaluationService.js`: `nextNodeId === null || (undefined && choice.terminal)`).
**No node before Day 7 may carry a `terminal` block.** Validator-enforced.

**Outcome logic may not run before Day 7.** This is engine-guaranteed, not merely a rule:
`resolveOutcome` is called only inside the terminal branch.

**Ordering at terminal:** `setState` → `derivedState` → reflection picked from `nextState` (**before**
the outcome key is written, so a reflection can never read the outcome — `pickReflection(scenario,
nextState)`) → outcome resolved into `finalState` → aftermath and `finalMessage` resolved against
`finalState`. **All engine behaviour, all already correct, none of it changes.**

**Persistence relative to that ordering:** everything above happens server-side within one
`/respond`. The client receives the complete terminal payload and only then writes
`phase: "complete"`. **Persistence is strictly after aftermath and reflection**, because both arrive
in the same response.

**Node persisted at a boundary:** the next day's opening node ID, with the post-mutation state from
the same response.

**The root-node constraint.** `initialState` (`personaService.js:31–49`) sets `stateSchema` initials
and applies `seed`, but **never calls `applyDerived`**. Derived band keys therefore do not exist in
the state returned by `/today`, and `matchesAll` returns false on a missing key. Consequently:

> **The root node may not reference any derived-state key in any matcher or variant condition.**
> This binds `messageVariants`, `threadVariants` and `requires` on the root node and its choices. It
> may reference raw enum and boolean keys, which do exist at that point. Every subsequent node is
> unaffected, because `/respond` applies `applyDerived` on every turn — and resumed days are
> unaffected, because a snapshot is always written from a `/respond` response and therefore always
> contains the bands.

**Technical boundary, recorded so the rule is not later loosened by someone who rediscovers half of
it:**

| Call site | State at root | Safe? |
|---|---|---|
| `messageVariants` | `initialState` output, no derived keys | **Unsafe** |
| `threadVariants` | same | **Unsafe** |
| `requires` (in `publicNode`) | same | **Unsafe** |
| `requires` (re-check, `evaluationService.js:171`) | client-returned root state, still underived | **Unsafe** |
| `nextRules` | `applyDerived(applySetState(...))` — bands present | **Safe** |

`nextRules` on a root-node choice is technically fine. **The blanket rule is adopted regardless.**
The root node carries one node's worth of content and typically one choice; the exception buys
nothing, and a rule that holds for four matchers but not the fifth beside them will be
misremembered.

This has never surfaced because The Instruction's root node has a single `continue` choice and no
variants. It would surface on Day 1 of The Streets and the failure would be silent: the default
message every time, with no error.

**The node-read endpoint must recompute derived state** from the raw keys before resolving, so that
resume is correct even if a snapshot were ever written from a source that lacked them.

### Implementation impact

**REQUIRED — backend contract, described only:** the node-read endpoint, which must apply
`derivedState` before resolving the node. **NONE** for day semantics, terminal detection, outcome
ordering, reflections or aftermath — all existing, all correct.

---

## Final authoring contract

1. Every node declares `day` (1–7) and a node ID prefixed `d<n>_`.
2. Every reachable Day N path resolves to exactly one canonical Day N+1 opening node; multiple edges
   may converge on it. No `terminal` block before Day 7.
3. **The root node may not reference any derived-state key in any matcher or variant condition.**
4. `when` references bands, enums and booleans — **never a raw integer key**, in any of the six
   matcher call sites.
5. Bands declare `from`/`minus` on integer keys only, in descending `min` order, terminating at
   `-999`.
6. `requires` is DNF: OR of clauses, AND within a clause. Complements enumerated as OR clauses;
   beyond three clauses, prefer a flag or a narrower enum (guidance, warned not failed).
7. Maximum 3 `messageVariants` per node.
8. Branches diverge for at most two nodes before rejoining a spine node. Day 4 is the sole exception.
9. `textLayer: "native"`. Bubbles by explicit opt-in only, eight nodes maximum, ≤3 bubbles and ≤120
   chars each.
10. Native node messages ~700 characters as guidance.
11. Every state key written by ≥1 choice and read by ≥1 `when`.
12. Every one of the nine trajectories reached by ≥1 `testPlaythrough`; ten playthroughs minimum.
13. Every environment is a scene token including its time. Two dual-time locations, no more.
14. Two figures maximum per frame.
15. No beat depends on the player being unable to discover a state value.
16. No node permits extraction of a procedure. The camera cuts before method; `mode: "none"` is the
    mechanism for a deliberate blank.

---

## Validator contract

Build-time only. No runtime validation is added. Two layers, no requirement removed or weakened.

### Layer A — static structural validation

Single pass over the scenario, config and asset manifest. No graph traversal, no state simulation.
Fast enough to run on save.

**Hard failures:** unknown `setState` key · unknown `when` key · undeclared band reference · band
`from`/`minus` on a non-integer key · non-descending or unterminated band list · raw integer in any
`when` · `requires` not an array · empty clause in `requires` · derived-state key referenced by the
root node in any matcher or variant condition · >3 `messageVariants` on a node · >3 bubbles or >120
chars on a bubble node · >8 bubble-enabled nodes · >3 montage panels · >40-char caption · >1
`exitBeat` · `terminal` block before Day 7 · duplicate node ID across scenarios · duplicate
render-block key · invalid render mode · register requested outside a character's declared set ·
missing render asset · invalid character or prop reference · outcome rule referencing an undeclared
trajectory · trajectory with no outcome rule.

**Warnings:** `requires: []` · state key never written · state key never read · native message >700
chars · complement enumerated in >3 clauses.

### Layer B — graph and state simulation

Requires traversal and state simulation. Runs on commit.

**Hard failures:** unreachable node · choice reachable in no state · trajectory unreachable ·
trajectory with no reaching `testPlaythrough` · more than one canonical Day N+1 opening node · a day
reachable by no path · state mutation that can never occur · delayed consequence that can never
trigger · branch that permanently diverges without rejoining a spine · non-terminating path ·
environment failing continuous occlusion y=600→900.

### Precondition

Both layers run green against `the_secret.json` and `the_instruction.json` **unmodified**. If either
fails, fix the validator — unless the failure reveals a genuine existing contract violation, which
gets its own decision rather than a loosened rule.

---

## Implementation contract

### Backend

1. **Node-read endpoint** — `{scenarioId, nodeId, state}` → `publicNode` payload. Must apply
   `derivedState` before resolving. Server stays stateless. Reuses `loadScenario`,
   `resolveNodeContent`, `publicNode`, all already exported.
2. **`contentRevision`** — additive scenario field, echoed in `/today` and the node response.
3. **`lockedLabel`** *(recommended, not blocking)* — in `publicNode`, stop filtering; emit
   `available` on every choice and substitute `lockedLabel` where present and failing. Behaviour
   byte-identical when the field is absent.

**No changes to:** state mutation, `derivedState`, `matchesAll`/`matchesAny`, `nextRules`, terminal
detection, `outcomeRules`, reflections, aftermath, `finalMessage`, any render module, the cache key.

### Flutter

1. **Storage dependency** and the snapshot read/write per SPEC-08.
2. **`TurnBreakdown.toJson`/`fromJson`**; `StatDelta.toJson` already exists.
3. **`AppState` persistence**, separate key, separate lifecycle.
4. **Resume path** — on launch, read the snapshot, validate `snapshotVersion` and `contentRevision`,
   call the node-read endpoint, enter at the day-opening node with an empty transcript.
5. **`ScenarioChoice.available` and `lockedLabel`**, defaulting `available: true`; pass
   `disabled: _choiceInputLocked || !choice.available`. `ChoiceTile` already renders disabled at
   0.42 opacity — **no widget work**.
6. **Streets `DistrictTheme`** entry and the home-screen scenario-count case.

**Not required:** transcript persistence · state projection · `visible` handling · any render or
`SceneView` change. **Flagged, not scheduled:** `_isNeighborhood` (`scenario_screen.dart:159`) should
become `DistrictTheme` properties rather than growing a `||` per district — its own change, not
Streets work.

### Tooling

1. **Scenario validator** per the validator contract.
2. **Render-block concatenation assertion** — duplicate node ID or block key fails the build.
3. `dump_render.py` run for `the_streets`, output concatenated.

### Content / config

`the_streets.json` · `mapping.the_streets.json` with `textLayer: "native"` ·
`registries.json` additions (6 characters, 10 scene tokens, 18 props, 6 vignettes, Streets keys
appended to `scoring_keys_forbidden`) · `anchors.json` additions (scene slots, prop anchors, bubble
placement) · `bubble_nodes.json` entries, maximum 8.

### Visual assets

**~85 SVG** per SPEC-13: 6 front bodies, 3 rear, 26 front registers, 3 rear, 10 front wardrobes, 3
rear, 10 environments, 18 props, 6 vignettes.

---

## Sequencing recommendation

| # | Step | Gate |
|---|---|---|
| 1 | **Verify `anchors.json`** — one global character contract or per-figure sockets | Character production brief is unambiguous |
| 2 | **Build the scenario validator** | Green against both existing scenarios, **unmodified** |
| 3 | **Author `stateSchema`, 12 bands, 9 outcome rules** | Validator green. Every band has ≥2 reachable values. |
| 4 | **Author the 95-node skeleton — no prose, no assets** | Validator green; exhaustive path simulation; all 9 trajectories reachable; multi-pair `requires` asserted |
| 5 | **Geometry on paper** — 26 tilt values, occluding element per environment, dialogue vs prop column | Every scenario-adjacent register pair clears ≥5° or is flagged for measurement |
| 6 | **Day 1 prose + first environment + first figure** | Occlusion alpha test; 390pt readability; asset locked |
| 7 | **Day 1 assets (~18 SVG)** | Each through the §J.1 gate |
| 8 | **Day 1 playable — current engine, no persistence, one sitting** | **Does it feel like a game?** Playtest 14–24s. |
| 9 | **Node-read endpoint + `contentRevision` + client persistence + analytics identity** (`runId`, `installId`, `turnSeq`) | Kill/relaunch resumes at the day boundary; stale `contentRevision` retires the run; a replayed day is distinguishable in the log |
| 10 | **`lockedLabel`** | Parity fixtures unchanged |
| 11 | **Days 2–3, retention gate** | Day-1 → Day-2 return rate instrumented |
| 12 | **Days 4–7, full visual audit, district theme, ship** | Flutter work ≈ theme entry + disabled choice |

**Step 8 precedes step 9 deliberately.** Day 1 needs no persistence, no endpoint and no client
change. The cheapest possible proof that the product is worth building comes before the most
expensive work in the programme.

---

## Remaining unknowns

**NONE — SPEC v1.1 IS CLOSED.**

The cross-check found no remaining contradiction. State mutation, derived bands, differentials,
`nextRules` timing, terminal detection, outcome rules, reflections, aftermath, final messages, the six
render modes, render-block identity, client/server state flow, day-boundary persistence, the nine
trajectories, Day 4 divergence, ten environments, six characters and the no-new-engine principle are
mutually consistent as specified.

Two items are **production prerequisites, not specification blockers**, and both are sequenced as
step 1 and step 2 above:

- **`anchors.json` was not in the audit upload.** `resolvePlan.js:35` reads a single global
  `A.character` block, while `IRX_VISUAL_SYSTEM_SCOPE.md` describes `headSocket` as per-figure
  (figure_a y=210, figure_b y=196). Either reading works for six new characters — one shared contract
  is simpler, two is what the scope document describes and what Ray and Dana were built against. It
  changes no decision in this document, but the character-production brief cannot be written without
  knowing which is true. **One file.**
- **The validator must run green against both existing scenarios before The Streets uses it.** If it
  flags a real defect in `the_secret` or `the_instruction`, that defect gets its own decision — not a
  silent fix, and not a loosened rule.

---

**SPEC v1.1 CLOSED — NO FILES MODIFIED.**