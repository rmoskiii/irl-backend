#!/usr/bin/env python3
"""Sync the canonical token block into every asset.

WHY THIS EXISTS. validate_assets.py rule 8 requires the @tokens block in every
asset to be BYTE-IDENTICAL to the :root body of tokens.css. So the moment
tokens.css gains the Career tokens, every asset that does not carry the new
body fails rule 8 - including all 45 Neighbourhood assets, which are otherwise
untouched by the Career work.

That is not a reason to avoid appending. It is the reason to do the re-embed
mechanically rather than by hand across 54 files. The change is ADDITIVE: no
existing token name or value moves, the Career tokens are namespaced
--irx-career-*, and no asset's rendering changes. Verify that with a render
diff before committing, not by trusting this docstring.

Usage:
    python3 tools/visual/sync_tokens.py --check     # report, change nothing
    python3 tools/visual/sync_tokens.py --write     # append + re-embed
"""
import re
import sys
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
TOKENS = HERE / "assets" / "tokens.css"
ASSETS = HERE / "assets"
CAREER_BLOCK = HERE / "assets" / "tokens.career.css"
MARK = "/* ==== career district ==== */"


def root_body(css: str) -> str:
    """The :root { ... } body of tokens.css, exactly as rule 8 reads it."""
    return css.split(":root {", 1)[1].rsplit("}", 1)[0]


def canonical(css: str) -> str:
    return f"/* @tokens-begin */\n:root {{{root_body(css)}}}\n/* @tokens-end */"


def assets():
    return sorted(p for p in ASSETS.rglob("*.svg")
                  if "qa" not in p.parts and "frames" not in p.parts)


def main(write: bool) -> int:
    if not TOKENS.exists():
        print(f"missing {TOKENS}"); return 2
    css = TOKENS.read_text(encoding="utf-8")

    if MARK not in css:
        if not CAREER_BLOCK.exists():
            print(f"missing {CAREER_BLOCK} - the Career token definitions to append")
            return 2
        add = CAREER_BLOCK.read_text(encoding="utf-8").strip()
        body = root_body(css)
        new_css = css.replace(":root {" + body + "}",
                              ":root {" + body.rstrip() + "\n\n  " + MARK + "\n"
                              + add + "\n}")
        print(f"tokens.css: appending {len(re.findall(r'--irx-career-', add))} "
              f"Career token references")
        if write:
            TOKENS.write_text(new_css, encoding="utf-8")
        css = new_css
    else:
        print("tokens.css: Career block already present")

    want = canonical(css)
    stale, ok = [], 0
    for p in assets():
        txt = p.read_text(encoding="utf-8")
        m = re.search(r"/\* @tokens-begin \*/.*?/\* @tokens-end \*/", txt, re.S)
        if not m:
            stale.append((p, "NO TOKEN BLOCK")); continue
        if m.group(0) == want:
            ok += 1; continue
        stale.append((p, "differs"))
        if write:
            p.write_text(txt[:m.start()] + want + txt[m.end():], encoding="utf-8")

    print(f"\nassets already canonical: {ok}")
    print(f"assets rewritten:         {len(stale) if write else 0}")
    if stale and not write:
        print(f"assets that WOULD be rewritten: {len(stale)}")
        for p, why in stale[:12]:
            print(f"   {p.relative_to(ASSETS)}  ({why})")
        if len(stale) > 12:
            print(f"   ...and {len(stale)-12} more")
    print("\nNEXT: re-render one Neighbourhood frame and one Career frame and diff "
          "against their committed PNGs. Expect zero differing pixels. If anything "
          "moves, a token name collided rather than being namespaced - stop and report.")
    return 0


if __name__ == "__main__":
    sys.exit(main(write="--write" in sys.argv))