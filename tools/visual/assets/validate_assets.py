#!/usr/bin/env python3
"""IRX Phase 2A asset validator.

Structural checks only — it cannot tell you whether the art is any good.
That is what qa_render.py plus a pair of eyes is for.

Usage: python3 validate_assets.py
"""
import json
import re
import sys
import pathlib
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent
SVG = "http://www.w3.org/2000/svg"
fails, warns = [], []


def fail(n, m):
    fails.append(f"[{n}] {m}")


def warn(n, m):
    warns.append(f"[{n}] {m}")


def assets():
    return sorted(p for p in ROOT.rglob("*.svg")
                  if "qa" not in p.parts and "frames" not in p.parts)


def main():
    A = json.loads((ROOT / "anchors.json").read_text(encoding="utf-8"))
    frame = A["frames"]["frame_1_confession"]

    # 1 — every required Frame 1 asset exists
    required = [ROOT / "environments" / f"{frame['scene']}.svg"]
    for c in frame["cast"]:
        required += [
            ROOT / "characters" / f"{c['base']}.body.svg",
            ROOT / "characters" / f"{c['base']}.wardrobe.{c['wardrobe']}.svg",
            ROOT / "characters" / f"{c['base']}.register.{c['register']}.svg",
            ]
    for p in frame["props"]:
        required.append(ROOT / "props" / f"{p['id']}.svg")
    for p in required:
        if not p.exists():
            fail(1, f"missing required asset: {p.relative_to(ROOT)}")

    # 2 — valid SVG
    roots = {}
    for p in assets() + [ROOT / "frames" / "frame_1_confession.svg"]:
        try:
            roots[p] = ET.parse(p).getroot()
        except Exception as e:
            fail(2, f"{p.relative_to(ROOT)}: not well-formed — {e}")

    # 2b — XML comments may not contain "--". This has broken the build three
    # times (scene.kitchen dividers, figure_b.body, figure_b.register.bright)
    # because CSS custom property names start with a double hyphen and get
    # quoted in explanatory comments. Caught here rather than as a parse crash.
    for p in assets():
        for m in re.finditer(r"<!--(.*?)-->", p.read_text(encoding="utf-8"), re.S):
            if "--" in m.group(1):
                fail(2, f"{p.relative_to(ROOT)}: XML comment contains '--' "
                        f"(illegal): ...{m.group(1).strip()[:60]}...")

    # 3 — no raster
    for p, r in roots.items():
        txt = p.read_text(encoding="utf-8")
        if re.search(r"<image\b|data:image/|\.png|\.jpg|\.jpeg", txt):
            fail(3, f"{p.relative_to(ROOT)}: contains a raster reference")

    # 4 — viewBox conventions
    expect = {
        "environments/scene.kitchen.svg": A["canvas"]["viewBox"],
        "characters/figure_a.body.svg": A["character"]["localViewBox"],
        "characters/figure_a.wardrobe.home_casual.svg": A["character"]["localViewBox"],
        **{f"characters/{q.name}": A["register"]["localViewBox"]
           for q in sorted((ROOT / "characters").glob("*.register.*.svg"))},
        "props/prop.jacket_chair.svg": A["props"]["prop.jacket_chair"]["localViewBox"],
        "props/prop.last_glass.svg": A["props"]["prop.last_glass"]["localViewBox"],
        "frames/frame_1_confession.svg": A["canvas"]["viewBox"],
    }
    for rel, vb in expect.items():
        p = ROOT / rel
        if p in roots and roots[p].get("viewBox") != vb:
            fail(4, f"{rel}: viewBox {roots[p].get('viewBox')!r}, contract says {vb!r}")

    # 5 — character anchor documented and honoured
    want = f"{A['register']['neckAnchor']['x']},{A['register']['neckAnchor']['y']}"
    for rp in sorted((ROOT / "characters").glob("*.register.*.svg")):
        if rp not in roots:
            continue
        na = roots[rp].get("data-neck-anchor")
        if na != want:
            fail(5, f"{rp.name}: neckAnchor {na!r} != contract {want!r}")
        rot = roots[rp].get("data-register-rotate")
        lim = A["register"].get("rotateLimit", {"min": -16, "max": 16})
        if rot is not None and not (lim["min"] <= float(rot) <= lim["max"]):
            fail(5, f"{rp.name}: register rotate {rot} outside contract limit "
                    f"{lim['min']}..{lim['max']} (rotation is tilt, not yaw)")
    for bp in sorted((ROOT / "characters").glob("*.body.svg")):
        if bp not in roots:
            continue
        base = bp.name.split(".body.svg")[0]
        cc = A.get("characters", {}).get(base) or A["character"]
        hs = roots[bp].get("data-head-socket")
        want = f"{cc['headSocket']['x']},{cc['headSocket']['y']}"
        if hs != want:
            fail(5, f"{bp.name}: headSocket {hs!r} != contract {want!r}")
        if base not in A.get("characters", {}):
            fail(5, f"{bp.name}: no anchors.characters['{base}'] entry — neckSpan is "
                    f"per-character and must be declared before the figure is used")

    # 6 — slot anchors documented
    for s in ("left", "centre", "right"):
        if s not in A["scenes"]["scene.kitchen"]["slots"]:
            fail(6, f"scene.kitchen missing slot anchor '{s}'")

    # 7 — layer names consistent
    exported = {
        "environments/scene.kitchen.svg":
            ["background", "architecture", "environmental_detail", "furniture", "foreground"],
        "characters/figure_a.body.svg":
            ["character_back", "character_body", "character_contact", "character_front"],
        "characters/figure_a.wardrobe.home_casual.svg": ["character_clothing"],
        **{f"characters/{q.name}": ["character_head"]
           for q in sorted((ROOT / "characters").glob("*.register.*.svg"))},
        "props/prop.jacket_chair.svg": ["prop"],
        "props/prop.last_glass.svg": ["prop"],
    }
    for rel, names in exported.items():
        p = ROOT / rel
        if p not in roots:
            continue
        have = {g.get("id") for g in roots[p].iter(f"{{{SVG}}}g")}
        for n in names:
            if n not in have:
                fail(7, f"{rel}: missing layer group '{n}'")
            if n not in A["layerOrder"]:
                fail(7, f"{rel}: layer '{n}' is not in anchors.json layerOrder")

    # 8 — colour tokens consistent
    tok = (ROOT / "tokens.css").read_text(encoding="utf-8")
    body = tok.split(":root {", 1)[1].rsplit("}", 1)[0]
    canonical = f"/* @tokens-begin */\n:root {{{body}}}\n/* @tokens-end */"
    declared = set(re.findall(r"(--irx-[a-z-]+)\s*:", tok))
    for p in assets():
        txt = p.read_text(encoding="utf-8")
        if canonical not in txt:
            fail(8, f"{p.relative_to(ROOT)}: token block not byte-identical to tokens.css")
        for u in set(re.findall(r"var\((--irx-[a-z-]+)\)", txt)):
            if u not in declared:
                fail(8, f"{p.relative_to(ROOT)}: uses undeclared token {u}")
        art = re.sub(r"<defs>.*?</defs>", "", txt, flags=re.S)
        hard = [h for h in re.findall(r'(?:fill|stroke)="(#[0-9A-Fa-f]{3,6})"', art)]
        for h in set(hard):
            warn(8, f"{p.relative_to(ROOT)}: hard-coded colour {h} outside <defs>")

    # 9 — IDs correspond to render blocks
    rb = json.loads((ROOT.parent.parent / "render_blocks.json").read_text(encoding="utf-8"))
    block = rb["confession"]["default"]
    if block["scene"]["id"] != frame["scene"]:
        fail(9, "frame scene does not match render block")
    if sorted(p["id"] for p in frame["props"]) != sorted(block["props"]):
        fail(9, f"frame props {[p['id'] for p in frame['props']]} != render block {block['props']}")
    c0, b0 = frame["cast"][0], block["cast"][0]
    for k in ("id", "slot", "register", "wardrobe"):
        if c0[k] != b0[k]:
            fail(9, f"cast {k}: frame {c0[k]!r} != render block {b0[k]!r}")
    if frame.get("framing", block["framing"]) != block["framing"]:
        fail(9, "framing mismatch")

    # 10 — no undocumented offsets in the composed frame
    fp = ROOT / "frames" / "frame_1_confession.svg"
    if fp in roots:
        legal = set()
        sc = A["scenes"][frame["scene"]]
        cx, cy = A["character"]["basePoint"]["x"], A["character"]["basePoint"]["y"]
        for c in frame["cast"]:
            s = sc["slots"][c["slot"]]
            legal.add((s["x"] - cx, s["y"] - cy))
            legal.add((A["character"]["headSocket"]["x"] - A["register"]["neckAnchor"]["x"],
                       A["character"]["headSocket"]["y"] - A["register"]["neckAnchor"]["y"]))
        for p_ in frame["props"]:
            m = A["props"][p_["id"]]["basePoint"]
            a = sc["propAnchors"][p_["anchor"]]
            legal.add((a["x"] - m["x"], a["y"] - m["y"]))
        for g in roots[fp].iter(f"{{{SVG}}}g"):
            t = g.get("transform")
            if not t:
                continue
            for mt in re.finditer(r"translate\(([-\d.]+),([-\d.]+)\)", t):
                v = (float(mt.group(1)), float(mt.group(2)))
                if v not in legal:
                    fail(10, f"composed frame has undocumented offset translate{v}")

    # 11 — every register is independently composable and self-identifying
    for rp in sorted((ROOT / "characters").glob("*.register.*.svg")):
        if rp not in roots:
            continue
        r = roots[rp]
        declared = r.get("data-register")
        from_name = rp.name.split(".register.")[1].rsplit(".svg", 1)[0]
        if declared != from_name:
            fail(11, f"{rp.name}: data-register={declared!r} does not match filename")
        # resolve the character from the BASE, not hardcoded to Jessica.
        # This rule previously validated every register against char.jessica's
        # list, so Alex's own registers failed as soon as he existed.
        reg_list = json.loads((ROOT.parent / "registries.json").read_text(encoding="utf-8"))
        base = rp.name.split(".register.")[0]
        cid = next((k for k, v in reg_list["characters"].items()
                    if v.get("base") == base), None)
        if cid is None:
            fail(11, f"{rp.name}: base {base!r} maps to no character in registries.json")
        else:
            allowed = reg_list["characters"][cid]["registers"]
            if declared not in allowed:
                fail(11, f"{rp.name}: register {declared!r} not declared for {cid} {allowed}")

    # 11b — all registers of a base must carry an IDENTICAL hair block.
    # A register is atomic, so the haircut is duplicated across every register
    # file. Without this check a character can silently change haircut between
    # nodes — which is exactly how the hairline and hair-mass geometry drifted
    # apart during 2B.1 before it was caught by eye.
    import collections
    hair = collections.defaultdict(dict)
    for rp in sorted((ROOT / "characters").glob("*.register.*.svg")):
        base = rp.name.split(".register.")[0]
        txt = rp.read_text(encoding="utf-8")
        m = re.search(r'<g id="hair">.*?</g>', txt, re.S)
        if m:
            hair[base][rp.name] = re.sub(r"\s+", " ", m.group(0)).strip()
    for base, files in hair.items():
        if len(set(files.values())) > 1:
            fail(11, f"{base}: registers carry DIFFERENT hair blocks — the character "
                     f"changes haircut between nodes. Files: {sorted(files)}")

    # 12 — Phase 1 untouched
    scn = ROOT.parent.parent / "scenarios" / "the_secret.json"
    if scn.exists():
        d = json.loads(scn.read_text(encoding="utf-8"))
        n = d["nodes"]["confession"]["presentation"]["data"]
        if "cast" in n.get("visual", {}):
            fail(12, "scenario now contains a hand-authored cast block")
        if len(d["nodes"]) != 30:
            fail(12, f"scenario node count changed: {len(d['nodes'])}")

    print("=" * 70)
    print("IRX PHASE 2A — ASSET VALIDATION")
    print("=" * 70)
    print(f"\nassets: {len(assets())}   composed frames: 1\n")
    if fails:
        print(f"FAILURES ({len(fails)})")
        for f in fails:
            print("  " + f)
    else:
        print("no structural failures")
    if warns:
        print(f"\nWARNINGS ({len(warns)})")
        for w in warns:
            print("  " + w)
    print("\n" + "=" * 70)
    print("FAIL" if fails else "PASS")
    print("=" * 70)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())