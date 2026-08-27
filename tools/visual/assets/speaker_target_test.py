#!/usr/bin/env python3
"""Synthetic two-character speaker-targeting test (MATERIAL-6).

Proves the tail resolves against the bubble's declared `speaker`, not against
cast order. Runs entirely on synthetic fixtures written outside the source tree:
the scenario is never consulted and anchors.json is never modified.
"""
import json, pathlib, re, subprocess, sys, shutil, xml.etree.ElementTree as ET

SRC = pathlib.Path("/home/claude/irx/irx_handoff/tools/visual/assets")
RIG = pathlib.Path("/home/claude/irx/audit_only/speaker_rig_root/assets")
SVGNS = "http://www.w3.org/2000/svg"

RIG.mkdir(exist_ok=True); (RIG / "frames").mkdir(exist_ok=True)
for d in ("characters", "environments", "props", "vignettes"):
    tgt = RIG / d
    if not tgt.exists():
        tgt.symlink_to(SRC / d)
# --composer <path> runs the same fixtures against a different composer, which is
# how the negative control (the pre-fix composer) is demonstrated.
COMPOSER = pathlib.Path(sys.argv[sys.argv.index("--composer") + 1]) \
    if "--composer" in sys.argv else SRC / "compose_frame.py"
shutil.copy(COMPOSER, RIG / "compose_frame.py")
print(f"composer under test: {COMPOSER}")

A = json.loads((SRC / "anchors.json").read_text())
JESS = {"id": "char.jessica", "base": "figure_a", "slot": "left",
        "register": "open", "wardrobe": "home_casual"}
ALEX = {"id": "char.alex", "base": "figure_b", "slot": "right",
        "register": "open", "wardrobe": "home_casual"}

def frame(cast):
    return {"renderBlockSource": "SYNTHETIC - speaker targeting test, not a scenario state",
            "scene": "scene.kitchen", "time": "night", "framing": "direct",
            "cast": cast, "props": [], "bubblesFrom": "spk_test"}

A2 = dict(A)
A2["frames"] = {"spk_AB": frame([JESS, ALEX]), "spk_BA": frame([ALEX, JESS])}
(RIG / "anchors.json").write_text(json.dumps(A2, indent=2))
# one bubble, spoken by Alex (right slot) in both frames
(RIG.parent / "render_blocks.json").write_text(json.dumps({"spk_test": {"default": {
    "mode": "scene", "framing": "direct", "scene": {"id": "scene.kitchen", "time": "night"},
    "cast": [JESS, ALEX], "props": [],
    "bubbles": [{"speaker": "char.alex", "text": "This line is mine."}]}}}, indent=2))

slots = A["scenes"]["scene.kitchen"]["slots"]
def tail_apex(name):
    subprocess.run([sys.executable, str(RIG / "compose_frame.py"), name, "--bubbles"],
                   cwd=RIG, capture_output=True, text=True, check=True)
    root = ET.parse(RIG / "frames" / f"{name}.svg").getroot()
    g = [x for x in root.iter(f"{{{SVGNS}}}g") if x.get("data-layer") == "bubbles"][0]
    for p in g.iter(f"{{{SVGNS}}}path"):
        m = re.match(r"M([\d.]+) ([\d.]+) L([\d.-]+) ([\d.-]+) L", p.get("d", ""))
        if m:
            return float(m.group(3)), float(m.group(4)), float(m.group(1))
    return None

# The tail is length-clamped, so its apex sits near the balloon, not on the
# speaker. Direction is therefore the signal: Alex is at the RIGHT slot (x=1130)
# and Jessica at the LEFT (x=470), and the balloon origin is x=48, so a tail
# aimed at Alex points right (apex_x > base_x) and one aimed at Jessica points left.
ok = True
res = []
for name, order in (("spk_AB", "cast order Jessica,Alex"), ("spk_BA", "cast order Alex,Jessica")):
    ax, ay, bx = tail_apex(name)
    good = ax > bx
    ok &= good
    res.append((ax, ay))
    print(f"{order:28} tail base x={bx:6.1f} apex x={ax:6.1f}  -> "
          f"{'ALEX (right slot) - correct' if good else 'JESSICA (left slot) - WRONG'}")

ok &= res[0] == res[1]
print(f"{'cast-order independence':28} {'identical apex in both orders' if res[0]==res[1] else 'APEX MOVED WITH CAST ORDER'}")
print("\nSPEAKER TARGETING:",
      "PASS - tail follows bubble.speaker, and is unchanged by cast order" if ok else "FAIL")
sys.exit(0 if ok else 1)