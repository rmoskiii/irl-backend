#!/usr/bin/env python3
"""Side-by-side register comparison sheet.

Composes the SAME body + SAME wardrobe with each register, at identical scale,
with the head socket and neck anchor drawn as crosshairs so the join can be
inspected rather than taken on trust.

Diagnostic output. Not a shipping asset.

Usage: python3 compare_registers.py open tight
"""
import re
import sys
import json
import pathlib
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent
SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)

CELL_W, CELL_H = 520, 620
SCALE = 0.72


def load(p):
    return ET.parse(p).getroot()


def group(root, gid):
    return root.find(f".//{{{SVG}}}g[@id='{gid}']")


def styles(root):
    return [c.text or "" for d in root.findall(f"{{{SVG}}}defs")
            for c in d if c.tag.endswith("style")]


def main(*regs, outname="register_comparison"):
    A = json.loads((ROOT / "anchors.json").read_text(encoding="utf-8"))
    hs = A["character"]["headSocket"]
    n = len(regs)
    W, H = CELL_W * n, CELL_H + 90

    out = ET.Element(f"{{{SVG}}}svg", {"viewBox": f"0 0 {W} {H}",
                                       "id": "register_comparison"})
    d = ET.SubElement(out, f"{{{SVG}}}defs")
    st = ET.SubElement(d, f"{{{SVG}}}style")

    body = load(ROOT / "characters" / "figure_a.body.svg")
    ward = load(ROOT / "characters" / "figure_a.wardrobe.home_casual.svg")
    blocks = styles(body) + styles(ward)

    ET.SubElement(out, f"{{{SVG}}}rect", {
        "x": "0", "y": "0", "width": str(W), "height": str(H),
        "fill": "var(--irx-tile)"})

    for i, reg in enumerate(regs):
        rp = ROOT / "characters" / f"figure_a.register.{reg}.svg"
        r = load(rp)
        blocks += styles(r)
        nx, ny = (float(v) for v in r.get("data-neck-anchor").split(","))
        rot = float(r.get("data-register-rotate", "0") or 0)

        cell = ET.SubElement(out, f"{{{SVG}}}g", {
            "transform": f"translate({i*CELL_W},0)"})

        lbl = ET.SubElement(cell, f"{{{SVG}}}text", {
            "x": str(CELL_W // 2), "y": "44", "text-anchor": "middle",
            "font-family": "monospace", "font-size": "26",
            "fill": "var(--irx-line)"})
        lbl.text = f"register: {reg}"
        sub = ET.SubElement(cell, f"{{{SVG}}}text", {
            "x": str(CELL_W // 2), "y": "70", "text-anchor": "middle",
            "font-family": "monospace", "font-size": "15",
            "fill": "var(--irx-line)", "opacity": "0.65"})
        sub.text = f"neckAnchor {nx:g},{ny:g}   rotate {rot:g}"

        # identical placement for every cell: same scale, same origin
        stage = ET.SubElement(cell, f"{{{SVG}}}g", {
            "transform": f"translate({CELL_W/2 - 210*SCALE:g},90) scale({SCALE})"})

        stage.append(group(body, "character_body"))
        stage.append(group(ward, "character_clothing"))
        head = ET.SubElement(stage, f"{{{SVG}}}g", {
            "transform": f"translate({hs['x']-nx:g},{hs['y']-ny:g}) "
                         f"rotate({rot:g},{nx:g},{ny:g})"})
        head.append(group(r, "character_head"))
        stage.append(group(body, "character_front"))

        # head socket crosshair, drawn last so it sits over the artwork
        ch = ET.SubElement(stage, f"{{{SVG}}}g", {"opacity": "0.85"})
        for path in (f"M{hs['x']-46} {hs['y']} h92", f"M{hs['x']} {hs['y']-46} v92"):
            ET.SubElement(ch, f"{{{SVG}}}path", {
                "d": path, "stroke": "#E0483C", "stroke-width": "2.4",
                "stroke-dasharray": "9 7", "fill": "none"})
        ET.SubElement(ch, f"{{{SVG}}}circle", {
            "cx": str(hs["x"]), "cy": str(hs["y"]), "r": "6",
            "fill": "none", "stroke": "#E0483C", "stroke-width": "2.4"})
        # shoulder line: if this ever needs to move per register, the contract
        # needs an optional shoulder variant. it does not move here.
        ET.SubElement(ch, f"{{{SVG}}}path", {
            "d": "M118 272 h184", "stroke": "#2E7DBF", "stroke-width": "2.2",
            "stroke-dasharray": "7 6", "fill": "none", "opacity": "0.8"})

    merged, seen = [], set()
    for b in blocks:
        for rule in re.findall(r"[^{}]+\{[^{}]*\}", b):
            k = rule.strip()
            if k not in seen:
                seen.add(k)
                merged.append(k)
    st.text = "\n" + "\n".join(merged) + "\n"

    dest = ROOT / "frames" / f"{outname}.svg"
    ET.ElementTree(out).write(dest, encoding="unicode", xml_declaration=False)
    dest.write_text("<!-- GENERATED diagnostic. red = head socket, "
                    "blue = shoulder line. -->\n" + dest.read_text(encoding="utf-8"),
                    encoding="utf-8")
    print(f"wrote {dest.relative_to(ROOT)}  ({', '.join(regs)})")
    return 0


if __name__ == "__main__":
    argv = sys.argv[1:]
    out = "register_comparison"
    if "--out" in argv:
        i = argv.index("--out")
        out = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    sys.exit(main(*(argv or ["open", "tight"]), outname=out))