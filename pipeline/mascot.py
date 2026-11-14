"""Professor Hoot — Wit Wonderland's owl mascot, drawn entirely in code.

hoot(size, pose="idle", blink=0.0, bob=0.0, look=(0,0)) -> RGBA image (size x size)
poses: idle, think, point, cheer, wow
"""
import math
from PIL import Image, ImageDraw, ImageFilter

BODY = (122, 84, 160)       # plum purple
BODY_DK = (88, 58, 122)
BELLY = (255, 236, 205)
SCALLOP = (238, 206, 168)
EYE_RING = (255, 255, 255)
IRIS = (255, 176, 40)
PUPIL = (35, 28, 50)
BEAK = (255, 140, 40)
FEET = (255, 150, 50)
GLASS = (45, 40, 60)
CAP = (35, 35, 55)
TASSEL = (255, 210, 60)
CHEEK = (255, 140, 170)
OUT = (40, 28, 60)

def _wing(d, S, side, angle, cx, cy, length):
    """draw a rounded wing rotated by angle (deg, 0 = hanging down) from shoulder (cx, cy)."""
    a = math.radians(angle)
    pts = []
    w = length * 0.42
    for i in range(24):
        u = i / 23 * math.pi
        x = math.sin(u) * w * (1 if side > 0 else -1) * 0.5
        y = (1 - math.cos(u)) / 2 * length
        pts.append((x, y))
    pts += [(0, length * 0.0)]
    rot = [(cx + x * math.cos(a) + y * math.sin(a) * side, cy - x * math.sin(a) * side + y * math.cos(a)) for x, y in pts]
    d.polygon(rot, fill=BODY_DK, outline=OUT, width=int(S * 0.008))

def hoot(size, pose="idle", blink=0.0, bob=0.0, look=(0.0, 0.0)):
    S = size * 2  # supersample
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    lw = max(2, int(S * 0.012))
    oy = -bob * S * 0.03
    cx = S / 2
    # shadow
    d.ellipse((cx - S * 0.26, S * 0.93, cx + S * 0.26, S * 0.98), fill=(0, 0, 0, 60))
    # wings behind body for cheer/point
    shoulder_y = S * 0.55 + oy
    L = S * 0.30
    wl, wr = 15, 15
    if pose == "cheer": wl, wr = 150, 150
    elif pose == "point": wl, wr = 15, 120
    elif pose == "think": wl, wr = 15, 155
    elif pose == "wow": wl, wr = 60, 60
    # feet
    for fx in (-0.1, 0.1):
        x = cx + fx * S
        for k in (-1, 0, 1):
            d.ellipse((x + k * S * 0.03 - S * 0.025, S * 0.885, x + k * S * 0.03 + S * 0.025, S * 0.935), fill=FEET, outline=OUT, width=lw // 2)
    # body
    body = (cx - S * 0.3, S * 0.3 + oy, cx + S * 0.3, S * 0.92 + oy * 0.5)
    d.ellipse(body, fill=BODY, outline=OUT, width=lw)
    # ear tufts
    for sx in (-1, 1):
        d.polygon([(cx + sx * S * 0.2, S * 0.36 + oy), (cx + sx * S * 0.3, S * 0.2 + oy), (cx + sx * S * 0.1, S * 0.32 + oy)], fill=BODY, outline=OUT)
    d.ellipse((cx - S * 0.3, S * 0.3 + oy, cx + S * 0.3, S * 0.75 + oy), fill=BODY)
    # belly with scallops
    belly = (cx - S * 0.19, S * 0.56 + oy, cx + S * 0.19, S * 0.9 + oy * 0.5)
    d.ellipse(belly, fill=BELLY)
    for r_ in range(3):
        for k in range(-2 + (r_ % 2 == 1), 3):
            if r_ % 2 == 1 and k == 2: continue
            x = cx + (k + (0.5 if r_ % 2 else 0)) * S * 0.065
            y = S * 0.63 + r_ * S * 0.065 + oy * (1 - r_ * 0.2)
            if abs(x - cx) < S * 0.15 - r_ * S * 0.01:
                d.arc((x - S * 0.03, y - S * 0.02, x + S * 0.03, y + S * 0.03), 20, 160, fill=SCALLOP, width=lw)
    # wings (front)
    if wl <= 40: _wing(d, S, -1, 6, cx - S * 0.26, shoulder_y - S * 0.02, L * 0.92)
    else: _wing(d, S, -1, wl, cx - S * 0.26, shoulder_y, L)
    if pose == "think": pass
    elif wr <= 40: _wing(d, S, 1, 6, cx + S * 0.26, shoulder_y - S * 0.02, L * 0.92)
    else: _wing(d, S, 1, wr, cx + S * 0.26, shoulder_y, L)
    # face disc
    face = (cx - S * 0.25, S * 0.33 + oy, cx + S * 0.25, S * 0.6 + oy)
    d.ellipse(face, fill=(150, 112, 186))
    # eyes
    er = S * (0.105 if pose != "wow" else 0.12)
    ey = S * 0.45 + oy
    lx, ly = look
    for sx in (-1, 1):
        ex = cx + sx * S * 0.115
        d.ellipse((ex - er, ey - er, ex + er, ey + er), fill=EYE_RING, outline=OUT, width=lw)
        if blink < 0.85:
            ir = er * 0.62
            px, py = ex + lx * er * 0.25, ey + ly * er * 0.25
            d.ellipse((px - ir, py - ir, px + ir, py + ir), fill=IRIS)
            pr = ir * (0.55 if pose != "wow" else 0.4)
            d.ellipse((px - pr, py - pr, px + pr, py + pr), fill=PUPIL)
            d.ellipse((px - pr * 0.2 + pr * 0.35, py - pr * 0.75, px + pr * 0.35 + pr * 0.25, py - pr * 0.25), fill=(255, 255, 255))
        if blink > 0:
            lid = (ey - er) + 2 * er * min(1, blink)
            d.chord((ex - er, ey - er, ex + er, ey + er), 180, 360, fill=BODY) if blink >= 0.5 else None
            d.rectangle((ex - er, ey - er, ex + er, lid), fill=BODY) if blink < 0.5 else None
            if blink >= 0.85:
                d.ellipse((ex - er, ey - er, ex + er, ey + er), fill=BODY, outline=OUT, width=lw)
                d.arc((ex - er * 0.7, ey - er * 0.5, ex + er * 0.7, ey + er * 0.5), 20, 160, fill=OUT, width=lw)
    # glasses
    for sx in (-1, 1):
        ex = cx + sx * S * 0.115
        gr = er * 1.12
        d.ellipse((ex - gr, ey - gr, ex + gr, ey + gr), outline=GLASS, width=int(lw * 1.2))
    d.arc((cx - S * 0.03, ey - er * 0.6, cx + S * 0.03, ey - er * 0.1), 200, 340, fill=GLASS, width=int(lw * 1.2))
    # brows
    for sx in (-1, 1):
        ex = cx + sx * S * 0.115
        tilt = {"think": 0.04 * sx, "wow": -0.03, "cheer": -0.02}.get(pose, 0)
        y0 = ey - er * 1.2 - (S * 0.008 if pose == "wow" else 0)
        d.line((ex - er * 0.6, y0 + tilt * S * sx, ex + er * 0.6, y0 - tilt * S * sx), fill=OUT, width=int(lw * 1.4))
    # beak
    by = S * 0.535 + oy
    if pose in ("wow", "cheer"):
        d.polygon([(cx - S * 0.04, by), (cx + S * 0.04, by), (cx, by + S * 0.07)], fill=BEAK, outline=OUT)
        d.ellipse((cx - S * 0.022, by + S * 0.012, cx + S * 0.022, by + S * 0.04), fill=(170, 60, 40))
    else:
        d.polygon([(cx - S * 0.04, by), (cx + S * 0.04, by), (cx, by + S * 0.06)], fill=BEAK, outline=OUT)
    # cheeks
    for sx in (-1, 1):
        d.ellipse((cx + sx * S * 0.2 - S * 0.035, S * 0.53 + oy, cx + sx * S * 0.2 + S * 0.035, S * 0.56 + oy), fill=CHEEK)
    # think: wing to chin drawn in front
    if pose == "think":
        _wing(d, S, -1, 100, cx + S * 0.27, shoulder_y + S * 0.04, L * 0.85)
        try:
            from PIL import ImageFont
            qf = ImageFont.truetype(__file__.replace("mascot.py", "fonts/Poppins-Bold.ttf"), int(S * 0.12))
            d.ellipse((cx + S * 0.3, S * 0.02 + oy, cx + S * 0.46, S * 0.17 + oy), fill=(255, 255, 255), outline=OUT, width=lw // 2)
            d.text((cx + S * 0.345, S * 0.015 + oy), "?", font=qf, fill=(122, 84, 160))
        except Exception:
            pass
        d.ellipse((cx + S * 0.33, S * 0.15 + oy, cx + S * 0.41, S * 0.23 + oy), fill=(255, 255, 255), outline=OUT, width=lw // 2)
        d.ellipse((cx + S * 0.37, S * 0.24 + oy, cx + S * 0.4, S * 0.27 + oy), fill=(255, 255, 255), outline=OUT, width=lw // 2)
    # sparkles for cheer
    if pose == "cheer":
        for (sx, sy) in ((0.12, 0.18), (0.88, 0.2), (0.08, 0.5), (0.92, 0.52)):
            x, y = sx * S, sy * S + oy
            r = S * 0.03
            d.polygon([(x, y - r), (x + r * 0.3, y - r * 0.3), (x + r, y), (x + r * 0.3, y + r * 0.3), (x, y + r), (x - r * 0.3, y + r * 0.3), (x - r, y), (x - r * 0.3, y - r * 0.3)], fill=TASSEL)
    return im.resize((size, size), Image.LANCZOS)

if __name__ == "__main__":
    import sys
    from PIL import ImageFont
    out = sys.argv[1] if len(sys.argv) > 1 else "hoot_sheet.png"
    W, H = 2400, 1500
    sheet = Image.new("RGB", (W, H), (28, 30, 70)); d = ImageDraw.Draw(sheet)
    try:
        f = ImageFont.truetype(__file__.replace("mascot.py", "fonts/Poppins-Bold.ttf"), 44)
        f2 = ImageFont.truetype(__file__.replace("mascot.py", "fonts/Poppins-Bold.ttf"), 80)
    except Exception:
        f = f2 = None
    d.text((60, 40), "PROFESSOR HOOT — character sheet", font=f2, fill=(255, 210, 60))
    big = hoot(820, "idle")
    sheet.paste(big, (40, 180), big)
    d.text((300, 1000 + 40), "Main pose", font=f, fill=(255, 255, 255))
    poses = [("think", "Thinking"), ("point", "Pointing"), ("cheer", "Cheering"), ("wow", "Surprised")]
    for i, (p, name) in enumerate(poses):
        im = hoot(520, p); x = 900 + (i % 2) * 720; y = 170 + (i // 2) * 640
        sheet.paste(im, (x, y), im); d.text((x + 170, y + 520), name, font=f, fill=(255, 255, 255))
    for i, b in enumerate([0.0, 0.5, 1.0]):
        im = hoot(260, "idle", blink=b); sheet.paste(im, (60 + i * 260, 1180), im)
    d.text((140, 1440), "Blink", font=f, fill=(255, 255, 255))
    sheet.save(out); print(out)
