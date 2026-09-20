#!/usr/bin/env python3
"""split_bands.py — extract a composed IRX scene into parallax bands.

Destination: irl-backend/tools/visual/tools/split_bands.py

One scene in; one SVG per band out, each keeping the source viewBox so the
outputs stack in register with no repositioning maths. The splitter is a
splitter: it never redraws, reorders or re-styles a path.

Two separations are not obvious and both were discovered by measurement rather
than assumed.

1. `foreground` is not a depth band. In every shipped scene it mixes near
   geometry with full-canvas atmosphere rects carrying the grain filter and
   vignette gradient. Parallaxed together, the lighting slides across the
   frame — a defect that renders correctly on load and only appears on scroll.
   Atmosphere is emitted separately and flagged data-parallax="false".

2. `architecture` is not one plane. In a one-point-perspective scene it holds
   both the receding side terraces AND the far terrace at the vanishing point.
   The far terrace carries the target house and n-window-lit: it is the plane
   the camera approaches, so it is the parallax REFERENCE and must not
   translate. Measured with them merged, the destination rendered at 5.6% of
   the camera's zoom and never approached.

   The split uses two independent rules and requires them to agree:
     structural — a far-plane path is axis-aligned (h/v only, no L segments),
                  because the far terrace is frontal by construction
     geometric  — its bounding box lies inside the far-plane box
   Structural alone is fragile (an author could draw a frontal wall with L).
   Geometric alone over-captures: the deepest side-terrace units fall inside
   the box but still recede, and must keep parallaxing. The intersection is
   exact, and disagreement raises rather than guessing.

Usage:
    python3 split_bands.py <scene.svg> <outdir> [--far-box x0 x1 y0 y1]
"""
from __future__ import annotations
import argparse
import json
import pathlib
import re
import sys

BANDS = ["background", "architecture", "environmental_detail", "furniture", "foreground"]

# The far plane for scene.neighbourhood_night: the head of the T-junction.
# Passed in rather than hard-coded so a second scene declares its own.
DEFAULT_FAR_BOX = (960.0, 1500.0, 100.0, 560.0)


class SplitError(RuntimeError):
    pass


def read_group(svg: str, gid: str) -> str:
    """Body of <g id="gid">. Raises unless found exactly once."""
    hits = re.findall(r'<g id="%s"[^>]*>' % re.escape(gid), svg)
    if len(hits) != 1:
        raise SplitError(f'group "{gid}" found {len(hits)} times, expected exactly 1')
    start = svg.index(hits[0]) + len(hits[0])
    depth = 1
    i = start
    while depth and i < len(svg):
        nxt_open = svg.find("<g", i)
        nxt_close = svg.find("</g>", i)
        if nxt_close == -1:
            raise SplitError(f'group "{gid}" is not closed')
        if nxt_open != -1 and nxt_open < nxt_close:
            depth += 1
            i = nxt_open + 2
        else:
            depth -= 1
            i = nxt_close + 4
    return svg[start : i - 4]


def path_bbox(path_el: str):
    """Approximate bbox from the d attribute. Handles M/L/h/v/q, absolute and
    relative, which is the full command set the IRX generators emit."""
    m = re.search(r'\sd="([^"]+)"', path_el)
    if not m:
        return None
    toks = re.findall(r"[MmLlHhVvQqZz]|-?\d+\.?\d*", m.group(1))
    x = y = 0.0
    xs: list[float] = []
    ys: list[float] = []
    cmd = None
    buf: list[float] = []

    def flush():
        nonlocal x, y
        if not cmd:
            return
        c = cmd
        if c in "ML":
            for i in range(0, len(buf) - 1, 2):
                x, y = buf[i], buf[i + 1]
                xs.append(x); ys.append(y)
        elif c in "ml":
            for i in range(0, len(buf) - 1, 2):
                x += buf[i]; y += buf[i + 1]
                xs.append(x); ys.append(y)
        elif c == "H":
            for v in buf:
                x = v; xs.append(x); ys.append(y)
        elif c == "h":
            for v in buf:
                x += v; xs.append(x); ys.append(y)
        elif c == "V":
            for v in buf:
                y = v; xs.append(x); ys.append(y)
        elif c == "v":
            for v in buf:
                y += v; xs.append(x); ys.append(y)
        elif c in "Qq":
            rel = c == "q"
            for i in range(0, len(buf) - 3, 4):
                cx = x + buf[i] if rel else buf[i]
                cy = y + buf[i + 1] if rel else buf[i + 1]
                xs.append(cx); ys.append(cy)
                x = x + buf[i + 2] if rel else buf[i + 2]
                y = y + buf[i + 3] if rel else buf[i + 3]
                xs.append(x); ys.append(y)

    for t in toks:
        if re.match(r"[A-Za-z]", t):
            flush()
            cmd = t
            buf = []
        else:
            buf.append(float(t))
    flush()
    return (min(xs), max(xs), min(ys), max(ys)) if xs else None


def is_atmosphere(el: str) -> bool:
    """Full-canvas overlay rather than geometry: a filter, a gradient fill, or
    explicitly non-interactive."""
    return (
            el.lstrip().startswith("<rect")
            and ('filter="url(' in el or 'fill="url(' in el or 'pointer-events="none"' in el)
    )


def split_architecture(body: str, far_box):
    """Return (side_plane, far_plane) as element lists. Raises on disagreement."""
    els = re.findall(r"<path[^>]*/>", body)
    if not els:
        raise SplitError("architecture contains no paths — refusing to emit an empty band")
    side, far, disagree = [], [], []
    x0, x1, y0, y1 = far_box
    for el in els:
        bb = path_bbox(el)
        if bb is None:
            side.append(el)
            continue
        structural = " L" not in el
        geometric = bb[0] >= x0 and bb[1] <= x1 and bb[3] <= y1
        if structural and not geometric:
            # An axis-aligned path outside the far box means the far plane has
            # moved or a frontal element was added elsewhere. Guessing here is
            # how a band silently loses geometry.
            disagree.append((el[:70], tuple(round(v, 1) for v in bb)))
        (far if (structural and geometric) else side).append(el)
    if disagree:
        raise SplitError(
            "architecture split: %d axis-aligned path(s) fall outside the far-plane "
            "box %s — the far plane has moved or a frontal element was added "
            "elsewhere. First: %r" % (len(disagree), far_box, disagree[0])
        )
    if not far:
        raise SplitError("architecture split produced an empty far plane")
    return side, far


def split_environmental(body: str):
    """Return (mid_plane, overhead) element lists.

    Same class of finding as the architecture split, found the same way. The
    telegraph wire spans the corridor OVERHEAD, far nearer the camera than the
    street lamps authored beside it in the same band. Held at one depth, it
    either lagged into the terminal frame (desktop failed) or, raised, lagged
    into the narrow one (mobile failed) — a single factor cannot serve both,
    which is the definition of two planes.

    Rule: an element wider than 500 units that sits entirely above the
    occlusion line is an overhead span, not street furniture. Nothing standing
    on the pavement is that wide and that high.
    """
    els = re.findall(r"<path[^>]*/>", body)
    if not els:
        raise SplitError("environmental_detail contains no paths")
    mid, over = [], []
    for el in els:
        bb = path_bbox(el)
        wide_overhead = bb is not None and (bb[1] - bb[0]) > 500 and bb[3] < 600
        (over if wide_overhead else mid).append(el)
    return mid, over


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("outdir")
    ap.add_argument("--far-box", nargs=4, type=float, default=list(DEFAULT_FAR_BOX))
    args = ap.parse_args()

    src = pathlib.Path(args.scene).read_text()
    out = pathlib.Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    # Web output only. Source keeps its provenance.
    src_stripped = re.sub(r"<metadata>.*?</metadata>", "", src, flags=re.S)

    root = re.search(r"<svg[^>]*>", src_stripped).group(0)
    view_box = re.search(r'viewBox="([^"]+)"', root).group(1)
    carried = {
        k: v
        for k, v in re.findall(r'(data-[a-z-]+)="([^"]*)"', root)
        if k in ("data-time", "data-occlusion-line", "data-camera-frame",
                 "data-authoring-canvas", "data-vanishing-point", "data-asset")
    }
    style = re.search(r"<style>(.*?)</style>", src_stripped, re.S)
    defs = re.search(r"<defs>(.*?)</defs>", src_stripped, re.S)

    # VALIDATE EVERYTHING BEFORE WRITING ANYTHING.
    bodies = {b: read_group(src_stripped, b) for b in BANDS}
    side, far = split_architecture(bodies["architecture"], tuple(args.far_box))
    env_mid, env_over = split_environmental(bodies["environmental_detail"])

    fg = bodies["foreground"]
    near_body = read_group(fg, "n-near-geometry") if 'id="n-near-geometry"' in fg else ""
    atmo_body = read_group(fg, "n-atmosphere") if 'id="n-atmosphere"' in fg else ""
    if not atmo_body:
        atmo_els = [e for e in re.findall(r"<rect[^>]*/>", fg) if is_atmosphere(e)]
        near_body = "\n".join(e for e in re.findall(r"<path[^>]*/>", fg))
        atmo_body = "\n".join(atmo_els)
    if not atmo_body.strip():
        raise SplitError(
            "foreground yielded no atmosphere. Every shipped scene carries grain "
            "and vignette here; an empty result means the band shape changed and "
            "the lighting would parallax with the near geometry."
        )

    aperture = read_group(src_stripped, "n-window-lit") if 'id="n-window-lit"' in src_stripped else ""
    ap_attrs = ""
    if aperture:
        ap_attrs = re.search(r'<g id="n-window-lit"([^>]*)>', src_stripped).group(1)

    emitted = [
        ("background", bodies["background"], "true"),
        ("architecture", "\n".join(side), "true"),
        ("architecture_far", "\n".join(far), "true"),
        ("environmental_detail", "\n".join(env_mid), "true"),
        ("furniture", bodies["furniture"], "true"),
        ("overhead", "\n".join(env_over), "true") if env_over else None,
        ("near", near_body, "true"),
        ("atmosphere", atmo_body, "false"),
    ]
    if aperture:
        emitted.insert(3, ("n-window-lit", aperture, "true"))

    emitted = [e for e in emitted if e is not None]

    for name, body, _ in emitted:
        if not body.strip():
            raise SplitError(f'band "{name}" extracted nothing — refusing a silent no-op')

    attrs = " ".join(f'{k}="{v}"' for k, v in carried.items())
    manifest = {"source": pathlib.Path(args.scene).name, "viewBox": view_box, "bands": []}

    for name, body, parallax in emitted:
        extra = ap_attrs if name == "n-window-lit" else ""
        doc = (
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}"\n'
                f'     data-band="{name}" data-parallax="{parallax}" {attrs}>\n'
                + (f"<style>{style.group(1)}</style>\n" if style else "")
                + (f"<defs>{defs.group(1)}</defs>\n" if defs else "")
                + f'<g id="{name}"{extra}>\n{body}\n</g>\n</svg>\n'
        )
        (out / f"{name}.svg").write_text(doc)
        manifest["bands"].append(
            {
                "id": name,
                "file": f"{name}.svg",
                "paths": body.count("<path"),
                "rects": body.count("<rect"),
                "parallax": parallax == "true",
            }
        )

    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    total = sum(b["paths"] for b in manifest["bands"])
    src_total = src_stripped.count("<path")
    if total != src_total:
        raise SplitError(f"path count changed: source {src_total}, emitted {total}")
    print(f"{manifest['source']}: {len(emitted)} bands, {total} paths (source {src_total}) OK")
    for b in manifest["bands"]:
        print(f'  {b["id"]:22} {b["paths"]:4} paths  {b["rects"]:2} rects  parallax={b["parallax"]}')
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SplitError as e:
        print(f"split_bands: {e}", file=sys.stderr)
        sys.exit(2)