"""
IRX Visual Render Layer — reference resolver.
Spec v1.0 §7 / §8.

Compiles a node into a flat `render` block. This is the reference for what the
Node/Express engine must do server-side. The client receives only the output and
never sees state, mood, or the mapping table.

READ-ONLY on the scenario. Never mutates the loaded scenario dict.

2B.7A: three changes for the Career district, all inert for the_secret.
  1. mode "none" short-circuits alongside "messages" — an authored deliberate
     blank, distinct from a node that simply has no artwork by presentation type.
  2. the wardrobe floor is read per character from registries rather than
     hard-coded to "home_casual", which no Career character has.
  3. mapping.textLayer == "native" suppresses bubbles and narration in the
     render block, because the client carries the prose itself.

The Streets: three changes, all inert for the_secret and the_instruction, and
none of them alters the render-block SHAPE. Every field a block carries today it
carried before; only the way three values are arrived at has changed.

  D1. `nodeOverrides.<id>.time` selects the scene's time per node, falling back
      to `default_time`. Spec v1.0 §6.2 always said time was "a lighting variant,
      not a separate asset"; the resolver never implemented it, and the cost was
      paid in duplicate assets — scene.desk_evening and scene.desk_day are one
      room drawn twice. The Streets is where that stops scaling: five of its ten
      rooms recur at two hours across a seven-day week.
  D9. `nodeOverrides.<id>.scene` names the scene token directly, resolved BEFORE
      the location-token prefix match. The Streets authors "The kitchen" as the
      location of three nodes in two different flats. Prefix matching cannot
      separate byte-identical strings, and the authored scenario is frozen, so
      the disambiguation has to live in the mapping.
  D10. `mapping.nodeProps` attaches props by node id. resolve_props reads
      `presentation.data.visual.props`, and none of The Streets' 51 nodes carries
      a visual block — so without this, ten authored props are unreachable and
      `render["props"]` is unconditionally empty. Keyed by node id, exactly as
      montagePanels and exitBeats already are.

REACHABILITY IS A VALIDATION OBLIGATION, NOT AN ASSET-COUNT VARIABLE. If a
frozen asset is unreachable after these changes, the implementation is defective
unless the frozen set itself is reopened through sign-off. That is why unknown
scene tokens, unknown times and unknown prop ids all raise here rather than
resolving to a silent default.
"""

import json
import re
import copy


class ResolveError(Exception):
    pass


def load(scenario_path, registries_path, mapping_path):
    with open(scenario_path, encoding="utf-8") as f:
        scenario = json.load(f)
    with open(registries_path, encoding="utf-8") as f:
        registries = json.load(f)
    with open(mapping_path, encoding="utf-8") as f:
        mapping = json.load(f)
    return scenario, registries, mapping


# ---------------------------------------------------------------- reachability

def reachable_nodes(scenario):
    """Walk next / nextRules / choice targets from rootNode."""
    nodes = scenario["nodes"]
    seen = set()
    stack = [scenario["rootNode"]]
    while stack:
        nid = stack.pop()
        if nid in seen or nid not in nodes:
            continue
        seen.add(nid)
        for ch in nodes[nid].get("choices", []):
            for rule in ch.get("nextRules", []) or []:
                if rule.get("next"):
                    stack.append(rule["next"])
            if ch.get("next"):
                stack.append(ch["next"])
    return seen


# ------------------------------------------------------------------ mode / cast

def character_id(node, mapping):
    name = (
        node.get("presentation", {})
        .get("data", {})
        .get("character", {})
        .get("name")
    )
    return mapping["characterIds"].get(name)


def node_mood(node):
    return (
        node.get("presentation", {})
        .get("data", {})
        .get("character", {})
        .get("mood")
    )


def classify_mode(node_id, node, mapping):
    """Spec §3. Explicit override > presentation.type > moodMap."""
    if node_id in mapping.get("modeOverrides", {}):
        return mapping["modeOverrides"][node_id]

    ptype = node.get("presentation", {}).get("type")
    if ptype == "messages":
        return "messages"

    authored = node.get("presentation", {}).get("data", {}).get("visual", {})
    if authored.get("mode"):
        return authored["mode"]

    cid = character_id(node, mapping)
    mood = node_mood(node)
    entry = mapping["moodMap"].get(cid, {}).get(mood, {})
    if "mode" in entry:
        return entry["mode"]

    return "scene"


def resolve_scene_token(node, mapping, overrides=None):
    """Explicit override > authored setting > location prefix match.

    D9: the override comes FIRST and short-circuits everything, including the
    location lookup that would otherwise raise. A node whose location string is
    ambiguous, or shared with a different room, is named outright."""
    explicit = (overrides or {}).get("scene")
    if explicit:
        return explicit
    data = node.get("presentation", {}).get("data", {})
    authored = data.get("visual", {})
    setting = authored.get("setting")
    if setting:
        tok = mapping["settingTokens"].get(setting)
        if tok:
            return tok
    loc = data.get("location", "") or ""
    for prefix, tok in mapping["locationTokens"]:
        if loc.startswith(prefix):
            return tok
    raise ResolveError(f"cannot resolve scene from location {loc!r}")


def resolve_scene_time(node_id, scene_tok, scene_def, overrides):
    """D1: per-node time, falling back to the scene's default_time.

    Validated against the scene's declared `times`. A time branch that is not
    declared is the worst failure mode available here: the composer would filter
    on a value no element carries, silently dropping every time-varying element
    and producing a frame that looks merely underdressed rather than broken."""
    declared = scene_def.get("times") or [scene_def["default_time"]]
    time = overrides.get("time", scene_def["default_time"])
    if time not in declared:
        raise ResolveError(
            f"{node_id}: time {time!r} is not declared by {scene_tok} "
            f"(declared: {declared}). Add it to registries.scenes or fix the "
            f"nodeOverrides entry — do not let it resolve to the default.")
    return time


def resolve_props(node_id, node, registries, mapping):
    """Authored props (scenario visual block) plus mapping-level nodeProps.

    D10: `mapping.nodeProps[node_id]` is a list of prop TOKENS, already resolved
    — it is the mapping's own statement about the node, not prose to be matched
    through propSynonyms. Appended after the authored ones and de-duplicated, so
    a scenario that carries visual blocks is unaffected.

    Unknown tokens raise. A typo here would make a frozen prop unreachable while
    every test stayed green, which is precisely the class of defect the frozen
    set exists to catch."""
    authored = node.get("presentation", {}).get("data", {}).get("visual", {})
    out, unknown = [], []
    for p in authored.get("props", []) or []:
        tok = mapping["propSynonyms"].get(p)
        if tok:
            if tok not in out:
                out.append(tok)
        elif p not in mapping["unrenderableProps"]:
            unknown.append(p)

    for tok in mapping.get("nodeProps", {}).get(node_id, []) or []:
        if tok not in registries.get("props", {}):
            raise ResolveError(
                f"{node_id}: nodeProps names {tok!r}, which is not in "
                f"registries.props. A prop the mapping cannot resolve is an "
                f"unreachable asset, not an omission.")
        if tok not in out:
            out.append(tok)

    return out, unknown


# ------------------------------------------------------------------- dialogue

QUOTE_RE = re.compile(r'"([^"]+)"')


def extract_bubbles(text, speaker):
    """Phase 1 extraction: quoted spans become candidate bubbles.
    Phase 3 (compression pass) replaces this with authored bubbles.

    NOTE: these are CANDIDATES. Which candidates become drawn balloons is a
    downstream allowlist decision (bubble_nodes.json), deliberately not enforced
    here — see the open item in the Phase 1 notes."""
    return [{"speaker": speaker, "text": m.group(1).strip()}
            for m in QUOTE_RE.finditer(text or "")]


def strip_dialogue(text):
    return QUOTE_RE.sub("", text or "").strip()


def node_message(node, variant_index=None):
    if variant_index is not None:
        return node["messageVariants"][variant_index]["message"]
    return node.get("message", "")


# --------------------------------------------------------------------- resolve

def resolve(node_id, node, registries, mapping, variant_index=None):
    """Compile one node (optionally one messageVariant) into a render block."""
    mode = classify_mode(node_id, node, mapping)

    # "messages" = the existing phone UI (§3.5).
    # "none"     = an authored deliberate blank, set only through an explicit
    #              modeOverrides entry. Never inferred from a missing visual
    #              block, which already means "infer the scene from location".
    if mode in ("messages", "none"):
        return None

    # The client carries dialogue and narration itself when the district uses a
    # native text layer, so the block asserts artwork only.
    native = mapping.get("textLayer") == "native"

    render = {"mode": mode}

    if mode == "montage":
        panels = mapping["montagePanels"].get(node_id)
        if not panels:
            raise ResolveError(f"{node_id}: montage mode but no panels authored")
        render["panels"] = copy.deepcopy(panels)
        return render

    # read before the scene is resolved: the overrides block now carries the
    # scene token and the time as well as framing, slot and cast.
    overrides = mapping.get("nodeOverrides", {}).get(node_id, {})

    scene_tok = resolve_scene_token(node, mapping, overrides)
    scene_def = registries["scenes"].get(scene_tok)
    if scene_def is None:
        raise ResolveError(f"{node_id}: unknown scene token {scene_tok}")
    render["scene"] = {
        "id": scene_tok,
        "time": resolve_scene_time(node_id, scene_tok, scene_def, overrides),
    }

    props, unknown = resolve_props(node_id, node, registries, mapping)
    render["props"] = props
    if unknown:
        render["_unknownProps"] = unknown

    cid = character_id(node, mapping)
    message = node_message(node, variant_index)

    if mode == "absent":
        render["framing"] = "empty"
        eb = mapping.get("exitBeats", {}).get(node_id)
        render["exitBeat"] = copy.deepcopy(eb) if eb else None
        render["cast"] = []
        render["narration"] = None if native else strip_dialogue(message)
        return render

    if mode == "remote":
        render["framing"] = "empty"
        render["cast"] = []
        render["bubbles"] = [] if native else extract_bubbles(message, cid)
        render["remoteSpeaker"] = cid
        render["narration"] = None if native else strip_dialogue(message)
        return render

    # --- scene ---
    chars = registries["characters"]
    if cid not in chars:
        raise ResolveError(f"{node_id}: unknown character {cid!r}")

    mood = node_mood(node)
    entry = mapping["moodMap"].get(cid, {}).get(mood)
    if entry is None or "register" not in entry:
        raise ResolveError(f"{node_id}: no register mapping for {cid} mood {mood!r}")
    register = entry["register"]
    wardrobe = chars[cid].get("defaultWardrobe", "home_casual")

    cast_over = overrides.get("cast", {}).get(cid, {})
    register = cast_over.get("register", register)
    wardrobe = cast_over.get("wardrobe", wardrobe)

    if variant_index is not None:
        for vo in mapping.get("variantOverrides", {}).get(node_id, []):
            if vo["variantIndex"] == variant_index:
                vc = vo.get("cast", {}).get(cid, {})
                register = vc.get("register", register)
                wardrobe = vc.get("wardrobe", wardrobe)

    render["framing"] = overrides.get("framing", "direct")
    render["cast"] = [{
        "id": cid,
        "slot": overrides.get("slot", "centre"),
        "presence": "present",
        "register": register,
        "wardrobe": wardrobe,
        "speaking": True,
    }]
    render["bubbles"] = [] if native else extract_bubbles(message, cid)
    render["narration"] = None if native else (strip_dialogue(message) or None)
    return render