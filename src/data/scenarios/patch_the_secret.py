#!/usr/bin/env python3
"""
Final refinement pass for the_secret.json.

Adds:
  - jessicaLoyalty / alexLoyalty meters, wired across every meaningful choice
  - endingReached, set on every terminal choice
  - derivedState: loyaltyBand (differential), jessicaStanding, alexStanding
  - outcomeRules: coupleOutcome (married / proposed_later / postponed / split / unknown)
  - Hoisted jessicaAftermath / alexAftermath / finalMessage prose arrays

Removes:
  - jessicaTrust (superseded by jessicaLoyalty; its delta sites are remapped)

Usage:  python3 patch_the_secret.py path/to/the_secret.json
Writes in place. Asserts loudly rather than silently skipping.
"""

import json
import sys
from collections import OrderedDict

# ---------------------------------------------------------------------------
# Loyalty deltas, keyed "node_id:choice_id" -> (jessicaLoyalty, alexLoyalty)
#
# The model, per the design:
#   protect Jessica / help conceal   -> +2 J, -2 A
#   encourage Jessica to tell Alex   -> +1 J, +1 A   (the honest-broker route)
#   tell Alex yourself               -> -2 J, +2 A
#   refuse to support Jessica        -> -1 J
#   lie to Alex                      -> additional -1 A
#
# Note the asymmetry the design calls for: doing something Jessica hates does
# NOT automatically make Alex love you. Telling Alex badly (deflecting the
# timeline, telling him at the party in front of everyone) costs Jessica
# without fully crediting Alex.
# ---------------------------------------------------------------------------
LOYALTY = {
    # Act 1 -- showing up for her, or not
    "start:open":                          (1, 0),
    "start:guarded":                       (-1, 0),
    "confession:hold":                     (1, 1),
    "confession:judge":                    (-1, 0),
    "confession:neutral":                  (0, 0),
    "confession_guarded:recover":          (1, 0),
    "confession_guarded:let_drop":         (-1, 0),
    "jessica_reacts_judge:repair":         (1, 0),
    "jessica_reacts_judge:double_down":    (-1, 0),

    # Act 2 -- the first real fork: perform for Alex, or don't
    "act2_alex_reveal:match_energy":       (2, -2),
    "act2_alex_reveal:gentle_probe":       (0, 1),
    "act2_alex_reveal:honest_pause":       (0, 1),
    "act2_alex_reveal:break_now":          (-2, 2),

    "act2_alex_checks_in:im_fine":         (1, -2),
    "act2_alex_checks_in:long_week":       (1, -1),

    "act2_probe_response:back_off":        (2, -2),
    "act2_probe_response:hold_line":       (0, 1),
    "act2_probe_response:crack":           (-2, 2),

    "act2_pause_response:recover":         (1, -1),
    "act2_pause_response:stay_honest":     (0, 1),

    "act2_pause_pressed:direct_lie":       (2, -2),
    "act2_pause_pressed:deflect_honestly": (1, 0),
    "act2_pause_pressed:crack_late":       (-2, 2),

    # Act 3 -- pushing her toward doing it herself scores on BOTH meters
    "act3_jessica_returns:direct":         (1, 1),
    "act3_jessica_returns:hand_back":      (0, 0),
    "act3_jessica_returns:name_limit":     (1, 1),
    "act3_direct_response:yes":            (1, 0),
    "act3_direct_response:unsure":         (1, 0),
    "act3_hand_back_response:tell_tonight": (1, 1),
    "act3_hand_back_response:dont_know":   (1, -1),
    "act3_limit_response:not_angry":       (1, 1),
    "act3_limit_response:maybe_i_am":      (0, 0),

    # Act 3b -- HOW you tell him matters to him
    "act3b_alex_told:honest_timeline":     (0, 1),
    "act3b_alex_told:deflect_timeline":    (0, -1),
    "act3b_alex_told:take_responsibility": (0, 2),
    "act3b_jessica_calls:own_it":          (0, 1),
    "act3b_jessica_calls:name_burden":     (1, 0),
    "act3b_jessica_calls:just_sorry":      (0, 0),

    # Act 4 -- the party
    "act4_engagement_party:love_you_too":   (2, -2),
    "act4_engagement_party:yeah_of_course": (1, -1),
    "act4_engagement_party:late_disclosure": (-2, 2),
    "act4_late_disclosure:outside":         (0, 1),
    "act4_late_disclosure:here":            (0, 0),
    "act4_late_disclosure:backtrack":       (1, -2),
    "act4_party_night:of_course":           (2, -2),
    "act4_party_night:are_you_okay_c":      (1, 0),
    "act4_party_night:unanswered":          (0, 0),

    # Act 4 -- avoidant tail
    "act4_avoidant_outside:should_have":    (0, 1),
    "act4_avoidant_outside:nothing_to_say":  (0, 0),
    "act4_alex_ripple:nothing":             (1, -2),
    "act4_alex_ripple:coffee":              (-1, 2),
    "act4_alex_ripple:no_reply_d":          (0, -2),

    # Endings -- the last text still says something
    "act4_ending_a:glad":                   (1, 0),
    "act4_ending_a:are_you_okay":           (1, 0),
    "act4_ending_a:sorry":                  (0, 0),
    "act4_ending_a:no_reply":               (-1, 0),
    "act4_ending_b:courage":                (1, 0),
    "act4_ending_b:how_did_he_take_it":     (0, 0),
    "act4_ending_b:no_reply_b":             (-1, 0),
    "act4_ending_e:open_and_reply":         (1, 0),
    "act4_ending_e:miss_you":               (1, 0),
    "act4_ending_e:wish_different":         (1, 0),
    "act4_ending_e:dont_open":              (0, 0),
}

# Distinct endingReached per terminal choice where the couple's fate differs.
# C2 splits three ways because "told him outside", "told him in front of
# eighty people" and "lost your nerve" are three different outcomes for them.
ENDING_REACHED = {
    "act4_ending_a":        "A",
    "act4_ending_b":        "B",
    "act4_party_night":     "C",
    "act4_avoidant_outside": "D",
    "act4_alex_ripple":     "D2",
    "act4_ending_e":        "E",
}
ENDING_REACHED_BY_CHOICE = {
    "act4_late_disclosure:outside":   "C2_outside",
    "act4_late_disclosure:here":      "C2_here",
    "act4_late_disclosure:backtrack": "C2_backtrack",
}

NEW_STATE = OrderedDict([
    ("jessicaLoyalty", {
        "type": "int", "initial": 0, "range": [-12, 12],
        "note": "Whose side Jessica believes you were on. Distinct from whether she likes you."
    }),
    ("alexLoyalty", {
        "type": "int", "initial": 0, "range": [-12, 12],
        "note": "Whose side Alex believes you were on. Doing something Jessica hates does not automatically raise this."
    }),
    ("endingReached", {
        "type": "enum",
        "values": ["none", "A", "B", "C", "C2_outside", "C2_here",
                   "C2_backtrack", "D", "D2", "E"],
        "initial": "none",
        "note": "Set on every terminal choice. Drives outcomeRules."
    }),
])

DERIVED_STATE = OrderedDict([
    ("loyaltyBand", {
        "from": "jessicaLoyalty",
        "minus": "alexLoyalty",
        "bands": [
            {"min": 3,    "value": "jessica"},
            {"min": -2,   "value": "balanced"},
            {"min": -999, "value": "alex"}
        ],
        "note": "The differential, not the magnitude. 'balanced' is earned by pushing for honest disclosure, not by pleasing everyone -- concealment swings this hard."
    }),
    ("jessicaStanding", {
        "from": "jessicaLoyalty",
        "bands": [
            {"min": 4,    "value": "warm"},
            {"min": -1,   "value": "neutral"},
            {"min": -999, "value": "cold"}
        ]
    }),
    ("alexStanding", {
        "from": "alexLoyalty",
        "bands": [
            {"min": 4,    "value": "warm"},
            {"min": -1,   "value": "neutral"},
            {"min": -999, "value": "cold"}
        ]
    }),
])

# Ordered, first match wins. Evaluated after setState + derivedState at the
# moment a terminal resolves. A split requires accumulated damage, never one
# isolated choice.
OUTCOME_RULES = [
    {"when": {"endingReached": "B"}, "value": "unknown"},

    {"when": {"endingReached": "C"}, "value": "married"},
    {"when": {"endingReached": "D"}, "value": "married"},
    {"when": {"endingReached": "C2_backtrack"}, "value": "married"},

    {"when": {"endingReached": "C2_here"}, "value": "split"},
    {"when": {"endingReached": "C2_outside"}, "value": "postponed"},

    {"when": {"endingReached": "D2", "liedToAlex": True}, "value": "split"},
    {"when": {"endingReached": "D2"}, "value": "married"},

    {"when": {"endingReached": "A", "liedToAlex": True}, "value": "split"},
    {"when": {"endingReached": "A", "judgedFirst": True}, "value": "postponed"},
    {"when": {"endingReached": "A"}, "value": "proposed_later"},

    {"when": {"endingReached": "E"}, "value": "split"},
]
OUTCOME_DEFAULT = "split"

JESSICA_AFTERMATH = [
    {"when": {"jessicaStanding": "warm", "coupleOutcome": "married"},
     "text": "Jessica still talks to you like nothing has changed. Same voice, same jokes, same habit of ringing at eleven on a Tuesday.\n\nBut you notice she tells you things now that she doesn't tell Alex. Small ones, mostly. She trusts you.\n\nMaybe more than she should."},

    {"when": {"jessicaStanding": "warm", "coupleOutcome": "proposed_later"},
     "text": "Jessica doesn't say thank you, exactly. What she says, months later and slightly drunk, is that you were the only person who didn't make her feel like a monster and didn't let her off either.\n\nShe means it as the highest thing she has to give you. It probably is."},

    {"when": {"jessicaStanding": "warm", "coupleOutcome": "postponed"},
     "text": "Jessica keeps you close. Closer than before, actually — you're the only person who knows the whole shape of it, and being known is worth something to her right now.\n\nShe asks your advice a lot. You've started noticing that you're careful how you answer."},

    {"when": {"jessicaStanding": "warm", "coupleOutcome": "unknown"},
     "text": "Jessica calls you the way she always did. Nothing in her voice suggests you cost her anything.\n\nWhat she never does is bring up that night in the kitchen. Not once. You decide that's her way of saying it's finished, and you let it be finished."},

    {"when": {"jessicaStanding": "warm", "coupleOutcome": "split"},
     "text": "Jessica lost the thing she was most afraid of losing, and she still picks up when you call. That's not nothing — that's most of what she had left, handed to you.\n\nShe doesn't talk about Alex. You've learned not to ask."},

    {"when": {"jessicaStanding": "neutral", "coupleOutcome": "split"},
     "text": "Jessica forgives you eventually. Properly, not performatively — she stops flinching when your name comes up, and by spring you're in the same rooms again without it being a thing.\n\nShe just never tells you another secret."},

    {"when": {"jessicaStanding": "neutral"},
     "text": "Jessica is fine with you. That's the accurate word for it — fine. You get invited to the same things, you sit at the same tables, nobody has to be managed.\n\nSomething has quietly reorganised itself, though, and neither of you is going to be the one who names it."},

    {"when": {"jessicaStanding": "cold", "coupleOutcome": "split"},
     "text": "Jessica doesn't forgive you. Not because she thinks you were wrong — she's said, more than once and to other people, that you weren't wrong.\n\nIt's that she told you first, and you were the one who decided what happened next. She can hold both of those at the same time. She just can't get past the second one."},

    {"when": {"jessicaStanding": "cold"},
     "text": "Jessica is polite to you now, which is a thing she never used to have to be.\n\nShe replies to messages a day later. She doesn't ask how you are, and when you ask her, she tells you about work."},
]

ALEX_AFTERMATH = [
    {"when": {"alexStanding": "warm", "coupleOutcome": "split"},
     "text": "Alex doesn't thank you for what you did. Not really — not in words, not in a way you could point to.\n\nBut months later, when something else goes wrong in his life, you're still the person he calls."},

    {"when": {"alexStanding": "warm", "coupleOutcome": "married"},
     "text": "Alex tells people you're the reason it worked out. He's wrong about the specifics and right about the thing underneath, and you've stopped correcting him.\n\nYou're at their table at the wedding. He asks you to say something. You do."},

    {"when": {"alexStanding": "warm"},
     "text": "Alex knows you didn't manage him. He can't articulate how he knows — you never made a speech about it — but somewhere in those weeks he worked out that you were the one person in the room telling him something true.\n\nHe still rings you first."},

    {"when": {"alexStanding": "neutral", "coupleOutcome": "married"},
     "text": "Alex is never cruel to you. That's almost worse.\n\nHe's polite. Warm, even — hugs you at things, remembers your birthday, means it. But you stop being the person he calls first, and you can't work out exactly when that happened, because there was never a moment where it did."},

    {"when": {"alexStanding": "neutral"},
     "text": "Alex doesn't hold anything against you, as far as you can tell. There's nothing to hold — you didn't lie to him, exactly.\n\nHe's just slightly more formal with you than he used to be, in a way you only notice when you compare it to how he is with other people."},

    {"when": {"alexStanding": "cold", "coupleOutcome": "married"},
     "text": "Alex works it out eventually. Not the affair — that stays buried — but the shape of you standing in his kitchen with your face doing something that wasn't what your voice was doing.\n\nHe never says so. He just stops telling you things, and it takes you almost a year to notice."},

    {"when": {"alexStanding": "cold"},
     "text": "Alex knows you lied to him. Whatever else happened, whatever else was true, that's the sentence he keeps.\n\nHe's civil. He'll be civil for the rest of your lives. You've stopped expecting it to thaw."},
]

FINAL_MESSAGE = [
    {"when": {"loyaltyBand": "balanced", "jessicaStanding": "cold", "alexStanding": "cold"},
     "text": "You didn't choose either of them.\n\nThat sounds like neutrality. It wasn't — you managed both of them, carefully, for weeks, and they each ended up with the same quiet suspicion that you'd been doing exactly that.\n\nNeither of them thinks you betrayed them. Neither of them thinks you showed up, either."},

    {"when": {"loyaltyBand": "balanced", "coupleOutcome": "unknown"},
     "text": "You don't ask what happened between them. Jessica doesn't tell you.\n\nFor once you understand that knowing isn't the same thing as being entitled to know. Whatever happens next belongs to them.\n\nWhat belongs to you is this: neither of them thinks you picked the other one. That's rarer than it sounds, and it cost you something neither of them will ever see."},

    {"when": {"loyaltyBand": "balanced"},
     "text": "Neither of them thinks you picked the other one.\n\nYou did that by refusing the easy version every single time it was offered — by not covering for her, and not going around her either. Nobody thanks you for it, because from the outside it just looks like you didn't do very much.\n\nYou know what it cost."},

    {"when": {"loyaltyBand": "jessica", "coupleOutcome": "married"},
     "text": "Jessica knows whose side you were on.\n\nAlex knows too. He couldn't tell you when he worked it out or what gave it away, and he'll never once say it out loud.\n\nThere are three people in that marriage who know something, and only two of them know that you're one of them."},

    {"when": {"loyaltyBand": "jessica"},
     "text": "Jessica knows whose side you were on.\n\nAlex knows too.\n\nNeither of them is ever going to say it to you directly, which means you get to decide for yourself what it was — loyalty, or cowardice, or the only thing you could actually do. You'll pick a different answer depending on the year."},

    {"when": {"loyaltyBand": "alex", "coupleOutcome": "split"},
     "text": "Alex knows whose side you were on.\n\nSo does Jessica.\n\nYou were right, and being right turned out to be a completely separate question from what it cost, and you're going to be working out the exchange rate on that for a while."},

    {"when": {"loyaltyBand": "alex"},
     "text": "Alex knows whose side you were on. It's not gratitude exactly — it's more that he's stopped wondering about you, and that turns out to be worth more.\n\nJessica knows too. She's never going to bring it up. That's not the same as it being over."},
]

DEFAULT_FINAL = {
    "text": "You were the one person who knew before either of them did.\n\nThat's its own kind of weight, whatever you decided to do with it."
}


def main(path):
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh, object_pairs_hook=OrderedDict)

    nodes = d["nodes"]
    choice_index = {}
    for nid, node in nodes.items():
        for c in node["choices"]:
            choice_index[f"{nid}:{c['id']}"] = c

    # --- assert every delta target exists before mutating anything ---
    missing = [k for k in LOYALTY if k not in choice_index]
    assert not missing, f"LOYALTY targets not found in graph: {missing}"
    missing = [k for k in ENDING_REACHED_BY_CHOICE if k not in choice_index]
    assert not missing, f"ENDING_REACHED_BY_CHOICE targets not found: {missing}"
    for nid in ENDING_REACHED:
        assert nid in nodes, f"ENDING_REACHED node not found: {nid}"

    # --- state schema: drop jessicaTrust, add the new keys ---
    schema = d["stateSchema"]
    schema.pop("jessicaTrust", None)
    for k, v in NEW_STATE.items():
        schema[k] = v

    d["derivedState"] = DERIVED_STATE
    d["outcomeRules"] = OUTCOME_RULES
    d["outcomeDefault"] = OUTCOME_DEFAULT
    d["jessicaAftermath"] = JESSICA_AFTERMATH
    d["alexAftermath"] = ALEX_AFTERMATH
    d["finalMessage"] = FINAL_MESSAGE
    d["defaultFinalMessage"] = DEFAULT_FINAL

    d["engineContract"]["derivedState"] = (
        "Computed from real state after every setState, merged in before any "
        "`when` is evaluated. Exists so authored conditions can band a numeric "
        "stat without `when` needing operators. `minus` makes the band read a "
        "differential between two keys."
    )
    d["engineContract"]["outcomeRules"] = (
        "Evaluated only when a terminal resolves, after setState and "
        "derivedState. Declaration order, first match wins, result merged into "
        "state as `coupleOutcome` before aftermath variants are picked."
    )
    d["engineContract"]["aftermath"] = (
        "jessicaAftermath / alexAftermath / finalMessage are scenario-level, "
        "not per-terminal. Same first-match semantics. Composed at terminal "
        "time so one couple outcome yields very different emotional endings "
        "depending on loyalty."
    )

    # --- strip dead jessicaTrust deltas, apply loyalty, set endingReached ---
    stripped = 0
    for key, choice in choice_index.items():
        ss = choice.get("setState")
        if ss and "jessicaTrust" in ss:
            ss.pop("jessicaTrust")
            stripped += 1
            if not ss:
                choice.pop("setState")

    applied = 0
    for key, (jl, al) in LOYALTY.items():
        if jl == 0 and al == 0:
            continue
        choice = choice_index[key]
        ss = choice.setdefault("setState", OrderedDict())
        if jl:
            ss["jessicaLoyalty"] = ss.get("jessicaLoyalty", 0) + jl
        if al:
            ss["alexLoyalty"] = ss.get("alexLoyalty", 0) + al
        applied += 1

    marked = 0
    for nid, ending in ENDING_REACHED.items():
        for c in nodes[nid]["choices"]:
            if "terminal" in c:
                c.setdefault("setState", OrderedDict())["endingReached"] = ending
                marked += 1
    for key, ending in ENDING_REACHED_BY_CHOICE.items():
        choice = choice_index[key]
        assert "terminal" in choice, f"{key} is not terminal"
        choice.setdefault("setState", OrderedDict())["endingReached"] = ending
        marked += 1

    # --- post-patch validation ---
    known = set(schema) | set(DERIVED_STATE) | {"coupleOutcome"}
    unknown = set()

    def chk(w):
        if w:
            unknown.update(set(w) - known)

    for nid, node in nodes.items():
        for v in node.get("messageVariants", []) + node.get("threadVariants", []):
            chk(v.get("when"))
        for c in node["choices"]:
            chk(c.get("setState"))
            for r in c.get("nextRules", []):
                chk(r.get("when"))
            for req in c.get("requires", []):
                chk(req)
    for arr in (JESSICA_AFTERMATH, ALEX_AFTERMATH, FINAL_MESSAGE, OUTCOME_RULES):
        for v in arr:
            chk(v.get("when"))
    assert not unknown, f"unknown state keys after patch: {unknown}"

    # every terminal choice must carry an endingReached
    for nid, node in nodes.items():
        for c in node["choices"]:
            if "terminal" in c:
                ss = c.get("setState", {})
                assert "endingReached" in ss, f"terminal {nid}:{c['id']} has no endingReached"

    # graph still intact
    for nid, node in nodes.items():
        for c in node["choices"]:
            for t in [c.get("next")] + [r.get("next") for r in c.get("nextRules", [])]:
                assert t is None or t in nodes, f"dangling next {nid}:{c['id']} -> {t}"

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(f"stripped {stripped} dead jessicaTrust deltas")
    print(f"applied loyalty to {applied} choices")
    print(f"marked {marked} terminal choices with endingReached")
    print(f"added {len(JESSICA_AFTERMATH)} + {len(ALEX_AFTERMATH)} + "
          f"{len(FINAL_MESSAGE)} aftermath blocks")
    print("validation passed")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "the_secret.json")
