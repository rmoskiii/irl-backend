#!/usr/bin/env python3
"""scene.neighbourhood_night — perspective rebuild (spec v1.1).

One-point perspective. The vanishing point sits INSIDE n-window-lit, so the
street geometry itself aims the camera at the target. Left and right terraces
recede obliquely toward a T-junction; the far terrace is frontal, which keeps
the target window undistorted for the 1.41:1 match cut into k-window.

Authoring canvas 2200x900. Camera frame 300,0,1600,900.
"""
import random

random.seed(1998)

VPX, VPY = 1240, 470
L_NEAR_X, L_GROUND, L_ROOF = 100, 838, 146
R_NEAR_X, R_GROUND, R_ROOF = 2100, 838, 164
FAR_BASE = 515          # junction depth t=0.877


def lerp(a, b, t):
    return a + (b - a) * t


def left(t):
    return lerp(L_NEAR_X, VPX, t), lerp(L_ROOF, VPY, t), lerp(L_GROUND, VPY, t)


def right(t):
    return lerp(R_NEAR_X, VPX, t), lerp(R_ROOF, VPY, t), lerp(R_GROUND, VPY, t)


def r(v):
    return round(v, 1)


def w(v, amt=2.5):
    return round(v + random.uniform(-amt, amt), 1)


def ln(d, sw, opacity=None, soft=False):
    cls = "ln soft" if soft else "ln"
    o = f' opacity="{opacity}"' if opacity else ""
    return f'<path class="{cls}" stroke-width="{round(sw,2)}" d="{d}"{o}/>'


def fill(d, cls, opacity=None):
    o = f' opacity="{opacity}"' if opacity else ""
    return f'<path class="{cls}" d="{d}"{o}/>'


BANDS = {}

# ----------------------------------------------------------------- background
b = [
    fill(f"M0 0 h2200 v186 q-550 {w(6)} -1100 {w(2)} q-550 {w(-6)} -1100 {w(2)} z", "sky"),
    fill(f"M0 186 q550 {w(4)} 1100 {w(1)} q550 {w(-4)} 1100 {w(1)} v146 "
         f"q-550 {w(5)} -1100 {w(2)} q-550 {w(-5)} -1100 {w(2)} z", "skym"),
    fill(f"M0 332 q550 {w(4)} 1100 {w(1)} q550 {w(-4)} 1100 {w(1)} v140 h-2200 z", "skyl"),
    fill("M1636 112 a30 30 0 1 0 0.1 0 z", "moon", "0.38"),
    # distant city: towers rise above the far terrace, which is why the kitchen
    # window can see a skyline. Flat silhouette, one token, no glow.
    fill("M760 470 v-96 h30 v-58 h26 v58 h22 v-132 h34 v132 h26 v-74 h30 v74 h34 v-40 h28 v40 "
         "h30 v-108 h32 v108 h26 v-64 h34 v64 h28 v-92 h30 v92 h34 v-46 h26 v46 h30 v-120 h32 "
         "v120 h28 v-70 h30 v70 h26 v-38 h34 v38 z", "dark", "0.92"),
    ln("M0 470 q550 -6 1100 -3 q550 3 1100 -1", 2.0, "0.45", soft=True),
]
BANDS["background"] = b

# --------------------------------------------------------------- architecture
a = []

L_T = [0.0, 0.19, 0.36, 0.505, 0.60, 0.70, 0.79, 0.877]
L_GAP = 4
L_RISE = [0, -18, 10, 0, -14, 6, -8]

for i in range(len(L_T) - 1):
    t0, t1 = L_T[i], L_T[i + 1]
    x0, ry0, gy0 = left(t0)
    x1, ry1, gy1 = left(t1)
    ry0 += L_RISE[i]
    ry1 += L_RISE[i] * (1 - t1)
    if i == L_GAP:
        a.append(fill(f"M{r(x0)} {r(gy0)} L{r(x1)} {r(gy1)} L{r(x1)} {r(ry1)} L{r(x0)} {r(ry0)} z",
                      "skyl", "0.3"))
        a.append(ln(f"M{r(x0)} {r(ry0)} L{r(x0)} {r(gy0)}", 3.0))
        a.append(ln(f"M{r(x1)} {r(ry1)} L{r(x1)} {r(gy1)}", 2.6, "0.8", soft=True))
        continue
    a.append(fill(f"M{r(x0)} {r(ry0)} L{r(x1)} {r(ry1)} L{r(x1)} {r(gy1)} L{r(x0)} {r(gy0)} z",
                  "brick" if i % 2 == 0 else "brickd"))
    h0, h1 = 26 * (1 - t0 * 0.55), 26 * (1 - t1 * 0.55)
    if t0 <= 0.55:
        a.append(fill(f"M{r(x0)} {r(ry0-h0)} L{r(x1)} {r(ry1-h1)} L{r(x1)} {r(ry1)} "
                      f"L{r(x0)} {r(ry0)} z", "roof"))
    a.append(ln(f"M{r(x0)} {r(ry0-h0)} L{r(x1)} {r(ry1-h1)}", max(5.0 - t0 * 2, 1.6)))
    a.append(ln(f"M{r(x1)} {r(ry1)} L{r(x1)} {r(gy1)}", max(3.0 - t1 * 1.4, 1.4), "0.85"))
    bc0, bc1 = 22 * (1 - t0 * 0.6), 22 * (1 - t1 * 0.6)
    a.append(ln(f"M{r(x0)} {r(gy0-bc0)} L{r(x1)} {r(gy1-bc1)}", max(3.4 - t0 * 1.4, 1.4), "0.85"))
    a.append(ln(f"M{r(x0)} {r(gy0)} L{r(x1)} {r(gy1)}", max(4.6 - t0 * 2, 1.8)))
    wins = ((0.26, i == 1),) if i >= 4 else ((0.26, i == 1), (0.64, False))
    for u, lit in wins:
        tu, tv = lerp(t0, t1, u), lerp(t0, t1, u + 0.22)
        xa, rya, gya = left(tu)
        xb, ryb, gyb = left(tv)
        a.append(fill(f"M{r(xa)} {r(lerp(rya,gya,0.24))} L{r(xb)} {r(lerp(ryb,gyb,0.24))} "
                      f"L{r(xb)} {r(lerp(ryb,gyb,0.52))} L{r(xa)} {r(lerp(rya,gya,0.52))} z",
                      "accd" if lit else "dark"))
        a.append(ln(f"M{r(xa)} {r(lerp(rya,gya,0.24))} L{r(xb)} {r(lerp(ryb,gyb,0.24))} "
                    f"L{r(xb)} {r(lerp(ryb,gyb,0.52))} L{r(xa)} {r(lerp(rya,gya,0.52))} z",
                    max(2.4 - tu, 1.2)))

R_T = [0.0, 0.195, 0.37, 0.515, 0.625, 0.72, 0.80, 0.877]
R_RISE = [0, 14, -16, 6, -10, 8, -6]
for i in range(len(R_T) - 1):
    t0, t1 = R_T[i], R_T[i + 1]
    x0, ry0, gy0 = right(t0)
    x1, ry1, gy1 = right(t1)
    ry0 += R_RISE[i]
    ry1 += R_RISE[i] * (1 - t1)
    a.append(fill(f"M{r(x0)} {r(ry0)} L{r(x1)} {r(ry1)} L{r(x1)} {r(gy1)} L{r(x0)} {r(gy0)} z",
                  "brickd" if i % 2 == 0 else "brick"))
    h0, h1 = 26 * (1 - t0 * 0.55), 26 * (1 - t1 * 0.55)
    if t0 <= 0.55:
        a.append(fill(f"M{r(x0)} {r(ry0-h0)} L{r(x1)} {r(ry1-h1)} L{r(x1)} {r(ry1)} "
                      f"L{r(x0)} {r(ry0)} z", "roof"))
    a.append(ln(f"M{r(x0)} {r(ry0-h0)} L{r(x1)} {r(ry1-h1)}", max(5.0 - t0 * 2, 1.6)))
    a.append(ln(f"M{r(x1)} {r(ry1)} L{r(x1)} {r(gy1)}", max(3.0 - t1 * 1.4, 1.4), "0.85"))
    bc0, bc1 = 22 * (1 - t0 * 0.6), 22 * (1 - t1 * 0.6)
    a.append(ln(f"M{r(x0)} {r(gy0-bc0)} L{r(x1)} {r(gy1-bc1)}", max(3.4 - t0 * 1.4, 1.4), "0.85"))
    a.append(ln(f"M{r(x0)} {r(gy0)} L{r(x1)} {r(gy1)}", max(4.6 - t0 * 2, 1.8)))
    wins = ((0.28, i == 0),) if i >= 4 else ((0.28, i == 0), (0.66, i == 2))
    for u, lit in wins:
        tu, tv = lerp(t0, t1, u), lerp(t0, t1, u + 0.22)
        xa, rya, gya = right(tu)
        xb, ryb, gyb = right(tv)
        a.append(fill(f"M{r(xa)} {r(lerp(rya,gya,0.26))} L{r(xb)} {r(lerp(ryb,gyb,0.26))} "
                      f"L{r(xb)} {r(lerp(ryb,gyb,0.54))} L{r(xa)} {r(lerp(rya,gya,0.54))} z",
                      "accd" if lit else "dark"))
        a.append(ln(f"M{r(xa)} {r(lerp(rya,gya,0.26))} L{r(xb)} {r(lerp(ryb,gyb,0.26))} "
                    f"L{r(xb)} {r(lerp(ryb,gyb,0.54))} L{r(xa)} {r(lerp(rya,gya,0.54))} z",
                    max(2.3 - tu, 1.2)))

FAR = [(980, 1060, 322), (1060, 1400, 180), (1400, 1480, 330)]
for x0, x1, ry in FAR:
    target = (x0 == 1060)
    a.append(fill(f"M{x0} {ry} h{x1-x0} v{FAR_BASE-ry} h-{x1-x0} z",
                  "brick" if target else "brickd"))
    a.append(fill(f"M{x0-8} {ry-16} h{x1-x0+16} v16 h-{x1-x0+16} z", "roof"))
    a.append(ln(f"M{x0-8} {ry-16} h{x1-x0+16}", 4.6 if target else 3.4))
    a.append(ln(f"M{x1} {ry} v{FAR_BASE-ry}", 2.4, "0.8", soft=True))
    if not target:
        a.append(ln(f"M{x0+34} {ry+40} h44 v52 h-44 z", 2.2))
    else:
        a.append(fill("M1318 148 h40 v32 h-40 z", "brickd"))
        a.append(ln("M1318 148 h40 v32", 2.6))
        a.append(fill("M1086 424 h54 v91 h-54 z", "dark"))
        a.append(ln("M1086 424 h54 v91", 3.0))
        a.append(fill("M1152 226 h64 v70 h-64 z", "dark"))
        a.append(ln("M1152 226 h64 v70 h-64 z", 2.8))
        a.append(fill("M1256 226 h64 v70 h-64 z", "dark"))
        a.append(ln("M1256 226 h64 v70 h-64 z", 2.8))
        a.append(ln("M1070 330 h320", 2.0, "0.45", soft=True))

# --- corridor detail (x1135-1591): the only strip mobile sees, centre of desktop
# target house: downpipe, eaves shadow, doorstep
a.append(ln("M1386 180 v335", 3.0, "0.7"))
a.append(fill("M1080 503 h66 v12 h-66 z", "kerb", "0.8"))
a.append(ln("M1080 503 h66", 2.2, "0.7", soft=True))
# right-hand neighbour gains a lit ground-floor window and a door
a.append(fill("M1412 380 h42 v50 h-42 z", "accd", "0.55"))
a.append(ln("M1412 380 h42 v50 h-42 z", 2.4))


# left-hand neighbour: door and sill course
a.append(fill("M1000 435 h38 v80 h-38 z", "dark"))
a.append(ln("M1000 435 h38 v80", 2.6))

# depth-plane boundary: where each terrace tail meets the far terrace
a.append(ln("M1100 515 v-190", 4.2))
a.append(ln("M1346 515 v-185", 4.2))
# target house facade construction
a.append(ln("M1060 296 h340", 2.0, "0.4", soft=True))
a.append(ln("M1060 420 h340", 1.8, "0.35", soft=True))
a.append(ln("M1060 180 v335", 3.0, "0.75"))
a.append(ln("M1400 180 v335", 3.0, "0.75"))
a.append(fill("M980 515 h500 v26 h-500 z", "pave"))
a.append(ln("M980 515 h500", 3.4))
a.append(ln("M980 541 h500", 2.4, "0.7", soft=True))
BANDS["architecture"] = a

# -------------------------------------------------- n-window-lit (1.4167 : 1)
WX, WY, WW, WH = 1155, 360, 170, 120
BANDS["_window"] = [
    fill(f"M{WX} {WY} h{WW} v{WH} h-{WW} z", "accd"),
    fill(f"M{WX+8} {WY+8} h{WW-16} v{WH-46} h-{WW-16} z", "lampwarm", "0.85"),
    fill(f"M{WX+8} {WY+WH-38} h{WW-16} v30 h-{WW-16} z", "acc", "0.55"),
    fill(f"M{WX+8} {WY+8} h34 q-6 52 2 {WH-16} h-36 z", "curt", "0.9"),
    ln(f"M{WX+42} {WY+8} q-6 52 2 {WH-16}", 2.0, "0.8", soft=True),
    ln(f"M{WX+WW//2} {WY} v{WH}", 3.0),
    ln(f"M{WX} {WY+int(WH*0.46)} h{WW}", 3.0),
    ln(f"M{WX} {WY} h{WW} v{WH} h-{WW} z", 3.4),
    fill(f"M{WX-10} {WY+WH} h{WW+20} v12 h-{WW+20} z", "brickd"),
    ln(f"M{WX-10} {WY+WH} h{WW+20} v12", 2.8),
    fill(f"M{WX-6} {WY+WH+12} q{WW//2+6} 24 {WW+12} 0 v46 q-{WW//2+6} 18 -{WW+12} 0 z",
         "acc", "0.11"),
]

# -------------------------------------------------- environmental_detail
e = []
for t, side in ((0.06, 'L'), (0.38, 'L'), (0.66, 'L'), (0.22, 'R'), (0.55, 'R')):
    x, _, gy = left(t) if side == "L" else right(t)
    x += 46 if side == "L" else -46
    h = 250 * (1 - t * 0.72)
    sw = max(5.0 * (1 - t * 0.6), 1.6)
    e.append(ln(f"M{r(x)} {r(gy)} v-{r(h)}", sw))
    arm = 26 * (1 - t * 0.6)
    e.append(ln(f"M{r(x)} {r(gy-h)} q4 -{r(arm*0.7)} {r(arm)} -{r(arm*0.8)}", max(sw * 0.9, 1.4)))
    lw = 30 * (1 - t * 0.6)
    e.append(fill(f"M{r(x+arm)} {r(gy-h-arm*0.8)} h{r(lw)} v{r(lw*0.62)} h-{r(lw)} z",
                  "lampwarm", "0.9"))

for side in ("L", "R"):
    pts = []
    for t in (0.0, 0.22, 0.42, 0.60, 0.74, 0.877):
        x, _, gy = left(t) if side == "L" else right(t)
        pts.append((x, gy - 34 * (1 - t * 0.7)))
    d = f"M{r(pts[0][0])} {r(pts[0][1])} " + " ".join(f"L{r(p[0])} {r(p[1])}" for p in pts[1:])
    xe, _, gye = left(0.877) if side == "L" else right(0.877)
    xs, _, gys = left(0.0) if side == "L" else right(0.0)
    e.append(fill(d + f" L{r(xe)} {r(gye)} L{r(xs)} {r(gys)} z", "fol"))
    e.append(ln(d, 3.0, "0.9"))

e.append(ln("M368 726 v-402", 5.4))
e.append(ln("M326 354 h84", 3.4))
e.append(ln("M368 324 q400 60 872 116", 1.8, "0.5", soft=True))

for t, side, bw in ((0.24, "L", 46), (0.30, "L", 46)):
    x, _, gy = left(t) if side == "L" else right(t)
    x += 30 if side == "L" else -70
    bh = 54 * (1 - t * 0.6)
    e.append(fill(f"M{r(x)} {r(gy-bh)} h{bw} v{r(bh)} h-{bw} z", "brickd"))
    e.append(ln(f"M{r(x)} {r(gy-bh)} h{bw} v{r(bh)}", 2.6))

xb, _, gyb = right(0.52)
e.append(ln(f"M{r(xb-96)} {r(gyb-14)} a15 15 0 1 0 0.1 0", 2.2))
e.append(ln(f"M{r(xb-48)} {r(gyb-14)} a15 15 0 1 0 0.1 0", 2.2))
e.append(ln(f"M{r(xb-92)} {r(gyb-16)} l20 -26 h22 l16 26", 2.0))

e.append(ln("M1174 515 v-12 q4 -3 4 -9 v-4 h6 v4 q0 6 4 9 v12", 1.6))
e.append(ln("M1190 515 v-12 q4 -3 4 -9 v-4 h6 v4 q0 6 4 9 v12", 1.6))

# lamp on the far pavement beside the target house
e.append(ln("M1412 515 v-150", 3.0))
e.append(ln("M1412 365 q3 -12 17 -13", 2.6))
e.append(fill("M1392 510 q38 -9 76 0 q-37 10 -76 0 z", "acc", "0.14"))

BANDS["environmental_detail"] = e

# ------------------------------------------------------------------- furniture
f = []
lx0, _, lgy0 = left(0.0)
lx1, _, lgy1 = left(0.877)
rx0, _, rgy0 = right(0.0)
rx1, _, rgy1 = right(0.877)

f.append(fill(f"M{r(lx0)} {r(lgy0)} L{r(lx1)} {r(lgy1)} L{r(lx1+34)} {r(lgy1+16)} "
              f"L{r(lx0+86)} {r(lgy0+36)} z", "pave"))
f.append(ln(f"M{r(lx0+86)} {r(lgy0+36)} L{r(lx1+34)} {r(lgy1+16)}", 5.0))
f.append(fill(f"M{r(rx0)} {r(rgy0)} L{r(rx1)} {r(rgy1)} L{r(rx1-34)} {r(rgy1+16)} "
              f"L{r(rx0-86)} {r(rgy0+36)} z", "pave"))
f.append(ln(f"M{r(rx0-86)} {r(rgy0+36)} L{r(rx1-34)} {r(rgy1+16)}", 5.0))
f.append(fill(f"M{r(lx0+86)} {r(lgy0+36)} L{r(lx1+34)} {r(lgy1+16)} L{r(lx1+37)} {r(lgy1+23)} "
              f"L{r(lx0+96)} {r(lgy0+76)} z", "kerb"))
f.append(fill(f"M{r(rx0-86)} {r(rgy0+36)} L{r(rx1-34)} {r(rgy1+16)} L{r(rx1-37)} {r(rgy1+23)} "
              f"L{r(rx0-96)} {r(rgy0+76)} z", "kerb"))
f.append(fill(f"M{r(lx0+96)} {r(lgy0+76)} L{r(lx1+37)} {r(lgy1+23)} L{r(rx1-37)} {r(rgy1+23)} "
              f"L{r(rx0-96)} {r(rgy0+76)} L2200 900 L0 900 z", "dark"))
f.append(ln(f"M{r(lx0+96)} {r(lgy0+76)} L{r(lx1+37)} {r(lgy1+23)}", 3.4, "0.9"))
f.append(ln(f"M{r(rx0-96)} {r(rgy0+76)} L{r(rx1-37)} {r(rgy1+23)}", 3.4, "0.9"))
f.append(ln("M1080 541 h60", 2.4, "0.6", soft=True))
f.append(ln("M1330 541 h56", 2.4, "0.6", soft=True))
f.append(ln("M1100 528 h246", 1.8, "0.4", soft=True))

# centre-line dashes converging on the vanishing point
for t, seg in ((0.02, 74), (0.20, 58), (0.38, 42), (0.54, 30), (0.68, 20)):
    y = lerp(900, 646, t)
    x = lerp(1110, VPX, t)
    f.append(ln(f"M{r(x)} {r(y)} L{r(x + (VPX-x)*0.14)} {r(y-seg)}",
                max(5.0 * (1 - t * 0.7), 1.4), "0.32"))

wx0, _, wgy0 = left(0.0)
wx1, _, wgy1 = left(0.30)
f.append(fill(f"M{r(wx0)} {r(wgy0-70)} L{r(wx1)} {r(wgy1-44)} L{r(wx1)} {r(wgy1)} "
              f"L{r(wx0)} {r(wgy0)} z", "brickd"))
f.append(ln(f"M{r(wx0)} {r(wgy0-70)} L{r(wx1)} {r(wgy1-44)}", 4.2))
f.append(ln(f"M{r(lerp(wx0,wx1,0.5))} {r(lerp(wgy0-70,wgy1-44,0.5))} "
            f"L{r(lerp(wx0,wx1,0.5))} {r(lerp(wgy0,wgy1,0.5))}", 1.6, "0.4", soft=True))

# second vehicle — mid-corridor depth cue, sits behind the near car.
# Deliberately simpler: no wheel arch highlight, no indicator, flatter cabin.
f.append(fill("M1349 776 q32 -44 104 -47 q74 -3 106 45 q23 5 24 27 q1 24 -21 27 "
              "q-107 8 -216 0 q-23 -3 -21 -27 q1 -23 24 -25 z", "carbody"))
f.append(ln("M1349 776 q32 -44 104 -47 q74 -3 106 45 q23 5 24 27 q1 24 -21 27 "
            "q-107 8 -216 0 q-23 -3 -21 -27 q1 -23 24 -25 z", 4.2))
f.append(ln("M1381 770 q24 -31 70 -33 q47 -2 68 33", 2.4))
f.append(ln("M1451 737 v33", 1.6, "0.55", soft=True))
f.append(ln("M1352 800 q104 8 208 0", 2.0, "0.5", soft=True))
f.append(fill("M1366 812 a18 18 0 1 0 0.1 0 z", "dark"))
f.append(fill("M1556 812 a18 18 0 1 0 0.1 0 z", "dark"))
f.append(ln("M1366 812 a18 18 0 1 0 0.1 0", 2.6))
f.append(ln("M1556 812 a18 18 0 1 0 0.1 0", 2.6))

f.append(fill("M1596 786 q46 -62 148 -66 q106 -4 150 64 q32 7 34 39 q2 34 -30 39 "
              "q-152 11 -306 0 q-32 -5 -30 -39 q2 -32 34 -37 z", "carbody"))
f.append(ln("M1596 786 q46 -62 148 -66 q106 -4 150 64 q32 7 34 39 q2 34 -30 39 "
            "q-152 11 -306 0 q-32 -5 -30 -39 q2 -32 34 -37 z", 5.0))
f.append(fill("M1642 780 q34 -44 102 -46 q69 -2 99 46 q-101 9 -201 0 z", "dark", "0.85"))
f.append(ln("M1642 780 q34 -44 102 -46 q69 -2 99 46", 2.8))
f.append(ln("M1744 734 v46", 1.8, "0.6", soft=True))
f.append(fill("M1610 834 a23 23 0 1 0 0.1 0 z", "dark"))
f.append(fill("M1858 834 a23 23 0 1 0 0.1 0 z", "dark"))
f.append(ln("M1610 834 a23 23 0 1 0 0.1 0", 3.0))
f.append(ln("M1858 834 a23 23 0 1 0 0.1 0", 3.0))
f.append(fill(f"M{r(wx0)} {r(wgy0)} L{r(wx1)} {r(wgy1)} L{r(wx1)} {r(wgy1+18)} "
              f"L{r(wx0)} {r(wgy0+30)} z", "shad", "0.45"))
# ground contact — without this the terraces float
for side in ("L", "R"):
    p0 = left(0.0) if side == "L" else right(0.0)
    p1 = left(0.66) if side == "L" else right(0.66)
    off = 26
    f.append(fill(f"M{r(p0[0])} {r(p0[2])} L{r(p1[0])} {r(p1[2])} "
                  f"L{r(p1[0])} {r(p1[2]+off*0.35)} L{r(p0[0])} {r(p0[2]+off)} z", "shad", "0.5"))


# junction ground detail, inside the corridor
f.append(ln("M1346 525 q40 4 78 10", 2.4, "0.7"))
f.append(ln("M1190 560 h34", 2.0, "0.45", soft=True))
f.append(ln("M1195 566 h24", 1.4, "0.35", soft=True))

BANDS["furniture"] = f

# ------------------------------------------------------- foreground geometry
g = [
    # trunk, leaning slightly into frame, running off the bottom edge
    fill("M120 900 q46 -246 26 -400 q-12 -78 -46 -134 h104 q-28 64 -24 138 "
         "q16 154 30 396 z", "fold"),
    ln("M132 900 q44 -250 24 -402 q-12 -78 -46 -134", 6.6),
    ln("M188 900 q-16 -244 -14 -394 q2 -78 22 -138", 5.0),
    # primary limbs, reaching right and up, thinning as they go
    ln("M150 470 q104 -38 190 -122 q66 -64 96 -156", 5.4),
    ln("M162 372 q70 -54 104 -140 q22 -56 26 -108", 4.2),
    ln("M258 348 q68 -22 112 -74", 3.2),
    ln("M300 268 q52 -34 74 -86", 2.6),
    ln("M344 198 q40 -32 54 -76", 2.0),
    # canopy: asymmetric silhouette, heavier low-left, breaking the top and
    # left edges of the canvas so it reads as passed rather than pictured
    fill("M-40 236 q-14 -102 78 -134 q26 -96 118 -84 q42 -74 122 -46 q66 -58 118 6 "
         "q88 -22 92 62 q64 20 30 90 q40 62 -34 84 q-14 70 -96 56 q-40 54 -110 22 "
         "q-64 44 -124 -6 q-88 24 -122 -42 q-84 -4 -72 -8 z", "fol", "0.96"),
    ln("M-40 236 q-14 -102 78 -134 q26 -96 118 -84 q42 -74 122 -46 q66 -58 118 6 "
       "q88 -22 92 62 q64 20 30 90 q40 62 -34 84 q-14 70 -96 56 q-40 54 -110 22 "
       "q-64 44 -124 -6 q-88 24 -122 -42", 3.0, "0.5"),
    ln("M292 150 q76 -58 146 -10 q52 34 4 76 q-64 52 -134 12 q-58 -36 -16 -78 z", 2.2, "0.4"),
    # near hedge along the lower edge, following the road's recession
    fill("M0 900 q180 -96 420 -74 q220 20 372 62 v12 h-792 z", "fold"),
    ln("M0 826 q180 -96 420 -74 q220 20 372 62", 4.6),
]
for hx in range(60, 740, 138):
    g.append(ln(f"M{hx} {w(846,16)} q10 -20 {w(18,3)} {w(-26,4)}", 1.8, "0.4", soft=True))
BANDS["foreground_geometry"] = g

# ------------------------------------------------------------------- assemble
TOKENS = """
/* @tokens-begin */
:root {
  /* line — shared craft language, unchanged */
  --irx-line:          #241D19;
  --irx-line-soft:     #3B302A;
  --irx-shadow:        #2A231E;

  /* sky — reused verbatim from scene.kitchen's window. The exterior and the
     kitchen look at the same sky from opposite sides. */
  --irx-sky-high:      #334051;
  --irx-sky-mid:       #4D4656;
  --irx-sky-low:       #785A4F;
  --irx-outside-dark:  #2A333E;
  --irx-curtain:       #424E56;

  /* accent — neighbourhood district, warm light only */
  --irx-accent:        #FFC15E;
  --irx-accent-dim:    #C89A4E;
  --irx-lamp-warm:     #F2C77E;
  --irx-cool-spill:    #7E93A8;

  /* new — neighbourhood exterior. Values held in the kitchen's large-area
     luminance band (L 83-116) so the L=30 linework still reads. Night comes
     from hue, silhouette and the vignette, not from dark fills. */
  --irx-neighbourhood-brick:        #7A6459;
  --irx-neighbourhood-brick-dark:   #64514A;
  --irx-neighbourhood-roof:         #55606B;
  --irx-neighbourhood-pavement:     #5A616A;
  --irx-neighbourhood-kerb:         #3C424A;
  --irx-neighbourhood-foliage:      #46584B;
  --irx-neighbourhood-foliage-dark: #35463A;
  --irx-neighbourhood-car:          #5A5F66;

  /* stroke weights */
  --irx-stroke-xheavy: 6.6;
  --irx-stroke-heavy:  5;
  --irx-stroke:        3.4;
  --irx-stroke-fine:   2.1;
  --irx-stroke-hair:   1.4;
}
/* @tokens-end */
.ln    { stroke: var(--irx-line); fill: none; stroke-linecap: round; stroke-linejoin: round; }
.soft  { stroke: var(--irx-line-soft); }
.sky   { fill: var(--irx-sky-high); }
.skym  { fill: var(--irx-sky-mid); }
.skyl  { fill: var(--irx-sky-low); }
.dark  { fill: var(--irx-outside-dark); }
.moon  { fill: var(--irx-lamp-warm); }
.brick { fill: var(--irx-neighbourhood-brick); }
.brickd{ fill: var(--irx-neighbourhood-brick-dark); }
.roof  { fill: var(--irx-neighbourhood-roof); }
.pave  { fill: var(--irx-neighbourhood-pavement); }
.kerb  { fill: var(--irx-neighbourhood-kerb); }
.fol   { fill: var(--irx-neighbourhood-foliage); }
.fold  { fill: var(--irx-neighbourhood-foliage-dark); }
.acc   { fill: var(--irx-accent); }
.accd  { fill: var(--irx-accent-dim); }
.lampwarm { fill: var(--irx-lamp-warm); }
.curt  { fill: var(--irx-curtain); }
.carbody { fill: var(--irx-neighbourhood-car); }
.shad  { fill: var(--irx-shadow); }
"""

DEFS = """
  <filter id="n-grain" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.82" numOctaves="3" stitchTiles="stitch"/>
    <feColorMatrix type="saturate" values="0"/>
  </filter>
  <radialGradient id="n-vignette" cx="56%" cy="50%" r="70%">
    <stop offset="0.48" stop-color="#000000" stop-opacity="0"/>
    <stop offset="1" stop-color="#000000" stop-opacity="0.55"/>
  </radialGradient>
  <radialGradient id="n-nightspill" cx="56%" cy="52%" r="44%">
    <stop offset="0" stop-color="var(--irx-cool-spill)" stop-opacity="0.10"/>
    <stop offset="1" stop-color="var(--irx-cool-spill)" stop-opacity="0"/>
  </radialGradient>
"""


def band(bid, items, overscan):
    return f'<g id="{bid}" data-overscan="{overscan}">\n  ' + "\n  ".join(items) + "\n</g>"


parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2200 900" width="2200" height="900"',
    '     id="scene.neighbourhood_night"',
    '     data-asset="scene.neighbourhood_night"',
    '     data-web-only="true"',
    '     data-time="night"',
    '     data-occlusion-line="600"',
    '     data-camera-frame="300,0,1600,900"',
    '     data-authoring-canvas="2200,900"',
    f'     data-vanishing-point="{VPX},{VPY}">',
    f"<style>{TOKENS}</style>",
    f"<defs>{DEFS}</defs>",
    band("background", BANDS["background"], 300),
    band("architecture", BANDS["architecture"], 180),
    '<g id="n-window-lit" data-camera-anchor="primary" data-aperture="1155,360,170,120">\n  '
    + "\n  ".join(BANDS["_window"]) + "\n</g>",
    band("environmental_detail", BANDS["environmental_detail"], 200),
    band("furniture", BANDS["furniture"], 140),
    '<g id="foreground">',
    '  <g id="n-near-geometry" data-parallax="true" data-overscan="100">\n    '
    + "\n    ".join(BANDS["foreground_geometry"]) + "\n  </g>",
    '  <g id="n-atmosphere" data-parallax="false">',
    '    <rect x="0" y="0" width="2200" height="900" fill="url(#n-nightspill)" pointer-events="none"/>',
    '    <rect x="0" y="0" width="2200" height="900" fill="url(#n-vignette)" pointer-events="none"/>',
    '    <rect x="0" y="0" width="2200" height="900" filter="url(#n-grain)" opacity="0.07"'
    ' style="mix-blend-mode:multiply" pointer-events="none"/>',
    "  </g>",
    "</g>",
    "</svg>",
    ]

open("scene_neighbourhood_night.svg", "w").write("\n".join(parts))
print("written")