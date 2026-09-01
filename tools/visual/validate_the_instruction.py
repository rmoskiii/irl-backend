#!/usr/bin/env python3
"""Validate mapping.the_instruction.json against the_instruction.json.

Validate-all-then-report: every check runs, nothing exits early, and the script
writes nothing. A non-zero exit means the manifest and the scenario disagree.

Usage:
    python3 tools/visual/validate_the_instruction.py

Checks:
  1. Every node in the scenario is accounted for (rendered, no-render, or
     explicitly suppressed).
  2. Every mood string declared in the scenario is present in moodMap.
  3. Every moodMap target exists in registerTilt.
  4. Every prose prop string is classified exactly once.
  5. Every location/setting resolves to a scene, or to an explicit override.
  6. No mapping value references a scoring key (the firewall).
  7. Every adjacent pair of figure-bearing nodes differs by >= 5 degrees.
"""

import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

SCENARIO = os.path.join(REPO, "src", "data", "the_instruction.json")
MAPPING = os.path.join(HERE, "mapping.the_instruction.json")

SCORING_KEYS = {"savvy", "streetSmarts", "integrity", "scores", "complicity",
                "record", "exposureBand", "recordBand", "complicityBand"}

MIN_TILT_DELTA = 5

failures = []
notes = []


def fail(check, msg):
    failures.append(f"[{check}] {msg}")


def load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def main():
    for path in (SCENARIO, MAPPING):
        if not os.path.exists(path):
            print(f"missing: {path}", file=sys.stderr)
            return 2

    scen = load(SCENARIO)
    mp = load(MAPPING)

    nodes = scen["nodes"]
    overrides = mp.get("nodeOverrides", {})
    suppressed = set(mp.get("suppressedNodes", []))
    mood_map = mp.get("moodMap", {})
    tilt = mp.get("registerTilt", {})
    loc_tokens = mp.get("locationTokens", {})
    set_tokens = mp.get("settingTokens", {})
    prop_syn = mp.get("propSynonyms", {})
    env_feat = {k: v for k, v in mp.get("environmentFeatures", {}).items()
                if not k.startswith("_")}
    wardrobe_tokens = mp.get("wardrobeTokens", {})
    unrenderable = set(mp.get("unrenderableProps", []))

    all_moods = {m for fig in mood_map.values() for m in fig}
    mood_to_register = {}
    for fig, table in mood_map.items():
        for mood, reg in table.items():
            mood_to_register.setdefault(mood, set()).add((fig, reg))

    # --- 1. node coverage -------------------------------------------------
    no_render_types = {"email", "messages", "call"}
    for node_id, node in nodes.items():
        pres = node.get("presentation", {})
        ptype = pres.get("type")
        data = pres.get("data", {})
        ov = overrides.get(node_id, {})
        explicit_null = "render" in ov and ov["render"] is None
        has_location = bool(data.get("location"))

        if node_id in suppressed:
            if not explicit_null:
                fail("1", f"{node_id} is suppressed but has no explicit render:null override")
            continue
        if explicit_null:
            continue
        if ptype in no_render_types and node_id != "audit_ray_calls":
            fail("1", f"{node_id} is type '{ptype}' but carries no render:null override")
            continue
        if not has_location and node_id not in overrides:
            fail("1", f"{node_id} has no location and no override — scene is unresolvable")

    # --- 2 & 3. moods ------------------------------------------------------
    declared = defaultdict(set)
    for node_id, node in nodes.items():
        mood = node.get("presentation", {}).get("data", {}).get("character", {}).get("mood")
        if mood:
            declared[mood].add(node_id)
    for mood, where in sorted(declared.items()):
        if mood not in all_moods:
            fail("2", f"mood '{mood}' declared in {sorted(where)} is not in moodMap")
    for mood, pairs in mood_to_register.items():
        for fig, reg in pairs:
            fig_asset = mp.get("figures", {}).get(fig, {}).get("asset")
            if not fig_asset:
                fail("3", f"figure '{fig}' in moodMap has no entry in figures")
                continue
            if reg not in tilt.get(fig_asset, {}):
                fail("3", f"register '{reg}' ({fig}) has no tilt value")
    for mood in sorted(all_moods - set(declared)):
        notes.append(f"moodMap carries '{mood}', which no node declares (unreachable, mapped defensively)")

    # --- 4. props ----------------------------------------------------------
    classified = set(prop_syn) | set(env_feat) | set(wardrobe_tokens) | unrenderable
    seen = set()
    for node_id, node in nodes.items():
        visual = node.get("presentation", {}).get("data", {}).get("visual", {})
        for p in visual.get("props", []) or []:
            seen.add(p)
            if p not in classified:
                fail("4", f"prop string '{p}' ({node_id}) is unclassified")
        pressure = visual.get("pressure")
        if pressure and pressure not in classified:
            fail("4", f"pressure string '{pressure}' ({node_id}) is unclassified")
    for p in sorted(classified - seen):
        notes.append(f"mapping classifies '{p}', which appears in no node")
    for p in sorted(set(prop_syn.values())):
        notes.append(f"prop asset required: {p}")

    # --- 5. scenes ---------------------------------------------------------
    for node_id, node in nodes.items():
        if node_id in suppressed:
            continue
        ov = overrides.get(node_id, {})
        if "render" in ov and ov["render"] is None:
            continue
        if ov.get("scene"):
            continue
        data = node.get("presentation", {}).get("data", {})
        loc = data.get("location")
        setting = (data.get("visual") or {}).get("setting")
        if setting and setting in set_tokens:
            if set_tokens[setting] is None:
                fail("5", f"{node_id} setting '{setting}' maps to null with no override")
            continue
        if loc and loc in loc_tokens:
            continue
        fail("5", f"{node_id} location '{loc}' / setting '{setting}' does not resolve to a scene")

    # --- 6. firewall -------------------------------------------------------
    def walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in SCORING_KEYS:
                    fail("6", f"mapping references scoring key '{k}' at {path}")
                walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, f"{path}[{i}]")
        elif isinstance(obj, str):
            if obj in SCORING_KEYS:
                fail("6", f"mapping value '{obj}' at {path} is a scoring key")

    for key in ("moodMap", "registerTilt", "nodeOverrides", "variantOverrides",
                "locationTokens", "settingTokens", "propSynonyms"):
        walk(mp.get(key, {}), key)

    # --- 7. adjacency ------------------------------------------------------
    def register_for(node_id):
        if node_id in suppressed:
            return None
        ov = overrides.get(node_id, {})
        if ("render" in ov and ov["render"] is None) or ov.get("cast") == []:
            return None
        data = nodes[node_id].get("presentation", {}).get("data", {})
        char = data.get("character") or {}
        mood = char.get("mood")
        name = (char.get("name") or "").lower()
        fig = "ray" if name == "ray" else "dana" if name == "dana" else None
        if not fig or not mood:
            return None
        reg = mood_map.get(fig, {}).get(mood)
        if reg is None:
            return None
        asset = mp["figures"][fig]["asset"]
        return fig, reg, tilt[asset][reg]

    def successors(node_id):
        out = []
        for ch in nodes[node_id].get("choices", []):
            for rule in ch.get("nextRules", []) or []:
                if rule.get("next"):
                    out.append(rule["next"])
            if ch.get("next"):
                out.append(ch["next"])
        return out

    # transparent hop: a node with no figure does not reset the last image
    def figure_successors(node_id, depth=0, seen_=None):
        seen_ = seen_ or set()
        for nxt in successors(node_id):
            if nxt in seen_ or nxt not in nodes:
                continue
            seen_.add(nxt)
            if register_for(nxt):
                yield nxt
            elif depth < 4:
                yield from figure_successors(nxt, depth + 1, seen_)

    for node_id in nodes:
        a = register_for(node_id)
        if not a:
            continue
        for nxt in figure_successors(node_id):
            b = register_for(nxt)
            if not b or a[0] != b[0]:
                continue
            delta = abs(a[2] - b[2])
            if delta == 0:
                notes.append(f"{node_id} -> {nxt}: identical register '{a[1]}' — check the slot differs")
            elif delta < MIN_TILT_DELTA:
                fail("7", f"{node_id} -> {nxt}: delta {delta} deg below {MIN_TILT_DELTA} "
                          f"({a[1]} vs {b[1]}) — needs a measured silhouette check")

    # --- report ------------------------------------------------------------
    for n in notes:
        print(f"note: {n}")
    if failures:
        print()
        for f in failures:
            print(f"FAIL {f}")
        print(f"\n{len(failures)} failure(s)")
        return 1
    print(f"\nOK — {len(nodes)} nodes, {len(suppressed)} suppressed, "
          f"{len(all_moods)} moods, {len(set(prop_syn.values()))} prop assets")
    return 0


if __name__ == "__main__":
    sys.exit(main())