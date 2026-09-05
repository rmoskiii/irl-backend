#!/usr/bin/env python3
"""Career district-wide visual audit. READ-ONLY on source.

Runs the PRODUCTION pipeline over every Career render state and reports.
It does not patch, edit or regenerate a single source asset: it calls
compose_frame.py and validate_assets.py as subprocesses, reads the render
blocks the resolver produced, and measures the composed output.

Generated output (frames/*.svg from compose_frame, qa/*.png from qa_render) is
the existing audit pipeline's own artefact and is clearly separated in the
report from source changes.

Usage, from tools/visual/assets:
    python3 audit_career.py

Exit code 1 if any BLOCKER or DEFECT is found.
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent


def find(name, extra=()):
    """Locate a tool or data file without assuming the tree layout.

    The first version of this script resolved every tool as ROOT.parent, one
    directory above itself. The production tools live in the SAME directory as
    this script, so every composition check invoked a path that does not exist
    and the audit reported a composer failure that was entirely its own.

    Search order is nearest-first, then a bounded walk up. Whatever is found is
    printed, so a wrong pick is visible rather than silent.
    """
    seen = []
    for base in (ROOT, ROOT.parent, ROOT.parent.parent, *[ROOT.parents[i] for i in range(2, 5)]):
        for c in (base / name, *(base / e / name for e in extra)):
            seen.append(c)
            if c.exists():
                return c
    for up in list(ROOT.parents)[:5]:
        hits = sorted(up.rglob(name))
        hits = [h for h in hits if "node_modules" not in h.parts]
        if hits:
            return hits[0]
    print(f"  NOT FOUND: {name}   looked in {[str(x.parent) for x in seen[:6]]}")
    return None


TOOLS = {t: find(t) for t in ("compose_frame.py", "dump_render.py", "validate_assets.py",
                              "prop_occlusion_test.py", "register_swap_test.py",
                              "inject_tokens.py", "qa_render.py")}
MAPPING = find("mapping.the_instruction.json")
REGISTRIES = find("registries.json")
SCENARIO = find("the_instruction.json", extra=("src/data/scenarios", "scenarios", "src/data"))

CAREER_SCENES = {"scene.desk_evening", "scene.desk_day", "scene.meeting_room",
                 "scene.review_room", "scene.office_floor"}
CAREER_PROPS = {"prop.laptop_open", "prop.notepad"}
CAREER_VIGS = {"vig.call_without_you", "vig.kitchen_pleasantry", "vig.june_two_seats"}
issues = []


def issue(kind, state, asset, problem, evidence, action):
    issues.append(dict(kind=kind, state=state, asset=asset, problem=problem,
                       evidence=evidence, action=action))


def run(cmd):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    print("=" * 70)
    print("CAREER DISTRICT-WIDE VISUAL AUDIT")
    print("=" * 70)

    # --- 0. working tree, recorded before anything runs -------------------
    _, st = run(["git", "status", "--short", "--", str(ROOT)])
    print("\n[0] WORKING TREE BEFORE AUDIT\n" + (st or "  clean"))

    print("\n[0] RESOLVED TOOL PATHS")
    for k, v in TOOLS.items():
        print(f"  {k:26s} {v if v else 'NOT FOUND'}")
    for k, v in (("mapping", MAPPING), ("registries", REGISTRIES), ("scenario", SCENARIO)):
        print(f"  {k:26s} {v if v else 'NOT FOUND'}")
    for k, v in TOOLS.items():
        if v is None and k in ("compose_frame.py", "dump_render.py", "validate_assets.py"):
            issue("BLOCKER", "-", k, "required production tool not found on disk",
                  f"searched from {ROOT}", "confirm the repository layout; do not patch the tool")
    if any(TOOLS[k] is None for k in ("compose_frame.py", "dump_render.py", "validate_assets.py")) \
            or MAPPING is None or REGISTRIES is None or SCENARIO is None:
        return report()

    # --- A. resolution and coverage ---------------------------------------
    print("\n[A] RESOLUTION / COVERAGE")
    rc, out = run(["python3", str(TOOLS["dump_render.py"]), str(SCENARIO),
                   str(REGISTRIES), str(MAPPING), "render_blocks.the_instruction.json"])
    print(out.strip())
    if rc:
        issue("BLOCKER", "-", "dump_render.py", "resolver failed", out.strip()[:400],
              "stop; the audit cannot proceed without resolved blocks")
        return report()

    rbp = find("render_blocks.the_instruction.json")
    rb = json.loads(rbp.read_text(encoding="utf-8"))
    anchors = json.loads((ROOT / "anchors.json").read_text(encoding="utf-8"))
    regs = json.loads(REGISTRIES.read_text(encoding="utf-8"))

    states = [(n, k, b) for n, e in rb.items() for k, b in e.items()]
    render = [(n, k, b) for n, k, b in states if b]
    modes = {}
    for _, _, b in render:
        modes[b["mode"]] = modes.get(b["mode"], 0) + 1
    print(f"  states {len(states)} | render {len(render)} | non-render {len(states)-len(render)}")
    print(f"  modes {modes}")
    if len(render) != 34:
        issue("BLOCKER", "-", "render_blocks", f"expected 34 render states, resolver produced {len(render)}",
              f"modes {modes}", "reconcile the mapping against the scenario before locking")

    # every referenced asset must exist on disk
    def path_for(kind, ident):
        if kind == "scene":
            return ROOT / "environments" / f"{ident}.svg"
        if kind == "prop":
            return ROOT / "props" / f"{ident}.svg"
        if kind == "vig":
            return ROOT / "vignettes" / f"{ident}.svg"
        return None

    missing = set()
    for n, k, b in render:
        if b["mode"] == "montage":
            for p in b["panels"]:
                if not path_for("vig", p["vignette"]).exists():
                    missing.add((f"{n}:{k}", p["vignette"]))
            continue
        if not path_for("scene", b["scene"]["id"]).exists():
            missing.add((f"{n}:{k}", b["scene"]["id"]))
        for p in b["props"]:
            if not path_for("prop", p).exists():
                missing.add((f"{n}:{k}", p))
        for c in b.get("cast", []):
            base = regs["characters"][c["id"]]["base"]
            for f in (f"{base}.body.svg", f"{base}.register.{c['register']}.svg",
                      f"{base}.wardrobe.{c['wardrobe']}.svg"):
                if not (ROOT / "characters" / f).exists():
                    missing.add((f"{n}:{k}", f))
    for state, a in sorted(missing):
        issue("BLOCKER", state, a, "referenced asset does not exist", "file not found",
              "create the asset or correct the mapping")
    print(f"  referenced assets missing on disk: {len(missing)}")

    # every render state must have a frame declared to compose it
    frames = anchors["frames"]
    by_source = {}
    for fname, fr in frames.items():
        src = fr.get("renderBlockSource", "")
        m = re.search(r"->\s*(\S+)\s*->\s*(\S+)", src) or re.search(r"-> (\S+) -> (\S+)", src)
        if m:
            by_source[(m.group(1), m.group(2))] = fname
    uncovered = [(n, k) for n, k, b in render if (n, k) not in by_source]
    print(f"  render states with a declared frame: {len(render)-len(uncovered)}/{len(render)}")
    if uncovered:
        print("  NOTE: states with no frame of their own usually share a block with a state that has one.")
        blocks = {}
        for n, k, b in render:
            blocks.setdefault(json.dumps(b, sort_keys=True), []).append((n, k))
        for n, k in uncovered:
            grp = blocks[json.dumps(dict(rb[n][k]), sort_keys=True)]
            if not any((a, c) in by_source for a, c in grp):
                issue("DEFECT", f"{n}:{k}", "anchors.json",
                      "render state has no frame and shares no block with one that does",
                      f"block group {grp}", "add a frame entry or confirm the state is unreachable in play")

    # --- B..G. compose every declared Career frame ------------------------
    print("\n[B-G] COMPOSITION")
    career_frames = [f for f, fr in frames.items()
                     if fr.get("scene") in CAREER_SCENES or "montage" in str(fr.get("mode", ""))
                     or any(p.get("vignette") in CAREER_VIGS for p in fr.get("panels", []))]
    print(f"  Career frames declared in anchors: {len(career_frames)}")
    composed, failed = [], []
    for f in sorted(career_frames):
        rc, out = run(["python3", str(TOOLS["compose_frame.py"]), f])
        if rc:
            failed.append((f, out.strip().splitlines()[-1] if out.strip() else "no output"))
            issue("BLOCKER", f, "compose_frame.py", "frame failed to compose",
                  out.strip()[-300:], "stop; do not patch the composer during the audit")
        else:
            composed.append(f)
            layers = re.search(r"layers: \[(.*?)\]", out)
            print(f"  {f:34s} OK  {layers.group(1)[:96] if layers else ''}")
    for f, err in failed:
        print(f"  {f:34s} FAIL  {err}")

    # --- validators -------------------------------------------------------
    print("\n[E,J] VALIDATORS")
    for tool in ("validate_assets.py", "prop_occlusion_test.py"):
        if TOOLS.get(tool) is None:
            print(f"  {tool}: NOT FOUND, skipped")
            continue
        rc, out = run(["python3", str(TOOLS[tool])])
        tail = out.strip().splitlines()
        print(f"  {tool}: {'PASS' if rc == 0 else 'FAIL'}")
        for line in tail[-14:]:
            print("    " + line)
        if rc:
            issue("BLOCKER", "-", tool, "validator reported failures", "\n".join(tail[-8:]),
                  "resolve the reported rule violations before locking")

    if TOOLS.get("register_swap_test.py"):
        for a, b in (("audit_ask1_reaction", "audit_ask1_reaction_v0"),
                     ("audit_escalate_meeting", "audit_escalate_documented")):
            if a in composed and b in composed:
                rc, out = run(["python3", str(TOOLS["register_swap_test.py"]), a, b])
                print(f"\n  register_swap_test {a} vs {b}: {'PASS' if rc == 0 else 'FAIL'}")
                for line in out.strip().splitlines()[-10:]:
                    print("    " + line)

    # --- J. token and SVG integrity across Career source ------------------
    print("\n[J] TOKEN / SVG INTEGRITY (Career source assets)")
    canonical = None
    tok = find("tokens.css")
    if tok:
        body = tok.read_text(encoding="utf-8").split(":root {", 1)[1].rsplit("}", 1)[0]
        canonical = f"/* @tokens-begin */\n:root {{{body}}}\n/* @tokens-end */"
    career_files = sorted(
        [ROOT / "environments" / f"{s}.svg" for s in CAREER_SCENES] +
        [ROOT / "props" / f"{p}.svg" for p in CAREER_PROPS] +
        [ROOT / "vignettes" / f"{v}.svg" for v in CAREER_VIGS] +
        list((ROOT / "characters").glob("figure_c.*.svg")) +
        list((ROOT / "characters").glob("figure_d.*.svg")))
    NEIGHBOURHOOD_ONLY = {"--irx-skin-b", "--irx-hair-b", "--irx-cloth", "--irx-curtain",
                          "--irx-cabinet", "--irx-counter", "--irx-jacket", "--irx-lamp-warm"}
    for p in career_files:
        if not p.exists():
            issue("BLOCKER", "-", p.name, "Career asset missing from disk", "file not found",
                  "restore or create the asset")
            continue
        txt = p.read_text(encoding="utf-8")
        if canonical and canonical not in txt:
            issue("BLOCKER", "-", p.name, "token block not byte-identical to tokens.css",
                  "rule 8", "run inject_tokens.py")
        if re.search(r"var\(--", re.sub(r"/\* @tokens-begin \*/.*?/\* @tokens-end \*/", "", txt, flags=re.S)):
            declared = set(re.findall(r"(--irx-[a-z0-9-]+)\s*:", txt))
            for u in set(re.findall(r"var\((--irx-[a-z0-9-]+)\)", txt)) - declared:
                issue("BLOCKER", "-", p.name, f"undeclared token {u}", "", "add to tokens.css or correct the reference")
        mk = re.sub(r"<!--.*?-->", "", txt, flags=re.S)
        for t in NEIGHBOURHOOD_ONLY:
            if t in mk:
                issue("DEFECT", "-", p.name, f"Neighbourhood-only token {t} used in a Career asset",
                      "", "replace with the Career equivalent")
        if re.search(r"<image\b|data:image/|\.png|\.jpg", txt):
            issue("BLOCKER", "-", p.name, "raster reference", "", "remove")
        for m in re.finditer(r"<!--(.*?)-->", txt, re.S):
            if "--" in m.group(1):
                issue("BLOCKER", "-", p.name, "illegal XML comment containing a double hyphen",
                      m.group(1)[:60], "remove the double hyphen")
    print(f"  checked {len(career_files)} Career source assets")

    # --- repo discipline --------------------------------------------------
    print("\n[REPO] AFTER AUDIT")
    for cmd in (["git", "status", "--short", "--", str(ROOT)],
                ["git", "diff", "--stat", "--", str(ROOT)],
                ["git", "diff", "--name-only", "--", str(ROOT)]):
        _, o = run(cmd)
        print(f"\n$ {' '.join(cmd[:3])}\n{o or '  (none)'}")
    return report()


def report():
    print("\n" + "=" * 70)
    print("ISSUES")
    print("=" * 70)
    if not issues:
        print("  none")
    for kind in ("BLOCKER", "DEFECT", "OBSERVATION"):
        for i in [x for x in issues if x["kind"] == kind]:
            print(f"\n[{i['kind']}] {i['state']}  {i['asset']}")
            print(f"  problem  : {i['problem']}")
            if i["evidence"]:
                print(f"  evidence : {i['evidence']}")
            print(f"  action   : {i['action']}")
    blockers = sum(1 for i in issues if i["kind"] == "BLOCKER")
    defects = sum(1 for i in issues if i["kind"] == "DEFECT")
    print("\n" + "=" * 70)
    print(f"RESULT: {'FAIL' if blockers else ('PASS WITH OBSERVATIONS' if defects else 'PASS')}"
          f"   blockers {blockers} | defects {defects} | observations "
          f"{sum(1 for i in issues if i['kind']=='OBSERVATION')}")
    print("=" * 70)
    return 1 if (blockers or defects) else 0


if __name__ == "__main__":
    sys.exit(main())