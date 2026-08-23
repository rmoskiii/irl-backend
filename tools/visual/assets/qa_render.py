#!/usr/bin/env python3
"""QA rasteriser. NOT part of the shipping pipeline.

cairosvg does not resolve CSS custom properties, so this flattens var(--x) to
literal hex purely so a PNG can be produced for visual inspection. The shipping
SVGs keep their token layer untouched.

Usage: python3 qa_render.py frames/frame_1_confession.svg [width]
"""
import re
import sys
import pathlib
import cairosvg

ROOT = pathlib.Path(__file__).resolve().parent
QA = ROOT / "qa"


def tokens():
    src = (ROOT / "tokens.css").read_text(encoding="utf-8")
    return dict(re.findall(r"(--irx-[a-z-]+)\s*:\s*([^;]+);", src))


def flatten(svg_text, tk):
    def sub_var(m):
        name, fallback = m.group(1), m.group(2)
        return tk.get(name, (fallback or "#FF00FF").strip())
    out = re.sub(r"var\(\s*(--irx-[a-z-]+)\s*(?:,\s*([^)]+))?\)", sub_var, svg_text)
    # class rules survive; only the :root block is now dead weight
    out = re.sub(r":root\s*\{[^}]*\}", "", out)
    return out


def main(path, width=1600):
    tk = tokens()
    src = pathlib.Path(path)
    flat = flatten(src.read_text(encoding="utf-8"), tk)
    QA.mkdir(exist_ok=True)
    tmp = QA / (src.stem + ".flat.svg")
    tmp.write_text(flat, encoding="utf-8")
    png = QA / (src.stem + ".png")
    cairosvg.svg2png(url=str(tmp), write_to=str(png), output_width=int(width))
    leftover = re.findall(r"var\(--irx-[a-z-]+\)", flat)
    print(f"rendered {png.relative_to(ROOT)}  ({width}px)")
    if leftover:
        print(f"  WARNING unresolved tokens: {sorted(set(leftover))}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 1600))