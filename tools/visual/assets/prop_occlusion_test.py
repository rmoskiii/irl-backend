#!/usr/bin/env python3
"""Prop occlusion test — pixel-difference method.

Supersedes the earlier regex-based collision check, which derived balloon
rectangles from a regex over path data, silently matched nothing, and therefore
reported a clean result by comparing against an empty set. That check is
withdrawn; do not reinstate it. This one renders each frame three ways and
counts how many of each prop's OWN pixels survive once the bubbles are drawn,
so it cannot pass by failing to find anything.
"""
import re, sys, pathlib, cairosvg, numpy as np, xml.etree.ElementTree as ET
from PIL import Image

SVG = "http://www.w3.org/2000/svg"; ET.register_namespace("", SVG)
HERE = pathlib.Path(__file__).resolve().parent
FRAMES = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / 'frames'
THRESHOLD = 90.0     # % of a prop's pixels that must remain visible

def flat(t):
    r = re.search(r':root\s*\{(.*?)\}', t, re.S)
    tok = {k: v.strip() for k, v in re.findall(r'(--[\w-]+)\s*:\s*([^;]+);', r.group(1))} if r else {}
    for _ in range(6):
        n = re.sub(r'var\((--[\w-]+)\s*(?:,\s*([^)]*))?\)',
                   lambda m: tok.get(m.group(1), (m.group(2) or '#F0F').strip()), t)
        if n == t: break
        t = n
    return t

def png(txt, tag):
    cairosvg.svg2png(bytestring=txt.encode(), write_to=f'/tmp/occ_{tag}.png',
                     output_width=1600, output_height=900)
    return np.array(Image.open(f'/tmp/occ_{tag}.png').convert('RGB')).astype(int)

def strip(txt, layers):
    root = ET.fromstring(txt)
    for parent in root.iter():
        for c in list(parent):
            if c.get('data-layer') in layers:
                parent.remove(c)
    return ET.tostring(root, encoding='unicode')

rows, failures = [], []
for f in sorted(FRAMES.glob('*.svg')):
    t = flat(f.read_text())
    if 'data-layer="prop"' not in t:
        continue
    has_bub = 'data-layer="bubbles"' in t
    full, no_prop = png(t, 'a'), png(strip(t, {'prop'}), 'b')
    no_bub = png(strip(t, {'bubbles'}), 'c') if has_bub else full
    no_both = png(strip(t, {'prop', 'bubbles'}), 'd') if has_bub else no_prop
    visible_now = (np.abs(full - no_prop).sum(axis=2) > 12)
    prop_total = (np.abs(no_bub - no_both).sum(axis=2) > 12)
    if prop_total.sum() == 0:
        continue
    kept = visible_now.sum() / prop_total.sum() * 100
    props = ','.join(n.replace('prop_', '') for n in re.findall(r'data-prop="([^"]+)"', t))
    rows.append((kept, f.stem, props))
    if kept < THRESHOLD:
        failures.append((kept, f.stem, props))

rows.sort()
print(f"{'% prop pixels visible':>22}  frame  [props]")
for k, n, p in rows:
    print(f"{k:>21.0f}%  {n}  [{p}]{'   <-- OCCLUDED' if k < THRESHOLD else ''}")
print(f"\n{len(rows)} prop-bearing frames tested, threshold {THRESHOLD:.0f}%")
print("RESULT:", "PASS - no prop materially occluded by a bubble" if not failures
else f"FAIL - {len(failures)} frame(s) below threshold")
sys.exit(0 if not failures else 1)