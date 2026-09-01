# THE INSTRUCTION — VISUAL MANIFEST (Career district)

Pre-drawing manifest, conformed to `mapping.the_secret.json`, `registries.json`,
`anchors.json` and `resolve.py`. Nothing is drawn until this is signed off.

**22 assets. Three resolver changes, totalling four lines.**

---

## 1. Pipeline changes required

All three are in `resolve.py` except one enum value in `registries.json`. None
of them touches the scenario. None changes any render block The Secret produces
— that is the acceptance test.

### 1.1 Mode `none` — the deliberate blank (decision 5)

`classify_mode` returns whatever string `modeOverrides` holds, but `resolve`
only short-circuits on `"messages"`. Any other unrecognised mode falls through
the montage check, resolves a scene from the location, misses the `absent` and
`remote` branches, and lands in the scene branch. For `escalate_bare` that
means it would resolve Dana into a manufactured office — silently, with no
error. **The pipeline currently cannot distinguish an intentional blank from a
missing one**, which is what you asked me to confirm before proposing anything.

```python
# resolve.py, in resolve()
-    if mode == "messages":
-        return None  # existing phone UI; no render block (§3.5)
+    if mode in ("messages", "none"):
+        return None  # phone UI (§3.5), or an authored deliberate blank
```

```json
// registries.json
"modes": ["scene", "montage", "remote", "absent", "messages", "none"]
```

The intent lands where you wanted it: `"escalate_bare": "none"` in
`modeOverrides` is a positive assertion, not an absence. `dump_render.py` still
emits the key with a null value, so a deliberate blank and a node missing from
the file remain distinguishable downstream. The scenario is untouched.

### 1.2 Per-character default wardrobe

`resolve` hard-codes `wardrobe = "home_casual"` before applying overrides. No
Career character has a `home_casual`. Without this, every one of Ray's fifteen
scene nodes needs an identical `nodeOverrides` entry purely to name a wardrobe
that should be his default.

```python
# resolve.py, scene branch
-    wardrobe = "home_casual"
+    wardrobe = chars[cid].get("defaultWardrobe", "home_casual")
```

`registries.json` gains `defaultWardrobe` on all four characters. Jessica and
Alex restate `home_casual`, so The Secret's blocks are byte-identical.

### 1.3 `textLayer: "native"` — bubbles off (decision 3)

This one is not cosmetic. `extract_bubbles` pulls every quoted span out of the
message, and `anchors.bubbles` sets `maxPerNode: 3` / `maxChars: 120`, both
enforced as hard fails by the composer and the validator. Counting the actual
prose:

| Node | Quoted spans | Longest span |
|---|---|---|
| `ask2_qa` default | 3 | 135 chars |
| `ask2_qa` variant[0] | **4** | 128 chars |
| `audit_ray_calls` default | 3 | 121 chars |

So Career blocks generate fine and then fail to compose. Turning bubbles off at
compose time doesn't help, because the breakage is upstream. The alternative is
the Phase 3 compression pass you've ruled out for this scenario.

```python
# resolve.py — scene, remote and absent branches
+    native = mapping.get("textLayer") == "native"
...
-    render["bubbles"] = extract_bubbles(message, cid)
-    render["narration"] = strip_dialogue(message) or None
+    render["bubbles"] = [] if native else extract_bubbles(message, cid)
+    render["narration"] = None if native else (strip_dialogue(message) or None)
```

`narration` goes to null rather than to the stripped message, because with a
native text layer the client already has the full prose from `publicNode`. A
block carrying the message-minus-its-dialogue would be a second, mangled copy
of text the player is reading in full six pixels lower.

### 1.4 Not needed

No change for the player's absence (decision 2). `modeOverrides: {"resolution":
"absent"}` is the mechanism The Secret already uses for `jessica_reacts_neutral`.
`character_id` returns `None` for `"You"`, the absent branch never reads it,
`cast` comes out `[]` and `framing` `"empty"`. Zero scenario edits, zero new
convention.

---

## 2. Resolved node mapping

23 nodes. 18 render, 1 returns null by presentation type, 4 return null by
explicit override.

| # | Node | Mode | Scene | Figure | Register | Tilt | Props |
|---|---|---|---|---|---|---|---|
| 1 | establish_northstar | scene | office_floor | ray / work | open | 0 | — |
| 2 | establish_delivery | scene | desk_evening | ray / work_coat | heavy | −10 | — |
| 3 | ask1_date | scene | desk_evening | ray / work_coat | open | 0 | — |
| 4 | ask1_reaction | scene | desk_evening | ray / work_coat | heavy | −10 | — |
| 5 | ask1_redirect_response | scene | desk_evening | ray / work_coat | guarded | −5 | — |
| 6 | ask1_refuse_response | scene | desk_evening | ray / work_coat | set | −15 | — |
| 7 | ask2_qa | scene | meeting_room | ray / work | squared | +8 | laptop_open |
| 8 | ask2_redirect_closed | scene | meeting_room | ray / work | set | −15 | laptop_open |
| 9 | ask2_reaction | scene | office_floor | ray / work | open | 0 | — |
| 10 | ask2_refuse_response | montage | — | — | — | — | 3 panels |
| 11 | escalate_meeting | scene | review_room | dana / work_formal | level | 0 | notepad |
| 12 | escalate_bare | **none** | — | — | — | — | — |
| 13 | escalate_documented | scene | review_room | dana / work_formal | noting | −6 | — |
| 14 | escalate_aftermath | scene | office_floor | ray / work | set | −15 | — |
| 15 | ask3_client_email | none | — | — | — | — | — |
| 16 | ask3_reaction | scene | office_floor | ray / work (slot **right**) | open | 0 | — |
| 17 | ask3_redirect_response | scene | desk_day | ray / work | guarded | −5 | — |
| 18 | ask3_refuse_response | scene | office_floor | ray / work | guarded | −5 | — |
| 19 | ask4_ownership | messages (auto) | — | — | — | — | — |
| 20 | audit_email | none | — | — | — | — | — |
| 21 | audit_ray_calls | none | — | — | — | — | — |
| 22 | audit_reply | absent | desk_day | — | — | — | — |
| 23 | resolution | absent | office_floor | — | — | — | — |

`escalate_documented` resolves `review_room` from its `visual.setting`, which
takes priority over its location string ("The office, the weeks after"). Its
three prose props are all unrenderable, so it composes with an empty prop list.

`audit_ray_calls` is `none` rather than `remote`: it has no `location` and no
`visual.setting`, so `resolve_scene_token` would raise. The empty-desk beat it
would carry is already served by `audit_reply` two nodes later, so the choice is
between adding scenario metadata to draw a near-duplicate frame, or not drawing
it. Not drawing it is the smaller change and the better sequence.

### Variant overrides

| Node | variantIndex | Register | Basis in prose |
|---|---|---|---|
| ask1_reaction | 0 (`record:1`) | guarded (−5) | "Not annoyed. Slightly puzzled." |
| ask2_reaction | 0 (`record:2`) | guarded (−5) | "It isn't hostile. It's almost hurt." |

Note the index on `ask2_reaction`: `record:2` is declared **first**, so it is
index 0 and `record:1` is index 1. I had these the wrong way round in the first
pass. Every other variant in the scenario changes text only, so one block serves
all of them.

---

## 3. Register / tilt matrix

Registers are named by posture, not emotion, per spec §5. Tilt is
`data-register-rotate` on the register root, so it lives in the SVG rather than
in any config file — recorded here because it has to be decided before drawing
and verified by `register_swap_test.py` after.

**char.ray (figure_c)** — `open` 0 · `guarded` −5 · `heavy` −10 · `set` −15 · `squared` +8
**char.dana (figure_d)** — `level` 0 · `noting` −6

| Adjacent pair | Δ | Result |
|---|---|---|
| 1 open → 2 heavy | 10 | pass |
| 2 heavy → 3 open | 10 | pass |
| 3 open → 4 heavy | 10 | pass |
| 3 open → 5 guarded | 5 | pass (5° measured 19% in The Secret) |
| 3 open → 6 set | 15 | pass |
| 4 heavy → 7 squared | 18 | pass |
| 5 guarded → 7 squared | 13 | pass |
| 6 set → 7 squared | 23 | pass |
| 7 squared → 8 set | 23 | pass |
| 7 squared → 9 open | 8 | pass |
| 8 set → 9 open | 15 | pass |
| 9 open → 16 open | 0 | same register — resolved by the slot change, see below |
| 9 open → 17 guarded | 5 | pass |
| 9 open → 18 guarded | 5 | pass |
| 11 level → 13 noting | 6 | pass |

Minimum Δ across all figure-adjacent pairs: **5°**.

`ask2_reaction` → `ask3_reaction` is the same figure, register and room. Rather
than editorialise Ray's face into a change the prose doesn't establish, the
`right` slot moves him. `resolve` already reads `overrides.get("slot")`, so this
needs no code — The Secret simply never used it.

Dana's two registers sit at Δ6 with a fixed hair policy, which is above the
threshold but the tightest pair in the scenario. `noting` earns its separation
from a drawn head-down to the notepad and reading glasses, not from the tilt.
If it measures under 13% at 390pt, the fix is more drawn asymmetry, not more
rotation.

---

## 4. Asset manifest — 22 files

| Kind | Count | Files |
|---|---|---|
| Bodies | 2 | `figure_c.body.svg`, `figure_d.body.svg` |
| Registers | 7 | `figure_c.register.{open,guarded,heavy,set,squared}.svg`, `figure_d.register.{level,noting}.svg` |
| Wardrobes | 3 | `figure_c.wardrobe.{work,work_coat}.svg`, `figure_d.wardrobe.work_formal.svg` |
| Environments | 5 | `scene.{desk_evening,desk_day,meeting_room,review_room,office_floor}.svg` |
| Props | 2 | `prop.laptop_open.svg`, `prop.notepad.svg` |
| Vignettes | 3 | `vig.{call_without_you,kitchen_pleasantry,june_two_seats}.svg` |

Down from 29 in the first pass and 23 in the second. The last file went when
`anchors.montage` turned out to fix `panelWidth` at 440 with a 48px gap: four
panels span 1904 on a 1600 canvas. Three panels it is.

Against The Secret's 45, and against the scope doc's own estimate of 24–40, the
marginal cost of scenario two is roughly half of scenario one — which is the
number the whole exercise exists to produce.

Destination:
`irl-backend/tools/visual/assets/{characters,environments,props,vignettes}/`

---

## 5. Career palette

Line, shadow and stroke-weight tokens are **identical to Neighbourhood**. The
craft language does not fork per district. What changes is architecture, light
and character.

| Token | Proposed | Note |
|---|---|---|
| `--irx-accent` | `#B4A0FF` | Career accent, still the placeholder from the design tokens |
| `--irx-accent-dim` | `#8C7BC7` | |
| `--irx-wall` / `--irx-wall-dark` | `#6E757E` / `#5C636B` | cool partition grey |
| `--irx-floor` | `#4A4F55` | carpet tile |
| `--irx-desk` / `--irx-desk-edge` | `#8A8478` / `#6F6A60` | |
| `--irx-fluoro` | `#E8EDF2` | overhead key, replacing the warm lamp family |
| `--irx-screen-glow` | `#9FC4D8` | the monitor, and the only warm-cool inversion in the district |
| `--irx-skin-c` / `-shade` | `#D9A886` / `#B98565` | Ray |
| `--irx-hair-c` / `-light` | `#6E655C` / `#8A8076` | Ray — grey-brown, greying at the sides |
| `--irx-skin-d` / `-shade` | `#E0B294` / `#BE8D6F` | Dana |
| `--irx-hair-d` / `-light` | `#4A4038` / `#6A5C50` | Dana |

Provisional until the value-lock pass. `apply_value_lock.py` refuses to run
twice, so the lock band is decided before any environment is drawn.

**The identity risk to name now.** Two middle-aged white faces sit close on the
skin axis, so tone does almost no separating work. It has to come from head
shape, hair mass and proportion — the figure_b lesson, where the fix was a
squarer cranium and a different hair silhouette rather than a recolour. They
never share a frame, so this is an identity problem rather than a composition
one, but it is the thing most likely to read badly at 390pt.

Both figures also have to stay recognisably from the same universe as Jessica
and Alex: same line weight, same tonal grouping discipline, same two-to-three
values per surface. Same grammar, different people.

---

## 6. Validation

The real check is the pipeline, not a bespoke script. After the three resolver
changes and with the assets stubbed:

```bash
python3 tools/visual/dump_render.py \
    src/data/scenarios/the_instruction.json \
    tools/visual/registries.json \
    tools/visual/mapping.the_instruction.json
```

That exercises every check that matters. `reachable_nodes` walks the graph,
`classify_mode` resolves all 23, `resolve_scene_token` raises on any location
that doesn't match a prefix, `resolve_props` reports anything that reached
`_unknownProps`, and the closing lines print unused prop tokens — which should
be exactly the eleven Neighbourhood props, since this run only sees Career.

Then re-run it for The Secret and diff against the committed `render_blocks.json`.
**It must come back byte-identical.** That is the acceptance test for all three
resolver changes.

Hand-validation against the scenario, ahead of that run:

| Check | Result |
|---|---|
| Nodes accounted for | 23 / 23 |
| Render-bearing | 18 |
| Null by presentation type | 1 (`ask4_ownership`, messages) |
| Null by explicit override | 4 (1 deliberate blank, 3 no-artwork presentation types) |
| Declared moods mapped | 14 / 14 |
| Unreachable moods mapped defensively | 1 (`careful`) |
| Prose prop strings classified | 30 / 30 — 3 → prop ids, 27 → unrenderable |
| Locations resolving to a scene | 12 / 12, prefix order verified |
| Nodes over `maxPerNode` with bubbles on | 1 (`ask2_qa` variant[0]) — moot under `textLayer: native` |
| Adjacency pairs below 5° | 0 |
| Mapping entries naming a scoring key | 0 |

---

## 7. Open items

1. **Sign off the three resolver changes** in §1. Four lines and an enum value.
2. **Ray on figure_a geometry makes Dana the larger figure.** `figure_b` is the
   taller build — 196 shoulder width against 185, socket 14px higher. Swapping
   the assignment gives Ray the broader frame at no cost, since both are pure
   geometry contracts. Raised last turn, still unanswered. I'll take the
   original assignment if you'd rather not move it.
3. **`audit_ray_calls` gets no artwork.** If you want the empty desk at 18:04,
   it needs `"visual": {"setting": "desk"}` added to that node's
   `presentation.data` and the override changed from `none` to `remote` — a
   metadata addition, not prose. My recommendation is to leave it.
4. **Where does the Flutter dialogue card sit relative to the artwork?** With
   `textLayer: native` the collision moves from the SVG bubble column to the
   client layout. If the card overlays the lower band of the contained 16:9
   rather than sitting below it, that band is unusable for props and figure
   detail and the slot plan changes. This is the last thing that could still
   move the environment designs.
5. **`render_blocks.json` for two scenarios.** One merged file, per the scope
   doc — node ids are unique across both. Ties into the deployment problem: the
   file is gitignored, which is why nothing renders live.

---

## 8. Sequence from here

1. Sign off §1 and §7.
2. Apply the resolver changes. Re-run `dump_render.py` for The Secret and diff
   against the committed blocks. Byte-identical or stop.
3. Merge the `registries.json` and `anchors.json` additions.
4. Run `dump_render.py` for The Instruction against stub assets. Every node
   resolves or the mapping is wrong, and it is much cheaper to be wrong now.
5. Draw `scene.desk_evening` and `figure_c` only. Compose `ask1_date`.
   Alpha-column test on the occluder, then read it at 390pt.
6. Nothing else gets drawn until that frame passes.