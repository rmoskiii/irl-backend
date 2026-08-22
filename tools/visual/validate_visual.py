#!/usr/bin/env python3
"""
IRX Visual Render Layer — validator.
Spec v1.0 §12 (rules 1-8) and §13.1 (Phase 1 exit criteria).

Usage:
  python3 validate_visual.py <scenario.json> <registries.json> <mapping.json>

Read-only on all inputs. Exits non-zero on any hard failure.
"""

import sys
import os
import json
import hashlib
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resolve as R  # noqa: E402

EXPECTED_MODES = {"scene": 19, "absent": 3, "montage": 2, "remote": 1, "messages": 5}
BUBBLE_CAP = 120
BUBBLES_PER_NODE = 3
CAPTION_CAP = 40
NARRATION_ABSENT_CAP = 140

fails, warns, reports = [], [], []


def fail(rule, msg):
    fails.append(f"[RULE {rule}] {msg}")


def warn(rule, msg):
    warns.append(f"[RULE {rule}] {msg}")


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main(scn_path, reg_path, map_path):
    before = sha(scn_path)
    scenario, registries, mapping = R.load(scn_path, reg_path, map_path)
    nodes = scenario["nodes"]

    reach = R.reachable_nodes(scenario)
    unreachable = sorted(set(nodes) - reach)

    # ---------------------------------------------------- classify + resolve
    modes, blocks, variant_blocks = {}, {}, {}
    for nid in sorted(reach):
        node = nodes[nid]
        try:
            modes[nid] = R.classify_mode(nid, node, mapping)
        except Exception as e:
            fail(1, f"{nid}: mode classification failed — {e}")
            continue
        try:
            blocks[nid] = R.resolve(nid, node, registries, mapping)
        except Exception as e:
            fail(1, f"{nid}: resolve failed — {e}")
            continue
        for i, _ in enumerate(node.get("messageVariants", []) or []):
            try:
                variant_blocks[(nid, i)] = R.resolve(
                    nid, node, registries, mapping, variant_index=i)
            except Exception as e:
                fail(1, f"{nid}[variant {i}]: resolve failed — {e}")

    # ------------------------------------------------------- RULE 2: tokens
    for nid, b in blocks.items():
        if b is None:
            continue
        if "scene" in b and b["scene"]["id"] not in registries["scenes"]:
            fail(2, f"{nid}: unknown scene {b['scene']['id']}")
        for p in b.get("props", []):
            if p not in registries["props"]:
                fail(2, f"{nid}: unknown prop {p}")
        for panel in b.get("panels", []):
            if panel["vignette"] not in registries["vignettes"]:
                fail(2, f"{nid}: unknown vignette {panel['vignette']}")
        for c in b.get("cast", []):
            if c["id"] not in registries["characters"]:
                fail(2, f"{nid}: unknown character {c['id']}")
            if c["wardrobe"] not in registries["characters"][c["id"]]["wardrobe"]:
                fail(2, f"{nid}: {c['id']} wardrobe {c['wardrobe']} not in registry")
        if b.get("_unknownProps"):
            warn(2, f"{nid}: props not in synonym or unrenderable list: {b['_unknownProps']}")

    # --------------------------------------------- RULE 3: register in set
    for key, b in list(blocks.items()) + list(variant_blocks.items()):
        if b is None:
            continue
        nid = key if isinstance(key, str) else f"{key[0]}[v{key[1]}]"
        for c in b.get("cast", []):
            allowed = registries["characters"][c["id"]]["registers"]
            if c["register"] not in allowed:
                fail(3, f"{nid}: {c['id']} register {c['register']!r} not in {allowed}")

    # ----------------------------------------------------- RULE 4: slots
    for nid, b in blocks.items():
        if b is None:
            continue
        for c in b.get("cast", []):
            if c["slot"] not in registries["slots"]:
                fail(4, f"{nid}: slot {c['slot']!r} not in global vocabulary")
    for nid, ov in mapping.get("nodeOverrides", {}).items():
        if "slot" in ov and ov["slot"] not in registries["slots"]:
            fail(4, f"{nid}: override slot {ov['slot']!r} not in global vocabulary")

    # -------------------------------- RULE 5: text budget (REPORT pre-Phase 3)
    over = []
    for nid, b in blocks.items():
        if b is None:
            continue
        m = b["mode"]
        bubbles = b.get("bubbles", [])
        long_b = [x for x in bubbles if len(x["text"]) > BUBBLE_CAP]
        issues = []
        if long_b:
            issues.append(f"{len(long_b)} bubble(s) >{BUBBLE_CAP}c (max {max(len(x['text']) for x in long_b)})")
        if len(bubbles) > BUBBLES_PER_NODE:
            issues.append(f"{len(bubbles)} bubbles >{BUBBLES_PER_NODE}")
        nar = b.get("narration") or ""
        if m == "scene" and nar:
            issues.append(f"narration {len(nar)}c (cap 0)")
        if m == "absent" and len(nar) > NARRATION_ABSENT_CAP:
            issues.append(f"narration {len(nar)}c (cap {NARRATION_ABSENT_CAP})")
        for p in b.get("panels", []):
            if p.get("caption") and len(p["caption"]) > CAPTION_CAP:
                issues.append(f"caption {len(p['caption'])}c (cap {CAPTION_CAP})")
        if b.get("exitBeat") and len(b["exitBeat"]["text"]) > BUBBLE_CAP:
            issues.append("exitBeat over cap")
        if issues:
            over.append((nid, m, issues))
    reports.append(("RULE 5 — Phase 3 compression worklist", over))

    # ------------------------------------------- RULE 6: montage pass-through
    for nid, m in modes.items():
        if m != "montage":
            continue
        chs = nodes[nid].get("choices", [])
        if len(chs) != 1:
            fail(6, f"{nid}: montage has {len(chs)} choices, must be 1")
        for ch in chs:
            if any(v != 0 for v in (ch.get("scores") or {}).values()):
                fail(6, f"{nid}: montage choice carries non-zero scores")
            if ch.get("setState"):
                fail(6, f"{nid}: montage choice carries setState")

    # ------------------------------------------------- RULE 7: THE FIREWALL
    forbidden = set(registries["scoring_keys_forbidden"])

    def scan(obj, path):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in forbidden:
                    fail(7, f"FIREWALL BREACH at {path}: references scoring key {k!r}")
                scan(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                scan(v, f"{path}[{i}]")
        elif isinstance(obj, str) and obj in forbidden:
            fail(7, f"FIREWALL BREACH at {path}: value is scoring key {obj!r}")

    for nid, node in nodes.items():
        v = node.get("presentation", {}).get("data", {}).get("visual")
        if v:
            scan(v, f"nodes.{nid}.visual")
    for section in ("nodeOverrides", "variantOverrides", "modeOverrides",
                    "montagePanels", "exitBeats", "moodMap"):
        scan(mapping.get(section), f"mapping.{section}")

    # ------------------------------------------------- RULE 8: orphan assets
    used_scenes = {b["scene"]["id"] for b in blocks.values() if b and "scene" in b}
    used_vigs = {p["vignette"] for b in blocks.values() if b for p in b.get("panels", [])}
    used_props = {p for b in blocks.values() if b for p in b.get("props", [])}
    used_chars = {c["id"] for b in blocks.values() if b for c in b.get("cast", [])}
    used_chars |= {b["remoteSpeaker"] for b in blocks.values()
                   if b and b.get("remoteSpeaker")}
    used_chars |= {e["speaker"] for e in mapping["exitBeats"].values() if e}

    for label, used, declared in (
            ("scene", used_scenes, set(registries["scenes"])),
            ("vignette", used_vigs, set(registries["vignettes"])),
            ("prop", used_props, set(registries["props"])),
            ("character", used_chars, set(registries["characters"])),
    ):
        for orphan in sorted(declared - used):
            warn(8, f"orphan {label}: {orphan} declared but never referenced")

    # ------------------------------------------------------- EXIT CRITERIA
    counts = Counter(modes.values())
    crit = []
    crit.append(("1  harness ran against unmodified scenario", True, f"sha256 {before[:16]}…"))
    ok2 = dict(counts) == EXPECTED_MODES
    crit.append(("2  mode classification matches spec §3", ok2,
                 f"got {dict(sorted(counts.items()))}, expected {EXPECTED_MODES}"))
    scene_ids = [n for n, m in modes.items() if m == "scene"]
    resolved = [n for n in scene_ids if blocks.get(n) and blocks[n].get("cast")]
    hand_cast = [n for n, nd in nodes.items()
                 if (nd.get("presentation", {}).get("data", {})
                     .get("visual", {}).get("cast"))]
    ok3 = len(resolved) == len(scene_ids) and not hand_cast
    crit.append(("3  all scene nodes resolve by inference alone", ok3,
                 f"{len(resolved)}/{len(scene_ids)} resolved, {len(hand_cast)} hand-authored cast blocks"))
    absent_ids = [n for n, m in modes.items() if m == "absent"]
    eb = {n: bool(blocks[n].get("exitBeat")) for n in absent_ids}
    ok4 = eb == {"jessica_leaves_halfsecret": True,
                 "jessica_reacts_neutral": True,
                 "jessica_walks_out": False}
    crit.append(("4  absent nodes emit correct exitBeat presence", ok4, str(eb)))
    d = blocks.get("jessica_reacts_hold")
    v = variant_blocks.get(("jessica_reacts_hold", 0))
    dr = d["cast"][0]["register"] if d and d.get("cast") else None
    vr = v["cast"][0]["register"] if v and v.get("cast") else None
    ok5 = dr is not None and vr is not None and dr != vr
    crit.append(("5  variant exception (§2.1) demonstrated", ok5,
                 f"default={dr!r} judgedFirst={vr!r}"))
    ok6 = not fails
    crit.append(("6  validator rules 1-8 pass", ok6, f"{len(fails)} hard failures"))
    crit.append(("7  rule 7 negative test", None, "run separately: negative_test.py"))
    after = sha(scn_path)
    ok8 = before == after
    crit.append(("8  scenario file unmodified by the harness", ok8,
                 "checksum identical" if ok8 else "CHECKSUM CHANGED"))

    # ------------------------------------------------------------- OUTPUT
    print("=" * 74)
    print("IRX VISUAL RENDER LAYER — PHASE 1 VALIDATION")
    print("=" * 74)
    print(f"\nnodes: {len(nodes)}   reachable: {len(reach)}   unreachable: {unreachable or 'none'}")
    print(f"mode distribution: {dict(sorted(counts.items()))}\n")

    print("-" * 74)
    print("MODE CLASSIFICATION")
    print("-" * 74)
    for m in ("scene", "absent", "remote", "montage", "messages"):
        ids = sorted(n for n, mm in modes.items() if mm == m)
        print(f"  {m:9s} ({len(ids):2d})  {', '.join(ids)}")

    if fails:
        print("\n" + "-" * 74)
        print(f"HARD FAILURES ({len(fails)})")
        print("-" * 74)
        for f in fails:
            print("  " + f)
    if warns:
        print("\n" + "-" * 74)
        print(f"WARNINGS ({len(warns)})")
        print("-" * 74)
        for w in warns:
            print("  " + w)

    for title, rows in reports:
        print("\n" + "-" * 74)
        print(f"{title} — {len(rows)} node(s)")
        print("-" * 74)
        for nid, m, issues in rows:
            print(f"  {nid} ({m}): {'; '.join(issues)}")

    print("\n" + "=" * 74)
    print("PHASE 1 EXIT CRITERIA (spec §13.1)")
    print("=" * 74)
    for name, ok, detail in crit:
        mark = "PASS" if ok else ("----" if ok is None else "FAIL")
        print(f"  [{mark}] {name}")
        print(f"         {detail}")

    hard = [c for c in crit if c[1] is False]
    print("\n" + "=" * 74)
    print(f"RESULT: {len(crit) - len(hard) - 1}/{len(crit) - 1} automated criteria pass"
          f"   |   {len(fails)} hard failures, {len(warns)} warnings")
    print("=" * 74)
    return 1 if (fails or hard) else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))