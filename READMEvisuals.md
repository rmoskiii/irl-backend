# IRX Visual Render Layer — `tools/visual`

Phase 1 deliverable for the visual render layer spec (v1.0).

**Nothing in this folder runs in production.** Your Express server does not import
it, `nodemon` does not watch it, and `npm start` does not touch it. It is dev-time
tooling plus a reference implementation.

---

## What each file is

| File | What it is | Ships to prod? |
|---|---|---|
| `registries.json` | Character / scene / vignette / prop / slot registries. Scenario-agnostic. | **Yes, eventually** — Node reads this at runtime in Phase 2+ |
| `mapping.the_secret.json` | Per-scenario visual config: mood→register table, node and variant overrides, exit beats, montage panels, prop synonyms. | **Yes, eventually** — same |
| `resolve.py` | **Reference implementation** of the render-block compiler. Defines exactly what `renderService.js` must do. | **No** — it gets *ported* to Node, not deployed |
| `validate_visual.py` | Validator: spec rules 1–8 + Phase 1 exit criteria. | No — CI / pre-commit |
| `negative_test.py` | Firewall verification (rule 7). Injects scoring keys into a scratch copy, confirms rejection. | No — CI |
| `dump_render.py` | Dumps every resolved render block to `render_blocks.json`. Inspection aid. | No |

The two JSON files are the only things with a future at runtime. The Python is
either a spec-in-code (`resolve.py`) or a test harness.

**Nothing to install.** Pure Python 3 standard library — no pip, no venv, no
`requirements.txt`.

---

## Where it goes

```
irl-backend/
├── src/
│   ├── data/scenarios/the_secret.json      ← read-only input, never written to
│   ├── services/
│   └── index.js
└── tools/
    └── visual/                             ← this folder
        ├── registries.json
        ├── mapping.the_secret.json
        ├── resolve.py
        ├── validate_visual.py
        ├── negative_test.py
        ├── dump_render.py
        └── README.md
```

`tools/` sits beside `src/`, not inside it — it is not application code.

Add to `.gitignore`:

```
tools/visual/render_blocks.json
tools/visual/__pycache__/
```

---

## Commands

All run from the repo root (`irl-backend/`).

### Validate — the one you run most

```bash
python3 tools/visual/validate_visual.py \
  src/data/scenarios/the_secret.json \
  tools/visual/registries.json \
  tools/visual/mapping.the_secret.json
```

Exits `0` on success, `1` on any hard failure. Prints mode classification, the
Phase 3 compression worklist, and the eight exit criteria.

### Firewall check — run before touching the mapping file

```bash
python3 tools/visual/negative_test.py \
  src/data/scenarios/the_secret.json \
  tools/visual/registries.json \
  tools/visual/mapping.the_secret.json
```

Copies everything to a temp dir, injects scoring-key references, confirms the
validator rejects each one, then confirms the real scenario still passes and is
byte-identical. Your files are never written to.

### Dump render blocks — when you want to see the output

```bash
python3 tools/visual/dump_render.py \
  src/data/scenarios/the_secret.json \
  tools/visual/registries.json \
  tools/visual/mapping.the_secret.json
```

Writes `tools/visual/render_blocks.json` — every node, plus each `messageVariant`,
fully resolved. This is what the Flutter client will receive.

---

## npm scripts

Add to `package.json`:

```json
{
  "scripts": {
    "visual:validate": "python3 tools/visual/validate_visual.py src/data/scenarios/the_secret.json tools/visual/registries.json tools/visual/mapping.the_secret.json",
    "visual:firewall": "python3 tools/visual/negative_test.py src/data/scenarios/the_secret.json tools/visual/registries.json tools/visual/mapping.the_secret.json",
    "visual:dump": "python3 tools/visual/dump_render.py src/data/scenarios/the_secret.json tools/visual/registries.json tools/visual/mapping.the_secret.json",
    "visual:check": "npm run visual:validate && npm run visual:firewall"
  }
}
```

Then:

```bash
npm run visual:check
```

---

## No migrations

There is no database, no schema change, no migration step. The scenario JSON is
**never modified** — that is exit criterion 8, and `negative_test.py` verifies it
by checksum on every run. If a run ever leaves `the_secret.json` with a different
hash, that is a bug in the tooling, not a migration.

---

## Other scenarios

`registries.json` is shared. The mapping file is per-scenario. When The Prince or
The Instruction gets a visual pass, it needs its own `mapping.the_prince.json`
built from that scenario's own `character.mood` values — the validator already
takes the scenario path as an argument, so no code changes.

`the_bank.json` and `the_favor.json` are untouched by any of this.

---

## What Phase 2 changes

Phase 2 is assets (~46 SVG). The Node port of `resolve.py` — a `renderService.js`
that reads the two JSON files and attaches a `render` block to the node response —
comes with it.

When that port happens, `resolve.py` stays in the repo as the reference. The
validator should then run against **both** implementations and confirm they
produce identical render blocks. That is the cheapest possible guard against the
Node version drifting from the spec.

---

## Before you commit

The `the_secret.json` used to build this was a transcription, not your file.
Validate against your actual copy in `src/data/scenarios/` first. If mode
classification comes back as anything other than 19 scene / 3 absent / 2 montage /
1 remote / 5 messages, the two files have diverged and the mapping needs a look.
