#!/usr/bin/env python3
"""Erzeugt rondofeed.json, das Kommandoskript fuer solidcraft-cli.

Aufbau:  python3 build.py && solidcraft-cli run rondofeed.json --save rondofeed.sc
Koordinaten: Ursprung Bodenmitte, -Y ist vorn (Auslauf), Z nach oben. Masse in mm.
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).parent

# Gehaeuse
W = 206            # Sechskant, Schluesselweite aussen in Y (flache Wand vorn und hinten), Ecken zeigen nach +-X
WALL = 3
FLOOR = 3
BASE_H = 112       # Oberkante Unterteil
PLATE_T = 4
TOP = BASE_H + PLATE_T
CORNER_R = 6
COS30 = math.cos(math.radians(30))

# Schrauben
M3_CLEAR = 3.4
INSERT_D = 4.0     # Gewindeeinsatz M3, am Einsatz pruefen
INSERT_DEPTH = 6

# Scheibe
DISC_D = 200
DISC_T = 10
DISC_GAP = 0.5
CY = 0             # Scheibenmitte
HOLE_D = 15
R_INNER = 70
R_OUTER = 87
N_RING = 24        # Loecher je Ring, ergibt 48 Positionen
EXTRA_DISCS = ((12, 30), (10, 35))  # (Lochdurchmesser, Loecher je Ring)
SHAFT_D = 5.2      # NEMA-Welle 5 mm plus Druckzugabe
DZ = TOP + DISC_GAP

# Motor, Lochbild und Pilot aus nema17_disc.sc
NEMA_SPACING = 31
PILOT_D = 22.4
PILOT_DEPTH = 2.2
NEMA_BLOCK = 50
NEMA_BLOCK_H = 6
MOTOR_FACE = BASE_H - NEMA_BLOCK_H
NEMA_L = 48
HEAD_D = 6.0
HEAD_DEPTH = 3.5

# Abdeckung
LID_TOP_T = 2.5
LID_Z = DZ + DISC_T + 0.5
LID_HOLE_D = 12    # Loch fuer das Wellenende, Welle Ø5 ragt etwa 0,5 mm ueber den Deckel
LID_BOSS_D = 14    # Dom im Deckel, in jeder Ecke, nimmt den Magneten auf
POST_DEGS = range(0, 360, 60)  # alle 6 Ecken: eine M3x8 haelt die Platte, ein Magnet im Deckel darueber haelt den Deckel
MAGNET_D = 6       # Neodym-Scheibe Ø6 x 2, haelt am Stahlkopf der Schraube darunter
MAGNET_T = 2
MAGNET_FIT = 0.25  # Zugabe im Durchmesser und in der Tiefe
HEAD_CB_D = 6.5    # Senkung fuer den Schraubenkopf in der Platte
HEAD_CB_DEPTH = 3

# Rutsche: rundes Rohr, Achse faellt nach vorn. Liegt beim Druck mit der Plattenseite auf dem Bett.
CHUTE_DEG = 40
CHUTE_D = 24       # innen
CHUTE_WALL = 2.5
CHUTE_Y0 = -78.5   # Achse an der Plattenunterseite, Mitte zwischen beiden Auslaessen
SPOUT_Y = -122
AX = (0, -math.cos(math.radians(CHUTE_DEG)), -math.sin(math.radians(CHUTE_DEG)))
EAR_X = 28         # Platte innen an der Frontwand, Schrauben M3 von aussen, Mutter innen
EAR_Z = 90
IR_D = 5.2
IR_Y = -85


# Netzteil LRS-35/50 (Case 239A), hochkant an der rechten Wand, Klemmen zeigen nach hinten
PSU = (99, 82, 30) # Laenge in Y, Breite in X, Dicke in Z, liegt flach auf dem Boden, Klemmen zeigen nach +Y
PSU_C = (27, -26)  # Mitte in x, y
PSU_GAP = 5        # Abstand zum Boden, Hoehe der Auflagen
PSU_HOLE_L = (20.5, 75.5)  # ab Klemmenende
PSU_HOLE_D = 4.2
PSU_Y1 = PSU_C[1] + PSU[0] / 2   # Klemmenende
PSU_Z0 = FLOOR + PSU_GAP
COVER_Z = 8

# Luftschlitze am Netzteil: Boden unten, Seitenwand um 45 Grad gedreht und druckbar ohne Stuetzmaterial
VENT_W = 4
VENT_L = 30
FLOOR_VENT_X = (-28, -16, 16, 28)  # Bodenschlitze unter dem Netzteil, neben den Auflagen

# Elektroniktraeger
CARR_A = (-86, -32, -22, 42)  # x0, y0, x1, y1, unter der Loetplatine
CARR_B = [(-66, 41), (-3, 41), (-3, 52), (-14, 52), (-14, 99.5), (-45, 99.5), (-45, 70), (-66, 70)]  # unter dem Pico
CARR_HOLES = [(-80, -26), (-24, -27), (-10, 46), (-60, 50)]  # alle ausserhalb von Pico und Loetplatine
CARR_Z = 10
CARR_T = 3
PICO_C = (-34, 73)
PICO_DX = 47       # aus pico_case.sc, entlang Y verbaut
PICO_DY = 11.4
PICO_STANDOFF = 2.4
PERF_C = (-52, 8)
PERF_L = 44        # Adafruit Perma-Proto Quarter-Size, lange Seite quer in X, die 2 Loecher liegen auf der kurzen Achse (Y)
PERF_W = 55
PERF_HOLE_DY = 35.6  # 2 Loecher M3, Lage mittig auf der Laengsachse angenommen, am Board pruefen

# Rueckwand
IEC_C = (0, 50)    # x, z
IEC_CUT = (27.5, 47.5)
USB_C = (-34, 18)
USB_CUT = (13, 10)

cmds = []
_n = 0


def add(command, **params):
    cmds.append({"command": command, "params": params})


def name(prefix):
    global _n
    _n += 1
    return f"{prefix}_{_n}"


def box(x0, y0, z0, x1, y1, z1, op=None, target=None, body=None, label="box"):
    p = dict(length=x1 - x0, width=y1 - y0, height=z1 - z0, corner=[x0, y0, z0], name=name(label))
    if op:
        p.update(operation=op, targets=[target])
    if body:
        p["body_name"] = body
    add("solid.box", **p)
    return p["name"]


def cyl(d, base, h, op=None, target=None, body=None, axis=None, label="cyl"):
    p = dict(diameter=d, height=h, base=list(base), name=name(label))
    if axis:
        p["axis"] = axis
    if op:
        p.update(operation=op, targets=[target])
    if body:
        p["body_name"] = body
    add("solid.cylinder", **p)
    return p["name"]


def prism(pts, z0, z1, op=None, target=None, body=None, label="prism"):
    """Gerades Prisma ueber dem Polygon pts (x, y) von z0 bis z1."""
    sk = name(label + "_sk")
    add("sketch.create", plane="XY", offset=z0, name=sk)
    add("sketch.line", points=[[round(x, 4), round(y, 4)] for x, y in pts], closed=True)
    add("sketch.finish")
    p = dict(sketch=sk, distance=z1 - z0, name=name(label))
    if op:
        p.update(operation=op, targets=[target])
    elif body:
        p.update(operation="new")
    if body:
        p["body_name"] = body
    add("solid.extrude", **p)


def hexagon(apothem):
    r = apothem / COS30
    return [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in range(0, 360, 60)]


def polar(deg, r):
    return (r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg)))


def wall_slot(a0, c, z):
    """Schneidet einen um 45 Grad gedrehten Schlitz durch die Wand zwischen den Ecken a0 und a0+60 Grad.
    Skizzenachsen: (s, z), s entlang der Wand ab der Ecke a0."""
    d = math.sqrt(0.5)
    u, v = VENT_L / 2, VENT_W / 2
    pts = [(c + a * d - b_ * d, z + a * d + b_ * d) for a, b_ in ((-u, -v), (u, -v), (u, v), (-u, v))]
    sk = name("slot")
    n = math.radians(a0 + 30)
    px, py = polar(a0, R_IN)
    ox, oy = px + math.cos(n) * WALL / 2, py + math.sin(n) * WALL / 2
    add("sketch.create", plane={"origin": [ox, oy, 0], "x_dir": [-math.sin(n), math.cos(n), 0], "y_dir": [0, 0, 1]},
        name=sk)
    add("sketch.line", points=[list(p) for p in pts], closed=True)
    add("sketch.finish")
    add("solid.extrude", sketch=sk, distance=WALL + 2, direction="symmetric", name=name("slot_ex"),
        operation="cut", targets=["Base"])


def chute_axis(y):
    """Punkt der Rohrachse bei gegebenem y."""
    t = (CHUTE_Y0 - y) / -AX[1]
    return (0, y, BASE_H + AX[2] * t)


# ---------- Parameter, zur Dokumentation in der Parameterliste ----------
for n, v, c in [
    ("disc_d", DISC_D, "Scheibendurchmesser"),
    ("disc_t", DISC_T, "Scheibendicke"),
    ("hole_d", HOLE_D, "Futterloch"),
    ("shaft_d", SHAFT_D, "Wellenbohrung"),
    ("pilot_d", PILOT_D, "NEMA-Pilot"),
    ("pilot_depth", PILOT_DEPTH, "NEMA-Pilot Tiefe"),
    ("nema_spacing", NEMA_SPACING, "NEMA-Lochbild"),
    ("screw_d", M3_CLEAR, "M3 Durchgang"),
    ("insert_d", INSERT_D, "M3 Gewindeeinsatz"),
]:
    add("parameters.add", name=n, expression=str(v), unit="mm", comment=c)

# ---------- Unterteil ----------
h = W / 2          # Schluesselweite / 2 aussen
in_ = h - WALL
R_OUT = h / COS30
R_IN = in_ / COS30
prism(hexagon(h), 0, BASE_H, body="Base", label="base")
add("solid.fillet", edges=[[*polar(a_, R_OUT), 50] for a_ in range(0, 360, 60)], radius=CORNER_R)
prism(hexagon(in_), FLOOR, BASE_H + 1, op="cut", target="Base", label="hollow")

POST_D = 6.93      # Mitte der Dome 6 mm von beiden Innenwaenden
POST_R = 8
POST_HOLES = [polar(a_, R_IN - POST_D) for a_ in POST_DEGS]
for x, y in POST_HOLES:  # Dom wird in der Ecke in die Wand gezogen, Innenkante rund
    cyl(2 * POST_R, (x, y, FLOOR - 0.5), BASE_H - FLOOR + 0.5, "join", "Base", label="post")
    cyl(INSERT_D, (x, y, BASE_H - INSERT_DEPTH), INSERT_DEPTH + 1, "cut", "Base", label="ins")

# Netzteil liegt flach auf zwei Auflagen, Schrauben von unten durch den Boden, Kopf versenkt
psx, psy = PSU_C
for hl in PSU_HOLE_L:
    y = PSU_Y1 - hl
    cyl(14, (psx, y, FLOOR - 0.5), PSU_GAP + 0.5, "join", "Base", label="psupad")
    cyl(PSU_HOLE_D, (psx, y, -1), FLOOR + PSU_GAP + 2, "cut", "Base", label="psuhole")
    cyl(6.5, (psx, y, -1), 4, "cut", "Base", label="psucb")
for x in FLOOR_VENT_X:  # Luft von unten, Abluft durch die Schlitze in der rechten vorderen Wand
    prism([(psx + x - 2, psy - 40), (psx + x + 2, psy - 40), (psx + x + 2, psy + 40), (psx + x - 2, psy + 40)],
          -1, FLOOR + 1, "cut", "Base", label="vent")
for c in range(20, 96, 9):
    wall_slot(300, c, 62)

# Dome fuer Elektroniktraeger und Klemmenabdeckung
for x, y in CARR_HOLES:
    cyl(9, (x, y, FLOOR - 0.5), CARR_Z - FLOOR + 0.5, "join", "Base", label="carrpost")
    cyl(INSERT_D, (x, y, CARR_Z - 5.5), 6.5, "cut", "Base", label="carrins")
COVER_EARS = [(psx + 50, PSU_Y1 - 8), (psx + 50, PSU_Y1 + 5)]
for x, y in COVER_EARS:
    cyl(9, (x, y, FLOOR - 0.5), COVER_Z - FLOOR + 0.5, "join", "Base", label="covpost")
    cyl(INSERT_D, (x, y, FLOOR + 0.5), COVER_Z - FLOOR, "cut", "Base", label="covins")

# Rueckwand: Kaltgeraetebuchse und USB
ix, iz = IEC_C
box(ix - IEC_CUT[0] / 2, in_ - 1, iz - IEC_CUT[1] / 2, ix + IEC_CUT[0] / 2, h + 1, iz + IEC_CUT[1] / 2,
    op="cut", target="Base", label="iec")
ux, uz = USB_C
box(ux - USB_CUT[0] / 2, in_ - 1, uz - USB_CUT[1] / 2, ux + USB_CUT[0] / 2, h + 1, uz + USB_CUT[1] / 2,
    op="cut", target="Base", label="usb")

# Front: schraeges Rohrloch, nach oben offen. Die Rutsche wird von innen eingesetzt.
chute_start = chute_axis(CHUTE_Y0 + 40)
chute_len = 120
wall_z = chute_axis(-h)[2]
cyl(CHUTE_D + 2 * CHUTE_WALL + 0.8, chute_start, chute_len, "cut", "Base", axis=list(AX), label="chuteopen")
box(-(CHUTE_D / 2 + CHUTE_WALL + 0.4), -h - 1, wall_z, CHUTE_D / 2 + CHUTE_WALL + 0.4, -in_ + 1, BASE_H + 1,
    op="cut", target="Base", label="chutenotch")
for sx in (1, -1):
    cyl(M3_CLEAR, (sx * EAR_X, -h - 1, EAR_Z), WALL + 2, "cut", "Base", axis="Y", label="earhole")

# ---------- Deckplatte ----------
prism(hexagon(h), BASE_H, TOP, body="Plate", label="plate")
add("solid.fillet", edges=[[*polar(a_, R_OUT), BASE_H + 2] for a_ in range(0, 360, 60)], radius=CORNER_R)
b = NEMA_BLOCK / 2
box(-b, CY - b, MOTOR_FACE, b, CY + b, BASE_H + 0.5, op="join", target="Plate", label="nemablock")
cyl(PILOT_D, (0, CY, MOTOR_FACE - 1), PILOT_DEPTH + 1, "cut", "Plate", label="pilot")
cyl(9, (0, CY, MOTOR_FACE), NEMA_BLOCK_H + PLATE_T + 1, "cut", "Plate", label="shaftclear")
s = NEMA_SPACING / 2
for x, y in [(sx * s, CY + sy * s) for sx in (1, -1) for sy in (1, -1)]:
    cyl(M3_CLEAR, (x, y, MOTOR_FACE - 1), NEMA_BLOCK_H + PLATE_T + 2, "cut", "Plate", label="nemahole")
    cyl(HEAD_D, (x, y, TOP - HEAD_DEPTH), HEAD_DEPTH + 1, "cut", "Plate", label="nemahead")

for r in (R_INNER, R_OUTER):
    cyl(HOLE_D, (0, CY - r, BASE_H - 1), PLATE_T + 2, "cut", "Plate", label="port")

# Versteifung quer vom Motorblock zu den Seitenwaenden
STIFF_END = R_IN - POST_D - POST_R - 0.5  # bis vor den Dom in der Ecke
for x0, x1 in ((b - 1, STIFF_END), (-STIFF_END, -b + 1)):
    box(x0, CY - 1.5, MOTOR_FACE, x1, CY + 1.5, BASE_H + 0.5, op="join", target="Plate", label="stiff")

for x, y in POST_HOLES:
    cyl(M3_CLEAR, (x, y, BASE_H - 1), PLATE_T + 2, "cut", "Plate", label="platehole")
    cyl(HEAD_CB_D, (x, y, TOP - HEAD_CB_DEPTH), HEAD_CB_DEPTH + 1, "cut", "Plate", label="platehead")
# ---------- Scheibe ----------
def food_disc(body, hole, n_ring, disc_d="disc_d", disc_t="disc_t", shaft="shaft_d"):
    """Lochscheibe mit n_ring Loechern je Ring. Position k liegt bei -90 + k * Schritt Grad, k=0 bleibt geschlossen."""
    step = 360 / (2 * n_ring)
    cyl(disc_d, (0, CY, DZ), disc_t, body=body, label="disc")
    cyl(shaft, (0, CY, DZ - 1), DISC_T + 2, "cut", body, label="bore")
    # Madenschraube entlang +X, Muttertasche von oben offen
    zm = DZ + DISC_T / 2
    cyl(M3_CLEAR, (1, CY, zm), 23, "cut", body, axis="X", label="setscrew")
    box(7, CY - 2.95, DZ + 1.5, 9.8, CY + 2.95, DZ + DISC_T + 1, op="cut", target=body, label="nutpocket")
    box(9.8, CY - 4, DZ + 1.5, 24, CY + 4, DZ + DISC_T + 1, op="cut", target=body, label="access")
    for k in range(1, 2 * n_ring):
        r = R_INNER if k % 2 == 0 else R_OUTER
        a = math.radians(-90 + step * k)
        cyl(hole, (r * math.cos(a), CY + r * math.sin(a), DZ - 1), DISC_T + 2, "cut", body, label="foodhole")


food_disc("Disc", "hole_d", N_RING)

# ---------- Abdeckung ----------
prism(hexagon(h), TOP, LID_Z + LID_TOP_T, body="Lid", label="lid")
add("solid.fillet", edges=[[*polar(a_, R_OUT), TOP + 5] for a_ in range(0, 360, 60)], radius=CORNER_R)
prism(hexagon(h - 2), TOP - 1, LID_Z, op="cut", target="Lid", label="lidhollow")
for x, y in POST_HOLES:  # Dom in jeder Ecke ueber dem Schraubenkopf der Platte
    cyl(LID_BOSS_D, (x, y, TOP), LID_Z + LID_TOP_T - TOP - 0.5, "join", "Lid", label="lidboss")
    # Magnettasche von unten, oben bleibt die Haut geschlossen
    cyl(MAGNET_D + MAGNET_FIT, (x, y, TOP - 1), 1 + MAGNET_T + MAGNET_FIT, "cut", "Lid", label="lidmagnet")
cyl(LID_HOLE_D, (0, CY, LID_Z - 1), LID_TOP_T + 2, "cut", "Lid", label="shafthole")

# ---------- Rutsche ----------
cyl(CHUTE_D + 2 * CHUTE_WALL, chute_start, chute_len, body="Chute", axis=list(AX), label="chute")
box(-EAR_X - 6, -in_, EAR_Z - 10, EAR_X + 6, -in_ + 3, BASE_H - 0.1, op="join", target="Chute", label="ears")
cyl(CHUTE_D, chute_start, chute_len + 5, "cut", "Chute", axis=list(AX), label="chutein")
box(-50, -220, BASE_H - 0.1, 50, 60, 200, op="cut", target="Chute", label="trimtop")
box(-50, -260, -60, 50, SPOUT_Y, 200, op="cut", target="Chute", label="trimend")
for sx in (1, -1):
    cyl(M3_CLEAR, (sx * EAR_X, -in_ - 1, EAR_Z), 5, "cut", "Chute", axis="Y", label="earhole")
ir_z = chute_axis(IR_Y)[2] - (CHUTE_D / 2) / math.cos(math.radians(CHUTE_DEG)) + 8
cyl(IR_D, (-30, IR_Y, ir_z), 60, "cut", "Chute", axis="X", label="irhole")

# ---------- Klemmenabdeckung ----------
# Haube ueber dem Klemmenende des Netzteils, oben geschlossen, zum Netzteil offen, Kabelausgang nach hinten.
# Gedruckt mit der Rueckseite auf dem Bett.
tx0, tx1 = psx - PSU[1] / 2 - 2.5, psx + PSU[1] / 2 + 2.5
ty0, ty1 = PSU_Y1 - 13, PSU_Y1 + 12
tzb = PSU_Z0 + PSU[2] + 5
box(tx0, ty0, FLOOR, tx1, ty1, tzb, body="TerminalCover", label="tc")
box(tx0 + 2, ty0 - 1, FLOOR - 1, tx1 - 2, ty1 - 2, tzb - 2, op="cut", target="TerminalCover", label="tcin")
box(psx - 15, ty1 - 3, FLOOR - 1, psx + 15, ty1 + 1, PSU_Z0 + PSU[2], op="cut", target="TerminalCover", label="tccable")
box(tx1 - 0.5, PSU_Y1 - 14, COVER_Z, psx + 56, PSU_Y1 + 10, COVER_Z + 3, op="join", target="TerminalCover", label="tcear")
for x, y in COVER_EARS:
    cyl(M3_CLEAR, (x, y, COVER_Z - 1), 5, "cut", "TerminalCover", label="tchole")

# ---------- Elektroniktraeger ----------
box(*CARR_A[:2], CARR_Z, *CARR_A[2:], CARR_Z + CARR_T, body="Carrier", label="carr")
prism(CARR_B, CARR_Z, CARR_Z + CARR_T, "join", "Carrier", label="carrb")
ct = CARR_Z + CARR_T
for x, y in CARR_HOLES:
    cyl(M3_CLEAR, (x, y, CARR_Z - 1), CARR_T + 2, "cut", "Carrier", label="carrhole")
px, py = PICO_C
pico_pts = [(px + a * PICO_DY / 2, py + b_ * PICO_DX / 2) for a in (1, -1) for b_ in (1, -1)]
for x, y in pico_pts:
    cyl(4, (x, y, ct - 0.5), PICO_STANDOFF + 0.5, "join", "Carrier", label="picopost")
    cyl(1.7, (x, y, ct + PICO_STANDOFF - 3.2), 3.3, "cut", "Carrier", label="picopilot")
qx, qy = PERF_C
for x, y in ((qx, qy - PERF_HOLE_DY / 2), (qx, qy + PERF_HOLE_DY / 2)):
    cyl(6, (x, y, ct - 0.5), 4.5, "join", "Carrier", label="perfpost")
    cyl(2.5, (x, y, ct), 4.5, "cut", "Carrier", label="perfpilot")

# ---------- Platzhalter, nicht drucken ----------
n = 42.3
box(-n / 2, CY - n / 2, MOTOR_FACE - NEMA_L, n / 2, CY + n / 2, MOTOR_FACE, body="DUMMY_Motor", label="dm")
cyl(22, (0, CY, MOTOR_FACE), 2, "join", "DUMMY_Motor", label="dmpilot")
cyl(5, (0, CY, MOTOR_FACE), 24, "join", "DUMMY_Motor", label="dmshaft")
box(n / 2 - 0.1, CY - 8, MOTOR_FACE - NEMA_L + 2, n / 2 + 14, CY + 8, MOTOR_FACE - NEMA_L + 12,
    op="join", target="DUMMY_Motor", label="dmplug")
box(psx - PSU[1] / 2, PSU_Y1 - PSU[0], PSU_Z0, psx + PSU[1] / 2, PSU_Y1, PSU_Z0 + PSU[2], body="DUMMY_PSU", label="dp")
pcb_z = ct + PICO_STANDOFF
box(px - 10.5, py - 25.5, pcb_z, px + 10.5, py + 25.5, pcb_z + 4.5, body="DUMMY_Pico", label="dpico")
box(qx - PERF_W / 2, qy - PERF_L / 2, ct + 4, qx + PERF_W / 2, qy + PERF_L / 2, ct + 24, body="DUMMY_Perfboard", label="dperf")
box(ix - 13.5, in_ - 30, iz - 24, ix + 13.5, in_, iz + 24, body="DUMMY_IEC", label="diec")

for bodies, color in (
    (["Disc"], "#d9a441"), (["Lid"], "#5aa9c9"), (["Chute"], "#e0e0e0"),
    (["DUMMY_Motor", "DUMMY_PSU", "DUMMY_Pico", "DUMMY_Perfboard", "DUMMY_IEC"], "#c0504d"),
):
    add("appearance.assign", bodies=bodies, color=color)

(HERE / "rondofeed.json").write_text(json.dumps({"commands": cmds}, indent=1))
print(len(cmds), "Befehle geschrieben")

# Wechselscheiben mit kleineren Loechern, passen auf dieselben Auslaesse
for hole, n_ring in EXTRA_DISCS:
    cmds.clear()
    food_disc(f"Disc_{hole}", hole, n_ring, DISC_D, DISC_T, SHAFT_D)
    (HERE / f"disc_{hole}.json").write_text(json.dumps({"commands": cmds}, indent=1))
