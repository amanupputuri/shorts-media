"""Custom eye & brain puzzle drawers. Each draw_X(c, im, item, phase, pt, t) draws the main area
and returns (x, y) for the confetti burst. min_ask(item) gives the minimum question phase length."""
import math
from PIL import Image, ImageDraw, ImageFilter
from engine import emoji_img, eob, eo, cl, paste, font, F_BOLD, text_center

def area(c):
    # main puzzle box (x0, y0, x1, y1)
    return (60, 640, c.W - 60, 1460) if c.v else (140, 260, c.W - 140, 900)

def min_ask(item):
    t = item.get("type")
    if t == "changed": return 5.2
    if t == "cups": return 1.9 + 0.6 * len(item["swaps"]) + 0.3
    if t == "hidden": return 3.2
    return 0

def glow_box(im, box, color=(60, 255, 120), r=30):
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).rounded_rectangle(box, radius=r, outline=color + (255,), width=14)
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(im).rounded_rectangle(box, radius=r, outline=color, width=8)

# ---------------------------------------------------------------- What changed?
def draw_changed(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    cols, rows = 3, 2
    cw, ch = (x1 - x0) / cols, (y1 - y0) / rows
    if not c.v: ch = min(ch, 300)
    oy = y0 + ((y1 - y0) - rows * ch) / 2
    blink_t = 3.0
    after = phase != "ask" or t >= blink_t
    d = ImageDraw.Draw(im)
    centers = []
    for i in range(6):
        r_, k = divmod(i, cols)
        cx, cy = x0 + cw * (k + 0.5), oy + ch * (r_ + 0.5)
        centers.append((cx, cy))
        box = (cx - cw / 2 + 18, cy - ch / 2 + 18, cx + cw / 2 - 18, cy + ch / 2 - 18)
        d.rounded_rectangle(box, radius=36, fill=(255, 255, 255, 235))
        em = item["after_emoji"] if (after and i == item["changed"]) else item["before"][i]
        s = eob((t - 0.3 - 0.12 * i) / 0.4) if phase == "ask" and t < blink_t else 1
        paste(im, emoji_img(em, min(cw, ch) * 0.55), cx, cy + 6, s)
        nf = font(F_BOLD, 40); d.ellipse((box[0] + 10, box[1] + 10, box[0] + 66, box[1] + 66), fill=c.accent)
        tw = d.textlength(str(i + 1), font=nf); d.text((box[0] + 38 - tw / 2, box[1] + 12), str(i + 1), font=nf, fill=(30, 30, 60))
    if phase == "ask" and blink_t <= t < blink_t + 0.45:
        a = 1 - abs((t - blink_t) - 0.22) / 0.22
        im.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, int(255 * cl(a)))))
    if phase == "ask" and t < blink_t:
        # memorise timer ring
        frac = t / blink_t
        bx, by = (c.W / 2, y1 + 40) if c.v else (c.W - 120, 150)
        d.arc((bx - 40, by - 40, bx + 40, by + 40), -90, -90 + 360 * (1 - frac), fill=c.accent, width=10)
    if phase == "reveal":
        cx, cy = centers[item["changed"]]
        box = (cx - cw / 2 + 12, cy - ch / 2 + 12, cx + cw / 2 - 12, cy + ch / 2 - 12)
        glow_box(im, box)
        if pt > 0.5:
            was = emoji_img(item["before"][item["changed"]], min(cw, ch) * 0.24)
            paste(im, was, box[2] - 50, box[1] + 50, eob((pt - 0.5) / 0.4))
        return cx, cy
    return c.W / 2, (y0 + y1) / 2

# ---------------------------------------------------------------- Follow the ball
def _cup(w, h, col):
    im = Image.new("RGBA", (int(w) + 20, int(h) + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    top, bot = 10 + w * 0.22, 10
    d.polygon([(10 + w * 0.2, 10), (10 + w * 0.8, 10), (10 + w, 10 + h), (10, 10 + h)], fill=col)
    d.ellipse((10 + w * 0.2, 10 - h * 0.06, 10 + w * 0.8, 10 + h * 0.08), fill=tuple(min(255, v + 40) for v in col))
    d.rounded_rectangle((4, 10 + h - 22, 16 + w, 10 + h + 6), radius=12, fill=tuple(max(0, v - 50) for v in col))
    for k in range(3):
        yy = 10 + h * (0.3 + 0.2 * k)
        d.line((10 + w * (0.2 - 0.06 * k) + 20, yy, 10 + w * (0.8 + 0.06 * k) - 20, yy), fill=(255, 255, 255, 60), width=6)
    return im

def cups_state(item, t):
    """returns slot position (float) for each cup id at time t (ask phase)"""
    slot = [0.0, 1.0, 2.0]; lift = 0.0
    if t < 1.6:
        lift = math.sin(cl((t - 0.4) / 1.0) * math.pi)
        return slot, lift, None
    k = int((t - 1.6) / 0.6); frac = ((t - 1.6) % 0.6) / 0.6
    pos = [0, 1, 2]  # pos[cup] = slot
    for j, (a, b) in enumerate(item["swaps"]):
        if j < k:
            ca, cb = pos.index(a), pos.index(b)
            pos[ca], pos[cb] = b, a
    slot = [float(p) for p in pos]
    arc = None
    if k < len(item["swaps"]):
        a, b = item["swaps"][k]
        ca, cb = pos.index(a), pos.index(b)
        e = 0.5 - 0.5 * math.cos(frac * math.pi)
        slot[ca] = a + (b - a) * e; slot[cb] = b + (a - b) * e
        arc = (ca, cb, math.sin(frac * math.pi))
    return slot, 0.0, arc

def final_slot(item):
    pos = [0, 1, 2]
    for a, b in item["swaps"]:
        ca, cb = pos.index(a), pos.index(b)
        pos[ca], pos[cb] = b, a
    return pos[item["start"]]

def draw_cups(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    sw = (x1 - x0) / 3
    cw, chh = sw * 0.62, sw * 0.62 * 1.05
    if not c.v: cw, chh = 230, 230
    base_y = (y0 + y1) / 2 + chh * (0.35 if c.v else 0.75)
    d = ImageDraw.Draw(im)
    tt = t if phase == "ask" else 1e9
    if phase == "ask":
        slot, lift, arc = cups_state(item, t)
    else:
        n = len(item["swaps"]); slot, lift, arc = cups_state(item, 1.6 + 0.6 * n + 0.01)
        lift = eo(pt / 0.5) if phase == "reveal" else 0.0
    # table line
    d.rounded_rectangle((x0, base_y + 10, x1, base_y + 30), radius=10, fill=(255, 255, 255, 50))
    # ball
    ball_cup = item["start"]
    bx = x0 + sw * (slot[ball_cup] + 0.5)
    br = cw * 0.18
    show_ball = (phase == "ask" and t < 1.6) or phase == "reveal"
    if show_ball:
        d.ellipse((bx - br, base_y - 2 * br, bx + br, base_y), fill=(255, 80, 80), outline=(255, 255, 255), width=6)
    cols = [(230, 70, 70), (60, 140, 230), (250, 180, 40)]
    for cup in range(3):
        cx = x0 + sw * (slot[cup] + 0.5)
        dy = 0
        if arc and cup in (arc[0], arc[1]):
            dy = -arc[2] * chh * 0.35 * (1 if cup == arc[0] else -0.4)
        l = 0
        if phase == "ask" and t < 1.6 and cup == item["start"]: l = lift
        if phase == "reveal": l = lift
        cup_im = _cup(cw, chh, cols[cup] if item.get("colors") else (220, 60, 70))
        s = eob((t - 0.1 * cup) / 0.4) if phase == "ask" else 1
        paste(im, cup_im, cx, base_y - chh / 2 + dy - l * chh * 0.75, s)
    # slot letters
    for k in range(3):
        f = font(F_BOLD, 64 if c.v else 56)
        L = "ABC"[k]; cx = x0 + sw * (k + 0.5)
        d.ellipse((cx - 44, base_y + 60, cx + 44, base_y + 148), fill=c.accent)
        tw = d.textlength(L, font=f); d.text((cx - tw / 2, base_y + 66), L, font=f, fill=(30, 30, 60))
    if phase == "reveal":
        fx = x0 + sw * (final_slot(item) + 0.5)
        if pt > 0.4: glow_box(im, (fx - sw / 2 + 20, base_y - chh * 1.9, fx + sw / 2 - 20, base_y + 160))
        return fx, base_y - chh
    return c.W / 2, base_y

# ---------------------------------------------------------------- Complete the pattern
def draw_pattern(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    seq = item["seq"]; n = len(seq) + 1
    size = min(170 if c.v else 150, (x1 - x0) / n * 0.8)
    rowy = y0 + (180 if c.v else 120)
    gap = (x1 - x0) / n
    d = ImageDraw.Draw(im)
    for i in range(n):
        cx = x0 + gap * (i + 0.5)
        s = eob((t - 0.3 - 0.15 * i) / 0.4) if phase == "ask" else 1
        if i < len(seq):
            paste(im, emoji_img(seq[i], size), cx, rowy, s)
        else:
            box = (cx - size * 0.62, rowy - size * 0.62, cx + size * 0.62, rowy + size * 0.62)
            if phase == "reveal" and pt > 0.2:
                glow_box(im, box, r=24)
                paste(im, emoji_img(item["options"][item["right"]], size), cx, rowy, eob((pt - 0.2) / 0.4))
            else:
                d.rounded_rectangle(box, radius=24, outline=c.accent, width=8, fill=(255, 255, 255, 30))
                qf = font(F_BOLD, size * 0.8); tw = d.textlength("?", font=qf)
                d.text((cx - tw / 2, rowy - size * 0.55), "?", font=qf, fill=c.accent)
    # options row
    opts = item["options"]; oy = y0 + (560 if c.v else 430)
    ow = (x1 - x0) / len(opts)
    for k, o in enumerate(opts):
        cx = x0 + ow * (k + 0.5)
        bw, bh = min(ow - 50, 300), 260 if c.v else 220
        box = (cx - bw / 2, oy - bh / 2, cx + bw / 2, oy + bh / 2)
        s = eob((t - 1.4 - 0.25 * k) / 0.4) if phase == "ask" else 1
        if s <= 0.01: continue
        fill = (255, 255, 255)
        if phase == "reveal":
            fill = (40, 190, 90) if k == item["right"] else (150, 40, 55)
        card = Image.new("RGBA", (int(bw) + 20, int(bh) + 20), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
        cd.rounded_rectangle((10, 10, bw + 10, bh + 10), radius=36, fill=fill, outline=c.accent, width=8)
        e = emoji_img(o, bh * 0.5); card.alpha_composite(e, (int(10 + bw / 2 - e.width / 2), int(10 + bh * 0.4 - e.height / 2)))
        lf = font(F_BOLD, 54); L = "ABC"[k]; tw = cd.textlength(L, font=lf)
        cd.text((10 + bw / 2 - tw / 2, 10 + bh * 0.72), L, font=lf, fill=(30, 30, 60) if phase != "reveal" else (255, 255, 255))
        paste(im, card, cx, oy, s, 0.55 if (phase == "reveal" and k != item["right"]) else 1)
    if phase == "reveal":
        return x0 + ow * (item["right"] + 0.5), oy
    return c.W / 2, oy

# ---------------------------------------------------------------- Find the hidden one
def draw_hidden(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    cols, rows = (6, 6) if c.v else (12, 5)
    if not c.v: y0 += 50
    cell = min((x1 - x0) / cols, (y1 - y0) / rows) * 0.94
    ox = x0 + ((x1 - x0) - cols * cell) / 2; oy = y0 + ((y1 - y0) - rows * cell) / 2
    orow, ocol = item["pos"]
    orow %= rows; ocol %= cols
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((ox - 20, oy - 20, ox + cols * cell + 20, oy + rows * cell + 20), radius=40, fill=(255, 255, 255, 230))
    a = eo((t - 0.3) / 0.5) if phase == "ask" else 1
    for r_ in range(rows):
        for k in range(cols):
            em = item["odd"] if (r_ == orow and k == ocol) else item["base"]
            paste(im, emoji_img(em, cell * 0.78), ox + cell * (k + 0.5), oy + cell * (r_ + 0.5), 1, a)
    cx, cy = ox + cell * (ocol + 0.5), oy + cell * (orow + 0.5)
    if phase == "reveal":
        rr = cell * (0.75 + 0.1 * math.sin(pt * 6))
        im.alpha_composite(Image.new("RGBA", im.size, (0, 0, 0, int(90 * cl(pt / 0.4)))))
        paste(im, emoji_img(item["odd"], cell * 0.78 * (1 + 0.4 * eo(pt / 0.5))), cx, cy)
        d = ImageDraw.Draw(im)
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=(60, 255, 120), width=12)
    return cx, cy

DRAW = {"changed": draw_changed, "cups": draw_cups, "pattern": draw_pattern, "hidden": draw_hidden}

# ================================================================ BATCH 2
def _key_img(teeth, scale, col=(250, 200, 60)):
    u = scale
    w, h = int(u * 9), int(u * 3.2)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    r = u * 1.3
    d.ellipse((0, h / 2 - r, 2 * r, h / 2 + r), fill=col)
    d.ellipse((r * 0.55, h / 2 - r * 0.45, r * 1.45, h / 2 + r * 0.45), fill=(0, 0, 0, 0))
    sx = 2 * r - 6; sy = h / 2 - u * 0.4
    d.rectangle((sx, sy, w - u * 0.3, sy + u * 0.8), fill=col)
    tw = (w - u * 0.6 - sx - u * 0.6) / len(teeth)
    for i, tv in enumerate(teeth):
        x = sx + u * 0.6 + i * tw
        d.rectangle((x + 3, sy + u * 0.8, x + tw - 3, sy + u * 0.8 + u * 0.38 * tv), fill=col)
    return im

def _lock_img(teeth, scale, open_=0.0, col=(120, 130, 150)):
    u = scale
    w, h = int(u * 11), int(u * 12)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    lift = open_ * u * 1.6
    d.arc((u * 2.5, u * 0.3 - lift, w - u * 2.5, u * 7 - lift), 180, 360, fill=(190, 195, 205), width=int(u * 1.1))
    d.line((u * 2.5 + u * 0.55, u * 3.65 - lift, u * 2.5 + u * 0.55, u * 5.5), fill=(190, 195, 205), width=int(u * 1.1))
    d.line((w - u * 2.5 - u * 0.55, u * 3.65 - lift, w - u * 2.5 - u * 0.55, u * 5.5), fill=(190, 195, 205), width=int(u * 1.1))
    d.rounded_rectangle((0, u * 5, w, h), radius=int(u * 1.2), fill=col)
    # keyway panel showing the tooth profile
    px0, py0 = u * 1.2, u * 7.2
    pw = w - u * 2.4
    d.rounded_rectangle((px0, py0, px0 + pw, py0 + u * 3), radius=int(u * 0.4), fill=(40, 44, 60))
    tw = (pw - u * 0.8) / len(teeth)
    pts = [(px0 + u * 0.4, py0 + u * 0.7)]
    for i, tv in enumerate(teeth):
        x = px0 + u * 0.4 + i * tw
        pts += [(x + 3, py0 + u * 0.7 + u * 0.5 * tv), (x + tw - 3, py0 + u * 0.7 + u * 0.5 * tv)]
    pts += [(px0 + pw - u * 0.4, py0 + u * 0.7)]
    d.line(pts, fill=(255, 210, 60), width=8, joint="curve")
    return im

def draw_keys(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    if c.v:
        lock_c = (c.W / 2, y0 + 170); u_l = 34
        key_cs = [(c.W / 2 + 60, y0 + 490 + i * 160) for i in range(3)]; u_k = 40
    else:
        lock_c = (x0 + 360, (y0 + y1) / 2 + 30); u_l = 40
        key_cs = [(x0 + 1100, y0 + 140 + i * 200) for i in range(3)]; u_k = 44
    op = 0.0
    if phase == "reveal": op = eo((pt - 0.9) / 0.4)
    paste(im, _lock_img(item["lock"], u_l, op), lock_c[0], lock_c[1], eob((t - 0.2) / 0.4) if phase == "ask" else 1)
    for k, teeth in enumerate(item["keys"]):
        kx, ky = key_cs[k]
        s = eob((t - 0.9 - 0.3 * k) / 0.4) if phase == "ask" else 1
        if phase == "reveal" and k == item["right"]:
            m = eo(pt / 0.8)
            tx, ty = lock_c[0], lock_c[1] + u_l * 2.7
            kx, ky = kx + (tx - kx) * m, ky + (ty - ky) * m
        a = 0.45 if (phase == "reveal" and k != item["right"]) else 1
        paste(im, _key_img(teeth, u_k), kx, ky, s, a)
        lx = key_cs[k][0] - u_k * 6.2
        f = font(F_BOLD, 56)
        d.ellipse((lx - 40, key_cs[k][1] - 40, lx + 40, key_cs[k][1] + 40), fill=c.accent)
        L = "ABC"[k]; tw = d.textlength(L, font=f); d.text((lx - tw / 2, key_cs[k][1] - 36), L, font=f, fill=(30, 30, 60))
    if phase == "reveal":
        return lock_c
    return c.W / 2, (y0 + y1) / 2

# ---------------------------------------------------------------- Which glass fills first
GL_POS_V = {1: (0.5, 0.05), 2: (0.27, 0.38), 3: (0.73, 0.38), 4: (0.13, 0.72), 5: (0.5, 0.72), 6: (0.87, 0.72)}
GL_POS_H = {1: (0.5, 0.0), 2: (0.3, 0.36), 3: (0.7, 0.36), 4: (0.12, 0.72), 5: (0.5, 0.72), 6: (0.88, 0.72)}

def glass_path(item):
    """follow lowest open outlet from glass 1; returns list of (glass, level_to_fill) ending with the glass that fills (level 1)"""
    g = 1; path = []
    pipes = item["pipes"]  # {"1": [[child, height, blocked], ...]}
    for _ in range(10):
        outs = [p for p in pipes.get(str(g), []) if not p[2]]
        if not outs:
            path.append((g, 1.0)); return path
        child, hgt, _ = min(outs, key=lambda p: p[1])
        path.append((g, hgt)); g = child
    return path

def draw_glasses(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    if not c.v: y0 += 70
    P = GL_POS_V if c.v else GL_POS_H
    gw, gh = (150, 200) if c.v else (130, 160)
    d = ImageDraw.Draw(im)
    def gbox(g):
        fx, fy = P[g]; cx = x0 + (x1 - x0) * fx; top = y0 + (y1 - y0 - gh) * fy + 60
        return (cx - gw / 2, top, cx + gw / 2, top + gh)
    path = glass_path(item)
    # fill animation in reveal
    levels = {g: 0.0 for g in P}
    if phase == "reveal":
        T = pt / 0.7
        for g, lvl in path:
            if T <= 0: break
            step = min(1.0, T); levels[g] = lvl * step; T -= 1.0
    # pipes
    for g, outs in item["pipes"].items():
        g = int(g); bx = gbox(g)
        for child, hgt, blocked in outs:
            cb = gbox(child)
            sx = bx[0] if (cb[0] + cb[2]) / 2 < (bx[0] + bx[2]) / 2 else bx[2]
            sy = bx[3] - (bx[3] - bx[1]) * hgt
            ex, ey = (cb[0] + cb[2]) / 2, cb[1] - 10
            mx = ex
            d.line((sx, sy, mx, sy, ex, ey), fill=(200, 210, 230), width=16, joint="curve")
            flowing = phase == "reveal" and any(pg == g for pg, _ in path) and levels[g] >= hgt - 1e-6 and not blocked and (g, hgt) in path
            if flowing:
                d.line((sx, sy, mx, sy, ex, ey), fill=(70, 160, 255), width=10, joint="curve")
            if blocked:
                bxm, bym = (sx + mx) / 2, sy
                d.rectangle((bxm - 14, bym - 22, bxm + 14, bym + 22), fill=(60, 60, 70))
                d.line((bxm - 22, bym - 22, bxm + 22, bym + 22), fill=(255, 70, 70), width=8)
                d.line((bxm + 22, bym - 22, bxm - 22, bym + 22), fill=(255, 70, 70), width=8)
    # tap
    b1 = gbox(1); tx = (b1[0] + b1[2]) / 2
    d.rounded_rectangle((tx - 70, b1[1] - 95, tx + 30, b1[1] - 60), radius=12, fill=(180, 185, 200))
    d.rectangle((tx - 10, b1[1] - 70, tx + 18, b1[1] - 40), fill=(180, 185, 200))
    if phase == "reveal" and pt < 0.7 * len(path) + 0.5:
        d.rectangle((tx - 2, b1[1] - 40, tx + 10, b1[1] + gh - levels[1] * gh), fill=(70, 160, 255))
    f = font(F_BOLD, 50)
    for g in P:
        bx = gbox(g)
        a = eob((t - 0.3 - 0.12 * g) / 0.4) if phase == "ask" else 1
        if a <= 0.05: continue
        lv = levels[g]
        if lv > 0:
            d.rectangle((bx[0] + 8, bx[3] - (gh - 8) * lv, bx[2] - 8, bx[3] - 6), fill=(70, 160, 255, 230))
        d.line((bx[0], bx[1], bx[0] + 8, bx[3], bx[2] - 8, bx[3], bx[2], bx[1]), fill=(255, 255, 255), width=8, joint="curve")
        L = str(g); tw = d.textlength(L, font=f)
        mx_, my_ = (bx[0] + bx[2]) / 2, bx[3] - 50
        d.ellipse((mx_ - 32, my_ - 32, mx_ + 32, my_ + 32), fill=c.accent)
        d.text((mx_ - tw / 2, my_ - 33), L, font=f, fill=(30, 30, 60))
    win = path[-1][0]
    if phase == "reveal" and pt > 0.7 * len(path):
        bx = gbox(win); glow_box(im, (bx[0] - 20, bx[1] - 20, bx[2] + 20, bx[3] + 20))
        return (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
    return c.W / 2, (y0 + y1) / 2

# ---------------------------------------------------------------- Which path gets the prize (ghost-leg)
def path_trace(item, lane, rows):
    """returns list of (lane_float, row_float) points and the end lane"""
    pts = [(lane, 0.0)]
    rungs = sorted(item["rungs"], key=lambda r: r[0])
    for r, left in rungs:
        if lane == left or lane == left + 1:
            other = left + 1 if lane == left else left
            pts.append((lane, r - 0.35)); pts.append((other, r + 0.35)); lane = other
    pts.append((lane, rows))
    return pts, lane

def draw_path(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    n = len(item["starters"]); rows = item.get("rows", 8)
    if not c.v: y0 += 70
    top, bot = y0 + (90 if c.v else 70), y1 - (110 if c.v else 80)
    lx = lambda l: x0 + (x1 - x0) * (l + 0.5) / n
    ry = lambda r: top + (bot - top) * r / rows
    d = ImageDraw.Draw(im)
    a = eo((t - 0.4) / 0.6) if phase == "ask" else 1
    col = (255, 255, 255, int(200 * a))
    def poly(pts):
        out = []
        for i in range(len(pts) - 1):
            (la, ra), (lb, rb) = pts[i], pts[i + 1]
            if la == lb:
                out += [(lx(la), ry(ra)), (lx(lb), ry(rb))]
            else:
                for s in range(13):
                    u = s / 12; e = 0.5 - 0.5 * math.cos(u * math.pi)
                    out.append((lx(la + (lb - la) * e), ry(ra + (rb - ra) * u)))
        return out
    for l in range(n):
        pts, _ = path_trace(item, l, rows)
        d.line(poly(pts), fill=col, width=12, joint="curve")
    right = None
    for l in range(n):
        _, end = path_trace(item, l, rows)
        if end == item["prize_slot"]: right = l
    for l, e in enumerate(item["starters"]):
        paste(im, emoji_img(e, 110 if c.v else 90), lx(l), top - 50, eob((t - 0.2 - 0.2 * l) / 0.4) if phase == "ask" else 1)
        f = font(F_BOLD, 44); L = "ABC"[l]; tw = d.textlength(L, font=f)
        d.text((lx(l) - 80 - tw / 2, top - 75), L, font=f, fill=c.accent)
    for l in range(n):
        if l == item["prize_slot"]:
            paste(im, emoji_img(item["prize"], 110 if c.v else 90), lx(l), bot + 55)
        else:
            paste(im, emoji_img("❌", 70), lx(l), bot + 55)
    if phase == "reveal":
        pts, _ = path_trace(item, right, rows)
        P = poly(pts); k = max(2, int(len(P) * cl(pt / 1.6)))
        d.line(P[:k], fill=(60, 255, 120), width=16, joint="curve")
        return lx(item["prize_slot"]), bot + 55
    return c.W / 2, (y0 + y1) / 2

# ---------------------------------------------------------------- Shadow match
def silhouette(em, size, flip=False, col=(20, 20, 35)):
    e = emoji_img(em, size)
    if flip: e = e.transpose(Image.FLIP_LEFT_RIGHT)
    sil = Image.new("RGBA", e.size, col + (0,)); sil.putalpha(e.split()[-1].point(lambda v: 255 if v > 60 else 0))
    return e, sil

def draw_shadow(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    big = 300 if c.v else 260
    oc = (c.W / 2, y0 + 180) if c.v else (x0 + 280, (y0 + y1) / 2)
    paste(im, emoji_img(item["object"], big), oc[0], oc[1], eob((t - 0.2) / 0.5) if phase == "ask" else 1)
    n = len(item["shadows"])
    for k, sh in enumerate(item["shadows"]):
        em, fl = (sh[:-5], True) if sh.endswith("|flip") else (sh, False)
        if c.v:
            cx, cy = x0 + (x1 - x0) * (k + 0.5) / n, y0 + 620; sz = 230
        else:
            cx, cy = x0 + 640 + k * 380, (y0 + y1) / 2; sz = 230
        box = (cx - sz * 0.72, cy - sz * 0.72, cx + sz * 0.72, cy + sz * 0.72)
        s = eob((t - 1.0 - 0.3 * k) / 0.4) if phase == "ask" else 1
        if s <= 0.02: continue
        d.rounded_rectangle(box, radius=30, fill=(255, 255, 255, 220))
        e, sil = silhouette(em, sz, fl)
        if phase == "reveal" and k == item["right"] and pt > 0.3:
            paste(im, e, cx, cy, 1)
            glow_box(im, box)
        else:
            paste(im, sil, cx, cy, s, 0.4 if phase == "reveal" else 1)
        f = font(F_BOLD, 50); L = "ABC"[k]; tw = d.textlength(L, font=f)
        d.ellipse((box[0] - 10, box[1] - 10, box[0] + 60, box[1] + 60), fill=c.accent)
        d.text((box[0] + 25 - tw / 2, box[1] - 8), L, font=f, fill=(30, 30, 60))
    if phase == "reveal":
        k = item["right"]
        return (x0 + (x1 - x0) * (k + 0.5) / n, y0 + 620) if c.v else (x0 + 640 + k * 380, (y0 + y1) / 2)
    return c.W / 2, (y0 + y1) / 2

# ---------------------------------------------------------------- Mirror match
def _content_img(item, size):
    if item.get("kind") == "text":
        f = font(F_BOLD, size); tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        w = int(tmp.textlength(item["content"], font=f)) + 40
        im = Image.new("RGBA", (w, int(size * 1.4)), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((20, 0), item["content"], font=f, fill=(30, 30, 60))
        return im.crop(im.getbbox())
    return emoji_img(item["content"], size)

def draw_mirror(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    base = _content_img(item, 150 if c.v else 130)
    oc = (c.W / 2, y0 + 120) if c.v else (c.W / 2, y0 + 170)
    bw = min(base.width + 80, c.W - 160)
    d.rounded_rectangle((oc[0] - bw / 2, oc[1] - base.height / 2 - 40, oc[0] + bw / 2, oc[1] + base.height / 2 + 40), radius=30, fill=(255, 255, 255))
    paste(im, base, oc[0], oc[1], min(1, (bw - 80) / base.width))
    tf = {"h": Image.FLIP_LEFT_RIGHT, "v": Image.FLIP_TOP_BOTTOM, "r": Image.ROTATE_180}
    n = len(item["opts"])
    for k, op in enumerate(item["opts"]):
        img = base.transpose(tf[op]) if op in tf else base
        if c.v:
            cx, cy = c.W / 2, y0 + 370 + k * 200; ow, oh = c.W - 220, 170
        else:
            cx, cy = x0 + (x1 - x0) * (k + 0.5) / n, y0 + 470; ow, oh = (x1 - x0) / n - 60, 230
        s = eob((t - 1.0 - 0.3 * k) / 0.4) if phase == "ask" else 1
        if s <= 0.02: continue
        fill = (255, 255, 255)
        if phase == "reveal": fill = (40, 190, 90) if k == item["right"] else (150, 40, 55)
        d.rounded_rectangle((cx - ow / 2, cy - oh / 2, cx + ow / 2, cy + oh / 2), radius=30, fill=fill, outline=c.accent, width=6)
        sc = min((ow - 160) / img.width, (oh - 50) / img.height)
        paste(im, img, cx + 30, cy, sc * s, 0.5 if (phase == "reveal" and k != item["right"]) else 1)
        f = font(F_BOLD, 52); L = "ABC"[k]; tw = d.textlength(L, font=f)
        d.ellipse((cx - ow / 2 + 20, cy - 40, cx - ow / 2 + 100, cy + 40), fill=c.accent)
        d.text((cx - ow / 2 + 60 - tw / 2, cy - 36), L, font=f, fill=(30, 30, 60))
    if phase == "reveal":
        k = item["right"]
        return (c.W / 2, y0 + 370 + k * 200) if c.v else (x0 + (x1 - x0) * (k + 0.5) / n, y0 + 470)
    return c.W / 2, (y0 + y1) / 2

DRAW.update({"keys": draw_keys, "glasses": draw_glasses, "path": draw_path, "shadow": draw_shadow, "mirror": draw_mirror})

# ================================================================ BATCH 3 + 4
import random as _rnd

def _label(d, x, y, L, c, r=40, size=52):
    f = font(F_BOLD, size); d.ellipse((x - r, y - r, x + r, y + r), fill=c.accent)
    tw = d.textlength(L, font=f); d.text((x - tw / 2, y - size * 0.68), L, font=f, fill=(30, 30, 60))

# ---------------------------------------------------------------- Which jar has more
def _jar_points(n, w, h, size, seed):
    rnd = _rnd.Random(seed); pts = []
    cols = max(1, int(w / size)); rows_needed = math.ceil(n / cols)
    for i in range(n):
        r_, k = divmod(i, cols)
        x = (k + 0.5) * (w / cols) + rnd.uniform(-size * 0.12, size * 0.12)
        y = h - (r_ + 0.5) * size * 0.92 + rnd.uniform(-size * 0.1, size * 0.1)
        pts.append((x, y))
    return pts

CANDY = [(255, 90, 110), (255, 200, 60), (90, 200, 255), (120, 230, 120), (200, 120, 255), (255, 150, 60)]

def draw_jar(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    jw, jh = (380, 620) if c.v else (420, 520)
    cy = (y0 + y1) / 2 + (0 if c.v else 40)
    win = 0 if item["counts"][0] > item["counts"][1] else 1
    for k in range(2):
        cx = x0 + (x1 - x0) * (0.27 + 0.46 * k)
        bx = (cx - jw / 2, cy - jh / 2, cx + jw / 2, cy + jh / 2)
        s = eob((t - 0.3 - 0.3 * k) / 0.4) if phase == "ask" else 1
        if s < 0.05: continue
        n = item["counts"][k]; size = 52 * item["sizes"][k] * (1 if c.v else 0.95)
        pts = _jar_points(n, jw - 40, jh - 80, size, item.get("seed", 1) + k)
        shown = n
        if phase == "reveal": shown = n
        cnt = int(n * cl(pt / 1.6)) if phase == "reveal" else 0
        for i, (px, py) in enumerate(pts[:shown]):
            col = CANDY[(i * 7 + k) % 6]
            X, Y = bx[0] + 20 + px, bx[1] + 60 + py
            hl = phase == "reveal" and i < cnt
            d.ellipse((X - size / 2, Y - size / 2, X + size / 2, Y + size / 2), fill=col, outline=(255, 255, 255) if hl else (0, 0, 0, 60), width=4 if hl else 2)
        d.rounded_rectangle(bx, radius=60, outline=(220, 240, 255), width=10)
        d.rounded_rectangle((bx[0] + 40, bx[1] - 40, bx[2] - 40, bx[1] + 10), radius=16, fill=(200, 160, 110))
        _label(d, cx, bx[3] + 70, "AB"[k], c)
        if phase == "reveal":
            f = font(F_BOLD, 90); txt = str(cnt); tw = d.textlength(txt, font=f)
            d.text((cx - tw / 2, bx[1] + jh / 2 - 60), txt, font=f, fill=(255, 255, 255), stroke_width=8, stroke_fill=(20, 10, 40))
            if pt > 1.7 and k == win: glow_box(im, (bx[0] - 20, bx[1] - 60, bx[2] + 20, bx[3] + 20), r=60)
    if phase == "reveal":
        return x0 + (x1 - x0) * (0.27 + 0.46 * win), cy
    return c.W / 2, cy

# ---------------------------------------------------------------- How many fit
def draw_fit(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    cols, rows = item["grid"]  # container holds cols x rows items exactly
    cell = (140 if c.v else 105) * item.get("scale", 1)
    bw, bh = cols * cell + 40, rows * cell + 40
    cx = c.W / 2 if c.v else x0 + 420
    cy = y0 + (60 + bh / 2 if c.v else (y1 - y0) / 2 + 30)
    bx = (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2)
    d.rounded_rectangle(bx, radius=30, fill=(150, 100, 60), outline=(90, 60, 30), width=10)
    d.rounded_rectangle((bx[0] + 14, bx[1] + 14, bx[2] - 14, bx[3] - 14), radius=20, fill=(255, 245, 225))
    n = cols * rows
    # sample item for scale
    sx, sy = (bx[2] + 100, bx[1] + 70) if not c.v else (bx[2] + 60, bx[1] + 40)
    if phase != "reveal":
        paste(im, emoji_img(item["item"], cell * 0.85), sx, sy, eob((t - 0.6) / 0.4) if phase == "ask" else 1)
    if phase == "reveal":
        k = int(n * cl(pt / 1.8))
        for i in range(k):
            r_, q = divmod(i, cols)
            paste(im, emoji_img(item["item"], cell * 0.85), bx[0] + 20 + cell * (q + 0.5), bx[3] - 20 - cell * (r_ + 0.5))
        f = font(F_BOLD, 80); txt = str(k); tw = d.textlength(txt, font=f)
        d.text((cx - tw / 2, bx[3] + 20), txt, font=f, fill=c.accent, stroke_width=6, stroke_fill=(20, 10, 40))
    # options
    opts = item["options"]
    for k, o in enumerate(opts):
        if c.v:
            ox, oy = x0 + (x1 - x0) * (k + 0.5) / len(opts), bx[3] + 200; ow, oh = 270, 150
        else:
            ox, oy = x0 + 880 + k * 290, (y0 + y1) / 2 + 30; ow, oh = 250, 190
        s = eob((t - 1.2 - 0.25 * k) / 0.4) if phase == "ask" else 1
        if s < 0.05: continue
        fill = (255, 255, 255)
        if phase == "reveal" and pt > 1.9: fill = (40, 190, 90) if k == item["right"] else (150, 40, 55)
        d.rounded_rectangle((ox - ow / 2, oy - oh / 2, ox + ow / 2, oy + oh / 2), radius=30, fill=fill, outline=c.accent, width=6)
        f = font(F_BOLD, 80); tw = d.textlength(o, font=f)
        d.text((ox - tw / 2 + 25, oy - 56), o, font=f, fill=(30, 30, 60) if fill == (255, 255, 255) else (255, 255, 255))
        _label(d, ox - ow / 2 + 45, oy, "ABC"[k], c, r=32, size=42)
    if phase == "reveal":
        return cx, cy
    return c.W / 2, cy

# ---------------------------------------------------------------- Find the twins (procedural creatures)
def twins_set(seed):
    rnd = _rnd.Random(seed)
    base = dict(body=rnd.randrange(6), eyes=rnd.choice([1, 2, 3]), mouth=rnd.choice(["smile", "o", "flat"]),
                spots=rnd.randrange(4), horns=rnd.choice([0, 1]), cheeks=rnd.choice([0, 1]))
    alts = {"body": [i for i in range(6)], "eyes": [1, 2, 3], "mouth": ["smile", "o", "flat"], "spots": [0, 1, 2, 3], "horns": [0, 1], "cheeks": [0, 1]}
    feats = list(alts.keys())
    creatures = []
    used = set()
    for i in range(5):
        while True:
            f = rnd.choice(feats); v = rnd.choice([x for x in alts[f] if x != base[f]])
            if (f, v) not in used: used.add((f, v)); break
        cr = dict(base); cr[f] = v; creatures.append(cr)
    pair = rnd.sample(range(6), 2)
    order = []; ci = 0
    for i in range(6):
        if i in pair: order.append(dict(base))
        else: order.append(creatures[ci]); ci += 1
    return order, sorted(pair)

def _creature(cr, size):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = CANDY[cr["body"]]
    s = size
    if cr["horns"]:
        d.polygon([(s * 0.3, s * 0.28), (s * 0.24, s * 0.08), (s * 0.4, s * 0.22)], fill=(255, 240, 200))
        d.polygon([(s * 0.7, s * 0.28), (s * 0.76, s * 0.08), (s * 0.6, s * 0.22)], fill=(255, 240, 200))
    d.ellipse((s * 0.12, s * 0.18, s * 0.88, s * 0.92), fill=col, outline=(30, 30, 60), width=5)
    for k in range(cr["spots"]):
        sx, sy = [(0.3, 0.72), (0.7, 0.7), (0.5, 0.82)][k]
        d.ellipse((s * (sx - 0.05), s * (sy - 0.04), s * (sx + 0.05), s * (sy + 0.04)), fill=tuple(max(0, v - 60) for v in col))
    ex = {1: [0.5], 2: [0.38, 0.62], 3: [0.32, 0.5, 0.68]}[cr["eyes"]]
    for x in ex:
        d.ellipse((s * (x - 0.07), s * 0.36, s * (x + 0.07), s * 0.5), fill=(255, 255, 255), outline=(30, 30, 60), width=3)
        d.ellipse((s * (x - 0.03), s * 0.41, s * (x + 0.03), s * 0.47), fill=(30, 30, 60))
    if cr["mouth"] == "smile":
        d.arc((s * 0.36, s * 0.48, s * 0.64, s * 0.68), 20, 160, fill=(30, 30, 60), width=6)
    elif cr["mouth"] == "o":
        d.ellipse((s * 0.45, s * 0.56, s * 0.55, s * 0.66), fill=(30, 30, 60))
    else:
        d.line((s * 0.4, s * 0.62, s * 0.6, s * 0.62), fill=(30, 30, 60), width=6)
    if cr["cheeks"]:
        d.ellipse((s * 0.2, s * 0.52, s * 0.3, s * 0.6), fill=(255, 150, 170))
        d.ellipse((s * 0.7, s * 0.52, s * 0.8, s * 0.6), fill=(255, 150, 170))
    return im

def draw_twins(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    order, pair = twins_set(item["seed"])
    cols, rows = (2, 3) if c.v else (3, 2)
    if not c.v: y0 += 40
    cw, ch = (x1 - x0) / cols, (y1 - y0) / rows
    sz = int(min(cw, ch) * 0.82)
    centers = []
    for i, cr in enumerate(order):
        r_, k = divmod(i, cols)
        cx, cy = x0 + cw * (k + 0.5), y0 + ch * (r_ + 0.5)
        centers.append((cx, cy))
        s = eob((t - 0.3 - 0.12 * i) / 0.4) if phase == "ask" else 1
        a = 0.35 if (phase == "reveal" and i not in pair and pt > 0.3) else 1
        paste(im, _creature(cr, sz), cx, cy, s, a)
        _label(d, cx - sz * 0.45, cy - sz * 0.4, str(i + 1), c, r=34, size=44)
    if phase == "reveal":
        for i in pair:
            cx, cy = centers[i]; glow_box(im, (cx - sz / 2, cy - sz / 2, cx + sz / 2, cy + sz / 2), r=40)
        return centers[pair[0]]
    return c.W / 2, (y0 + y1) / 2

# ---------------------------------------------------------------- Gears
def _gear(r, teeth, col, ang):
    size = int(r * 2.5); im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx = cy = size / 2; pts = []
    for i in range(teeth * 2):
        a = ang + i * math.pi / teeth
        rr = r * (1.18 if i % 2 == 0 else 0.95)
        for da in (-0.32, 0.32):
            aa = a + da * math.pi / teeth
            pts.append((cx + rr * math.cos(aa), cy + rr * math.sin(aa)))
    d.polygon(pts, fill=col, outline=(30, 30, 60))
    d.ellipse((cx - r * 0.35, cy - r * 0.35, cx + r * 0.35, cy + r * 0.35), fill=(40, 40, 60))
    d.line((cx, cy, cx + r * 0.8 * math.cos(ang), cy + r * 0.8 * math.sin(ang)), fill=(255, 255, 255), width=6)
    return im

def gears_answer(item):
    same = item["n"] % 2 == 1
    first_cw = item["first"] == "cw"
    last_cw = first_cw if same else not first_cw
    return 0 if last_cw else 1

def _arrow_arc(d, cx, cy, r, cw, col, width=10):
    if cw:
        d.arc((cx - r, cy - r, cx + r, cy + r), 200, 340, fill=col, width=width)
        a = math.radians(340); hx, hy = cx + r * math.cos(a), cy + r * math.sin(a)
        d.polygon([(hx + 22, hy - 4), (hx - 12, hy - 20), (hx - 4, hy + 18)], fill=col)
    else:
        d.arc((cx - r, cy - r, cx + r, cy + r), 200, 340, fill=col, width=width)
        a = math.radians(200); hx, hy = cx + r * math.cos(a), cy + r * math.sin(a)
        d.polygon([(hx - 22, hy - 4), (hx + 12, hy - 20), (hx + 4, hy + 18)], fill=col)

def draw_gears(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    n = item["n"]
    r = 105 if c.v else 85
    pitch = r * 2.12
    if c.v:
        cols = 3; pos = []
        for i in range(n):
            row, k = divmod(i, cols)
            k = k if row % 2 == 0 else cols - 1 - k
            pos.append((c.W / 2 - pitch + k * pitch, y0 + 150 + row * pitch))
    else:
        pos = [(x0 + 200 + i * pitch, y0 + 220 + (60 if i % 2 else 0)) for i in range(n)]
    spin = (pt * 2.2) if phase == "reveal" else 0
    first_cw = item["first"] == "cw"
    cols_ = [(250, 180, 60), (90, 180, 240), (240, 110, 110), (120, 210, 120), (200, 140, 240), (250, 150, 80)]
    for i, (gx, gy) in enumerate(pos):
        dirn = (1 if first_cw else -1) * (1 if i % 2 == 0 else -1)
        g = _gear(r, 10, cols_[i % 6], dirn * spin + (math.pi / 10 if i % 2 else 0))
        s = eob((t - 0.2 - 0.15 * i) / 0.4) if phase == "ask" else 1
        paste(im, g, gx, gy, s)
    fx, fy = pos[0]
    _arrow_arc(d, fx, fy, r * 1.45, first_cw, c.accent)
    lx, ly = pos[-1]
    f = font(F_BOLD, 70); tw = d.textlength("?", font=f)
    if phase != "reveal": d.text((lx - tw / 2, ly - r * 1.75 - 30), "?", font=f, fill=c.accent, stroke_width=6, stroke_fill=(20, 10, 40))
    # options
    labels = ["Clockwise", "Anticlockwise"]
    for k in range(2):
        if c.v:
            ox, oy, ow, oh = x0 + (x1 - x0) * (k + 0.5) / 2, y1 - 40, 440, 170
        else:
            ox, oy, ow, oh = x0 + 1400, y0 + 160 + k * 230, 400, 180
        s = eob((t - 1.4 - 0.3 * k) / 0.4) if phase == "ask" else 1
        if s < 0.05: continue
        fill = (255, 255, 255)
        right = gears_answer(item)
        if phase == "reveal" and pt > 1.0: fill = (40, 190, 90) if k == right else (150, 40, 55)
        d.rounded_rectangle((ox - ow / 2, oy - oh / 2, ox + ow / 2, oy + oh / 2), radius=30, fill=fill, outline=c.accent, width=6)
        _arrow_arc(d, ox, oy + 10, 50, k == 0, (30, 30, 60) if fill == (255, 255, 255) else (255, 255, 255), 9)
        f = font(F_BOLD, 40); tw = d.textlength(labels[k], font=f)
        d.text((ox - tw / 2, oy + 30), labels[k], font=f, fill=(30, 30, 60) if fill == (255, 255, 255) else (255, 255, 255))
        _label(d, ox - ow / 2 + 40, oy - oh / 2 + 40, "AB"[k], c, r=30, size=40)
    if phase == "reveal":
        _arrow_arc(d, lx, ly, r * 1.45, gears_answer(item) == 0, (60, 255, 120))
        return lx, ly
    return c.W / 2, (y0 + y1) / 2

# ---------------------------------------------------------------- Which piece fits
def _tile(src, idx, n, size, rot=False):
    w = src.width / n; r_, k = divmod(idx, n)
    t_ = src.crop((int(k * w), int(r_ * w), int((k + 1) * w), int((r_ + 1) * w))).resize((size, size), Image.LANCZOS)
    return t_.transpose(Image.ROTATE_180) if rot else t_

def draw_piece(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    n = 3; S = 540 if c.v else 520
    src = Image.new("RGBA", (S, S), (255, 255, 255, 255))
    e = emoji_img(item["emoji"], S * 0.92); src.alpha_composite(e, (int(S / 2 - e.width / 2), int(S / 2 - e.height / 2)))
    if item.get("bg"):
        bgc = Image.new("RGBA", (S, S), tuple(item["bg"]) + (255,)); bgc.alpha_composite(src.copy()); src = bgc
    cx, cy = (c.W / 2, y0 + S / 2 - 30) if c.v else (x0 + 380, (y0 + y1) / 2 + 30)
    pic = src.copy(); pd = ImageDraw.Draw(pic)
    w = S / n; mi = item["missing"]; r_, k = divmod(mi, n)
    hole = (k * w, r_ * w, (k + 1) * w, (r_ + 1) * w)
    pd.rectangle(hole, fill=(40, 40, 60, 255))
    pd.text((hole[0] + w / 2 - 25, hole[1] + w / 2 - 50), "?", font=font(F_BOLD, 90), fill=c.accent)
    frame = Image.new("RGBA", (S + 24, S + 24), (255, 255, 255, 255)); frame.alpha_composite(pic, (12, 12))
    paste(im, frame, cx, cy, eob((t - 0.2) / 0.5) if phase == "ask" else 1)
    opts = item["options"]
    for q, o in enumerate(opts):
        rot = isinstance(o, str) and o.endswith("r"); idx = int(str(o).rstrip("r"))
        ts = 200 if c.v else 190
        tile = _tile(src, idx, n, ts, rot)
        if c.v:
            ox, oy = x0 + (x1 - x0) * (q + 0.5) / len(opts), cy + S / 2 + 200
        else:
            ox, oy = x0 + 1000 + q * 300, (y0 + y1) / 2 + 30
        if phase == "reveal" and q == item["right"]:
            m = eo(pt / 0.8); tx, ty = cx - S / 2 + w * (k + 0.5), cy - S / 2 + w * (r_ + 0.5)
            ox, oy = ox + (tx - ox) * m, oy + (ty - oy) * m
            tile = tile.resize((int(ts + (w - ts) * m), int(ts + (w - ts) * m)))
        s = eob((t - 1.2 - 0.25 * q) / 0.4) if phase == "ask" else 1
        a = 0.4 if (phase == "reveal" and q != item["right"]) else 1
        fr = Image.new("RGBA", (tile.width + 12, tile.height + 12), c.accent + (255,)); fr.alpha_composite(tile, (6, 6))
        paste(im, fr, ox, oy, s, a)
        if not (phase == "reveal" and q == item["right"]):
            _label(d, ox - ts / 2, oy - ts / 2, "ABC"[q], c, r=30, size=40)
    if phase == "reveal":
        return cx, cy
    return c.W / 2, cy

# ---------------------------------------------------------------- Illusion check
def illusion_answer(item):
    dlt = item.get("diff", 0)
    return 2 if dlt == 0 else (0 if dlt > 0 else 1)

def draw_illusion(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    kind = item["kind"]; dlt = item.get("diff", 0)
    a = eo((t - 0.3) / 0.5) if phase == "ask" else 1
    col = (255, 255, 255, int(255 * a))
    cx = c.W / 2 if c.v else x0 + 520
    centers = []
    if kind == "lines":
        L = 420 if c.v else 440
        for k in range(2):
            ln = L * (1 + (dlt * 0.06 if k == 0 else -dlt * 0.06))
            yy = y0 + 70 + k * 240 if c.v else y0 + 200 + k * 260
            xa, xb = cx - ln / 2, cx + ln / 2
            d.line((xa, yy, xb, yy), fill=col, width=12)
            fin = 70
            if k == 0:
                for sx, sgn in ((xa, 1), (xb, -1)):
                    d.line((sx, yy, sx + sgn * fin, yy - fin), fill=col, width=10); d.line((sx, yy, sx + sgn * fin, yy + fin), fill=col, width=10)
            else:
                for sx, sgn in ((xa, -1), (xb, 1)):
                    d.line((sx, yy, sx + sgn * fin, yy - fin), fill=col, width=10); d.line((sx, yy, sx + sgn * fin, yy + fin), fill=col, width=10)
            centers.append((xa, xb, yy))
            _label(d, cx - 330 if c.v else cx - 380, yy, "AB"[k], c)
        if phase == "reveal":
            for k, (xa, xb, yy) in enumerate(centers):
                m = eo(pt / 0.6)
                d.line((xa, yy - 6, xa, yy + 6 + (centers[1][2] - yy if k == 0 else 0) * m), fill=(60, 255, 120), width=6)
                d.line((xb, yy - 6, xb, yy + 6 + (centers[1][2] - yy if k == 0 else 0) * m), fill=(60, 255, 120), width=6)
    else:  # circles (Ebbinghaus)
        R = 55 if c.v else 58
        for k in range(2):
            rr = R * (1 + (dlt * 0.07 if k == 0 else -dlt * 0.07))
            px = (cx - 230 + k * 460) if c.v else (cx - 260 + k * 520)
            py = y0 + 230 if c.v else (y0 + y1) / 2 + 30
            ring_r, ring_n, ring_d = ((rr * 1.5, 6, rr * 2.9) if k == 0 else (rr * 0.38, 8, rr * 1.65))
            for j in range(ring_n):
                an = j * 2 * math.pi / ring_n
                qx, qy = px + ring_d * math.cos(an), py + ring_d * math.sin(an)
                d.ellipse((qx - ring_r, qy - ring_r, qx + ring_r, qy + ring_r), fill=(160, 170, 200, int(255 * a)))
            d.ellipse((px - rr, py - rr, px + rr, py + rr), fill=(255, 150, 60, int(255 * a)))
            centers.append((px, py, rr))
            _label(d, px, py + (265 if c.v else 270), "AB"[k], c)
        if phase == "reveal":
            m = eo(pt / 0.8)
            px, py, rr = centers[0]
            tx, ty, tr = centers[1]
            gx = px + (tx - px) * m
            d.ellipse((gx - rr, py - rr, gx + rr, py + rr), outline=(60, 255, 120), width=8)
    # options
    labels = ["A is bigger", "B is bigger", "Same size"] if kind == "circles" else ["A is longer", "B is longer", "Same length"]
    for k in range(3):
        if c.v:
            ox, oy, ow, oh = c.W / 2, y1 - 250 + k * 122 + (40 if kind == "circles" else 0), 640, 105
        else:
            ox, oy, ow, oh = x0 + 1360, y0 + 140 + k * 170, 460, 130
        s = eob((t - 1.3 - 0.25 * k) / 0.4) if phase == "ask" else 1
        if s < 0.05: continue
        fill = (255, 255, 255)
        if phase == "reveal" and pt > 0.9: fill = (40, 190, 90) if k == illusion_answer(item) else (150, 40, 55)
        d.rounded_rectangle((ox - ow / 2, oy - oh / 2, ox + ow / 2, oy + oh / 2), radius=26, fill=fill, outline=c.accent, width=6)
        f = font(F_BOLD, 50 if c.v else 46); tw = d.textlength(labels[k], font=f)
        d.text((ox - tw / 2 + 20, oy - 34), labels[k], font=f, fill=(30, 30, 60) if fill == (255, 255, 255) else (255, 255, 255))
    if phase == "reveal":
        return cx, (y0 + y1) / 2
    return cx, (y0 + y1) / 2

# ---------------------------------------------------------------- Rotate match
def _shape_img(cells, color, cell=60):
    n = 4; im = Image.new("RGBA", (n * cell + 8, n * cell + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for (r_, k) in cells:
        d.rounded_rectangle((4 + k * cell, 4 + r_ * cell, 4 + (k + 1) * cell - 4, 4 + (r_ + 1) * cell - 4), radius=10, fill=color)
    d.ellipse((4 + cells[0][1] * cell + cell * 0.3, 4 + cells[0][0] * cell + cell * 0.3, 4 + cells[0][1] * cell + cell * 0.66, 4 + cells[0][0] * cell + cell * 0.66), fill=(255, 255, 255))
    return im

def draw_rotate(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    col = tuple(item.get("color", [255, 120, 80]))
    base = _shape_img([tuple(x) for x in item["cells"]], col, 70 if c.v else 62)
    oc = (c.W / 2, y0 + 200) if c.v else (x0 + 300, (y0 + y1) / 2 + 30)
    d.rounded_rectangle((oc[0] - base.width / 2 - 30, oc[1] - base.height / 2 - 30, oc[0] + base.width / 2 + 30, oc[1] + base.height / 2 + 30), radius=30, fill=(255, 255, 255, 230))
    rot_now = 0
    if phase == "reveal":
        target = item["opts"][item["right"]][0]
        rot_now = target * eo(pt / 1.0)
    paste(im, base.rotate(-rot_now, expand=True, resample=Image.BICUBIC), oc[0], oc[1], eob((t - 0.2) / 0.5) if phase == "ask" else 1)
    for k, (ang, mirror) in enumerate(item["opts"]):
        img = base.transpose(Image.FLIP_LEFT_RIGHT) if mirror else base
        img = img.rotate(-ang, expand=True, resample=Image.BICUBIC)
        if c.v:
            ox, oy = x0 + (x1 - x0) * (k + 0.5) / 3, y0 + 680
        else:
            ox, oy = x0 + 780 + k * 330, (y0 + y1) / 2 + 30
        bw = 290 if c.v else 290
        s = eob((t - 1.0 - 0.25 * k) / 0.4) if phase == "ask" else 1
        if s < 0.05: continue
        fill = (255, 255, 255, 230)
        if phase == "reveal" and pt > 1.0: fill = (40, 190, 90) if k == item["right"] else (150, 40, 55)
        d.rounded_rectangle((ox - bw / 2, oy - bw / 2, ox + bw / 2, oy + bw / 2), radius=30, fill=fill, outline=c.accent, width=6)
        paste(im, img, ox, oy, s * 0.82, 0.5 if (phase == "reveal" and pt > 1.0 and k != item["right"]) else 1)
        _label(d, ox - bw / 2 + 10, oy - bw / 2 + 10, "ABC"[k], c, r=30, size=40)
    if phase == "reveal":
        k = item["right"]
        return (x0 + (x1 - x0) * (k + 0.5) / 3, y0 + 680) if c.v else (x0 + 780 + k * 330, (y0 + y1) / 2 + 30)
    return c.W / 2, (y0 + y1) / 2

# ---------------------------------------------------------------- What's at the bottom (stack)
SHAPE_COLS = {"red": (235, 70, 80), "blue": (70, 140, 240), "green": (70, 200, 110), "yellow": (250, 200, 50), "purple": (170, 100, 230), "orange": (250, 140, 50)}

def _draw_shape(d, kind, color, cx, cy, s, outline=(30, 30, 60)):
    if kind == "circle": d.ellipse((cx - s, cy - s, cx + s, cy + s), fill=color, outline=outline, width=6)
    elif kind == "square": d.rounded_rectangle((cx - s, cy - s, cx + s, cy + s), radius=16, fill=color, outline=outline, width=6)
    elif kind == "triangle": d.polygon([(cx, cy - s * 1.1), (cx + s * 1.1, cy + s * 0.8), (cx - s * 1.1, cy + s * 0.8)], fill=color, outline=outline)
    elif kind == "star":
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5; rr = s * (1.15 if i % 2 == 0 else 0.5)
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, fill=color, outline=outline)

def draw_stack(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    shapes = item["shapes"]  # bottom -> top: [kind, color, dx, dy, size]
    cx, cy = (c.W / 2, y0 + 300) if c.v else (x0 + 420, (y0 + y1) / 2 + 30)
    sc = 1.0 if c.v else 0.9
    n = len(shapes)
    for i, (kind, colname, dx, dy, s) in enumerate(shapes):
        lift = 0
        if phase == "reveal":
            order_from_top = n - 1 - i
            if i != 0: lift = eo((pt - order_from_top * 0.35) / 0.35)
        ap = eob((t - 0.2 - 0.25 * i) / 0.35) if phase == "ask" else 1
        if ap < 0.05: continue
        if lift > 0.6: continue
        px, py = cx + dx * sc, cy + dy * sc - lift * 500
        _draw_shape(d, kind, SHAPE_COLS[colname], px, py, s * sc * ap)
    opts = item["options"]
    for k, (kind, colname) in enumerate(opts):
        if c.v:
            ox, oy = x0 + (x1 - x0) * (k + 0.5) / len(opts), y0 + 720
        else:
            ox, oy = x0 + 950 + k * 300, (y0 + y1) / 2 + 30
        bw = 250
        s = eob((t - 1.6 - 0.25 * k) / 0.4) if phase == "ask" else 1
        if s < 0.05: continue
        fill = (255, 255, 255, 230)
        if phase == "reveal" and pt > 0.35 * n: fill = (40, 190, 90) if k == item["right"] else (150, 40, 55)
        d.rounded_rectangle((ox - bw / 2, oy - bw / 2, ox + bw / 2, oy + bw / 2), radius=30, fill=fill, outline=c.accent, width=6)
        _draw_shape(d, kind, SHAPE_COLS[colname], ox, oy + 10, 70 * s)
        _label(d, ox - bw / 2 + 10, oy - bw / 2 + 10, "ABC"[k], c, r=30, size=40)
    if phase == "reveal":
        return cx, cy
    return cx, cy

# ---------------------------------------------------------------- Quick count
def draw_count(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    rnd = _rnd.Random(item.get("seed", 1))
    objs = [item["target"]] * item["n"] + [rnd.choice(item["others"]) for _ in range(item["m"])]
    rnd.shuffle(objs)
    bx = (x0 + 20, y0 - 20, x1 - 20, y0 + 470) if c.v else (x0 + 40, y0 + 40, x0 + 940, y1 - 20)
    cols, rows = (5, 4) if c.v else (6, 4)
    cells = [(r_, k) for r_ in range(rows) for k in range(cols)]; rnd.shuffle(cells)
    cw, ch = (bx[2] - bx[0]) / cols, (bx[3] - bx[1]) / rows
    show = phase == "ask" and 0.5 < t < 2.7 or phase == "reveal"
    d.rounded_rectangle(bx, radius=40, fill=(255, 255, 255, 230))
    hl = 0
    for i, em in enumerate(objs[:len(cells)]):
        r_, k = cells[i]
        px = bx[0] + cw * (k + 0.5) + rnd.uniform(-cw * 0.15, cw * 0.15); py = bx[1] + ch * (r_ + 0.5) + rnd.uniform(-ch * 0.12, ch * 0.12)
        if show:
            a = 0.3 if (phase == "reveal" and em != item["target"]) else 1
            paste(im, emoji_img(em, min(cw, ch) * 0.7), px, py, 1, a)
            if phase == "reveal" and em == item["target"]:
                hl += 1
                if hl <= int(item["n"] * cl(pt / 1.4)):
                    d.ellipse((px - 50, py - 50, px + 50, py + 50), outline=(60, 255, 120), width=7)
    if not show:
        mx, my = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
        if phase == "ask" and t <= 0.5:
            f = font(F_BOLD, 80); txt = "READY?"; tw = d.textlength(txt, font=f); d.text((mx - tw / 2, my - 50), txt, font=f, fill=(30, 30, 60))
        else:
            f = font(F_BOLD, 200); tw = d.textlength("?", font=f); d.text((mx - tw / 2, my - 130), "?", font=f, fill=(30, 30, 60))
    # target hint
    hx, hy = (c.W / 2, bx[3] + 75) if c.v else (x0 + 1250, y0 + 90)
    paste(im, emoji_img(item["target"], 110), hx, hy)
    opts = item["options"]
    for k, o in enumerate(opts):
        if c.v:
            ox, oy, ow, oh = x0 + (x1 - x0) * (k + 0.5) / 3, bx[3] + 240, 260, 150
        else:
            ox, oy, ow, oh = x0 + 1250, y0 + 260 + k * 190, 340, 150
        s = eob((t - 2.8 - 0.2 * k) / 0.4) if phase == "ask" else 1
        if s < 0.05: continue
        fill = (255, 255, 255)
        if phase == "reveal" and pt > 1.5: fill = (40, 190, 90) if k == item["right"] else (150, 40, 55)
        d.rounded_rectangle((ox - ow / 2, oy - oh / 2, ox + ow / 2, oy + oh / 2), radius=30, fill=fill, outline=c.accent, width=6)
        f = font(F_BOLD, 90); tw = d.textlength(o, font=f)
        d.text((ox - tw / 2 + 20, oy - 62), o, font=f, fill=(30, 30, 60) if fill == (255, 255, 255) else (255, 255, 255))
        _label(d, ox - ow / 2 + 40, oy, "ABC"[k], c, r=30, size=40)
    return ((bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2)

# ---------------------------------------------------------------- Remember the order
def draw_order(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    seq = item["seq"]; n = len(seq)
    rowy = y0 + 140 if c.v else y0 + 160
    gap = (x1 - x0) / n
    sz = min(170, gap * 0.75)
    for i, em in enumerate(seq):
        cx = x0 + gap * (i + 0.5)
        box = (cx - sz * 0.65, rowy - sz * 0.65, cx + sz * 0.65, rowy + sz * 0.65)
        d.rounded_rectangle(box, radius=26, fill=(255, 255, 255, 230))
        f = font(F_BOLD, 40); L = str(i + 1); tw = d.textlength(L, font=f)
        d.text((cx - tw / 2, box[3] + 10), L, font=f, fill=c.accent)
        if phase == "ask":
            ti = 0.5 + i * 0.75
            if ti <= t < 0.5 + n * 0.75 + 0.6:
                paste(im, emoji_img(em, sz), cx, rowy, eob((t - ti) / 0.3))
            elif t >= 0.5 + n * 0.75 + 0.6:
                qf = font(F_BOLD, sz * 0.7); tw = d.textlength("?", font=qf); d.text((cx - tw / 2, rowy - sz * 0.5), "?", font=qf, fill=(30, 30, 60))
        elif phase == "count":
            qf = font(F_BOLD, sz * 0.7); tw = d.textlength("?", font=qf); d.text((cx - tw / 2, rowy - sz * 0.5), "?", font=qf, fill=(30, 30, 60))
        else:
            paste(im, emoji_img(em, sz), cx, rowy, 1, 1 if i + 1 == item["ask_pos"] else 0.35)
            if i + 1 == item["ask_pos"]: glow_box(im, box, r=26)
    opts = item["options"]
    for k, o in enumerate(opts):
        if c.v:
            ox, oy = x0 + (x1 - x0) * (k + 0.5) / 3, y0 + 560
        else:
            ox, oy = x0 + (x1 - x0) * (k + 0.5) / 3, y0 + 480
        bw = 250 if c.v else 230
        s = eob((t - (0.5 + n * 0.75 + 0.8) - 0.2 * k) / 0.4) if phase == "ask" else 1
        if s < 0.05: continue
        fill = (255, 255, 255, 230)
        if phase == "reveal" and pt > 0.5: fill = (40, 190, 90) if k == item["right"] else (150, 40, 55)
        d.rounded_rectangle((ox - bw / 2, oy - bw / 2, ox + bw / 2, oy + bw / 2), radius=30, fill=fill, outline=c.accent, width=6)
        paste(im, emoji_img(o, bw * 0.55), ox, oy + 10, s)
        _label(d, ox - bw / 2 + 10, oy - bw / 2 + 10, "ABC"[k], c, r=30, size=40)
    if phase == "reveal":
        return x0 + gap * (item["ask_pos"] - 0.5), rowy
    return c.W / 2, (y0 + y1) / 2

DRAW.update({"jar": draw_jar, "fit": draw_fit, "twins": draw_twins, "gears": draw_gears, "piece": draw_piece,
             "illusion": draw_illusion, "rotate": draw_rotate, "stack": draw_stack, "count": draw_count, "order": draw_order})

_old_min_ask = min_ask
def min_ask(item):
    t_ = item.get("type")
    if t_ == "count": return 3.4
    if t_ == "order": return 0.5 + 0.75 * len(item["seq"]) + 1.4
    return _old_min_ask(item)
