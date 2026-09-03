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
        "characters/figure_b.body.svg":
            ["character_back", "character_body", "character_contact", "character_front"],
        "characters/figure_b_rear.body.svg":
            ["character_back", "character_body"],
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

    _rb = next((c for c in (ROOT.parent / "render_blocks.json",
                            ROOT.parent.parent / "render_blocks.json")
                if c.exists()), None)
    if _rb is None:
        fail(9, "render_blocks.json not found in tools/visual/ or its parent")
        block = None
    else:
        block = json.loads(_rb.read_text(encoding="utf-8"))["confession"]["default"]
    if block is not None:
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
            # per-character, same reason compose_frame's cast loop is: the global
            # anchors.character block is deprecated, and a figure_b frame legally
            # carries translate(110,-14) which this would have called undocumented.
            _cc = A.get("characters", {}).get(c["base"]) or A["character"]
            legal.add((_cc["headSocket"]["x"] - A["register"]["neckAnchor"]["x"],
                       _cc["headSocket"]["y"] - A["register"]["neckAnchor"]["y"]))
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
        turned_of = next((k for k, v in reg_list["characters"].items()
                          if v.get("turned") == base), None)
        if cid:
            allowed = reg_list["characters"][cid]["registers"]
            if declared not in allowed:
                fail(11, f"{rp.name}: register {declared!r} not declared for {cid} {allowed}")
        elif turned_of:
            # a `turned` base is a rear view. By standing rule it carries exactly
            # one register, 'rear' - rear figures report posture, not expression.
            if declared != "rear":
                fail(11, f"{rp.name}: rear base {base!r} may only declare register "
                         f"'rear', got {declared!r}")
        else:
            fail(11, f"{rp.name}: base {base!r} is neither a `base` nor a `turned` "
                     f"entry in registries.json")

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
        # Only enforce for characters whose hair is declared FIXED. Jessica's
        # hair varies per register by design; this rule previously applied to
        # anything with a <g id="hair"> wrapper, which happened to be Alex only.
        # That was luck, not intent.
        policy = (A.get("characters", {}).get(base) or {}).get("hairPolicy", "fixed")
        if policy != "fixed":
            continue
        if len(set(files.values())) > 1:
            fail(11, f"{base}: registers carry DIFFERENT hair blocks — the character "
                     f"changes haircut between nodes. Files: {sorted(files)}")

    # 13 — vignettes may use ONLY the --irx-vig-* ramp plus line and accent.
    # A vignette that reached into the full palette would compete with a real
    # environment and flatten the distinction between memory and present tense.
    allowed_vig = {"--irx-vig-light", "--irx-vig-base", "--irx-vig-mid",
                   "--irx-vig-dark", "--irx-line", "--irx-accent"}
    vdir = ROOT / "vignettes"
    if vdir.exists():
        for vp in sorted(vdir.glob("*.svg")):
            txt = vp.read_text(encoding="utf-8")
            art = re.sub(r"<defs>.*?</defs>", "", txt, flags=re.S)
            for tok in set(re.findall(r"var\((--irx-[a-z-]+)\)", art)):
                if tok not in allowed_vig:
                    fail(13, f"{vp.name}: uses {tok}, outside the vignette palette")
            body = re.search(r'<g id="vignette">(.*?)</g>\s*</svg>', txt, re.S)
            if body is None:
                fail(13, f"{vp.name}: missing layer group 'vignette'")

    # 12 — Phase 1 untouched
    scn = ROOT.parents[2] / "src" / "data" / "scenarios" / "the_secret.json"
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