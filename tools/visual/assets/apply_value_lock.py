#!/usr/bin/env python3
"""Apply ENVIRONMENT VALUE LOCK: C to tokens.css.

Approved art-direction decision. Applies exactly the transformation that
generated Variant C in value_variants.py:

    for each of the 16 environment tonal tokens
        L' = (L - mean_L_of_those_16) * 0.82 + mean_L_of_those_16

Hue and saturation are untouched. No token is hand-tweaked beyond the
transformation. Character, line, shadow and lighting tokens are not in the set
and are not read or written.

Idempotency guard: refuses to run twice. Re-running would compress the range
again and silently drift the palette.

Usage: python3 apply_value_lock.py
"""
import colorsys
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
TOKENS = ROOT / "tokens.css"
K = 0.82
MARK = "/* ENVIRONMENT VALUE LOCK: C applied (k=0.82) */"

ENV = ["wall", "wall-dark", "wall-pattern", "tile", "tile-alt", "floor",
       "cabinet", "cabinet-dark", "counter", "counter-edge",
       "curtain", "curtain-dark", "sky-high", "sky-mid", "sky-low",
       "outside-dark"]


def hls(h):
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return colorsys.rgb_to_hls(r, g, b)


def hexof(h, l, s):
    r, g, b = colorsys.hls_to_rgb(h, max(0.0, min(1.0, l)), s)
    return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))


def main():
    src = TOKENS.read_text(encoding="utf-8")
    if MARK in src:
        print("ALREADY APPLIED — refusing to compress the range a second time.")
        return 1

    vals = {}
    for n in ENV:
        m = re.search(rf"--irx-{n}:\s*(#[0-9A-Fa-f]{{6}});", src)
        if not m:
            print(f"ERROR: token --irx-{n} not found")
            return 1
        vals[n] = m.group(1)

    conv = {n: hls(v) for n, v in vals.items()}
    mean = sum(v[1] for v in conv.values()) / len(conv)

    print(f"environment tokens: {len(ENV)}   mean L = {mean:.4f}   k = {K}\n")
    print(f"  {'token':<18}{'before':<10}{'after':<10}{'dL%':>7}")
    out = src
    for n, (h, l, s) in conv.items():
        nl = (l - mean) * K + mean
        new = hexof(h, nl, s)
        out = re.sub(rf"(--irx-{n}:\s*)#[0-9A-Fa-f]{{6}};", rf"\g<1>{new};", out, count=1)
        print(f"  {n:<18}{vals[n]:<10}{new:<10}{(nl - l) * 100:+7.2f}")

    out = out.replace("/* IRX Visual Asset Tokens — Phase 2A",
                      f"{MARK}\n/* IRX Visual Asset Tokens — Phase 2A")
    TOKENS.write_text(out, encoding="utf-8")
    print(f"\nwritten to {TOKENS.name}")
    print("next: inject_tokens.py, then recompose frames")
    return 0


if __name__ == "__main__":
    sys.exit(main())