#!/usr/bin/env python3
"""Builds the_streets.json - Phase 2 structural skeleton.

Structure only. Prose is placeholder and marked as such; it exists so the graph
can be read and audited, not to be shipped. No visual blocks: registries.json
carries no Streets assets yet, and inventing cast/prop/scene references to make
the skeleton look finished is exactly what Phase 2 forbids. Render modes are
declared in mapping.the_streets.json instead.
"""

import json, collections

S = {}   # nodes


def node(nid, day, message, choices, variants=None, presentation=None,
         interstitial=None, delay=None):
    n = {"day": day, "message": message}
    if variants:
        n["messageVariants"] = variants
    if interstitial:
        n["interstitial"] = interstitial
    if delay:
        n["reactionDelay"] = delay
    n["presentation"] = presentation or {
        "type": "scene", "modal": False,
        "data": {"location": "PLACEHOLDER", "character": {"name": "", "role": "", "mood": "flat"}},
    }
    n["choices"] = choices
    S[nid] = n


def ch(cid, label, nxt=None, set_state=None, requires=None, rules=None,
       terminal=None, scores=(0, 0, 0), beat=None, locked=None):
    c = {"id": cid, "label": label,
         "scores": {"savvy": scores[0], "streetSmarts": scores[1], "integrity": scores[2]}}
    if requires:
        c["requires"] = requires
    if set_state:
        c["setState"] = set_state
    if beat:
        c["beat"] = beat
    if locked:
        c["lockedLabel"] = locked
    if rules:
        c["nextRules"] = rules
    if nxt:
        c["next"] = nxt
    if terminal:
        c["terminal"] = terminal
    return c


def cont(nxt, label="Continue"):
    return [ch("continue", label, nxt=nxt)]


P = "[PLACEHOLDER] "

# ===================================================================== DAY 1
# The Ordinary Day. Zero stakes on the surface. Root node carries no derived
# band reference - initialState() never runs applyDerived, so a band key does
# not exist yet and would match nothing, silently.

node("d1_open", 1,
     P + "Friday. Nothing is happening. The block, the flat, the last week of a term you have been half-attending.",
     cont("d1_kitchen"),
     presentation={"type": "scene", "modal": False,
                   "data": {"location": "The block, late afternoon",
                            "character": {"name": "", "role": "", "mood": "flat"}}})

node("d1_kitchen", 1,
     P + "Mum is on a shift changeover and wants ten minutes. She asks about college in the way that means she already knows.",
     [ch("d1k_straight", "Tell her where you actually are with it.",
         nxt="d1_kitchen_react", set_state={"mumTrust": 1, "discipline": 1, "answered_mum": True},
         scores=(10, 0, 15)),
      ch("d1k_manage", "Give her the version that ends the conversation.",
         nxt="d1_kitchen_react", set_state={"mumStrain": 1, "answered_mum": True},
         scores=(5, 5, -5)),
      ch("d1k_lie", "Tell her it's handled.",
         nxt="d1_kitchen_react", set_state={"mumStrain": 2, "lied_to_mum": True, "discipline": -1},
         scores=(0, 5, -15))])

node("d1_kitchen_react", 1,
     P + "She takes it, or takes what she's given. Either way she's out the door in four minutes.",
     cont("d1_street"),
     variants=[{"when": {"lied_to_mum": True},
                "message": P + "She doesn't push. That is not the same as believing you."},
               {"when": {"mumBand": "tight"},
                "message": P + "She stops in the doorway and says something that isn't about college."}])

node("d1_street", 1,
     P + "Outside, both of them want you. Jay has an evening planned. Tunde has a session at the cage and has asked twice already.",
     [ch("d1s_jay", "Jay.", nxt="d1_evening_jay",
         set_state={"jayTrust": 1, "tundeStrain": 1, "stayed_out": True}, scores=(0, 10, 0)),
      ch("d1s_tunde", "Tunde.", nxt="d1_evening_tunde",
         set_state={"tundeTrust": 1, "jayStrain": 1, "discipline": 1}, scores=(10, 0, 5)),
      ch("d1s_neither", "Neither. Go home.", nxt="d1_evening_alone",
         set_state={"jayStrain": 1, "tundeStrain": 1, "discipline": 1}, scores=(5, -5, 5))])

node("d1_evening_jay", 1,
     P + "Chicken shop. Jay is funny for two hours and then, near the end, is briefly not.",
     [ch("d1j_ask", "Ask what that was.", nxt="d1_close",
         set_state={"jayTrust": 1}, scores=(15, 5, 10)),
      ch("d1j_leave", "Let it go.", nxt="d1_close", set_state={"jayStrain": 1}, scores=(0, 5, -5))])

node("d1_evening_tunde", 1,
     P + "The cage. Tunde is training for something specific and does not make a thing of it.",
     [ch("d1t_in", "Say you'll come Thursday.", nxt="d1_close",
         set_state={"tundeTrust": 1, "discipline": 1}, scores=(10, 0, 10)),
      ch("d1t_vague", "Say maybe.", nxt="d1_close",
         set_state={"tundeStrain": 1, "tundeTrust": -1, "missed_training": True}, scores=(0, 5, -5))])

node("d1_evening_alone", 1,
     P + "Your room. The phone does most of the talking.",
     [ch("d1a_reply", "Reply to Amara properly.", nxt="d1_close",
         set_state={"amaraTrust": 1}, scores=(10, 5, 5)),
      ch("d1a_scroll", "Don't.", nxt="d1_close", set_state={"amaraStrain": 1}, scores=(0, 0, 0))],
     presentation={"type": "messages", "modal": True,
                   "data": {"location": "Your room, late",
                            "character": {"name": "Amara", "role": "", "mood": "flat"}}})

node("d1_close", 1,
     P + "23:40. A message from a number you don't have saved.",
     cont("d2_open"),
     variants=[{"when": {"jayBand": "tight"}, "message": P + "Jay's name is on the screen when it lights up."}],
     presentation={"type": "messages", "modal": True,
                   "data": {"location": "Your room, 23:40",
                            "character": {"name": "", "role": "", "mood": "flat"}}})

# ===================================================================== DAY 2
# The Favour. First real ask, small, from someone who has earned it. The
# redirect lane opens here and stays open until Day 5, where it closes.

node("d2_open", 2,
     P + "Saturday. Jay is outside before you've eaten.",
     cont("d2_ask"),
     interstitial={"label": "Saturday", "durationMs": 2000},
     variants=[{"when": {"jayBand": "frayed"}, "message": P + "Jay is outside and has clearly decided not to mention last night."},
               {"when": {"stayed_out": True}, "message": P + "Jay is outside, four hours after you left him."}])

node("d2_ask", 2,
     P + "He needs you to come somewhere and stand there. That's the whole ask. He is careful not to say more than that.",
     [ch("d2a_help", "Come. Don't ask.", nxt="d2_help",
         set_state={"jayTrust": 1, "heat": 2, "helped_jay": True, "credit": 1}, scores=(0, 10, -5)),
      ch("d2a_limited", "Come, but you're not holding anything.", nxt="d2_limited",
         set_state={"jayTrust": 1, "heat": 1, "helped_jay": True}, scores=(15, 5, 10)),
      ch("d2a_decline", "No.", nxt="d2_decline",
         set_state={"jayStrain": 2, "jayTrust": -1}, scores=(5, -10, 10)),
      ch("d2a_redirect", "Not that. I'll do the other thing instead.", nxt="d2_redirect",
         set_state={"jayTrust": 1, "credit": 1, "kept_the_receipt": True}, scores=(20, 5, 15))])

node("d2_help", 2,
     P + "You stand where you're told for forty minutes. Nothing happens. That is not the same as nothing having happened.",
     cont("d2_react"))

node("d2_limited", 2,
     P + "You come. You say the sentence once, in front of the person it was for. Jay looks at you a second longer than he needs to.",
     cont("d2_react"))

node("d2_decline", 2,
     P + "He doesn't argue. He says fine in the voice that means the opposite and goes anyway.",
     cont("d2_react"))

node("d2_redirect", 2,
     P + "You offer the version that costs you and not him. He takes it, surprised, and writes nothing down. You do.",
     cont("d2_react"))

node("d2_react", 2,
     P + "Afterwards.",
     cont("d2_kai"),
     variants=[{"when": {"jayBand": "tight"}, "message": P + "Afterwards he is easier with you than he has been in weeks."},
               {"when": {"jayBand": "frayed"}, "message": P + "Afterwards there is a gap in it that neither of you names."},
               {"when": {"heatBand": "warm"}, "message": P + "Afterwards you notice you are thinking about who saw you there."}])

node("d2_kai", 2,
     P + "Kai is on the walkway with two others. Something gets said that is meant to be heard.",
     [ch("d2k_answer", "Answer it.", nxt="d2_close",
         set_state={"kaiStrain": 2, "rep": 1}, scores=(0, 5, 0)),
      ch("d2k_past", "Walk past.", nxt="d2_close",
         set_state={"kaiStrain": 1, "walked_away": True, "rep": -1}, scores=(10, 0, 5)),
      ch("d2k_defuse", "Say the thing that ends it.", nxt="d2_close",
         set_state={"rep": 1, "walked_away": True, "credit": 1}, scores=(15, 10, 10))])

node("d2_close", 2, P + "Home. Nothing has changed that anyone could point to.",
     cont("d3_open"))

# ===================================================================== DAY 3
# The Room. Dee is introduced. Nothing is asked. He is warm, generous and
# genuinely good company - the scenario collapses if he reads as a threat.

node("d3_open", 3, P + "Sunday. Word comes that you should come by.",
     cont("d3_arrive"), interstitial={"label": "Sunday", "durationMs": 2000})

node("d3_arrive", 3,
     P + "A flat above the shops that is nicer than any flat you have been in. Dee knows your name and one thing about you that you did not tell him.",
     cont("d3_dee"), delay="long",
     variants=[{"when": {"helped_jay": True}, "message": P + "He knows your name and where you were standing on Saturday."},
               {"when": {"repBand": "quiet"}, "message": P + "He knows your name, which is more than you expected."}])

node("d3_dee", 3,
     P + "He asks what you're doing with yourself. It is a real question and he waits for the answer.",
     [ch("d3d_impress", "Give him the version that sounds like something.",
         nxt="d3_impress", set_state={"standing": "known", "deeTrust": 2, "rep": 1}, scores=(5, 10, -5)),
      ch("d3d_true", "Tell him the actual answer.",
         nxt="d3_true", set_state={"standing": "around", "deeTrust": 1}, scores=(15, 0, 15)),
      ch("d3d_leave", "Say very little and leave early.",
         nxt="d3_leave", set_state={"standing": "new", "deeStrain": 1, "rep": -1}, scores=(5, 5, 5))])

node("d3_impress", 3, P + "He likes it. You can feel exactly how much, and how easy it would be to keep doing.",
     cont("d3_react"))
node("d3_true", 3, P + "He doesn't flinch. He says something about his own eighteenth year that you don't know how to hold.",
     cont("d3_react"))
node("d3_leave", 3, P + "He walks you to the door and is nice about it, which is worse.",
     cont("d3_react"))

node("d3_react", 3,
     P + "On the walkway home.",
     cont("d3_tell"),
     variants=[{"when": {"standing": "known"}, "message": P + "You get to the bottom of the stairs before you notice you are pleased."},
               {"when": {"standing": "new"}, "message": P + "You get to the bottom of the stairs and feel like you failed a test you didn't sit."}])

node("d3_tell", 3,
     P + "Jay asks where you were.",
     [ch("d3t_tell", "Tell him.", nxt="d3_close",
         set_state={"jayTrust": 1, "told_jay_about_dee": True}, scores=(10, -5, 15)),
      ch("d3t_partial", "Tell him a version.", nxt="d3_close",
         set_state={"jayStrain": 1}, scores=(5, 10, -5)),
      ch("d3t_nothing", "Nothing.", nxt="d3_close",
         set_state={"jayStrain": 2, "jayTrust": -1}, scores=(0, 5, -10))])

node("d3_close", 3, P + "Sunday ends the way Sundays do.", cont("d4_open"))

# ===================================================================== DAY 4
# Two Things At Once. The one expensive divergence: three genuinely different
# lanes, three locations, three casts. Everything else in the run diverges
# through state.

node("d4_open", 4,
     P + "Monday. Three things want the same evening.",
     cont("d4_choose"), interstitial={"label": "Monday", "durationMs": 2000},
     variants=[{"when": {"amaraBand": "steady"}, "message": P + "Monday. Amara has asked, which she does not usually do."},
               {"when": {"tundeBand": "tight"}, "message": P + "Monday. Tunde has been counting on Thursday since Thursday."}])

node("d4_choose", 4,
     P + "Amara. Tunde's session. Or the thing with Kai that is going to happen whether you are there or not.",
     [ch("d4c_amara", "Amara.", nxt="d4_amara_1",
         requires=[{"amaraBand": "steady"}, {"amaraBand": "tight"}],
         locked="Amara. — she hasn't asked you anywhere",
         set_state={"dayFourWent": "amara", "tundeStrain": 1, "amaraTrust": 1}, scores=(10, 0, 5)),
      ch("d4c_tunde", "Tunde's session.", nxt="d4_tunde_1",
         set_state={"dayFourWent": "tunde", "discipline": 2, "amaraStrain": 1}, scores=(10, 0, 10)),
      ch("d4c_kai", "The thing with Kai.", nxt="d4_kai_1",
         set_state={"dayFourWent": "kai", "kaiStrain": 1, "heat": 1, "discipline": -1}, scores=(0, 10, -5)),
      ch("d4c_none", "None of it.", nxt="d4_none_1",
         set_state={"dayFourWent": "nowhere", "amaraStrain": 1, "tundeStrain": 1, "discipline": -1,
                    "rep": -1, "tundeTrust": -1, "missed_training": True},
         scores=(0, -5, 0))])

# --- lane A: Amara
node("d4_amara_1", 4, P + "The bus stop, then somewhere neither of you picked. She asks a question about Dee that she should not know to ask.",
     [ch("d4a_honest", "Answer it.", nxt="d4_amara_2", set_state={"amaraTrust": 2}, scores=(10, -5, 15)),
      ch("d4a_deflect", "Move it along.", nxt="d4_amara_2", set_state={"amaraStrain": 2}, scores=(5, 10, -10))])
node("d4_amara_2", 4, P + "Later, walking back. She says the thing she came to say.",
     cont("d4_after"),
     variants=[{"when": {"amaraBand": "tight"}, "message": P + "She says it plainly, and waits."}])

# --- lane B: Tunde
node("d4_tunde_1", 4, P + "The cage. Tunde has brought someone who runs the programme he keeps talking about.",
     [ch("d4t_ask", "Ask about it properly.", nxt="d4_tunde_2",
         set_state={"tundeTrust": 2, "discipline": 1, "credit": 1}, scores=(15, 5, 10)),
      ch("d4t_hang", "Stay at the edge of it.", nxt="d4_tunde_2",
         set_state={"tundeStrain": 1}, scores=(0, 0, 0))])
node("d4_tunde_2", 4, P + "Afterwards Tunde is careful not to ask whether you meant it.",
     cont("d4_after"),
     variants=[{"when": {"disciplineBand": "held"}, "message": P + "Afterwards he tells the other man you'll be there Thursday, and looks at you while he does."}])

# --- lane C: Kai
node("d4_kai_1", 4, P + "The stairwell end of the walkway. Twelve people who all want to be able to say they were there.",
     [ch("d4k_film", "Film it.", nxt="d4_kai_2",
         set_state={"filmed_the_fight": True, "rep": 2, "heat": 2, "kaiStrain": 2}, scores=(-5, 10, -15)),
      ch("d4k_stop", "Get in the middle of it.", nxt="d4_kai_2",
         set_state={"rep": 2, "heat": 1, "kaiStrain": -1, "walked_away": True}, scores=(10, -5, 15)),
      ch("d4k_watch", "Stand there.", nxt="d4_kai_2",
         set_state={"heat": 1, "rep": 1}, scores=(0, 5, -5))])
node("d4_kai_2", 4, P + "It ends the way these end. Someone's phone has it.",
     cont("d4_after"),
     variants=[{"when": {"filmed_the_fight": True}, "message": P + "It ends. Your phone has it. You have not decided anything yet."},
               {"when": {"kaiBand": "hostile"}, "message": P + "It ends, and Kai looks at you specifically on the way out."}])

# --- lane D: nowhere
node("d4_none_1", 4, P + "Your room. Three conversations you are not in.",
     [ch("d4n_watch", "Follow it on your phone anyway.", nxt="d4_none_2", set_state={"heat": 1}, scores=(0, 5, -5)),
      ch("d4n_off", "Put it face down.", nxt="d4_none_2", set_state={"discipline": 1, "rep": -1}, scores=(5, -5, 5))],
     presentation={"type": "messages", "modal": True,
                   "data": {"location": "Your room", "character": {"name": "", "role": "", "mood": "flat"}}})
node("d4_none_2", 4, P + "By eleven it has happened without you.", cont("d4_after"))

node("d4_after", 4,
     P + "Tuesday morning. Two people ask you where you were.",
     [ch("d4s_true", "Tell them.", nxt="d4_close", set_state={"dayFourSaid": "true"}, scores=(10, -5, 15)),
      ch("d4s_lie", "Don't.", nxt="d4_close",
         set_state={"dayFourSaid": "lied", "amaraStrain": 1, "tundeStrain": 1, "tundeTrust": -1}, scores=(0, 10, -15)),
      ch("d4s_silent", "Say nothing at all.", nxt="d4_close", set_state={"dayFourSaid": "silent"}, scores=(5, 5, 0))],
     variants=[{"when": {"dayFourWent": "kai"}, "message": P + "Tuesday morning. Everyone already knows where you were."},
               {"when": {"dayFourWent": "nowhere"}, "message": P + "Tuesday morning. Nobody asks, which is its own answer."}])

node("d4_close", 4, P + "Tuesday closes quietly.", cont("d5_open"))

# ===================================================================== DAY 5
# The Ask. The redirect lane closes here on most routes, for structural
# reasons that are nobody's fault.

node("d5_open", 5,
     P + "Wednesday. Dee asks you to come by. It is phrased as an invitation.",
     cont("d5_stairwell"), interstitial={"label": "Wednesday", "durationMs": 2000},
     variants=[{"when": {"standing": "known"}, "message": P + "Wednesday. Dee asks for you by name, through someone else."},
               {"when": {"deeBand": "steady"}, "message": P + "Wednesday. Dee texts directly, which he has not done before."}])

node("d5_stairwell", 5,
     P + "The stairwell. He is exactly as warm as he was on Sunday. He asks how the week has been and listens to the answer.",
     cont("d5_ask"), delay="long")

node("d5_ask", 5,
     P + "Then the ask. Small, specific, phrased as trust. He does not say what it is and you do not need him to.",
     [ch("d5_take", "Take it.", nxt="d5_took",
         set_state={"dayFive": "took", "heat": 3, "deeTrust": 2, "money": 60, "standing": "named"},
         scores=(-10, 15, -20)),
      ch("d5_limited", "Take it, with one condition.", nxt="d5_limited_n",
         set_state={"dayFive": "took_limited", "heat": 2, "deeTrust": 1, "money": 30, "kept_the_receipt": True},
         scores=(10, 10, -5)),
      ch("d5_decline", "No.", nxt="d5_declined",
         set_state={"dayFive": "declined", "deeStrain": 2, "refused_the_bag": True},
         scores=(10, -10, 20)),
      ch("d5_redirect", "Not that — I'll do the other thing.",
         requires=[{"creditBand": "owed"}],
         locked="Not that — I'll do the other thing. — there's nothing left to offer him",
         nxt="d5_redirect_n",
         set_state={"dayFive": "declined", "credit": -2, "deeTrust": 1, "refused_the_bag": True},
         scores=(20, 5, 15))])

node("d5_took", 5, P + "It is in your bag and it weighs nothing at all.", cont("d5_react"))
node("d5_limited_n", 5, P + "He agrees to the condition immediately, which tells you what the condition was worth.", cont("d5_react"))
node("d5_declined", 5, P + "He is not angry. He is disappointed in a way that costs more than anger would.", cont("d5_react"))
node("d5_redirect_n", 5, P + "You spend what you were owed. He takes it, and something in the room resets.", cont("d5_react"))

node("d5_react", 5,
     P + "Outside. The walk home is the same walk.",
     cont("d5_close"),
     variants=[{"when": {"dayFive": "took"}, "message": P + "Outside. You take a different route home and do not examine why."},
               {"when": {"dayFourSaid": "lied"}, "message": P + "Outside. You are still carrying Tuesday's version of Monday."},
               {"when": {"dayFive": "declined", "deeBand": "frayed"}, "message": P + "Outside. Nobody is following you. That was never the shape of it."}])

node("d5_close", 5,
     P + "Wednesday, late.",
     cont("d6_open"),
     variants=[{"when": {"moneyBand": "flush"}, "message": P + "Wednesday, late. There is more in your pocket than there was."}],
     presentation={"type": "scene", "modal": False,
                   "data": {"location": "Your room, late", "character": {"name": "", "role": "", "mood": "flat"}}})

# ===================================================================== DAY 6
# It Lands. The consequence arrives, and it lands on someone else.

node("d6_open", 6,
     P + "Thursday. It has landed, and not on you.",
     cont("d6_news"), interstitial={"label": "Thursday", "durationMs": 2000},
     variants=[{"when": {"exposureBand": "exposed"}, "message": P + "Thursday. Two people have already messaged you about it."},
               {"when": {"exposureBand": "clear"}, "message": P + "Thursday. You hear about it fourth-hand, which is its own kind of information."}])

node("d6_news", 6,
     P + "Jay is the one holding it. What he is holding is partly yours.",
     cont("d6_act"), delay="long",
     variants=[{"when": {"kept_the_receipt": True}, "message": P + "Jay is holding it. You still have the thing you wrote down in March."},
               {"when": {"helped_jay": True}, "message": P + "Jay is holding it, and part of what he is holding has your Saturday in it."},
               {"when": {"filmed_the_fight": True}, "message": P + "Jay is holding it, and there is a video going round that you took."}])

node("d6_act", 6,
     P + "You can put your name on it, keep it off, or let it sit where it landed.",
     [ch("d6a_front", "Front it.", nxt="d6_fronted",
         set_state={"daySixAct": "fronted", "heat": 2, "jayTrust": 2, "rep": 2, "credit": 1},
         scores=(5, -10, 20)),
      ch("d6a_cover", "Keep it off you and off him.", nxt="d6_covered",
         set_state={"daySixAct": "covered", "heat": 1, "jayTrust": 1, "lied_to_mum": True, "rep": 1},
         scores=(15, 10, -10)),
      ch("d6a_sit", "Let it sit.", nxt="d6_sat",
         set_state={"daySixAct": "sat", "jayStrain": 2, "jayTrust": -1, "rep": -1},
         scores=(0, 5, -15))])

node("d6_fronted", 6, P + "You say it was you. It is true enough to survive being said out loud.", cont("d6_tell_first"))
node("d6_covered", 6, P + "You put a version together that holds. It holds.", cont("d6_tell_first"))
node("d6_sat", 6, P + "You do nothing, and doing nothing turns out to be a thing you did.", cont("d6_tell_first"))

node("d6_tell_first", 6,
     P + "Someone has to hear it from you first.",
     [ch("d6t_mum", "Mum.", nxt="d6_close", set_state={"mumTrust": 2, "answered_mum": True}, scores=(10, -5, 15)),
      ch("d6t_jay", "Jay.", nxt="d6_close", set_state={"jayTrust": 1}, scores=(5, 5, 10)),
      ch("d6t_tunde", "Tunde.", nxt="d6_close", set_state={"tundeTrust": 1, "tundeStrain": 1}, scores=(5, 0, 5)),
      ch("d6t_none", "Nobody.", nxt="d6_close", set_state={"mumStrain": 1, "jayStrain": 1, "tundeStrain": 2}, scores=(0, 10, -10))])

node("d6_close", 6,
     P + "Thursday, late. It is not over.",
     cont("d7_open"),
     variants=[{"when": {"daySixAct": "fronted"}, "message": P + "Thursday, late. You are holding something that was not yours to hold."},
               {"when": {"daySixAct": "sat"}, "message": P + "Thursday, late. Nobody has said your name. That is what you chose."}])

# ===================================================================== DAY 7
# What You've Got Left. Options hard-gated on accumulated state: some players
# see three doors, some see one. That asymmetry is the run.

node("d7_open", 7,
     P + "Friday. A week.",
     cont("d7_situation"), interstitial={"label": "Friday", "durationMs": 2400},
     variants=[{"when": {"heatBand": "burnt"}, "message": P + "Friday. There is a version of this week that is now a thing that happened to you."},
               {"when": {"missed_training": True}, "message": P + "Friday. Tunde has stopped putting the sessions in the group chat."}])

node("d7_situation", 7,
     P + "It needs something from you today that you either have or don't.",
     cont("d7_move"), delay="long",
     variants=[{"when": {"creditBand": "owed"}, "message": P + "It needs something today, and there are two people who owe you a phone call."},
               {"when": {"creditBand": "owing"}, "message": P + "It needs something today, and you have already spent everything you had with everyone."}])

node("d7_move", 7,
     P + "Four doors. Some of them are shut.",
     [ch("d7m_pay", "Pay it and be done.",
         requires=[{"moneyBand": "flush"}, {"moneyBand": "enough"}],
         locked="Pay it and be done. — you don't have it",
         nxt="d7_paid", set_state={"money": -40, "paid_it_back": True, "heat": -2}, scores=(10, 10, 10)),
      ch("d7m_call", "Call in what you're owed.",
         requires=[{"creditBand": "owed"}, {"creditBand": "even"}],
         locked="Call in what you're owed. — there's nobody left to call",
         nxt="d7_called", set_state={"credit": -2, "rep": 1}, scores=(15, 10, 5)),
      ch("d7m_jay", "Go to Jay.",
         requires=[{"jayBand": "tight"}, {"jayBand": "steady"}],
         locked="Go to Jay. — you two aren't there any more",
         nxt="d7_jay", set_state={"jayTrust": 1, "heat": 1}, scores=(5, 5, 10)),
      ch("d7m_alone", "Handle it yourself.", nxt="d7_alone",
         set_state={"heat": 1, "rep": 1}, scores=(5, 0, 5))])

node("d7_paid", 7, P + "It costs what it costs and then it is closed.", cont("d7_final"))
node("d7_called", 7, P + "Two calls. Both answered. You notice that you counted.", cont("d7_final"))
node("d7_jay", 7, P + "Jay does not ask what it is for.", cont("d7_final"),
     variants=[{"when": {"told_jay_about_dee": True}, "message": P + "Jay does not ask what it is for, because you told him in March."}])
node("d7_alone", 7, P + "You do it on your own, which works, and costs something you can't name yet.", cont("d7_final"))

node("d7_final", 7,
     P + "Friday night. The block, the same as it was seven days ago, except for everything.",
     [ch("d7f_out", "Go out.",
         terminal={"consequence": P + "A week ends. It does not announce itself.",
                   "landing": P + "You work out on the walk back that the whole thing turned on about four minutes on Wednesday."},
         set_state={"stayed_out": True}, scores=(0, 5, 0)),
      ch("d7f_home", "Go home.",
         terminal={"consequence": P + "A week ends the way most weeks end, which is quietly.",
                   "landing": P + "Mum is on the sofa with the TV on and does not ask where you have been."},
         set_state={"answered_mum": True}, scores=(5, 0, 5)),
      ch("d7f_apologise", "Say the thing to Kai.",
         requires=[{"kaiBand": "hostile"}, {"kaiBand": "needled"}],
         locked="Say the thing to Kai. — there is nothing between you to settle",
         terminal={"consequence": P + "It does not fix it. It ends it, which is different and enough.",
                   "landing": P + "He nods once. Neither of you mentions it again."},
         set_state={"apologised_to_kai": True, "kaiStrain": -2}, scores=(15, 5, 15))],
     variants=[{"when": {"moneyBand": "short"}, "message": P + "Friday night. Four pounds and a week."},
               {"when": {"walked_away": True}, "message": P + "Friday night. Nobody on the walkway has a reason to stop you."}])

# ================================================================ SCENARIO

STATE = {
    "money": {"type": "int", "initial": 40, "range": [0, 200],
              "note": "The only number the player sees. A plot fact, not a stat."},
    "rep": {"type": "int", "initial": 3, "range": [0, 10]},
    "heat": {"type": "int", "initial": 0, "range": [0, 8]},
    "discipline": {"type": "int", "initial": 4, "range": [0, 8]},
    "credit": {"type": "int", "initial": 2, "range": [0, 6]},
    "jayTrust": {"type": "int", "initial": 4, "range": [0, 6]},
    "jayStrain": {"type": "int", "initial": 0, "range": [0, 6]},
    "tundeTrust": {"type": "int", "initial": 3, "range": [0, 6]},
    "tundeStrain": {"type": "int", "initial": 0, "range": [0, 6]},
    "amaraTrust": {"type": "int", "initial": 1, "range": [0, 6]},
    "amaraStrain": {"type": "int", "initial": 0, "range": [0, 6]},
    "deeTrust": {"type": "int", "initial": 0, "range": [0, 6]},
    "deeStrain": {"type": "int", "initial": 0, "range": [0, 6]},
    "mumTrust": {"type": "int", "initial": 4, "range": [0, 6]},
    "mumStrain": {"type": "int", "initial": 0, "range": [0, 6]},
    "kaiStrain": {"type": "int", "initial": 1, "range": [0, 6],
                  "note": "Kai has no trust axis. He is friction, not a relationship being built."},
    "standing": {"type": "enum", "initial": "new", "values": ["named", "known", "around", "new"]},
    "dayFive": {"type": "enum", "initial": "none", "values": ["none", "took", "took_limited", "declined"]},
    "dayFourWent": {"type": "enum", "initial": "nowhere", "values": ["amara", "tunde", "kai", "nowhere"]},
    "dayFourSaid": {"type": "enum", "initial": "none", "values": ["none", "true", "lied", "silent"]},
    "daySixAct": {"type": "enum", "initial": "none", "values": ["none", "fronted", "covered", "sat"]},
    "helped_jay": {"type": "bool", "initial": False},
    "refused_the_bag": {"type": "bool", "initial": False},
    "filmed_the_fight": {"type": "bool", "initial": False},
    "missed_training": {"type": "bool", "initial": False},
    "told_jay_about_dee": {"type": "bool", "initial": False},
    "lied_to_mum": {"type": "bool", "initial": False},
    "answered_mum": {"type": "bool", "initial": False},
    "stayed_out": {"type": "bool", "initial": False},
    "paid_it_back": {"type": "bool", "initial": False},
    "walked_away": {"type": "bool", "initial": False},
    "apologised_to_kai": {"type": "bool", "initial": False},
    "kept_the_receipt": {"type": "bool", "initial": False},
}


def band(src, pairs, minus=None):
    b = {"from": src}
    if minus:
        b["minus"] = minus
    b["bands"] = [{"min": m, "value": v} for m, v in pairs]
    return b


DERIVED = {
    "moneyBand": band("money", [(60, "flush"), (20, "enough"), (-999, "short")]),
    "repBand": band("rep", [(8, "known"), (5, "solid"), (2, "quiet"), (-999, "nobody")]),
    "heatBand": band("heat", [(6, "burnt"), (4, "hot"), (2, "warm"), (-999, "clear")]),
    "disciplineBand": band("discipline", [(6, "held"), (3, "slipping"), (-999, "gone")]),
    "creditBand": band("credit", [(4, "owed"), (2, "even"), (-999, "owing")]),
    "exposureBand": band("heat", [(4, "exposed"), (2, "watched"), (1, "noticed"), (-999, "clear")], minus="credit"),
    "jayBand": band("jayTrust", [(3, "tight"), (1, "steady"), (-1, "frayed"), (-999, "broken")], minus="jayStrain"),
    "tundeBand": band("tundeTrust", [(3, "tight"), (1, "steady"), (-1, "frayed"), (-999, "broken")], minus="tundeStrain"),
    "amaraBand": band("amaraTrust", [(3, "tight"), (1, "steady"), (-1, "frayed"), (-999, "broken")], minus="amaraStrain"),
    "deeBand": band("deeTrust", [(3, "tight"), (1, "steady"), (-1, "frayed"), (-999, "broken")], minus="deeStrain"),
    "mumBand": band("mumTrust", [(3, "tight"), (1, "steady"), (-1, "frayed"), (-999, "broken")], minus="mumStrain"),
    "kaiBand": band("kaiStrain", [(4, "hostile"), (2, "needled"), (-999, "quiet")]),
}

TRAJECTORIES = ["kept_both", "moving", "the_one_they_call", "useful", "in_it",
                "on_your_own", "invisible", "carrying_it", "holding"]

OUTCOME_RULES = [
    {"when": {"dayFive": "took", "exposureBand": "exposed"}, "value": "in_it"},
    {"when": {"heatBand": "burnt"}, "value": "in_it"},
    {"when": {"daySixAct": "fronted"}, "value": "carrying_it"},
    {"when": {"dayFive": "took", "creditBand": "owed"}, "value": "useful"},
    {"when": {"disciplineBand": "held", "jayBand": "tight"}, "value": "kept_both"},
    {"when": {"disciplineBand": "held"}, "value": "moving"},
    {"when": {"jayBand": "broken", "tundeBand": "broken"}, "value": "on_your_own"},
    {"when": {"creditBand": "owed", "repBand": "known"}, "value": "the_one_they_call"},
    {"when": {"repBand": "nobody", "heatBand": "clear"}, "value": "invisible"},
]

SCENARIO = {
    "id": "the_streets",
    "schemaVersion": 3,
    "title": "The Streets: 7 Days",
    "district": "streets",
    "difficulty": 2,
    "estimatedMinutes": 35,
    "premise": "Seven days on the block. Every decision is small. None of them stay small.",
    "skeletonNote": "PHASE 2 STRUCTURAL SKELETON. All prose is placeholder and marked [PLACEHOLDER]. "
                    "No visual blocks: registries.json carries no Streets assets, and inventing "
                    "cast/scene/prop references to make the skeleton look complete is out of scope.",
    "persona": {"name": "Jay", "role": "Best friend"},
    "design": {
        "noCorrectAnswer": True,
        "deeIsNotAVillain": "Dee never threatens and never punishes refusal. If he reads as "
                            "menacing the player refuses on Day 3 and there is no scenario.",
        "authoringRule": "The player is not choosing between right and wrong. They are choosing "
                         "what they are willing to spend, and what they have left on Day 7.",
    },
    "contentRating": {"minAge": 14,
                      "excluded": ["substance procedure", "weapon handling", "sexual content",
                                   "evasion technique", "violence choreography"]},
    "scoring": {"dimensions": ["savvy", "streetSmarts", "integrity"], "revealTiming": "end_only"},
    "cast": [
        {"id": "jay", "name": "Jay", "role": "Oldest friend"},
        {"id": "tunde", "name": "Tunde", "role": "Friend with a plan"},
        {"id": "amara", "name": "Amara", "role": "Has her own life and her own read"},
        {"id": "dee", "name": "Dee", "role": "Older, generous, genuinely good company"},
        {"id": "bola", "name": "Bola", "role": "Mum"},
        {"id": "kai", "name": "Kai", "role": "Friction"},
    ],
    "stateSchema": STATE,
    "derivedState": DERIVED,
    "trajectories": TRAJECTORIES,
    "rootNode": "d1_open",
    "nodes": S,
    "outcomeKey": "trajectory",
    "outcomeDefault": "holding",
    "outcomeRules": OUTCOME_RULES,
    "reflections": [
        {"when": {"daySixAct": "fronted"}, "title": "PLACEHOLDER", "text": P + "You took someone else's Thursday."},
        {"when": {"dayFive": "took"}, "title": "PLACEHOLDER", "text": P + "Wednesday was the hinge and you did not feel it as one."},
        {"when": {"refused_the_bag": True}, "title": "PLACEHOLDER", "text": P + "You said no on Wednesday and paid for it all week."},
        {"when": {"disciplineBand": "held"}, "title": "PLACEHOLDER", "text": P + "You did the boring thing every day it was available."},
    ],
    "defaultReflection": {"title": "PLACEHOLDER", "text": P + "A week."},
    "aftermath": {
        "jay": [{"when": {"jayBand": "tight"}, "text": P + "Jay is still Jay."},
                {"when": {"jayBand": "broken"}, "text": P + "Jay stops coming to the door."},
                {"when": {"trajectory": "carrying_it"}, "text": P + "Jay knows exactly what you did and never says so."}],
        "tunde": [{"when": {"disciplineBand": "held"}, "text": P + "Tunde puts your name forward."},
                  {"when": {"tundeBand": "broken"}, "text": P + "Tunde stops asking."}],
        "mum": [{"when": {"lied_to_mum": True}, "text": P + "She works it out in her own time."},
                {"when": {"answered_mum": True}, "text": P + "She notices that you picked up, every time, all week."},
                {"when": {"mumBand": "tight"}, "text": P + "She stops waiting up."}],
        "dee": [{"when": {"dayFive": "took"}, "text": P + "Dee remembers reliable people."},
                {"when": {"refused_the_bag": True}, "text": P + "Dee is warm to you for the rest of the year, and never asks again."}],
        "kai": [{"when": {"apologised_to_kai": True}, "text": P + "It stays ended."},
                {"when": {"kaiBand": "hostile"}, "text": P + "It does not stay ended."}],
        "amara": [{"when": {"amaraBand": "tight"}, "text": P + "Amara is still there in August."},
                  {"when": {"amaraBand": "broken"}, "text": P + "Amara is not."}],
    },
    "finalMessage": [
        {"when": {"trajectory": "kept_both"}, "text": P + "You paid for both and it cost more than either."},
        {"when": {"trajectory": "in_it"}, "text": P + "It is not a story about a bag. It is a story about a Wednesday."},
        {"when": {"paid_it_back": True}, "text": P + "You closed it yourself, and nobody will ever know."},
        {"when": {"trajectory": "invisible"}, "text": P + "A quiet week is a real outcome."},
        {"when": {"trajectory": "carrying_it"}, "text": P + "You are still holding it."},
    ],
    "defaultFinalMessage": {"text": P + "Seven days."},
    "testPlaythroughs": [],
}

if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "src/data/scenarios/the_streets.json"
    with open(out, "w") as f:
        json.dump(SCENARIO, f, indent=1)
    per_day = collections.Counter(n["day"] for n in S.values())
    print(f"wrote {out}: {len(S)} nodes, "
          f"{sum(len(n['choices']) for n in S.values())} choices, "
          f"per-day {dict(sorted(per_day.items()))}")