#!/usr/bin/env python3
"""Register swap stress test.

Composes two frames that differ in exactly one render-block field (register),
then proves mechanically that nothing except the character_head layer changed.

This is the actual contract test. Two SVGs that merely look compatible prove
nothing; this diffs the composed output layer by layer.

Usage: python3 register_swap_test.py
"""
import re
import sys
import pathlib
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent
SVG = "http://www.w3.org/2000/svg"
A_NAME = sys.argv[1] if len(sys.argv) > 2 else "frame_1_confession"
B_NAME = sys.argv[2] if len(sys.argv) > 2 else "frame_2_reacts_judge"
A_FRAME = ROOT / "frames" / f"{A_NAME}.svg"
B_FRAME = ROOT / "frames" / f"{B_NAME}.svg"

fails = []


def fail(m):
    fails.append(m)


def layers(path):
    root = ET.parse(path).getroot()
    out = {}
    for g in root:
        if g.tag == f"{{{SVG}}}g" and g.get("data-layer"):
            out.setdefault(g.get("data-layer"), []).append(g)
    return root, out


def canon(el):
    """Serialised form of a layer, for comparison."""
    return ET.tostring(el, encoding="unicode")


def transforms(el):
    return re.findall(r"translate\(([-\d.]+),([-\d.]+)\)|rotate\(([^)]*)\)",
                      " ".join(g.get("transform", "") for g in el.iter()))


def main():
    if not B_FRAME.exists():
        print(f"missing {B_FRAME.name} — run compose_frame.py frame_2_reacts_judge first")
        return 1

    ra, la = layers(A_FRAME)
    rb, lb = layers(B_FRAME)

    print("=" * 74)
    print("REGISTER SWAP STRESS TEST")
    print(f"{A_NAME}  vs  {B_NAME}")
    print("=" * 74)

    # A — canvas identical
    if ra.get("viewBox") != rb.get("viewBox"):
        fail(f"canvas differs: {ra.get('viewBox')} vs {rb.get('viewBox')}")
    print(f"\ncanvas            {ra.get('viewBox')}   {'same' if ra.get('viewBox')==rb.get('viewBox') else 'DIFFERS'}")

    # B — same layer set (props differ by render block, so exclude)
    IGNORE = {"prop", "bubbles"}   # render-block content, not character geometry
    sa, sb = set(la) - IGNORE, set(lb) - IGNORE
    if sa != sb:
        fail(f"layer sets differ: only-in-open {sa-sb}, only-in-tight {sb-sa}")
    print(f"layer set         {len(sa)} character/scene layers   "
          f"{'identical' if sa==sb else 'DIFFERS'}")

    # C — every non-head layer byte-identical
    print("\nlayer-by-layer comparison")
    print("-" * 74)
    for name in [n for n in la if n in lb]:
        if name in IGNORE:
            print(f"  {name:22s} skipped (render-block content, varies by node)")
            continue
        a_s = "".join(canon(g) for g in la[name])
        b_s = "".join(canon(g) for g in lb[name])
        same = a_s == b_s
        if name == "character_head":
            if same:
                fail("character_head is IDENTICAL — the register did not actually swap")
            print(f"  {name:22s} DIFFERS  <- expected: this is the swapped layer")
        else:
            if not same:
                fail(f"{name} changed when only the register should have")
            print(f"  {name:22s} {'identical' if same else 'CHANGED  <- CONTRACT FAILURE'}")

    # D — head placement transform identical across both
    ta = [g.get("transform") for g in la["character_head"][0].iter()
          if g.get("transform")]
    tb = [g.get("transform") for g in lb["character_head"][0].iter()
          if g.get("transform")]
    print("\nhead placement transforms")
    print("-" * 74)
    print(f"  open   {ta}")
    print(f"  tight  {tb}")
    tr = lambda L: [m.group(0) for t in L for m in re.finditer(r"translate\([^)]*\)", t)]
    ta_t, tb_t = tr(ta), tr(tb)
    if ta_t != tb_t:
        fail(f"head translate differs: {ta_t} vs {tb_t}")
    print(f"  translate components {'identical' if ta_t==tb_t else 'DIFFER'}"
          f"  (rotation is per-register and expected to vary)")

    # E — body placement identical
    ba = [g.get("transform") for g in la["character_body"][0].iter() if g.get("transform")]
    bb = [g.get("transform") for g in lb["character_body"][0].iter() if g.get("transform")]
    if ba != bb:
        fail(f"body transform differs: {ba} vs {bb}")
    print(f"\nbody placement    {ba}   {'identical' if ba==bb else 'DIFFERS'}")

    # F — neck join: both registers declare the same anchor
    print("\nneck anchor declared by each register")
    print("-" * 74)
    # iterate the actual FILES, not a name pattern rebuilt from figure_a.
    # This previously assumed every register belonged to figure_a and crashed
    # as soon as Alex had registers Jessica does not.
    files = sorted((ROOT / "characters").glob("*.register.*.svg"))
    for q in files:
        reg = q.name.split(".register.")[1].rsplit(".svg", 1)[0]
        base = q.name.split(".register.")[0]
        r = ET.parse(q).getroot()
        print(f"  {base}/{reg:10s} neckAnchor={r.get('data-neck-anchor')}  "
              f"viewBox={r.get('viewBox')}  rotate={r.get('data-register-rotate')}")
    anchors = {ET.parse(q).getroot().get("data-neck-anchor") for q in files}
    boxes = {ET.parse(q).getroot().get("viewBox") for q in files}
    if len(anchors) != 1:
        fail(f"registers declare different neck anchors: {anchors}")
    if len(boxes) != 1:
        fail(f"registers declare different viewBoxes: {boxes}")

    print("\n" + "=" * 74)
    if fails:
        print(f"FAIL ({len(fails)})")
        for f in fails:
            print("  " + f)
    else:
        print("PASS — swapping the register changed the head layer and nothing else")
    print("=" * 74)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())