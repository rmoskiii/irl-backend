#!/usr/bin/env python3
"""Dump every resolved render block. Phase 1 output artifact."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resolve as R

scn, reg, mp = sys.argv[1:4]
dest_arg = sys.argv[4] if len(sys.argv) > 4 else "render_blocks.json"
scenario, registries, mapping = R.load(scn, reg, mp)
blocks = {}
for nid in sorted(R.reachable_nodes(scenario)):
    node = scenario["nodes"][nid]
    entry = {"default": R.resolve(nid, node, registries, mapping)}
    for i, _ in enumerate(node.get("messageVariants", []) or []):
        entry[f"variant[{i}]"] = R.resolve(nid, node, registries, mapping, variant_index=i)
    blocks[nid] = entry
dest = dest_arg if os.path.isabs(dest_arg) else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), dest_arg)
with open(dest, "w", encoding="utf-8") as fh:
    json.dump(blocks, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
print(f"wrote {dest} — {len(blocks)} nodes")

used = set()
for e in blocks.values():
    for b in e.values():
        if b: used |= set(b.get("props", []))
print("props used:", len(used), "of", len(registries["props"]))
print("unused    :", sorted(set(registries["props"]) - used) or "none")