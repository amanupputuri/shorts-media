"""Hidden Animals v2: example intro, Hoot voice throughout, slide transitions, no reveal."""
import math, json, wave, subprocess, sys, random
import numpy as np
from PIL import Image, ImageDraw
import ws, os
from ws import W, H, FPS, GOLD, font, text_c, bg, cxy, fit, xform, paste_bottom, ease_back
from ws import COLS, ROWS, CELL, GX, GY, GW, GH, G, CH_Y0, CH_Y1, TITLE_Y, HP, ICON, SOC, PUZ, GRIDS

SEGV = json.load(open(os.path.join(ws.BASE,'segs.json')))
VL = [b - a + 0.08 for a, b in SEGV]                     # line durations
LINES = [(3, None, 4), (5, 6, 7), (8, None, 9), (10, 11, 12), (13, 14, 15),
         (16, 17, 18), (19, 20, 21), (22, None, 23), (24, 25, 26), (27, None, 28)]
ASKS = [4, 4, 4, 4, 5, 5, 5, 5, 5, 5]
TR, OUT = 0.5, 0.35

# ---------- timeline ----------
VOICE = []          # (line index, time)
EX_DUR = 0.2 + VL[0] + 0.35 + VL[1] + 0.35 + VL[2] + 0.3
VOICE += [(0, 0.2), (1, 0.2 + VL[0] + 0.35), (2, 0.2 + VL[0] + 0.35 + VL[1] + 0.35)]
EX_MARK = VOICE[1][1] + 2.2                       # red mark draws while saying "diagonally, backwards"
P = []
t = EX_DUR
for k, (s, m, e) in enumerate(LINES):
    ann = max(1.1, VL[s] + 0.35)
    end = max(1.3, (VL[e] if e is not None else 0) + 0.55)
    p = dict(t0=t, ann=ann, ask=ASKS[k], end=end)
    p['dur'] = TR + ann + ASKS[k] + end
    VOICE.append((s, t + TR - 0.1))
    if m is not None: VOICE.append((m, t + TR + ann + 0.3))
    if e is not None: VOICE.append((e, t + TR + ann + ASKS[k] + 0.15))
    P.append(p); t += p['dur']
BAR = 240 / 118
pad = math.ceil(t / BAR) * BAR - t
P[-1]['end'] += pad; P[-1]['dur'] += pad
TOTAL = t + pad

# voice envelope for "talking" Hoot
SR = 44100
_env = np.zeros(int(TOTAL * SR) + SR)
for li, vt in VOICE:
    with wave.open(os.path.join(ws.VOICE_DIR, f'l{li:02d}.wav')) as w:
        a = np.abs(np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768)
    s = int(vt * SR); _env[s:s + len(a)] = np.maximum(_env[s:s + len(a)], a[:len(_env) - s])
_k = int(0.06 * SR); _env = np.convolve(_env, np.ones(_k) / _k, 'same'); _env /= _env.max() + 1e-9
def talk(t): return float(_env[min(len(_env) - 1, int(t * SR))])

# ---------- example grid: ANIMAL diagonal backwards ----------
random.seed(11)
EXG = [[random.choice('BCDEFGHJKOPQRSTUVWXYZ') for _ in range(COLS)] for _ in range(ROWS)]
for k, ch in enumerate('ANIMAL'):
    EXG[5 - k][5 - k] = ch          # reads from bottom-right up to top-left

def draw_grid(d, grid, s=1.0):
    fc = font('Bold', max(4, int(86 * s)))
    for r in range(ROWS):
        for c in range(COLS):
            x0, y0 = cxy(r, c); hw = CELL / 2 * s
            d.rounded_rectangle((x0 - hw, y0 - hw, x0 + hw, y0 + hw), max(1, int(22 * s)), fill=(255, 255, 255, 235))
            ch = grid[r][c]; bb = d.textbbox((0, 0), ch, font=fc)
            d.text((x0 - (bb[2] + bb[0]) / 2, y0 - (bb[3] + bb[1]) / 2), ch, font=fc, fill=(40, 22, 80))

def chip_row(im, d, word, icon, color=GOLD):
    fz = font('Bold', 74)
    tw = d.textlength(word, font=fz) + 70
    ic = None
    if icon is not None:
        ic = fit(icon, 150) if icon.width / icon.height < 1.3 else fit(icon, 190, True)
    total = (ic.width + 24 if ic else 0) + tw
    x = (W - total) / 2
    cx = x + (ic.width + 24 if ic else 0)
    d.rounded_rectangle((cx, CH_Y0, cx + tw, CH_Y1), 30, fill=color)
    d.text((cx + 35, CH_Y0 + 8), word, font=fz, fill=(25, 12, 50))
    return (ic, int(x), (CH_Y0 + CH_Y1) // 2 - (ic.height // 2 if ic else 0))

def badge(im, kind, lt):
    bi = fit(SOC[kind], 110, True)
    pop = ease_back(lt / 0.5)
    tap = (lt % 1.6) / 1.6
    sq = 1 - 0.18 * math.exp(-((tap - 0.08) / 0.05) ** 2)
    ang = (14 * math.sin(lt * 9) * math.exp(-3 * ((lt - 0.2) % 1.6))) if kind == 'sub' else 10 * math.sin(lt * 5)
    b2 = xform(bi, pop * (2 - sq), pop * sq, ang)
    bx, byy = 95, 107
    glow = Image.new('RGBA', (W, H)); gd = ImageDraw.Draw(glow)
    rr = 70 + 40 * tap
    gd.ellipse((bx - rr, byy - rr, bx + rr, byy + rr), outline=(255, 255, 255, int(160 * (1 - tap))), width=6)
    for k in range(6):
        a = k * math.pi / 3 + 0.4; r1 = 60 + 70 * tap; rad = 7 * (1 - tap)
        sx_, sy_ = bx + r1 * math.cos(a), byy + r1 * math.sin(a)
        if rad > 0.5: gd.ellipse((sx_ - rad, sy_ - rad, sx_ + rad, sy_ + rad), fill=(255, 220, 90, int(255 * (1 - tap))))
    im = Image.alpha_composite(im, glow)
    im.alpha_composite(b2, (int(bx - b2.width / 2), int(byy - b2.height / 2)))
    lab = 'LIKE' if kind == 'like' else 'SUBSCRIBE'
    ld = ImageDraw.Draw(im); lf = font('Bold', 34); lw = ld.textlength(lab, font=lf)
    lx = 164; la = int(255 * min(1, max(0, (lt - 0.15) / 0.3)))
    ld.rounded_rectangle((lx, byy - 28, lx + lw + 36, byy + 28), 28, fill=(230, 40, 60, la) if kind == 'sub' else (40, 120, 255, la))
    ld.text((lx + 18, byy - 24), lab, font=lf, fill=(255, 255, 255, la))
    return im

def hoot(im, t, pose):
    hh = 300
    base = fit(HP[pose], hh)
    tk = talk(t)
    breath = 1 + 0.025 * math.sin(t * 4)
    sx, sy = 1 / breath, breath
    sy *= 1 + 0.07 * tk; sx *= 1 - 0.035 * tk                # bob with the voice
    ang = 4 * math.sin(t * 2.2) + 6 * tk * math.sin(t * 14)
    lift = 18 * tk
    if pose == 'magnify': ang += 5 * math.sin(t * 3.5)
    h2 = xform(base, sx, sy, ang)
    paste_bottom(im, h2, 20 + base.width / 2, H - 20 - lift)
    return im

def frame(t):
    im = bg(t)
    if t < EX_DUR:   # ---------- HOW TO PLAY example ----------
        lt = t
        ov = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(ov)
        a = int(255 * min(1, lt / 0.3))
        text_c(d, 'HOW TO PLAY', TITLE_Y - 12, font('Bold', 56), (255, 255, 255, a), 4)
        chip_row(ov, d, 'ANIMAL', None, (255, 120, 120))
        s = ease_back((lt - 0.2) / 0.5) if lt > 0.2 else 0
        if s > 0: draw_grid(d, EXG, min(1.05, s))
        im = Image.alpha_composite(im, ov)
        if lt > EX_MARK:   # red marker line from bottom-right to top-left
            pr = min(1, (lt - EX_MARK) / 0.8)
            ln = Image.new('RGBA', (W, H)); ld = ImageDraw.Draw(ln)
            xa, ya = cxy(5, 5); xb, yb = cxy(0, 0)
            xb = xa + (xb - xa) * pr; yb = ya + (yb - ya) * pr
            ld.line((xa, ya, xb, yb), fill=(235, 30, 50, 200), width=104)
            for xx, yy in ((xa, ya), (xb, yb)): ld.ellipse((xx - 52, yy - 52, xx + 52, yy + 52), fill=(235, 30, 50, 200))
            im = Image.alpha_composite(im, ln)
            if pr >= 1:   # letters turn white + arrow hint
                d2 = ImageDraw.Draw(im); fc = font('Bold', 86)
                for k in range(6):
                    x0, y0 = cxy(5 - k, 5 - k); ch = EXG[5 - k][5 - k]; bb = d2.textbbox((0, 0), ch, font=fc)
                    d2.text((x0 - (bb[2] + bb[0]) / 2, y0 - (bb[3] + bb[1]) / 2), ch, font=fc, fill=(255, 255, 255))
                by = GY + GH + G
                text_c(d2, 'DIAGONAL + BACKWARDS!', by + 10, font('Bold', 58), (255, 210, 90), 5)
        return hoot(im, t, 'cheer' if lt > EX_MARK + 0.8 else 'think').convert('RGB')

    i = max(k for k in range(len(P)) if P[k]['t0'] <= t)
    p = P[i]; lt = t - p['t0']
    title, words, kind_, _, _ = PUZ[i]; grid, _ = GRIDS[i]
    a0 = TR + p['ann']; a1 = a0 + p['ask']
    # content layer (slides in / out)
    ov = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(ov)
    text_c(d, title.upper(), TITLE_Y - 12, font('Bold', 56), (255, 255, 255), 4)
    ic = chip_row(ov, d, words[0], ICON[words[0]])
    draw_grid(d, grid)
    if lt < TR: off = W * (1 - ease_back(lt / TR))
    elif lt > p['dur'] - OUT: off = -W * ((lt - (p['dur'] - OUT)) / OUT) ** 2
    else: off = 0
    # animated icon onto content layer
    icim, ix, iy = ic
    pop = ease_back((lt - TR * 0.6) / 0.45)
    ang = 8 * math.sin(t * 5)
    if a0 <= lt < a1: ang = 10 * math.sin(t * 7)
    i2 = xform(icim, max(0.01, pop), max(0.01, pop), ang)
    ov.alpha_composite(i2, (int(ix + icim.width / 2 - i2.width / 2), int(iy + icim.height / 2 - i2.height / 2)))
    sh = Image.new('RGBA', (W, H)); sh.alpha_composite(ov, (int(off), 0)) if off >= 0 else sh.paste(ov.crop((int(-off), 0, W, H)), (0, 0))
    im = Image.alpha_composite(im, sh)
    d = ImageDraw.Draw(im)
    # top-right progress
    d.rounded_rectangle((W - 290, 70, W - 40, 134), 32, fill=(90, 70, 140))
    pf = font('Bold', 34); pt = f"PUZZLE {i+1}/10"
    d.text((W - 165 - d.textlength(pt, font=pf) / 2, 78), pt, font=pf, fill=(255, 255, 255))
    for k in range(10):
        x = W - 165 + (k - 4.5) * 25
        d.ellipse((x - 7, 157, x + 7, 171), fill=GOLD if k <= i else (90, 70, 140))
    # timer / status (stays put)
    by = GY + GH + G
    if off == 0:
        d.rounded_rectangle((GX, by, GX + GW, by + 34), 17, fill=(90, 70, 140))
        if a0 <= lt < a1:
            k = (lt - a0) / p['ask']
            d.rounded_rectangle((GX, by, GX + GW * (1 - k), by + 34), 17, fill=GOLD if k < 0.75 else (255, 90, 90))
            n = math.ceil(p['ask'] - (lt - a0))
            sc = 1 + 0.25 * max(0, 1 - ((lt - a0) % 1) / 0.2)
            text_c(d, str(n), by + 44, font('Bold', int(90 * sc)), (255, 255, 255), 5)
            if i == 4:   # pause hint
                hf = font('Bold', 38); txt = '⏸  PAUSE FOR MORE TIME'
                tw_ = d.textlength('II  PAUSE FOR MORE TIME', font=hf)
                d.rounded_rectangle(((W - tw_) / 2 - 24, by + 160, (W + tw_) / 2 + 24, by + 224), 32, fill=(255, 255, 255))
                text_c(d, 'II  PAUSE FOR MORE TIME', by + 168, hf, (60, 30, 110))
        elif lt < a0:
            text_c(d, 'GET READY…', by + 50, font('Bold', 64), (255, 255, 255), 4)
        else:
            text_c(d, "TIME'S UP!", by + 50, font('Bold', 80), (255, 120, 120), 5)
    im = badge(im, 'like' if i < 5 else 'sub', lt)
    pose = 'magnify' if a0 <= lt < a1 else ('cheer' if lt >= a1 else 'think')
    return hoot(im, t, pose).convert('RGB')

def events():
    ev = []
    for i, p in enumerate(P):
        s = p['t0']; a0 = s + TR + p['ann']
        ev += [('whoosh', s), ('boop', s + 0.05), ('pop', s + TR * 0.6)]
        ev += [('tick', a0 + j) for j in range(p['ask'])]
        ev += [('pop', a0 + p['ask']), ('whoosh', s + p['dur'] - OUT)]
    ev += [('pop', 0.3), ('swish', EX_MARK), ('ding', EX_MARK + 0.8)]
    return ev

if __name__ == '__main__':
    out = sys.argv[1]
    if len(sys.argv) > 2:
        ts = [float(x) for x in sys.argv[2:]]
        ims = [frame(x).resize((360, 640)) for x in ts]
        sh = Image.new('RGB', (360 * len(ims), 640))
        for k, m in enumerate(ims): sh.paste(m, (360 * k, 0))
        sh.save(out); sys.exit()
    pr = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for f in range(int(TOTAL * FPS)):
        pr.stdin.write(frame(f / FPS).tobytes())
    pr.stdin.close(); pr.wait()
