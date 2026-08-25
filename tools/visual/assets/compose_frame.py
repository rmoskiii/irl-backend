#!/usr/bin/env python3
"""Compose a demo frame from individual assets.

Reads placement ONLY from anchors.json. There are no hard-coded offsets in this
file. If a frame ever needs a nudge that is not expressible as
(anchor - basePoint), the asset contract is wrong and should be fixed there.

Usage: python3 compose_frame.py frame_1_confession
"""
import json
import re
import sys
import textwrap
import pathlib
import textwrap
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent
SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)


def load(p):
    return ET.parse(p).getroot()


def pt(s):
    x, y = s.split(",")
    return float(x), float(y)


def group(root, gid):
    return root.find(f".//{{{SVG}}}g[@id='{gid}']")


def defs_children(root):
    out = []
    for d in root.findall(f"{{{SVG}}}defs"):
        for c in d:
            if not c.tag.endswith("style"):
                out.append(c)
    return out


def style_blocks(root):
    return [c.text or "" for d in root.findall(f"{{{SVG}}}defs")
            for c in d if c.tag.endswith("style")]


def render_blocks_path():
    for c in (ROOT.parent / "render_blocks.json",
              ROOT.parent.parent / "render_blocks.json"):
        if c.exists():
            return c
    return None


def build_bubbles(A, fr, scene_cfg, node):
    """LOCKED treatment: rounded balloon + tail (variant 1).

    Text comes from render_blocks.json, so what is drawn is what the engine
    emits. The tail is aimed at the speaker's resolved head position, computed
    from the same anchors the character was placed with - it is never
    hand-placed."""
    rb = render_blocks_path()
    if rb is None or not node:
        return None
    blocks = json.loads(rb.read_text(encoding="utf-8"))
    if node not in blocks:
        raise SystemExit(f"bubbles: node '{node}' not in render_blocks.json")
    block = blocks[node]["default"]
    bs = list(block.get("bubbles", []))
    exit_beat = False
    if not bs and block.get("exitBeat"):
        # `absent` mode carries its departure line in exitBeat, not bubbles, and
        # has an EMPTY cast. Before this, the line was silently dropped and
        # placement crashed on cast[0]. Three of scene.kitchen's eight nodes.
        bs = [block["exitBeat"]]
        exit_beat = True
    if not bs:
        return None

    cfg = A["bubbles"]
    # an absent node has no cast, so the speaker must be declared on the frame
    spk = fr.get("bubbleSpeaker") or (fr["cast"][0] if fr.get("cast") else None)
    if spk is None:
        raise SystemExit(f"bubbles: node '{node}' has no cast; frame must declare "
                         f"`bubbleSpeaker` {{base, slot}} so the tail has a target")
    speaker_slot = spk["slot"]
    # a scene may override where bubbles sit; the free area is a fact about the room
    place = (scene_cfg.get("bubblePlacement") or {}).get(speaker_slot) \
            or cfg["placement"].get(speaker_slot)
    if place is None:
        raise SystemExit(f"bubbles: no placement defined for slot '{speaker_slot}'")

    base = spk["base"]
    cc = A.get("characters", {}).get(base) or A["character"]
    s = scene_cfg["slots"][speaker_slot]
    head_x = s["x"] + (cc["headSocket"]["x"] - cc["basePoint"]["x"])
    head_y = s["y"] - (cc["basePoint"]["y"] - cc["headSocket"]["y"])
    tx = head_x + cfg["tailTarget"]["dx"]
    ty = head_y + cfg["tailTarget"]["dy"]

    g = ET.Element(f"{{{SVG}}}g", {"data-layer": "bubbles",
                                   "data-exit-beat": "true" if exit_beat else "false"})
    w, r = cfg["maxWidth"], cfg["cornerRadius"]
    y = place["y"]
    for i, b in enumerate(bs):
        lines = textwrap.wrap(b["text"], cfg["charsPerLine"]) or [""]
        h = cfg["lineHeight"] * len(lines) + 34
        x = place["x"]
        bub = ET.SubElement(g, f"{{{SVG}}}g")
        ET.SubElement(bub, f"{{{SVG}}}path", {
            "d": (f"M{x} {y+r} q0 -{r} {r} -{r} h{w-2*r} q{r} 0 {r} {r} "
                  f"v{h-2*r} q0 {r} -{r} {r} h-{w-2*r} q-{r} 0 -{r} -{r} z"),
            "fill": "var(--irx-cloth-inner)", "stroke": "var(--irx-line)",
            "stroke-width": str(cfg["strokeWidth"]), "stroke-linejoin": "round"})
        # an exit beat has no tail: the speaker has left, and a tail pointing at the
        # empty room where she used to stand reads as a bug, not as intention.
        # `remote` frames have an empty cast: the speaker is on a phone. A tail
        # would point at nobody and claim she is standing there, exactly like the
        # exit-beat case. Voice, not presence.
        remote = not fr.get("cast")
        if i == len(bs) - 1 and not exit_beat and not remote:
            # tail: base on the balloon edge nearest the speaker, apex at target
            near_right = tx > x + w / 2
            bx = x + w if near_right else x
            by = y + h - 26
            hw = cfg["tail"]["baseWidth"] / 2
            # clamp to tail.length: aim at the speaker, but stop short. an
            # unclamped tail becomes a thin spike across the artwork.
            dx, dy = tx - bx, ty - by
            m = max(1e-6, (dx * dx + dy * dy) ** 0.5)
            L = cfg["tail"]["length"]
            ax, ay = bx + dx / m * L, by + dy / m * L
            ET.SubElement(bub, f"{{{SVG}}}path", {
                "d": f"M{bx} {by-hw:g} L{ax:g} {ay:g} L{bx} {by+hw:g} z",
                "fill": "var(--irx-cloth-inner)", "stroke": "var(--irx-line)",
                "stroke-width": str(cfg["strokeWidth"]), "stroke-linejoin": "round"})
            ET.SubElement(bub, f"{{{SVG}}}path", {
                "d": f"M{bx} {by-hw:g} v{2*hw:g}", "stroke": "var(--irx-cloth-inner)",
                "stroke-width": str(cfg["strokeWidth"] + 1.6), "fill": "none"})
        for j, ln in enumerate(lines):
            t = ET.SubElement(bub, f"{{{SVG}}}text", {
                "x": str(x + cfg["padding"]), "y": str(y + 40 + j * cfg["lineHeight"]),
                "font-family": "Zilla Slab, Georgia, serif",
                "font-size": str(cfg["fontSize"]), "fill": "var(--irx-line)"})
            t.text = ln
        y += h + cfg["gap"]
    return g


def main(frame_id, with_bubbles=False):
    A = json.loads((ROOT / "anchors.json").read_text(encoding="utf-8"))
    fr = A["frames"][frame_id]
    scene_id = fr["scene"]
    scene_cfg = A["scenes"][scene_id]

    env = load(ROOT / "environments" / f"{scene_id}.svg")
    layers = {}
    for name in ("background", "architecture", "environmental_detail",
                 "furniture", "foreground"):
        g = group(env, name)
        if g is None:
            raise SystemExit(f"{scene_id}: missing layer group '{name}'")
        layers[name] = [g]

    all_defs = defs_children(env)
    styles = style_blocks(env)

    # ------------------------------------------------------------- character
    for cast in fr["cast"]:
        base = cast["base"]
        cc = A["character"]
        bx, by = cc["basePoint"]["x"], cc["basePoint"]["y"]
        sx, sy = scene_cfg["slots"][cast["slot"]]["x"], scene_cfg["slots"][cast["slot"]]["y"]
        char_tx, char_ty = sx - bx, sy - by

        body = load(ROOT / "characters" / f"{base}.body.svg")
        ward = load(ROOT / "characters" / f"{base}.wardrobe.{cast['wardrobe']}.svg")
        reg = load(ROOT / "characters" / f"{base}.register.{cast['register']}.svg")
        styles += style_blocks(body) + style_blocks(ward) + style_blocks(reg)
        all_defs += defs_children(body) + defs_children(ward) + defs_children(reg)

        # head: register neckAnchor -> body headSocket
        nx, ny = pt(reg.get("data-neck-anchor"))
        hx, hy = cc["headSocket"]["x"], cc["headSocket"]["y"]
        head_tx, head_ty = hx - nx, hy - ny
        rot = float(reg.get("data-register-rotate", "0") or 0)

        gb = group(body, "character_body")
        gc = group(ward, "character_clothing")
        gh = group(reg, "character_head")
        gf = group(body, "character_front")
        gk = group(body, "character_back")       # optional: wall shadow
        gt = group(body, "character_contact")    # optional: contact shadow
        # character_front is OPTIONAL: a rear figure, or any figure whose hands
        # hang at its sides, has no layer that belongs in front of furniture.
        # Same treatment character_back and character_contact already get.
        for nm, g in (("character_body", gb), ("character_clothing", gc),
                      ("character_head", gh)):
            if g is None:
                raise SystemExit(f"{base}: missing required layer group '{nm}'")

        head_tf = f"translate({head_tx:g},{head_ty:g})"
        if rot:
            head_tf += f" rotate({rot:g},{nx:g},{ny:g})"

        # each character layer becomes its own wrapper carrying the slot transform
        def slot_layer(g, extra=None):
            w = ET.Element(f"{{{SVG}}}g", {"transform": f"translate({char_tx:g},{char_ty:g})"})
            if extra:
                inner = ET.SubElement(w, f"{{{SVG}}}g", {"transform": extra})
                inner.append(g)
            else:
                w.append(g)
            return w

        if gk is not None:
            layers.setdefault("character_back", []).append(slot_layer(gk))
        layers.setdefault("character_body", []).append(slot_layer(gb))
        layers.setdefault("character_clothing", []).append(slot_layer(gc))
        layers.setdefault("character_head", []).append(slot_layer(gh, head_tf))
        if gt is not None:
            layers.setdefault("character_contact", []).append(slot_layer(gt))
        if gf is not None:
            layers.setdefault("character_front", []).append(slot_layer(gf))

    # ----------------------------------------------------------------- props
    for pr in fr["props"]:
        pid = pr["id"]
        meta = A["props"][pid]
        px, py = meta["basePoint"]["x"], meta["basePoint"]["y"]
        anc = scene_cfg["propAnchors"][pr["anchor"]]
        tx, ty = anc["x"] - px, anc["y"] - py
        pa = load(ROOT / "props" / f"{pid}.svg")
        styles += style_blocks(pa)
        all_defs += defs_children(pa)
        g = group(pa, "prop")
        if g is None:
            raise SystemExit(f"{pid}: missing layer group 'prop'")
        w = ET.Element(f"{{{SVG}}}g", {"id": pid.replace(".", "_"),
                                       "transform": f"translate({tx:g},{ty:g})"})
        w.append(g)
        layers.setdefault("prop", []).append(w)

    # ------------------------------------------------------------- assemble
    out = ET.Element(f"{{{SVG}}}svg", {
        "viewBox": A["canvas"]["viewBox"],
        "id": frame_id,
        "data-frame": frame_id,
        "data-render-block": fr["renderBlockSource"],
    })
    d = ET.SubElement(out, f"{{{SVG}}}defs")
    st = ET.SubElement(d, f"{{{SVG}}}style")

    merged, seen_rule = [], set()
    for block in styles:
        for rule in re.findall(r"[^{}]+\{[^{}]*\}", block):
            key = rule.strip()
            if key not in seen_rule:
                seen_rule.add(key)
                merged.append(key)
    st.text = "\n" + "\n".join(merged) + "\n"

    seen_id = set()
    for c in all_defs:
        cid = c.get("id")
        if cid and cid in seen_id:
            continue
        if cid:
            seen_id.add(cid)
        d.append(c)

    for name in A["layerOrder"]:
        for g in layers.get(name, []):
            wrapper = ET.SubElement(out, f"{{{SVG}}}g", {"data-layer": name})
            wrapper.append(g)

    if with_bubbles:
        gb = build_bubbles(A, fr, scene_cfg, fr.get("bubblesFrom"))
        if gb is not None:
            out.append(gb)

    dest = ROOT / "frames" / f"{frame_id}.svg"
    dest.parent.mkdir(exist_ok=True)
    ET.ElementTree(out).write(dest, encoding="unicode", xml_declaration=False)
    txt = dest.read_text(encoding="utf-8")
    dest.write_text(
        f"<!-- GENERATED by compose_frame.py from anchors.json — do not hand-edit.\n"
        f"     Source render block: {fr['renderBlockSource']} -->\n" + txt,
        encoding="utf-8")
    print(f"composed {dest.relative_to(ROOT)}")
    print(f"  layers: {[n for n in A['layerOrder'] if layers.get(n)]}")
    return 0


if __name__ == "__main__":
    argv = [a for a in sys.argv[1:] if a != "--bubbles"]
    sys.exit(main(argv[0] if argv else "frame_1_confession",
                  with_bubbles="--bubbles" in sys.argv))