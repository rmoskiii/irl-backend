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
    cap = cfg.get("maxPerNode")
    if cap and len(bs) > cap:
        # Enforced, not advisory. The stack has no vertical bound: at the current
        # type scale a 4-bubble stack already reaches y877 of 900, and the 5- and
        # 6-bubble states resolved by the scenario cannot fit at any legible size.
        # Failing here is the point - a silently overflowing frame is worse than a
        # build error, and the fix belongs in Phase 3 content, not in the renderer.
        raise SystemExit(
            f"bubbles: node '{node}' resolves {len(bs)} bubbles; maxPerNode is {cap}. "
            f"This is a Phase 3 content issue - split or compress the dialogue in the "
            f"scenario. Do not raise maxPerNode to make it compose.")

    def resolve_speaker(bubble):
        """Each bubble names its own speaker; the frame's cast order does not.

        Previously the tail was aimed at cast[0] for every bubble. That is
        correct only while a frame has one cast member, which is true of all 27
        scenario frames today and will stop being true the moment a scene has
        two people in it. The render block's `speaker` field is authoritative;
        cast order is not."""
        sid = (bubble or {}).get("speaker")
        if sid:
            for c in fr.get("cast") or []:
                if c.get("id") == sid:
                    return c
        # an absent or remote node has no cast, so the frame declares the target
        return fr.get("bubbleSpeaker") or (fr["cast"][0] if fr.get("cast") else None)

    spk = resolve_speaker(bs[0])
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
        # paddingY / firstBaseline / tailInset were 34 / 40 / 26, hard-coded
        # against fontSize 26. Left literal, the balloon would not have grown
        # with the type and the text would have burst out of it.
        h = cfg["lineHeight"] * len(lines) + cfg["paddingY"]
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
            tspk = resolve_speaker(b) or spk
            ts = scene_cfg["slots"][tspk["slot"]]
            tcc = A.get("characters", {}).get(tspk["base"]) or A["character"]
            thx = ts["x"] + (tcc["headSocket"]["x"] - tcc["basePoint"]["x"])
            thy = ts["y"] - (tcc["basePoint"]["y"] - tcc["headSocket"]["y"])
            tx = thx + cfg["tailTarget"]["dx"]
            ty = thy + cfg["tailTarget"]["dy"]
            # tail: base on the balloon edge nearest the speaker, apex at target
            near_right = tx > x + w / 2
            bx = x + w if near_right else x
            by = y + h - cfg["tailInset"]
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
                "x": str(x + cfg["padding"]), "y": str(y + cfg["firstBaseline"] + j * cfg["lineHeight"]),
                "font-family": "Zilla Slab, Georgia, serif",
                "font-size": str(cfg["fontSize"]), "fill": "var(--irx-line)"})
            t.text = ln
        y += h + cfg["gap"]
    return g


def build_montage(A, fr, ROOTDIR):
    """Compose a montage node: an ordered strip of reduced-fidelity vignettes.

    Montage is a first-class presentation mode, not a scene with the figure
    removed. It carries compressed time - `establish` covers years of friendship,
    act4_avoidant_proposal covers two weeks - and the vignette language is what
    tells the player they are not in the present tense."""
    cfg = A["montage"]
    panels = fr["panels"]
    g = ET.Element(f"{{{SVG}}}g", {"data-layer": "montage"})
    ET.SubElement(g, f"{{{SVG}}}rect", {
        "x": "0", "y": "0", "width": str(A["canvas"]["width"]),
        "height": str(A["canvas"]["height"]), "fill": f"var({cfg['matte']})"})
    pw, ph = cfg["panelWidth"], cfg["panelHeight"]
    gap = cfg["gap"]
    total = len(panels) * pw + (len(panels) - 1) * gap
    x0 = (A["canvas"]["width"] - total) / 2
    defs_out, styles_out = [], []
    for i, panel in enumerate(panels):
        vid = panel["vignette"]
        vp = ROOTDIR / "vignettes" / f"{vid}.svg"
        if not vp.exists():
            raise SystemExit(f"montage: missing vignette asset {vp.name}")
        vr = ET.parse(vp).getroot()
        for d in vr.findall(f"{{{SVG}}}defs"):
            for c in d:
                if c.tag.endswith("style"):
                    styles_out.append(c.text or "")
                else:
                    defs_out.append(c)
        inner = vr.find(f".//{{{SVG}}}g[@id='vignette']")
        if inner is None:
            raise SystemExit(f"{vid}: missing layer group 'vignette'")
        x = x0 + i * (pw + gap)
        holder = ET.SubElement(g, f"{{{SVG}}}g", {
            "transform": f"translate({x:g},{cfg['top']}) "
                         f"scale({pw / cfg['sourceWidth']:g})"})
        holder.append(inner)
        ET.SubElement(g, f"{{{SVG}}}rect", {
            "x": f"{x:g}", "y": str(cfg["top"]), "width": str(pw), "height": str(ph),
            "fill": "none", "stroke": f"var({cfg['frame']})",
            "stroke-width": str(cfg["frameWidth"])})
        if panel.get("caption"):
            t = ET.SubElement(g, f"{{{SVG}}}text", {
                "x": f"{x + pw / 2:g}", "y": str(cfg["top"] + ph + cfg["captionGap"]),
                "text-anchor": "middle", "font-family": "monospace",
                "font-size": str(cfg["captionSize"]), "letter-spacing": "1.6",
                "fill": f"var({cfg['frame']})"})
            t.text = panel["caption"].upper()
    return g, defs_out, styles_out


def main(frame_id, with_bubbles=False):
    A = json.loads((ROOT / "anchors.json").read_text(encoding="utf-8"))
    fr = A["frames"][frame_id]

    # montage is checked BEFORE the scene lookup: a montage frame has panels,
    # not a scene, and reading fr["scene"] first made it a KeyError.
    if fr.get("mode") == "montage":
        g, extra_defs, extra_styles = build_montage(A, fr, ROOT)
        out = ET.Element(f"{{{SVG}}}svg", {
            "viewBox": A["canvas"]["viewBox"], "id": frame_id,
            "data-frame": frame_id, "data-mode": "montage",
            "data-render-block": fr["renderBlockSource"]})
        d = ET.SubElement(out, f"{{{SVG}}}defs")
        st = ET.SubElement(d, f"{{{SVG}}}style")
        merged, seen = [], set()
        for block in extra_styles:
            for rule in re.findall(r"[^{}]+\{[^{}]*\}", block):
                k = rule.strip()
                if k not in seen:
                    seen.add(k); merged.append(k)
        st.text = "\n" + "\n".join(merged) + "\n"
        seen_id = set()
        for c in extra_defs:
            cid = c.get("id")
            if cid and cid in seen_id:
                continue
            if cid:
                seen_id.add(cid)
            d.append(c)
        out.append(g)
        dest = ROOT / "frames" / f"{frame_id}.svg"
        ET.ElementTree(out).write(dest, encoding="unicode", xml_declaration=False)
        print(f"composed {dest.relative_to(ROOT)}")
        print(f"  montage: {[p['vignette'] for p in fr['panels']]}")
        return 0

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
        cc = A.get("characters", {}).get(base) or A["character"]
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
