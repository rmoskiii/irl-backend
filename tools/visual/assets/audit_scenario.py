#!/usr/bin/env python3
"""Full-scenario visual audit.

Walks EVERY reachable node in the render blocks and asks one question per node:
can this be composed with the assets that exist? Reports gaps by category rather
than crashing on the first one, because the point is a complete picture.

This is not a validator. Validators check the assets are internally consistent.
This checks the assets are SUFFICIENT for the scenario.

Usage: python3 audit_scenario.py
"""
import json, pathlib, collections, sys

ROOT = pathlib.Path(__file__).resolve().parent
RB = ROOT.parent / "render_blocks.json"
if not RB.exists(): RB = ROOT.parent.parent / "render_blocks.json"

A = json.loads((ROOT / "anchors.json").read_text(encoding="utf-8"))
blocks = json.loads(RB.read_text(encoding="utf-8"))
frames = A["frames"]

def have(sub, name): return (ROOT / sub / name).exists()

rows, gaps = [], collections.defaultdict(list)
modes = collections.Counter()
covered = set()
for f in frames.values():
    src = f.get("renderBlockSource","")
    if "->" in src: covered.add(src.split("->")[1].strip())

for nid in sorted(blocks):
    b = blocks[nid]["default"]
    if b is None:
        modes["messages"] += 1
        rows.append((nid, "messages", "phone UI", "n/a", "OK"))
        continue
    mode = b["mode"]; modes[mode] += 1
    missing = []
    if mode == "montage":
        panels = json.loads((ROOT.parent / "mapping.the_secret.json")
                            .read_text(encoding="utf-8"))["montagePanels"].get(nid, [])
        for p in panels:
            if not have("vignettes", f"{p['vignette']}.svg"):
                missing.append(p["vignette"])
        detail = f"{len(panels)} panels"
    else:
        sid = b["scene"]["id"]
        if not have("environments", f"{sid}.svg"): missing.append(sid)
        for c in b.get("cast", []):
            base = "figure_a" if c["id"]=="char.jessica" else "figure_b"
            if b.get("framing") == "turned": base += "_rear"
            reg = "rear" if base.endswith("_rear") else c["register"]
            for sub, fn in (("characters", f"{base}.body.svg"),
                            ("characters", f"{base}.register.{reg}.svg"),
                            ("characters", f"{base}.wardrobe.{c['wardrobe']}.svg")):
                if not have(sub, fn): missing.append(fn)
        for p in b.get("props", []):
            if not have("props", f"{p}.svg"): missing.append(p)
        detail = f"{sid} / {len(b.get('cast',[]))} cast / {len(b.get('props',[]))} props"
    status = "OK" if not missing else "MISSING"
    if missing: gaps[nid] = missing
    rows.append((nid, mode, detail, "composed" if nid in covered else "-", status))

print("="*100)
print("THE SECRET = FULL SCENARIO VISUAL AUDIT")
print("="*100)
print(f"\n{'node':28s}{'mode':10s}{'requires':44s}{'frame':10s}status")
print("-"*100)
for r in rows:
    print(f"{r[0]:28s}{r[1]:10s}{r[2]:44s}{r[3]:10s}{r[4]}")

print("\n" + "-"*100)
print("MODE DISTRIBUTION:", dict(sorted(modes.items())))
renderable = sum(v for k,v in modes.items() if k!="messages")
print(f"render-bearing nodes: {renderable}   messages (phone UI, no assets): {modes['messages']}")
print(f"nodes with all assets present: {sum(1 for r in rows if r[4]=='OK')}/{len(rows)}")
print(f"nodes with a composed frame:   {sum(1 for r in rows if r[3]=='composed')}/{len(rows)}")
if gaps:
    print("\nASSET GAPS")
    for n,m in gaps.items(): print(f"  {n}: {m}")
else:
    print("\nNO ASSET GAPS = every reachable node can be composed.")
sys.exit(1 if gaps else 0)