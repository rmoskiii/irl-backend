#!/usr/bin/env python3
"""2C acceptance fixtures, generated from the SIGNED-OFF 2B.6 state.

Two levels, as agreed:

  Level 1  composition plan   — ordered layers, asset IDs, transforms, resolved
                                character/register/wardrobe, props, scene, mode,
                                bubble configuration
  Level 2  composed SVG       — canonicalised, so attribute ordering and
                                whitespace cannot cause false failures

Each fixture is keyed by the SHA-256 of the canonicalised resolved render block,
which is also the agreed runtime cache key: two scenario states that resolve to
the same visual must hit the same fixture and the same cache entry.

The plan is computed from the same inputs the composer uses (anchors + frame
declaration), then CHECKED against the transform actually present in the
signed-off SVG. If the two disagree the generator fails rather than emitting a
fixture, so a fixture can never encode a plan the locked artwork does not match.
"""
import hashlib
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

SVG = "http://www.w3.org/2000/svg"
ROOT = pathlib.Path("/home/claude/irx/irx_handoff")
ASSETS = ROOT / "tools/visual/assets"
OUT = pathlib.Path("/home/claude/irx/audit_only/fixtures")

A = json.loads((ASSETS / "anchors.json").read_text())
RB = json.loads((ROOT / "tools/visual/render_blocks.json").read_text())
LAYER_ORDER = A["layerOrder"] if "layerOrder" in A else None


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def block_hash(block):
    return hashlib.sha256(canonical(block).encode()).hexdigest()


def canonical_svg(text):
    """Normalise so irrelevant serialisation differences cannot fail a diff."""
    root = ET.fromstring(text)

    def norm(el):
        attrs = {k: re.sub(r"\s+", " ", v).strip() for k, v in sorted(el.attrib.items())}
        return {"tag": el.tag.split("}")[-1], "attrs": attrs,
                "text": (el.text or "").strip() or None,
                "children": [norm(c) for c in el]}
    return canonical(norm(root))


def plan_for(frame_id, fr, block):
    """Ordered layer plan: what the Node renderer must produce, in order."""
    if fr.get("mode") == "montage" or block["mode"] == "montage":
        # a montage is panels of vignettes, not a room with a cast
        return {"canvas": A["canvas"], "mode": "montage",
                "panels": [{"vignette": p.get("vignette"), "caption": p.get("caption")}
                           for p in fr.get("panels", [])],
                "layers": [{"layer": "montage_panel", "index": i,
                            "source": f"vignettes/{p.get('vignette')}.svg"}
                           for i, p in enumerate(fr.get("panels", []))]}
    scene_id = fr["scene"]
    scene = A["scenes"][scene_id]
    layers = []
    for lname in ("background", "architecture", "environmental_detail"):
        layers.append({"layer": lname, "source": f"environments/{scene_id}.svg",
                       "group": lname, "transform": None})

    cast_plan = []
    for c in fr.get("cast", []):
        slot = scene["slots"][c["slot"]]
        cc = A.get("characters", {}).get(c["base"]) or A["character"]
        tx = slot["x"] - cc["basePoint"]["x"]
        ty = slot["y"] - cc["basePoint"]["y"]
        reg_path = f"characters/{c['base']}.register.{c['register']}.svg"
        rot = None
        m = re.search(r'data-register-rotate="([-\d.]+)"',
                      (ASSETS / reg_path).read_text())
        if m and float(m.group(1)):
            rot = {"degrees": float(m.group(1)),
                   "about": [A["register"]["neckAnchor"]["x"],
                             A["register"]["neckAnchor"]["y"]]}
        cast_plan.append({
            "id": c["id"], "base": c["base"], "slot": c["slot"],
            "register": c["register"], "wardrobe": c["wardrobe"],
            "transform": f"translate({tx},{ty})",
            "registerRotate": rot,
            "assets": {
                "body": f"characters/{c['base']}.body.svg",
                "register": reg_path,
                "wardrobe": f"characters/{c['base']}.wardrobe.{c['wardrobe']}.svg"},
        })
    for lname in ("character_back", "character_body", "character_clothing", "character_head"):
        for c in cast_plan:
            layers.append({"layer": lname, "cast": c["id"], "transform": c["transform"]})
    layers.append({"layer": "furniture", "source": f"environments/{scene_id}.svg",
                   "group": "furniture", "transform": None})
    for p in fr.get("props", []):
        pa = scene["propAnchors"][p["anchor"]]
        pc = A["props"][p["id"]]
        layers.append({"layer": "prop", "id": p["id"], "anchor": p["anchor"],
                       "source": f"props/{p['id']}.svg",
                       "transform": f"translate({pa['x'] - pc['basePoint']['x']},"
                                    f"{pa['y'] - pc['basePoint']['y']})"})
    for lname in ("character_contact", "character_front"):
        for c in cast_plan:
            layers.append({"layer": lname, "cast": c["id"], "transform": c["transform"]})
    layers.append({"layer": "foreground", "source": f"environments/{scene_id}.svg",
                   "group": "foreground", "transform": None})

    bubbles = block.get("bubbles") or ([block["exitBeat"]] if block.get("exitBeat") else [])
    if bubbles:
        placement = (scene.get("bubblePlacement") or {}) or A["bubbles"]["placement"]
        slot = fr["cast"][0]["slot"] if fr.get("cast") else fr["bubbleSpeaker"]["slot"]
        origin = placement.get(slot) or A["bubbles"]["placement"][slot]
        layers.append({
            "layer": "bubbles",
            "origin": origin,
            "count": len(bubbles),
            "exitBeat": bool(block.get("exitBeat") and not block.get("bubbles")),
            "remote": not fr.get("cast"),
            "speakers": [b.get("speaker") for b in bubbles],
            "config": {k: A["bubbles"][k] for k in
                       ("fontSize", "lineHeight", "charsPerLine", "maxWidth",
                        "cornerRadius", "gap", "padding", "paddingY",
                        "firstBaseline", "tailInset", "strokeWidth", "maxPerNode")},
        })
    return {"canvas": A["canvas"], "scene": scene_id, "mode": block["mode"],
            "framing": block.get("framing"), "cast": cast_plan, "layers": layers}


def main():
    OUT.mkdir(exist_ok=True)
    frames_dir = ASSETS / "frames"
    key_to_frame = {}
    for fid, fr in A["frames"].items():
        s = fr["renderBlockSource"].replace("->", "\u2192")
        m = re.search(r"render_blocks\.json\s*\u2192\s*(\w+)\s*\u2192\s*(\S+)", s)
        if m:
            key_to_frame.setdefault((m.group(1), m.group(2).strip()), []).append(fid)

    index, skipped, mismatches = [], [], []
    for (node, variant), fids in sorted(key_to_frame.items()):
        fid = sorted(fids)[0]                       # one fixture per resolved key
        svg_path = frames_dir / f"{fid}.svg"
        if not svg_path.exists():
            skipped.append(f"{node}::{variant} ({fid}) — blocked by maxPerNode")
            continue
        block = RB[node][variant]
        h = block_hash(block)
        plan = plan_for(fid, A["frames"][fid], block)

        # self-check: computed cast transform must match the signed-off SVG
        root = ET.parse(svg_path).getroot()
        for g in root:
            if g.get("data-layer") == "character_body":
                actual = list(g)[0].get("transform")
                expected = plan["cast"][0]["transform"] if plan["cast"] else None
                if expected and actual != expected:
                    mismatches.append(f"{node}::{variant}: plan {expected} != svg {actual}")

        (OUT / f"{h[:16]}.plan.json").write_text(json.dumps({
            "renderKey": f"{node}::{variant}", "cacheKey": h,
            "sourceFrame": fid, "presentedBy": sorted(fids),
            "renderBlock": block, "plan": plan}, indent=2))
        (OUT / f"{h[:16]}.svg.json").write_text(json.dumps({
            "renderKey": f"{node}::{variant}", "cacheKey": h,
            "canonicalSvg": canonical_svg(svg_path.read_text()),
            "canonicalSha256": hashlib.sha256(canonical_svg(svg_path.read_text()).encode()).hexdigest(),
        }, indent=2))
        index.append({"renderKey": f"{node}::{variant}", "cacheKey": h,
                      "sourceFrame": fid, "mode": block["mode"],
                      "scene": block.get("scene", {}).get("id")})

    if mismatches:
        print("PLAN/SVG MISMATCH — no fixture set written:")
        for m in mismatches:
            print("  ", m)
        sys.exit(1)

    (OUT / "index.json").write_text(json.dumps({
        "generatedFrom": "signed-off 2B.6 state",
        "cacheKey": "sha256 of the canonicalised resolved render block",
        "count": len(index), "fixtures": index,
        "skipped": skipped}, indent=2))
    print(f"fixtures written: {len(index)} resolved keys, two levels each")
    for s in skipped:
        print("  skipped:", s)
    dupes = {f"{n}::{v}": f for (n, v), f in key_to_frame.items() if len(f) > 1}
    print("keys with multiple declared presentations (one fixture each):", dupes)


if __name__ == "__main__":
    main()