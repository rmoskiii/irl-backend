"""Derive figure_c's four remaining registers from the APPROVED open baseline.

    PROVENANCE ONLY. DO NOT RE-RUN.

    The four registers this produced - guarded, heavy, set, squared - were
    reviewed and LOCKED on the 2B.7 character checkpoint, together with the
    `open` baseline they derive from. They are committed assets. This file is
    kept as the record of how they were made, not as a build step.

    If `figure_c.register.open.svg` is ever changed, re-running this would
    silently regenerate all four from the new baseline and overwrite locked,
    approved artwork. Any change to the baseline requires explicit
    re-baselining and review of all five registers, not a re-run.

Everything that carries identity - cranium, hair, ears, skin tones, neck
column, forehead line, nose - is copied byte-for-byte. Only the elements the
register contract says carry a register change are substituted: brows, lids,
pupils, under-eye creases, nasolabial strength, mouth, jaw tension, and tilt.

Tilts come from the locked matrix and are not invented here:
    open 0 | guarded -5 | heavy -10 | set -15 | squared +8

Any substitution string that does not match the baseline raises, so a silent
no-op is impossible - the failure mode Richard flagged as a known risk.
"""
import re

BASE = open("figure_c.register.open.svg").read()

# --- baseline fragments, quoted exactly ------------------------------------
BROW_L  = '<path class="ln" stroke-width="2.7" d="M64 95 q17 -6 34 -2" opacity="0.85"/>'
BROW_R  = '<path class="ln" stroke-width="2.7" d="M136 95 q-17 -6 -34 -2" opacity="0.85"/>'
LID_L   = '<path class="ln" stroke-width="3.2" d="M68 110 q13 -7 26 -1"/>'
LID_R   = '<path class="ln" stroke-width="3.2" d="M106 109 q13 -6 26 1"/>'
LOW_L   = '<path class="ln" stroke-width="1.4" d="M69 116 q12 4 24 0" opacity="0.7"/>'
LOW_R   = '<path class="ln" stroke-width="1.4" d="M107 116 q12 4 24 -1" opacity="0.7"/>'
PUP_L   = '<circle cx="81" cy="112" r="3.0" fill="var(--irx-line)"/>'
PUP_R   = '<circle cx="119" cy="112" r="3.0" fill="var(--irx-line)"/>'
CRE_L   = '<path class="ln" stroke-width="1.4" d="M70 126 q12 4 24 -1" opacity="0.18"/>'
CRE_R   = '<path class="ln" stroke-width="1.4" d="M107 126 q12 4 24 -1" opacity="0.18"/>'
NAS_L   = '<path class="ln" stroke-width="1.6" d="M88 150 q-5 12 -3 22" opacity="0.22"/>'
NAS_R   = '<path class="ln" stroke-width="1.6" d="M116 151 q5 12 3 21" opacity="0.18"/>'
LIP     = '<path d="M84 163 q16 -5 32 0 q-2 8 -16 8 q-14 0 -16 -8 z" fill="var(--irx-lip-c)"/>'
MOUTH   = '<path class="ln" stroke-width="2.8" d="M84 165 h32"/>'
JAW_L   = 'd="M97 201 q-11 -1 -21 -9 q-14 -10 -21 -33" opacity="0.34"'
JAW_R   = 'd="M103 201 q11 -1 21 -9 q14 -10 21 -33" opacity="0.20"'

REGISTERS = {
    "guarded": dict(tilt=-5, note="""'guarded' carried by: head tilted 5 degrees off level, brows dropped a little
     and flattened, upper lids slightly lower, mouth narrowed and compressed.
     This is Ray conceding a point or being pleasant without being present -
     'Yeah. Fine. Send that.' Nothing in the face is unfriendly, which is the
     difficulty of the register: polite and absent look the same.""", subs={
        BROW_L: '<path class="ln" stroke-width="2.7" d="M64 97 q17 -5 34 -2" opacity="0.90"/>',
        BROW_R: '<path class="ln" stroke-width="2.7" d="M136 97 q-17 -5 -34 -2" opacity="0.90"/>',
        LID_L:  '<path class="ln" stroke-width="3.2" d="M68 112 q13 -6 26 -1"/>',
        LID_R:  '<path class="ln" stroke-width="3.2" d="M106 111 q13 -5 26 1"/>',
        PUP_L:  '<circle cx="81" cy="114" r="3.0" fill="var(--irx-line)"/>',
        PUP_R:  '<circle cx="119" cy="114" r="3.0" fill="var(--irx-line)"/>',
        NAS_L:  '<path class="ln" stroke-width="1.6" d="M88 150 q-5 12 -3 22" opacity="0.26"/>',
        NAS_R:  '<path class="ln" stroke-width="1.6" d="M116 151 q5 12 3 21" opacity="0.22"/>',
        LIP:    '<path d="M86 163 q14 -4 28 0 q-2 7 -14 7 q-12 0 -14 -7 z" fill="var(--irx-lip-c)"/>',
        MOUTH:  '<path class="ln" stroke-width="2.8" d="M86 165 h28"/>',
    }),

    "heavy": dict(tilt=-10, note="""'heavy' carried by: head tilted 10 degrees, upper lids well down, brow ends
     falling away outward, under-eye creases at full strength, mouth slack and
     turned a fraction at the corners. Tired and distracted resolve here - a man
     four deliveries into a bad month, not an unhappy one.""", subs={
        BROW_L: '<path class="ln" stroke-width="2.7" d="M64 98 q17 -3 34 -4" opacity="0.78"/>',
        BROW_R: '<path class="ln" stroke-width="2.7" d="M136 98 q-17 -3 -34 -4" opacity="0.78"/>',
        LID_L:  '<path class="ln" stroke-width="3.4" d="M68 114 q13 -4 26 0"/>',
        LID_R:  '<path class="ln" stroke-width="3.4" d="M106 113 q13 -4 26 1"/>',
        LOW_L:  '<path class="ln" stroke-width="1.4" d="M70 119 q12 3 24 0" opacity="0.7"/>',
        LOW_R:  '<path class="ln" stroke-width="1.4" d="M108 119 q12 3 24 -1" opacity="0.7"/>',
        PUP_L:  '<circle cx="81" cy="117" r="2.9" fill="var(--irx-line)"/>',
        PUP_R:  '<circle cx="119" cy="117" r="2.9" fill="var(--irx-line)"/>',
        CRE_L:  '<path class="ln" stroke-width="1.6" d="M70 128 q12 5 24 -1" opacity="0.32"/>',
        CRE_R:  '<path class="ln" stroke-width="1.6" d="M107 128 q12 5 24 -1" opacity="0.32"/>',
        NAS_L:  '<path class="ln" stroke-width="1.6" d="M88 150 q-6 13 -4 24" opacity="0.30"/>',
        NAS_R:  '<path class="ln" stroke-width="1.6" d="M116 151 q6 13 4 23" opacity="0.26"/>',
        LIP:    '<path d="M85 164 q15 -4 30 1 q-3 8 -15 8 q-13 0 -15 -9 z" fill="var(--irx-lip-c)"/>',
        MOUTH:  '<path class="ln" stroke-width="2.6" d="M85 166 q15 3 30 -1"/>',
        JAW_L:  'd="M97 201 q-11 -1 -21 -9 q-14 -10 -21 -33" opacity="0.26"',
        JAW_R:  'd="M103 201 q11 -1 21 -9 q14 -10 21 -33" opacity="0.16"',
    }),

    "set": dict(tilt=-15, note="""'set' carried by: head at the far end of the tilt range, brows down and level
     against the eye, lids narrowed from both directions, mouth a firm straight
     line, jaw at full weight. Flat, immovable and distant resolve here. It is
     the only register where Ray's face is closed, and it is doing the work on
     the beat where he says the client call is at nine and there is no
     Thursday.""", subs={
        BROW_L: '<path class="ln" stroke-width="3.0" d="M64 99 q17 -4 34 -1" opacity="0.95"/>',
        BROW_R: '<path class="ln" stroke-width="3.0" d="M136 99 q-17 -4 -34 -1" opacity="0.95"/>',
        LID_L:  '<path class="ln" stroke-width="3.4" d="M68 112 q13 -5 26 -1"/>',
        LID_R:  '<path class="ln" stroke-width="3.4" d="M106 111 q13 -4 26 1"/>',
        LOW_L:  '<path class="ln" stroke-width="1.6" d="M69 118 q12 3 24 0" opacity="0.8"/>',
        LOW_R:  '<path class="ln" stroke-width="1.6" d="M107 118 q12 3 24 -1" opacity="0.8"/>',
        PUP_L:  '<circle cx="81" cy="115" r="3.0" fill="var(--irx-line)"/>',
        PUP_R:  '<circle cx="119" cy="115" r="3.0" fill="var(--irx-line)"/>',
        NAS_L:  '<path class="ln" stroke-width="1.6" d="M88 150 q-5 12 -3 22" opacity="0.28"/>',
        NAS_R:  '<path class="ln" stroke-width="1.6" d="M116 151 q5 12 3 21" opacity="0.24"/>',
        LIP:    '<path d="M85 164 q15 -3 30 0 q-2 6 -15 6 q-13 0 -15 -6 z" fill="var(--irx-lip-c)"/>',
        MOUTH:  '<path class="ln" stroke-width="3.0" d="M85 166 h30"/>',
        JAW_L:  'd="M97 201 q-11 -1 -21 -9 q-14 -10 -21 -33" opacity="0.44"',
        JAW_R:  'd="M103 201 q11 -1 21 -9 q14 -10 21 -33" opacity="0.28"',
    }),

    "squared": dict(tilt=8, note="""'squared' carried by: head tilted the other way - the only register on the
     positive side of the range, which is most of why it separates from the
     other four - brows drawn in and slightly up at the inner ends, eyes open
     and direct, mouth held. Pressed resolves here: Ray asking for the QA
     signature with the laptop turned round. He is not angry. He is a man who
     needs this to be over, and the brow is where that shows.""", subs={
        BROW_L: '<path class="ln" stroke-width="3.0" d="M66 93 q16 -6 32 1" opacity="0.95"/>',
        BROW_R: '<path class="ln" stroke-width="3.0" d="M134 93 q-16 -6 -32 1" opacity="0.95"/>',
        LID_L:  '<path class="ln" stroke-width="3.2" d="M67 108 q14 -8 27 -1"/>',
        LID_R:  '<path class="ln" stroke-width="3.2" d="M105 107 q14 -7 27 1"/>',
        PUP_L:  '<circle cx="81" cy="111" r="3.2" fill="var(--irx-line)"/>',
        PUP_R:  '<circle cx="119" cy="111" r="3.2" fill="var(--irx-line)"/>',
        NAS_L:  '<path class="ln" stroke-width="1.6" d="M88 150 q-5 12 -3 22" opacity="0.28"/>',
        NAS_R:  '<path class="ln" stroke-width="1.6" d="M116 151 q5 12 3 21" opacity="0.24"/>',
        LIP:    '<path d="M85 163 q15 -4 30 0 q-2 7 -15 7 q-13 0 -15 -7 z" fill="var(--irx-lip-c)"/>',
        MOUTH:  '<path class="ln" stroke-width="2.9" d="M85 165 h30"/>',
        JAW_L:  'd="M97 201 q-11 -1 -21 -9 q-14 -10 -21 -33" opacity="0.38"',
    }),
}

# glabella lines: the one element `squared` adds that no other register has
GLABELLA = ('  <!-- glabella: two short lines between the brows. The only element any\n'
            '       register adds rather than substitutes, and it is what makes pressed\n'
            '       read as pressed rather than merely awake. -->\n'
            '  <path class="ln" stroke-width="1.5" d="M96 90 q-1 8 0 13" opacity="0.30"/>\n'
            '  <path class="ln" stroke-width="1.5" d="M104 90 q1 8 0 13" opacity="0.26"/>\n')

OPEN_NOTE = """'open' carried by: head level and squared to camera, direct gaze, brows
     relaxed and slightly lifted, mouth closed and level. Ray in this register
     is at ease - but the face must not editorialise, so no smile. The warmth
     is in the prose, not drawn onto him."""

for name, spec in REGISTERS.items():
    s = BASE
    for old, new in spec["subs"].items():
        if s.count(old) != 1:
            raise SystemExit(f"{name}: baseline fragment matched {s.count(old)} times, "
                             f"expected 1 -> {old[:60]}")
        s = s.replace(old, new)
    if name == "squared":
        anchor = '  <!-- eyes: deep set under the brow, with a crease beneath each -->'
        assert s.count(anchor) == 1
        s = s.replace(anchor, GLABELLA + anchor)
    s = s.replace('id="figure_c.register.open"', f'id="figure_c.register.{name}"')
    s = s.replace('data-register="open"', f'data-register="{name}"')
    s = s.replace('data-register-rotate="0"', f'data-register-rotate="{spec["tilt"]}"')
    s = s.replace("IRX 2B.7 = figure_c register: open (Ray).",
                  f"IRX 2B.7 = figure_c register: {name} (Ray).")
    s = s.replace("     TILT 0. From the locked matrix",
                  f"     TILT {spec['tilt']}. From the locked matrix")
    assert OPEN_NOTE in s
    s = s.replace(OPEN_NOTE, spec["note"].strip())
    s = s.replace("Derived from the approved `open` baseline: cranium, hair, ears, skin, neck\n",
                  "")
    marker = ("     Derived from the APPROVED `open` baseline. Cranium, hair, ears, skin\n"
              "     tones, neck column, forehead line and nose are copied byte for byte;\n"
              "     only brows, lids, pupils, creases, nasolabial strength, mouth, jaw\n"
              "     weight and tilt differ. Identity does not change between registers.\n\n")
    s = s.replace("     'guarded' carried", marker + "     'guarded' carried")
    s = s.replace("     'heavy' carried", marker + "     'heavy' carried")
    s = s.replace("     'set' carried", marker + "     'set' carried")
    s = s.replace("     'squared' carried", marker + "     'squared' carried")
    open(f"figure_c.register.{name}.svg", "w").write(s)
    print(f"wrote figure_c.register.{name}.svg  tilt {spec['tilt']:+d}  "
          f"{len(spec['subs'])} substitutions")