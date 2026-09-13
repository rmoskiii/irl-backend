#!/usr/bin/env python3
"""Merge anchors.streets.additions.json into tools/visual/assets/anchors.json.

Assert-one-match discipline: every insert is checked before anything is written,
and the whole merge is refused if any check fails. A partial merge of a
coordinate contract is worse than no merge.

Usage:
    python3 merge_streets_anchors.py --dry-run          # report, write nothing
    python3 merge_streets_anchors.py                    # validate, then write

Both files are expected beside this script, or pass --anchors / --additions.

WHAT IT DOES
  scenes      + 10 new keys. Refuses if any already exists.
  characters  +  7 new keys. Refuses if any already exists.
  props       + 10 new keys, AND extends the defaultAnchor map of two props that
                already exist (prop.phone, prop.raised_glass). The additions file
                marks those with `_extend_defaultAnchor`; this script merges the
                key into the live map and never replaces it. Replacing it would
                strip The Secret's anchor and send the prop unplaceable in a
                district nobody is currently testing.

WHAT IT DOES NOT DO
  Nothing else in anchors.json is touched. No frames are added: Streets frames
  are declared at runtime from render blocks, not hand-authored in `frames`.
"""
import argparse, json, pathlib, sys, shutil, datetime

HERE = pathlib.Path(__file__).resolve().parent


def fail(msg):
    print(f"REFUSED: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anchors", default=str(HERE / "anchors.json"))
    ap.add_argument("--additions", default=str(HERE / "anchors.streets.additions.json"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    ap_path, add_path = pathlib.Path(a.anchors), pathlib.Path(a.additions)
    for p in (ap_path, add_path):
        if not p.exists():
            fail(f"{p} does not exist")

    anchors = json.loads(ap_path.read_text(encoding="utf-8"))
    add = json.loads(add_path.read_text(encoding="utf-8"))

    plan, errors = [], []

    # --- scenes and characters: strictly new keys ---------------------------
    for section in ("scenes", "characters"):
        for key in add.get(section, {}):
            if key in anchors.get(section, {}):
                errors.append(f"{section}.{key} already exists — refusing to overwrite")
            else:
                plan.append(("add", section, key))

    # --- props: new keys, plus two extensions -------------------------------
    for key, val in add.get("props", {}).items():
        if "_extend_defaultAnchor" in val:
            if key not in anchors["props"]:
                errors.append(f"props.{key} marked for extension but does not exist")
                continue
            live = anchors["props"][key].setdefault("defaultAnchor", {})
            for scene, anchor in val["_extend_defaultAnchor"].items():
                if scene in live and live[scene] != anchor:
                    errors.append(
                        f"props.{key}.defaultAnchor.{scene} already set to "
                        f"{live[scene]!r}, additions say {anchor!r}")
                else:
                    plan.append(("extend", "props", f"{key}.defaultAnchor.{scene}"))
        else:
            if key in anchors["props"]:
                errors.append(f"props.{key} already exists — refusing to overwrite")
            else:
                plan.append(("add", "props", key))

    # --- cross-checks against the contract ----------------------------------
    for sid, scene in add.get("scenes", {}).items():
        if "slots" not in scene or "centre" not in scene["slots"]:
            errors.append(f"scenes.{sid} declares no `centre` slot")
        occl = scene.get("occlusionLine", {})
        if occl.get("y") != 600:
            errors.append(f"scenes.{sid} occlusionLine is not 600")
        if not occl.get("exempt") and not occl.get("note"):
            errors.append(f"scenes.{sid} has no occluding-surface note")

    for fid, fig in add.get("characters", {}).items():
        for k in ("basePoint", "headSocket", "neckSpan"):
            if k not in fig:
                errors.append(f"characters.{fid} missing {k}")
        if fig.get("basePoint", {}).get("y") != 800:
            errors.append(f"characters.{fid} basePoint.y is not 800 — every figure shares it")

    # every prop anchor named must exist on the scene it names
    merged_scenes = {**anchors.get("scenes", {}), **add.get("scenes", {})}
    for key, val in add.get("props", {}).items():
        amap = val.get("defaultAnchor") or val.get("_extend_defaultAnchor") or {}
        for sid, name in amap.items():
            scene = merged_scenes.get(sid)
            if scene is None:
                errors.append(f"props.{key} anchors to unknown scene {sid}")
            elif name not in scene.get("propAnchors", {}):
                errors.append(f"props.{key} anchors to {sid}.{name}, which is not declared")

    print(f"planned operations: {len(plan)}")
    for kind, section, key in plan:
        print(f"  {kind:7} {section}.{key}")

    if errors:
        print(f"\n{len(errors)} problem(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        fail("nothing written")

    if a.dry_run:
        print("\n--dry-run: validated, nothing written")
        return

    # --- apply. Validated first, written second. ----------------------------
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = ap_path.with_suffix(f".json.bak-{stamp}")
    shutil.copy2(ap_path, backup)

    for section in ("scenes", "characters"):
        for key, val in add.get(section, {}).items():
            anchors.setdefault(section, {})[key] = val

    for key, val in add.get("props", {}).items():
        if "_extend_defaultAnchor" in val:
            live = anchors["props"][key].setdefault("defaultAnchor", {})
            live.update(val["_extend_defaultAnchor"])
            note = val.get("note")
            if note:
                anchors["props"][key]["streetsNote"] = note
        else:
            anchors["props"][key] = val

    ap_path.write_text(json.dumps(anchors, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
    print(f"\nwritten: {ap_path}")
    print(f"backup : {backup}")
    print(f"scenes {len(anchors['scenes'])} | props {len(anchors['props'])} | "
          f"characters {len(anchors['characters'])}")


if __name__ == "__main__":
    main()