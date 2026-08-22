#!/usr/bin/env python3
"""Dump every resolved render block. Phase 1 output artifact."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resolve as R

scn, reg, mp = sys.argv[1:4]
scenario, registries, mapping = R.load(scn, reg, mp)
out = {}
for nid in sorted(R.reachable_nodes(scenario)):
    node = scenario["nodes"][nid]
    entry = {"default": R.resolve(nid, node, registries, mapping)}
    for i, _ in enumerate(node.get("messageVariants", []) or []):
        entry[f"variant[{i}]"] = R.resolve(nid, node, registries, mapping, variant_index=i)
    out[nid] = entry
dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "render_blocks.json")
json.dump(out, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"wrote {dest} — {len(out)} nodes")

used = set()
for e in out.values():
    for b in e.values():
        if b: used |= set(b.get("props", []))
print("props used:", len(used), "of", len(registries["props"]))
print("unused    :", sorted(set(registries["props"]) - used) or "none")