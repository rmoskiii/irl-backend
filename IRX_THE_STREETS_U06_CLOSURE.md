# THE STREETS — U-06 CLOSURE & PERSISTENCE IMPLEMENTATION SHAPE
## Read-only audit of `irx-flutter` (`irl_app` v0.1.0)

**Status: diagnosis complete. No files modified. Read-only.**

**Suggested destination:** `irl-backend/IRX_THE_STREETS_U06_CLOSURE.md` (keep it with the other two
audit documents rather than splitting the trail across repos).

**Inspected:** 38 Dart files, `lib/` in full, `pubspec.yaml`, `pubspec.lock`.

**Every unknown from the original audit is now closed.**

---

## 1. CORRECTION TO THE PREVIOUS CLOSURE — READ THIS FIRST

I told you seven-day resume was a **Flutter-only change with zero backend work**. That was too
strong, and the reason is a single line of client code.

`lib/screens/scenario_screen.dart:174` — `initState` calls `_api.fetchTodayScenario(...)`, and
`GET /api/scenarios/today` returns `getRootView`, which is **always the root node**. There is no way
to ask the backend for the public view of an arbitrary node.

So the client can persist the state map perfectly well — but on relaunch it has nothing to render it
against. State without a node is not a resumable run.

**The corrected claim:**

> Seven-day resume needs **one small read endpoint** on a server that stays stateless, plus client
> persistence. Not a persistence tier, not a database, not auth — roughly twelve lines of Node
> reusing functions `personaService` already exports.

Still far smaller than the run-store the first audit was bracing for. But it is not zero, and the
difference matters when you are sequencing work.

---

## 2. U-06 — CLOSED

**Does Flutter hold and return the state map? Yes, verbatim, and it is lost on dispose.**

`scenario_screen.dart:146`:

```dart
/// Opaque scenario state — initialised by the backend from stateSchema,
/// updated on every /respond, sent back verbatim on the next turn. The
/// client NEVER reads a key out of this map...
Map<String, dynamic> _scenarioState = const {};
```

Set at `:182` from `scenario.state`, replaced at `:454` with `result.state ?? _scenarioState`, posted
back at `api_service.dart` `submitChoice`. The courier discipline is real and enforced by convention
in three separate comments. **Nothing reads a key out of it anywhere in `lib/`.**

**No persistence of any kind exists on the client.** `lib/state/app_state.dart:5`:

> *"Cumulative player stats, held in memory only for the MVP - no local persistence yet. This is
> intentional: the backend's results log is the source of truth..."*

**No storage dependency.** `pubspec.yaml` declares `provider`, `http`, `google_fonts`,
`cupertino_icons`, `flutter_svg`. No `shared_preferences`, no `hive`, no `isar`, no `path_provider`.
Adding one is part of the change.

**Everything run-scoped lives in `_ScenarioScreenState` and dies with the widget:** `_scenarioState`,
`_currentNodeId`, `_runningTotal`, `_breakdown`, `_visitedLocations`, `_transcript`.

---

## 3. THE GOOD NEWS, AND IT IS SUBSTANTIAL

### 3.1 Deserialisation is lenient — the backend can ship first

`lib/models/scenario.dart:1`:

> *"Keeping them as plain, explicit `fromJson` factories (no codegen)..."*

Hand-written factories that read named keys and ignore everything else. **No `json_serializable`, no
`checked: true`, nothing that throws on an unknown field.** A backend emitting `available` and
`lockedLabel` today would be silently ignored by the current client rather than crashing it.

**Backend and client changes can be sequenced independently.** That was the open question and it
resolves the permissive way.

### 3.2 The disabled choice style already exists

`lib/widgets/choice_tile.dart` already takes `disabled` and renders it at `Opacity(0.42)` with all
gesture handlers nulled. It is currently used for input-lock during submission
(`scenario_screen.dart:812`, `disabled: _choiceInputLocked`).

**`lockedLabel` needs no new widget and no new style.** The visual treatment for an unreachable door
is already in the codebase.

### 3.3 A day is naturally a session

`_transcript` is a list of private `_TranscriptEntry` objects holding rendered content — the hardest
thing in the screen to serialise, and the thing you would need to restore a mid-conversation scroll.

**You do not need it.** If The Streets checkpoints at **day boundaries only**, a resume opens at a
day-opening node with a fresh transcript, which is exactly what the screen already does on first
launch. No new rendering path, no scroll restoration.

Three things fall out of that, all good:

- **The hardest serialisation problem disappears** by aligning the save point with the fiction.
- **Save-scumming is structurally impossible.** Quitting mid-day resumes at the start of that day.
  You cannot back out of a decision you dislike — which for a consequence simulator is not a
  limitation, it is the product.
- **It matches the retention model.** One session per day was already the design.

**This should be a stated design rule in v1.1, not an implementation detail.** It is a constraint the
client architecture is handing you for free.

---

## 4. THREE RESUME STRATEGIES

### Strategy A — small read endpoint *(recommended)*

New: `POST /api/scenarios/node` with `{scenarioId, nodeId, state}` → the same `publicNode` payload
`/respond` already returns. `loadScenario`, `resolveNodeContent` and `publicNode` are all already
exported from `personaService.js`; the route is a lookup and a call.

| | |
|---|---|
| Backend | ~12 lines in `src/routes/scenarios.js`. **Server stays stateless** — state still arrives from the client. |
| Client payload | ~1–2 KB of JSON |
| Freshness | Node view is composed fresh, so an asset or scenario edit is picked up on resume |
| Risk | New endpoint accepts client-supplied state, exactly as `/respond` already does. No new exposure. |

### Strategy B — persist the node response *(literally zero backend)*

Store the raw JSON body of the last turn, composed SVG and all, and rehydrate offline.

Genuinely zero backend change. But the payload is tens of KB in shared preferences, and it goes
stale silently — a re-composed asset wouldn't reach a resumed run, and the client can't validate the
`cacheKey` without asking the server anyway. **Caching a rendered artefact to avoid writing twelve
lines is the wrong trade.** Listed because it is the honest answer to "can this truly be done with no
backend work at all": yes, but don't.

### Strategy C — replay the path through `/respond` *(reject)*

`logResult` fires per turn, so every resume would double-log analytics — corrupting the exact
Day-1→Day-2 return metric the retention gate depends on. Scores would also re-apply to `AppState`.
**Reject.**

---

## 5. WHAT ACTUALLY HAS TO PERSIST

More than the state map. Worth enumerating now, because two of these are easy to miss until Day 7.

| Field | Source | Notes |
|---|---|---|
| `scenarioId` | `_scenario!.scenarioId` | — |
| `nodeId` | `_currentNodeId` | the day-opening node |
| `state` | `_scenarioState` | opaque map, stored as-is |
| `runningTotal` | `_runningTotal` | `StatDelta.toJson()` **already exists** (`scenario.dart:218`) |
| `breakdown` | `_breakdown` | **Easy to miss.** Passed to `OutcomeScreen` at terminal. Without it the Day 7 outcome screen shows only Day 7's choices. `TurnBreakdown` (`:309`) has **no `toJson`** — needs one, plus `StatDelta.fromJson` and a `Map<String,String>` round-trip. |
| `visitedLocations` | `_visitedLocations` | drives the location strip |
| cross-scenario stats | `AppState.savvy/integrity/streetSmarts` | **Also easy to miss.** Resets to 50 on every launch. Over seven days the home screen would lie about the player's own history. |
| `startedAt`, `schemaVersion` | new | **RF-2.** Version the snapshot from the first commit. A mid-week `stateSchema` edit must be detectable so a stale run can be retired cleanly rather than resumed into nonsense. Not retrofittable. |

**Not persisted:** `_transcript` (per §3.3), `_revealToken`, `_presentationState`, `_showTyping` —
all presentation state, correctly rebuilt on entry.

---

## 6. `lockedLabel` — the full client cost

Three edits, roughly six lines.

1. **`lib/models/scenario.dart:20` `ScenarioChoice`** — add `final bool available` and
   `final String? lockedLabel`; in `fromJson`, `available: json['available'] as bool? ?? true`. The
   `?? true` default means the current backend keeps working unchanged.
2. **`lib/screens/scenario_screen.dart:812`** — `disabled: _choiceInputLocked || !choice.available`,
   and guard `onTap` on `choice.available`.
3. **`ChoiceTile`** — nothing. The style exists.

Backend side is the three-line change already scoped at `personaService.js:162–175`. The server
already rejects unavailable choices independently at `evaluationService.js:171`, so a disabled tile
that somehow fired would still be refused.

**Because deserialisation is lenient (§3.1), these can ship in either order.**

---

## 7. CLIENT WORK THE STREETS NEEDS REGARDLESS

The previous audit said a Streets node "draws with zero Flutter changes." True of *rendering*.
Not true of *shipping a district*.

| Item | File | Size |
|---|---|---|
| `DistrictTheme` entry for Streets — id, accent, gradient, font, `anchorScenarioId: 'the_streets'` | `lib/theme/district_theme.dart:110` (`Districts.all`) | small, content-shaped |
| Home screen scenario-count case | `lib/screens/home_screen.dart:23` — a hard-coded switch with a comment already flagging it should read `/api/scenarios/list` | one case, or fix the follow-up |
| **`_isNeighborhood` branches** | `scenario_screen.dart:159`, used at `:246` (reveal pacing) and `:733` (location strip) | **a decision, not a line** |

`_isNeighborhood` is the only hard-coded district id in the scenario screen. It gates
reading-time-based reveal pacing and the visited-locations strip. **Both are things The Streets
probably wants** — it is prose-led and moves between locations more than any existing district. So
the question isn't whether to add `'streets'` to the condition; it is whether these should become
`DistrictTheme` properties (`usesReadingPacing`, `showsLocationStrip`) rather than an id check that
grows a new `||` per district.

**Flag it, don't fix it.** It is two booleans on a theme object, but it is a refactor of shipped
behaviour and belongs in its own change, not smuggled into Streets work.

---

## 8. REVISED CHANGE SET

| # | Change | Layer | Size | Blocking? |
|---|---|---|---|---|
| 1a | `POST /api/scenarios/node` | backend, stateless | ~12 lines | **yes** |
| 1b | Run persistence: `shared_preferences` + save/restore + `TurnBreakdown.toJson` + `AppState` persistence + snapshot versioning | client | ~1 file + small model edits | **yes** |
| 2 | `lockedLabel` — 3 lines backend, ~6 lines client | both | trivial | no |
| 3 | Scenario validator (RF-10) | tooling | — | **before authoring** |
| 4 | Streets `DistrictTheme` + home-screen case | client | small | yes, at ship |
| 5 | `_isNeighborhood` → theme properties | client | small refactor | no — separate change |

**Still no new engine.** The verdict from the previous closure holds. The correction is that "zero
backend work" becomes "one small stateless read endpoint," and the client work is a little wider
than the state map alone — `_breakdown` and `AppState` in particular.

### Sequencing

Unchanged, and the reasoning is stronger now: **Day 1 needs none of this.** A single-session
playthrough runs on today's client against today's backend. Build the skeleton, build Day 1, put it
in front of 14–24s, and only then spend on 1a/1b.

When you do build it, the order is: **1a first** (it is small and independently testable with curl),
then **1b**, then **2**.

---

## 9. TWO THINGS WORTH KNOWING BEFORE AUTHORING

**The composed SVG ships inline in every node response** (`scene_render.dart` — `svg` as a `String`).
No CDN, no asset caching between turns beyond the server's 256-entry LRU. At 95 nodes with ~13
environments this is worth measuring once the first Streets frames exist. It is not a problem today
at 53 nodes; it is the kind of thing that becomes one quietly.

**`headAnchors` is already carried and currently unused** — the comment says it exists so that
"native dialogue, if it ever happens, needs no server change." Combined with `textLayer: "native"`
from the mapping config, the native-text path is further along than the v1.0 document assumed. That
strengthens the case for deciding SPEC-14 deliberately rather than defaulting to balloons.

---

**U-06 CLOSED. ALL AUDIT UNKNOWNS RESOLVED. NO FILES MODIFIED.**