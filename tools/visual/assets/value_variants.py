#!/usr/bin/env python3
"""Environment value calibration test.

Produces controlled tonal variants of scene.kitchen by scaling the LIGHTNESS of
environment colour tokens about their own mean. Nothing else changes:

  - no geometry, no path data, no stroke widths, no opacities
  - no composition, anchors, occlusion line, layer structure
  - no character tokens (skin / hair / cloth / glass / jacket)
  - no line, shadow or accent tokens (line art and lighting stay fixed)

k > 1 widens the environment's internal value spread (stronger separation).
k < 1 compresses it toward its mean (softer separation).

Usage: python3 value_variants.py
"""
import colorsys
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
KITCHEN = ROOT / "environments" / "scene.kitchen.svg"

# environment surfaces only. deliberately excludes:
#   skin/skin-shade/hair/hair-light/cloth*/glass*/jacket*  -> character + props
#   line/line-soft/shadow                                  -> line art, shared
#   accent/accent-dim/lamp-warm/cool-spill/highlight        -> lighting
ENV = ["wall", "wall-dark", "wall-pattern", "tile", "tile-alt", "floor",
       "cabinet", "cabinet-dark", "counter", "counter-edge",
       "curtain", "curtain-dark", "sky-high", "sky-mid", "sky-low",
       "outside-dark"]

VARIANTS = {"A": 1.00, "B": 1.20, "C": 0.82}


def hex2l(h):
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return colorsys.rgb_to_hls(r, g, b)


def l2hex(h, l, s):
    r, g, b = colorsys.hls_to_rgb(h, max(0.0, min(1.0, l)), s)
    return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))


def scale(svg_text, k):
    vals = {}
    for name in ENV:
        m = re.search(rf"--irx-{name}:\s*(#[0-9A-Fa-f]{{6}});", svg_text)
        if m:
            vals[name] = m.group(1)
    hls = {n: hex2l(v) for n, v in vals.items()}
    mean = sum(v[1] for v in hls.values()) / len(hls)
    out, report = svg_text, []
    for n, (h, l, s) in hls.items():
        nl = (l - mean) * k + mean
        new = l2hex(h, nl, s)
        out = re.sub(rf"(--irx-{n}:\s*)#[0-9A-Fa-f]{{6}};", rf"\g<1>{new};", out)
        report.append((n, vals[n], new, round((nl - l) * 100, 1)))
    return out, report, mean


def main():
    """Operate on the COMPOSED frame, not the kitchen source.

    compose_frame.py emits a :root block from every contributing asset, and the
    character blocks land after the environment block, so a modified kitchen
    token is overridden in the cascade. Scaling the composed frame instead is
    both correct and a cleaner single-variable test: identical geometry, one
    composition, only environment token VALUES differ."""
    subprocess.run([sys.executable, "compose_frame.py", "frame_1_confession"],
                   cwd=ROOT, capture_output=True, check=True)
    base = (ROOT / "frames" / "frame_1_confession.svg").read_text(encoding="utf-8")
    for tag, k in VARIANTS.items():
        text, report, mean = scale(base, k)
        dest = ROOT / "frames" / f"_value_{tag}.svg"
        dest.write_text(text, encoding="utf-8")
        subprocess.run([sys.executable, "qa_render.py",
                        f"frames/_value_{tag}.svg", "1600"],
                       cwd=ROOT, capture_output=True, check=True)
        print(f"\nVARIANT {tag}   k={k}   env mean L={mean:.3f}")
        print("  token              before   after    dL%")
        for n, a, b, d in report:
            flag = "" if abs(d) < 0.05 else ("  darker" if d < 0 else "  lighter")
            print(f"  {n:18s} {a}  {b}  {d:+5.1f}{flag}")
    print("\ncharacter tokens untouched; kitchen source untouched")
    return 0


if __name__ == "__main__":
    sys.exit(main())