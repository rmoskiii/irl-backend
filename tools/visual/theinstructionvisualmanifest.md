# THE INSTRUCTION — VISUAL MANIFEST (Career district)

Pre-drawing manifest. Nothing is drawn until this is signed off.

Status of every number below: derived by hand from `the_instruction.json` as
supplied, cross-checked against `IRX_VISUAL_SYSTEM_SCOPE.md`. Not yet machine-
validated — `validate_the_instruction.py` in this directory does that against
the scenario file in the repo.

---

## 1. Resolved node mapping

23 nodes. 19 render, 3 carry no render by presentation type, 1 is suppressed by
design.

| # | Node | Mode | Scene | Figure | Register | Tilt | Props |
|---|---|---|---|---|---|---|---|
| 1 | establish_northstar | scene | office_floor | ray / work | open | 0 | — |
| 2 | establish_delivery | scene | desk_evening | ray / work_coat | tired | −10 | — |
| 3 | ask1_date | scene (modal) | desk_evening | ray / work_coat | open | 0 | — |
| 4 | ask1_reaction | scene + artifact | desk_evening | ray / work_coat | tired | −10 | — |
| 5 | ask1_redirect_response | scene | desk_evening | ray / work_coat | civil | −5 | — |
| 6 | ask1_refuse_response | scene | desk_evening | ray / work_coat | closed | −15 | — |
| 7 | ask2_qa | scene (modal) + artifact | meeting_room | ray / work | pressed | +8 | laptop_open |
| 8 | ask2_redirect_closed | scene (modal) | meeting_room | ray / work | closed | −15 | laptop_open |
| 9 | ask2_reaction | scene | office_floor | ray / work | open | 0 | — |
| 10 | ask2_refuse_response | montage | — | — | — | — | 4 panels |
| 11 | escalate_meeting | scene (modal) | review_room | dana / work_formal | attentive | 0 | notepad_pen |
| 12 | escalate_bare | **suppressed** | — | — | — | — | — |
| 13 | escalate_documented | scene | review_room | dana / work_formal | procedural | −6 | notepad_pen |
| 14 | escalate_aftermath | scene | office_floor | ray / work | closed | −15 | — |
| 15 | ask3_client_email | no render | — | — | — | — | — |
| 16 | ask3_reaction | scene | office_floor | ray / work | open | 0 | — |
| 17 | ask3_redirect_response | scene | desk_day | ray / work | civil | −5 | — |
| 18 | ask3_refuse_response | scene | office_floor | ray / work | civil | −5 | — |
| 19 | ask4_ownership | no render (messages) | — | — | — | — | — |
| 20 | audit_email | no render | — | — | — | — | — |
| 21 | audit_ray_calls | remote | desk_evening | — (empty cast) | — | — | — |
| 22 | audit_reply | absent | desk_day | — (empty cast) | — | — | — |
| 23 | resolution | absent | office_floor | — (empty cast) | — | — | — |

Mode counts: scene 15 · montage 1 · remote 1 · absent 2 · no render 3 ·
suppressed 1.

### Variant handling

Message variants change the frame only where the variant prose establishes a
state the node-level mood does not. Two do:

| Node | Variant | Register | Basis in prose |
|---|---|---|---|
| ask1_reaction | 1 (`record:1`) | civil (−5) | "Not annoyed. Slightly puzzled" |
| ask2_reaction | 2 (`record:2`) | civil (−5) | "It isn't hostile. It's almost hurt." |

Every other variant (ask2_qa ×3, escalate_aftermath ×2, ask3_reaction ×2,
audit_email ×6, audit_ray_calls ×4, audit_reply ×6, resolution ×5) changes text
only. The room, the cast and the register are unchanged, so the render block is
unchanged and one block serves all variants of that node.

---

## 2. Register / tilt matrix

Tilts assigned before drawing, then checked pairwise against every adjacency in
the scenario graph.

### figure_c — Ray

| Register | Tilt | Absorbs | Nodes |
|---|---|---|---|
| open | 0 | warm, relieved, easy | 1, 3, 9, 16 |
| civil | −5 | conceding, polite, careful | 5, 17, 18, + 2 variants |
| tired | −10 | tired, distracted | 2, 4 |
| closed | −15 | flat, immovable, distant | 6, 8, 14 |
| pressed | +8 | pressed | 7 |

### figure_d — Dana

| Register | Tilt | Absorbs | Nodes |
|---|---|---|---|
| attentive | 0 | neutral | 11 |
| procedural | −6 | procedural | 13 |

### Adjacency check

Every ordered pair of nodes that can place a figure in consecutive frames.
Nodes with no render are transparent for this purpose — the previous frame is
still the last image the player saw.

| Pair | Δ tilt | Result |
|---|---|---|
| 1 open → 2 tired | 10 | pass |
| 2 tired → 3 open | 10 | pass |
| 3 open → 4 tired | 10 | pass |
| 3 open → 5 civil | 5 | pass (5° measured 19% in The Secret) |
| 3 open → 6 closed | 15 | pass |
| 4 tired → 7 pressed | 18 | pass |
| 5 civil → 7 pressed | 13 | pass |
| 6 closed → 7 pressed | 23 | pass |
| 7 pressed → 8 closed | 23 | pass |
| 7 pressed → 9 open | 8 | pass |
| 8 closed → 9 open | 15 | pass |
| 9 open → 16 open | 0 | **same register, same room — see note** |
| 9 open → 17 civil | 5 | pass |
| 9 open → 18 civil | 5 | pass |
| 14 closed → (21 remote, no figure) | — | n/a |
| 11 attentive → 13 procedural | 6 | pass |

Minimum Δ across all figure-adjacent pairs: **5°**.

**The one flagged pair.** `ask2_reaction` → `ask3_reaction` are both Ray, both
`open`, both `office_floor`. Nothing has changed for Ray between those beats,
so the identical frame is arguably correct — but the player sees the same image
twice. This is a composition problem, not a register problem. Options: change
the slot (centre → right), or accept it. My recommendation is to move the
figure to a different slot in `ask3_reaction` and leave the register alone.
Your call.

---

## 3. Asset manifest — 23 files

Revised down from the 29 in the first pass. See §4 for why.

| Kind | Count | Files |
|---|---|---|
| Bodies | 2 | `figure_c.body.svg`, `figure_d.body.svg` |
| Registers | 7 | `figure_c.register.{open,civil,tired,closed,pressed}.svg`, `figure_d.register.{attentive,procedural}.svg` |
| Wardrobes | 3 | `figure_c.wardrobe.{work,work_coat}.svg`, `figure_d.wardrobe.work_formal.svg` |
| Environments | 5 | `scene.desk_evening.svg`, `scene.desk_day.svg`, `scene.meeting_room.svg`, `scene.review_room.svg`, `scene.office_floor.svg` |
| Props | 2 | `prop.laptop_open.svg`, `prop.notepad_pen.svg` |
| Vignettes | 4 | `vignette.{call_without_you,kitchen_pleasantry,june_two_seats,empty_chair}.svg` |

No rear figures. Nothing in the scenario frames over a shoulder, and the player
is never drawn. That saves 2 bodies, 2 registers and 2 wardrobes against The
Secret's shape.

Destination: `irl-backend/tools/visual/assets/{characters,environments,props,vignettes}/`.

---

## 4. Props — the count came down, and this needs your sign-off

You approved eight drawable props. On a second pass against the prose, only two
objects are actually placed in a room by the text *and* moved between scenes:

- **laptop_open** — "They slide the laptop round" (ask2_qa), "the same laptop"
  (ask2_redirect_closed). Two nodes, two different anchors.
- **notepad_pen** — "a notepad" (escalate_meeting). Two nodes in `review_room`.

Three more are named in prose but belong to the room, not to a prop anchor,
because they never move and appear at one fixed position:

- "upload dialog", "completion date field" → the monitor on `desk_evening`,
  drawn into the environment with a lit but illegible screen. Screen *content*
  is never drawn — inventing legible text on a screen would assert a document
  the prose doesn't describe.
- "a closed door" → a feature of `meeting_room`.

"coat already on" and "coat" resolve to the `work_coat` wardrobe, not to a prop.

The other six props on my first list — mug, document_stack, phone_facedown,
report_folder, desk_lamp, monitor-as-prop — were mine, not the scenario's.
Drawing them would be exactly the set-dressing invention rule 4 rules out. They
become environment furniture where a room needs them and nothing where it
doesn't.

**Net effect: 29 files → 23.** This is a tightening of your rule 4, but it is a
change to what you signed off, so it needs an explicit yes.

---

## 5. Environments

| Scene | Nodes | Time | Occluding surface, y=600 → 900 |
|---|---|---|---|
| desk_evening | 2, 3, 4, 5, 6, 21 | evening | desk top at y=600, solid modesty panel to the floor line |
| desk_day | 17, 22 | day | same geometry, daylight gradients, cooler key |
| meeting_room | 7, 8 | day | table top at y=600 with a solid apron — **no legs, no pedestal** |
| review_room | 11, 13 | day | Dana's desk, solid front panel to floor |
| office_floor | 1, 9, 14, 16, 18, 23 | day | break-out counter run, solid to floor |

Every one gets the alpha-column test before a second asset is drawn. The 2B.6
finding stands: three of five Secret environments failed continuous occlusion
and it was a P0 each time. `meeting_room` and `review_room` are the two at risk
here, because a table and a desk both want legs.

`office_floor` as a break-out counter run solves two things at once: it gives a
continuous occluder, and it gives us the kitchen the prose keeps referring to
("Ray is perfectly friendly in the kitchen").

`desk_day` is the cut candidate if the budget tightens. It carries `audit_reply`,
which is the node the whole scenario resolves through, so I would rather keep it.

---

## 6. Career palette

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
| `--irx-fluoro` | `#E8EDF2` | overhead key — replaces the warm lamp family |
| `--irx-screen-glow` | `#9FC4D8` | |
| `--irx-skin-c` / `-shade` | `#D9A886` / `#B98565` | Ray |
| `--irx-hair-c` / `-light` | `#6E655C` / `#8A8076` | Ray, grey-brown |
| `--irx-skin-d` / `-shade` | `#E0B294` / `#BE8D6F` | Dana |
| `--irx-hair-d` / `-light` | `#4A4038` / `#6A5C50` | Dana |

Hexes are provisional until the value-lock pass. `apply_value_lock.py` refuses
to run twice, so the lock band is decided before any environment is drawn, not
after.

**The identity risk to name now:** two middle-aged white faces sit close on the
skin axis, so tone does almost no separating work. Separation has to come from
head shape, hair mass, proportion and register — the same lesson as figure_b,
where the fix was a squarer cranium and a different hair silhouette rather than
a recolour. Ray and Dana never share a frame, so this is an identity problem,
not a composition one, but it is the thing most likely to read badly at 390pt.

---

## 7. Validation against the scenario

| Check | Result |
|---|---|
| Nodes accounted for | 23 / 23 |
| Render-bearing nodes | 19 |
| No-render by presentation type | 3 (email, messages, review_notice with no location) |
| Suppressed by design | 1 (`escalate_bare`) |
| Declared mood strings mapped | 14 / 14 |
| Unreachable moods mapped anyway | 2 — `careful` (ask4_ownership is messages), `flat` on `resolution` (absent, empty cast). Mapped so a later change cannot fail the build silently. |
| Prose prop strings classified | 32 / 32 — 3 → prop ids, 2 → wardrobe, 3 → environment feature, 24 → unrenderable |
| Nodes over `maxPerNode: 3` | n/a — bubbles OFF, no Career ids added to `bubble_nodes.json` |
| Adjacency pairs below 5° | 0 |
| Mappings referencing a scoring key | 0 — the firewall test should confirm this independently |

---

## 8. Open items — all six need a yes before drawing

1. **Props: 8 → 2.** §4. The six I dropped were mine, not the scenario's.
2. **`ask2_reaction` → `ask3_reaction` render the same frame.** §2. Recommend a
   slot change on `ask3_reaction`, not a register change.
3. **Mapping schema is provisional.** The key names come from the scope doc; the
   internal shapes do not. I need `tools/visual/mapping.the_secret.json` and
   `tools/visual/assets/anchors.json` to conform exactly rather than guess.
4. **`suppressedNodes` is a new mechanism.** Nothing in The Secret needed one.
   It is one filter in `dump_render.py` — but only if a node with no block
   already yields `render: null` downstream rather than a fallback. That needs
   confirming in `renderBlocks.js` before I rely on it.
5. **Where does the Flutter dialogue card sit relative to the artwork?** With
   bubbles off, the collision risk moves from the SVG bubble column to the
   native layout. If the card overlays the artwork's lower band, that band is
   unusable for props and figure detail and the slot plan changes.
6. **`render_blocks.json` for two scenarios.** One merged file or a per-scenario
   map. The scope doc recommends merged; node ids are unique across both
   scenarios so it works. Related to the deployment problem — see the note on
   `.gitignore`.

---

## 9. Sequence from here

Unchanged from the scope doc, which put the expensive decisions first:

1. Sign off this manifest.
2. Conform the mapping to `mapping.the_secret.json`; add `scenes.*`, `props.*`
   and `characters.figure_c/figure_d` to `anchors.json`.
3. Run `validate_the_instruction.py` and the Phase 1 harness.
4. Draw `desk_evening` and `figure_c` only. Compose `ask1_date`. Alpha-column
   test, then read it at 390pt.
5. Nothing else gets drawn until that frame passes.