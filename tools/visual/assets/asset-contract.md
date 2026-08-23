# IRX Visual Asset Contract — Phase 2A

Status: **Frame 1 complete and visually inspected.** Contract proven. Art direction
**not yet signed off** — see §9.

Phase 1 specified the *data* contract (what the engine sends). This specifies the
*asset* contract (what the files must obey so they composite mechanically).

---

## 1. Canvas

| | |
|---|---|
| Canonical viewBox | `0 0 1600 900` (16:9) |
| Mobile safe area | `x 440 → 1160`, full height (4:5) |

Phase 1 defined no canvas, so this is a new decision. 16:9 suits the investor
surfaces (`ScenarioDemo`, deck). Anything narratively load-bearing must sit inside
the mobile safe area; slot `centre` is centred within it.

## 2. Character construction

Three separate assets per figure, composed at render time:

```
figure_a.body.svg                  viewBox 0 0 420 800
figure_a.wardrobe.<name>.svg       viewBox 0 0 420 800   (same space as body)
figure_a.register.<name>.svg       viewBox 0 0 200 220
```

| Anchor | Value | Meaning |
|---|---|---|
| body `basePoint` | `210,800` | bottom-centre; lands on the scene slot anchor |
| body `headSocket` | `210,210` | where a register's neckAnchor lands |
| register `neckAnchor` | `100,210` | the neck join point |

Placement is `anchor − basePoint`. For Frame 1: character `translate(590,100)`,
head `translate(110,0)`. Both derived, neither hand-tuned.

A register may declare `data-register-rotate` (degrees, about its own neckAnchor).
`open` uses `-2`. This lets head tilt carry part of a register while the join stays
mechanical.

**This is a composable system, not five drawings of one person.** Adding a register
means adding one 200×220 file. Adding a wardrobe means one 420×800 file. Neither
touches the others.

## 3. Scene slots and prop anchors

The environment owns all placement. `scene.kitchen` publishes:

```
slots            left(470,900)  centre(800,900)  right(1130,900)
                 foreground_left/right, background_left/right
occlusionLine    y=600   (counter top)
propAnchors      counter_left(430,604)   counter_right(1196,604)
                 floor_left(268,892)     floor_right(1340,892)
```

Props declare a bottom-centre `basePoint` and are placed onto a named anchor,
exactly as characters are. No prop is positioned by hand.

## 4. Layers

```
background · architecture · environmental_detail · character_back
character_body · character_clothing · character_head · furniture
prop · character_contact · character_front · foreground
```

Four deviations from the list proposed in the brief, all forced by the artwork:

1. **`character_face` / `character_hair` are not top-level layers.** A register is
   one atomic swappable unit; splitting face from hair would let them
   desynchronise across registers.
2. **`furniture` sits after `character_head`** so the counter occludes the figure
   below counter height. This is what puts her *in* the room.
3. **`character_front` sits after `prop`** so her hands rest on the counter surface
   — the beat the scenario actually describes.
4. **`character_contact` added during QA.** Without contact shadows the figure read
   as pasted onto the background. `character_back` carries her cast shadow on the
   splashback.

## 5. Colour tokens

`tokens.css` is the single source of truth. `inject_tokens.py` embeds it verbatim
into every asset so each file stays self-contained. `validate_assets.py` fails the
build if any embedded copy drifts, or if any colour is hard-coded outside `<defs>`.

Palette is muted and earthy: sage walls, warm oak joinery, terracotta wardrobe,
slate jacket. The neighbourhood accent `#FFC15E` appears only as warm light —
never as a surface fill.

**Gradients: three, all lighting, none on an object surface.** Key light
(warm, upper-left pendant), cool spill (window, right), vignette. Object shading
is flat tone-on-tone.

## 6. Files

```
tools/visual/assets/
├── tokens.css                          colour + stroke source of truth
├── anchors.json                        THE contract — all placement data
├── asset-contract.md                   this file
├── inject_tokens.py                    embeds tokens into every asset
├── compose_frame.py                    builds a frame from anchors.json alone
├── validate_assets.py                  12 structural checks
├── qa_render.py                        flattens tokens → PNG (QA only, not shipped)
├── characters/
│   ├── figure_a.body.svg
│   ├── figure_a.wardrobe.home_casual.svg
│   └── figure_a.register.open.svg
├── environments/scene.kitchen.svg
├── props/
│   ├── prop.jacket_chair.svg
│   └── prop.last_glass.svg
├── frames/frame_1_confession.svg       GENERATED — do not hand-edit
└── qa/                                 gitignore this
```

Commands, from the repo root:

```bash
python3 tools/visual/assets/inject_tokens.py
python3 tools/visual/assets/compose_frame.py frame_1_confession
python3 tools/visual/assets/validate_assets.py
python3 tools/visual/assets/qa_render.py tools/visual/assets/frames/frame_1_confession.svg 1400
```

## 7. Frame 1 provenance

Every element traces to `render_blocks.json → confession → default`:

| Render block | Asset |
|---|---|
| `scene.id: scene.kitchen`, `time: evening` | `scene.kitchen.svg` |
| `framing: direct` | figure faces camera |
| `cast[0].slot: centre` | slot anchor `(800,900)` |
| `cast[0].register: open` | `figure_a.register.open.svg` |
| `cast[0].wardrobe: home_casual` | `figure_a.wardrobe.home_casual.svg` |
| `props[0]: prop.jacket_chair` | `floor_left` |
| `props[1]: prop.last_glass` | `counter_right` |

Validator rule 9 asserts this correspondence, so the frame cannot silently drift
from the scenario.

**No dialogue UI.** The render block carries `bubbles` as data; it does not specify
chrome. Bubble treatment is a separate design task and would have obscured the
thing 2A exists to test.

## 8. The firewall, in the artwork

Spec §2: the face may never report verdict. Rev 1 of `register.open` breached this
— heavy brows and an upcurved mouth read as *smug*, which would have told the
player what to think about Jessica before she finished her sentence. Rev 4 has a
flat mouth, thin brows with only the inner ends lifted, and small eyes with a
heavier upper lid. Openness is carried by posture, gaze and parted lips.

**This is why registers must be reviewed rendered, not described.** "open" sounded
fine as a token for four phases. It was wrong the first time it was drawn.

## 9. Art direction: not yet signed off

What works: composition system, layering, lighting model, palette, environmental
storytelling, silhouette, the neutral face.

What does not yet reach the reference bar:

- **Line quality.** Strokes are geometrically uniform. The reference has visible
  weight variation and hand wobble. Currently four stroke weights with no
  irregularity — it reads *clean vector*, not *drawn*.
- **Surface shading.** Mostly single flat tones. The reference carries two or three
  tones on nearly every surface.
- **Texture.** The grain filter is present but nearly invisible at 0.075.
- **Hair.** Still slightly helmet-like in silhouette; the weakest part of the figure.

See §10 before committing to the remaining ~40 assets.

## 10. Required before Phase 2B

1. **Resolve line quality.** Either commission an illustrator against this contract,
   or add a wobble pass (path-level jitter, not a filter — filters do not survive
   rasterisation reliably). Decide *before* volume production; retrofitting 40
   assets is far more expensive than 6.
2. **Add a second shading tone** to the surface convention and encode it as tokens.
3. **Redraw the hair** with proper volume and asymmetry.
4. **Test a second register** (`tight` or `away`) against this exact body. The head
   swap is proven mechanically but has only ever been exercised with one head. `away`
   will test whether head-only rotation is sufficient or whether registers need an
   optional shoulder variant.
5. **Decide bubble treatment** — Frame 1 has no dialogue chrome, and the investor
   frames will need it.