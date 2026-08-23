#!/usr/bin/env python3
"""Inject tokens.css into every asset SVG.

Each shipping asset carries the token block verbatim so it is self-contained
(no external CSS dependency). This script is the only way that block should ever
be edited: change tokens.css, re-run, done. validate_assets.py enforces that all
embedded copies are byte-identical to the source.

Idempotent. Replaces either the <!--@TOKENS@--> marker or an existing block.
"""
import re
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
TOKENS = ROOT / "tokens.css"

BEGIN, END = "/* @tokens-begin */", "/* @tokens-end */"


def canonical_block():
    src = TOKENS.read_text(encoding="utf-8")
    body = src.split(":root {", 1)[1].rsplit("}", 1)[0]
    return f"{BEGIN}\n:root {{{body}}}\n{END}"


def main():
    block = canonical_block()
    changed = []
    for p in sorted(ROOT.rglob("*.svg")):
        s = p.read_text(encoding="utf-8")
        if BEGIN in s and END in s:
            new = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), block, s, flags=re.S)
        elif "<!--@TOKENS@-->" in s:
            new = s.replace("<!--@TOKENS@-->", block)
        else:
            print(f"  SKIP (no marker): {p.relative_to(ROOT)}")
            continue
        if new != s:
            p.write_text(new, encoding="utf-8")
            changed.append(p.relative_to(ROOT))
    print(f"tokens injected into {len(changed)} file(s)")
    for c in changed:
        print(f"  {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())