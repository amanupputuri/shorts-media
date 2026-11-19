"""Word/number search Short — silent draft. 1080x1920, 30fps."""
import os
BASE = os.path.dirname(os.path.abspath(__file__))
VOICE_DIR = os.environ.get('VOICE_DIR', os.path.join(BASE, 'sample_voice'))
import random, math, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
F = '/usr/share/fonts/truetype/google-fonts/Poppins-'
GOLD = (255, 196, 70)
COLS, ROWS = 6, 6
random.seed(7)

# (title, words, kind, placements: (word, row, col, dr, dc))
PUZ = [
    ("Find the animal", ["LION"], "L", [("LION", 4, 0, 0, 1)], 0),
    ("Find the animal", ["BEAR"], "L", [("BEAR", 0, 1, 1, 0)], 0),
    ("Find the animal", ["DUCK"], "L", [("DUCK", 1, 2, 0, 1)], 0),
    ("Find the animal", ["FISH"], "L", [("FISH", 2, 5, 1, 0)], 1),
    ("Find the animal", ["WOLF"], "L", [("WOLF", 1, 5, 0, -1)], 1),
    ("Find the animal", ["DEER"], "L", [("DEER", 5, 4, -1, 0)], 1),
    ("Find the animal", ["SEAL"], "L", [("SEAL", 0, 0, 1, 1)], 2),
    ("Find the animal", ["FROG"], "L", [("FROG", 2, 2, 1, 1)], 2),
    ("Find the animal", ["CRAB"], "L", [("CRAB", 5, 0, -1, 1)], 2),
    ("Find the animal", ["GOAT"], "L", [("GOAT", 5, 3, -1, -1)], 2),
]
DECOY = {"L": "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "N": "0123456789"}

def build(p):
    title, words, kind, pl, lvl = p
    g = [[None] * COLS for _ in range(ROWS)]
    cells = []
    for w, r, c, dr, dc in pl:
        path = []
        for i, ch in enumerate(w):
            rr, cc = r + dr * i, c + dc * i
            assert 0 <= rr < ROWS and 0 <= cc < COLS, (w, rr, cc)
            assert g[rr][cc] in (None, ch), (w, rr, cc, g[rr][cc])
            g[rr][cc] = ch
            path.append((rr, cc))
        cells.append(path)
    tw="".join(words); base=[ch for ch in DECOY[kind] if ch not in tw]
    pool = base if lvl==0 else (list(DECOY[kind]) if lvl==1 else list(DECOY[kind])+list(tw)*4)
    for r in range(ROWS):
        for c in range(COLS):
            if g[r][c] is None:
                g[r][c] = random.choice(pool)
    # make sure no accidental extra copy of a target
    def count(w):
        n = 0
        for r in range(ROWS):
            for c in range(COLS):
                for dr, dc in [(0,1),(1,0),(1,1),(1,-1),(0,-1),(-1,0),(-1,-1),(-1,1)]:
                    if all(0 <= r+dr*i < ROWS and 0 <= c+dc*i < COLS and g[r+dr*i][c+dc*i] == w[i] for i in range(len(w))):
                        n += 1
        return n
    for w in words:
        if count(w) != (2 if w == w[::-1] else 1):
            return None
    return g, cells

GRIDS = []
for p in PUZ:
    for _ in range(500):
        b = build(p)
        if b: break
    assert b, p
    GRIDS.append(b)

font = lambda s, n: ImageFont.truetype(F + s + '.ttf', n)
L_=lambda n: Image.open(BASE+f'/fl/{n}.png').convert('RGBA')
HP={k:L_('h_'+k) for k in ['think','magnify','cheer']}
ICON={k:L_('i_'+k.lower()) for k in ['LION','BEAR','WOLF','DEER','FROG','GOAT','DUCK','FISH','SEAL','CRAB']}
def ease_back(x):
    x=max(0,min(1,x)); c=1.7
    return 1+(c+1)*(x-1)**3+c*(x-1)**2
def xform(im, sx, sy, ang):
    w,h=max(1,int(im.width*sx)),max(1,int(im.height*sy))
    r=im.resize((w,h),Image.LANCZOS)
    return r.rotate(ang,resample=Image.BICUBIC,expand=True) if abs(ang)>0.1 else r
def paste_bottom(dst, im, cx, by):
    dst.alpha_composite(im,(int(cx-im.width/2),int(by-im.height)))
SOC={'like':Image.open(BASE+'/fl/s_like.png').convert('RGBA'),'sub':Image.open(BASE+'/fl/s_sub.png').convert('RGBA')}
def fit(im,h,box=False):
    k=h/max(im.width,im.height) if box else h/im.height
    return im.resize((int(im.width*k),int(im.height*k)),Image.LANCZOS)

def bg(t):
    im = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(im)
    for y in range(0, H, 4):
        k = y / H
        d.rectangle((0, y, W, y + 4), fill=(int(28 + 20 * k), int(10 + 8 * k), int(60 + 40 * k)))
    g = Image.new('RGBA', (W, H))
    a = 0.5 + 0.5 * math.sin(t * 1.3)
    ImageDraw.Draw(g).ellipse((90, 420, 990, 1500), fill=(140, 90, 255, int(70 + 30 * a)))
    im = Image.alpha_composite(im.convert('RGBA'), g.filter(ImageFilter.GaussianBlur(150)))
    return im

def text_c(d, s, y, f, fill, stroke=0):
    w = d.textlength(s, font=f)
    d.text(((W - w) / 2, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(20, 10, 40))

# layout (centred stack, equal gaps)
CELL, GAP = 140, 12
G = 44
PILL_Y, TITLE_Y, CH_Y0 = 170, 274, 388
CH_Y1 = CH_Y0 + 120
GW, GH = COLS * CELL + (COLS - 1) * GAP, ROWS * CELL + (ROWS - 1) * GAP
GX, GY = (W - GW) // 2, 388 + 120 + 44
def cxy(r, c):
    return GX + c * (CELL + GAP) + CELL / 2, GY + r * (CELL + GAP) + CELL / 2

INTRO, REVEAL = 0.6, 0.9
ASKS = [4, 4, 4, 4, 5, 5, 5, 5, 5, 5]
SEGS = [INTRO + a + REVEAL for a in ASKS]
STARTS = [sum(SEGS[:k]) for k in range(len(SEGS))]
BAR = 240 / 118
SEGS[-1] += math.ceil(sum(SEGS) / BAR) * BAR - sum(SEGS)
STARTS = [sum(SEGS[:k]) for k in range(len(SEGS))]
TOTAL = sum(SEGS)

def frame(t):
    i = max(k for k in range(len(PUZ)) if STARTS[k] <= t)
    lt = t - STARTS[i]
    ASK = ASKS[i]
    title, words, kind, _, _ = PUZ[i]
    grid, cells = GRIDS[i]
    im = bg(t)
    ov = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(ov)
    # progress pill + dots, top-right (badge sits top-left)
    d.rounded_rectangle((W - 290, 70, W - 40, 134), 32, fill=(255, 255, 255, 40))
    pf = font('Bold', 34); pt = f"PUZZLE {i+1}/10"
    d.text((W - 165 - d.textlength(pt, font=pf) / 2, 78), pt, font=pf, fill=(255, 255, 255))
    for k in range(len(PUZ)):
        x = W - 165 + (k - 4.5) * 25
        d.ellipse((x - 7, 164 - 7, x + 7, 164 + 7), fill=GOLD if k <= i else (255, 255, 255, 70))
    # title + target words
    text_c(d, title.upper(), TITLE_Y - 12, font('Bold', 56), (255, 255, 255), 4)
    found = lt >= INTRO + ASK
    REVEAL_ON = False
    chips = words
    fz = font('Bold', 74)
    IH = 150
    icons = [fit(ICON[w], IH) if ICON[w].width/ICON[w].height<1.3 else fit(ICON[w],190,True) for w in chips]
    widths = [ic.width + 24 + d.textlength(w, font=fz) + 70 for w, ic in zip(chips, icons)]
    x = (W - (sum(widths) + 40 * (len(chips) - 1))) / 2
    icon_pos = []
    for w, wd, ic in zip(chips, widths, icons):
        icon_pos.append((ic, int(x), (CH_Y0 + CH_Y1) // 2 - ic.height // 2))
        cx = x + ic.width + 24
        d.rounded_rectangle((cx, CH_Y0, x + wd, CH_Y1), 30, fill=GOLD)
        d.text((cx + 35, CH_Y0 + 8), w, font=fz, fill=(25, 12, 50))
        x += wd + 40
    # pop-in scale for grid
    s = min(1, lt / INTRO) if lt < INTRO else 1
    s = 1 - (1 - s) ** 3
    # cells
    fc = font('Bold', 86)
    hl = set()
    prog = 0
    if found:
        prog = min(1, (lt - INTRO - ASK) / 0.6)
    for r in range(ROWS):
        for c in range(COLS):
            x0, y0 = cxy(r, c)
            hw = CELL / 2 * s
            d.rounded_rectangle((x0 - hw, y0 - hw, x0 + hw, y0 + hw), int(22 * s), fill=(255, 255, 255, 235))
    # reveal capsules
    if found and REVEAL_ON:
        for path, col in zip(cells, [(255, 80, 120), (60, 200, 255)]):
            (r0, c0), (r1, c1) = path[0], path[-1]
            xa, ya = cxy(r0, c0); xb, yb = cxy(r1, c1)
            xb = xa + (xb - xa) * prog; yb = ya + (yb - ya) * prog
            d.line((xa, ya, xb, yb), fill=col + (170,), width=118)
            for (xx, yy) in [(xa, ya), (xb, yb)]:
                d.ellipse((xx - 59, yy - 59, xx + 59, yy + 59), fill=col + (170,))
            for rc in path: hl.add(rc)
    for r in range(ROWS):
        for c in range(COLS):
            x0, y0 = cxy(r, c)
            ch = grid[r][c]
            f2 = font('Bold', max(4,int(86 * s))) if s < 1 else fc
            bb = d.textbbox((0, 0), ch, font=f2)
            col = (40, 22, 80)
            d.text((x0 - (bb[2] + bb[0]) / 2, y0 - (bb[3] + bb[1]) / 2), ch, font=f2, fill=col)
    # timer bar (4s) under grid
    by = GY + GH + G
    d.rounded_rectangle((GX, by, GX + GW, by + 34), 17, fill=(255, 255, 255, 50))
    if INTRO <= lt < INTRO + ASK:
        k = (lt - INTRO) / ASK
        d.rounded_rectangle((GX, by, GX + GW * (1 - k), by + 34), 17, fill=GOLD if k < 0.75 else (255, 90, 90))
        n = math.ceil(ASK - (lt - INTRO))
        text_c(d, str(n), by + 44, font('Bold', 90), (255, 255, 255), 5)
    elif found:
        text_c(d, "TIME'S UP!", by + 50, font('Bold', 80), (255, 120, 120), 5)
    im = Image.alpha_composite(im, ov)
    # animated icons: pop-in with overshoot, idle wiggle, happy bounce on reveal
    for ic, ix, iy in icon_pos:
        pop = ease_back(lt / 0.45)
        ang = 8 * math.sin(t * 5)
        sy = 1.0
        if found:
            rt = lt - INTRO - ASK
            j = abs(math.sin(rt * 9)) * max(0, 1 - rt / 1.2)
            iy -= int(40 * j); ang = 14 * math.sin(rt * 12) * max(0, 1 - rt / 1.2)
            sy = 1 + 0.12 * j
        im2 = xform(ic, pop * (2 - sy), pop * sy, ang)
        cx, cy = ix + ic.width / 2, iy + ic.height / 2
        im.alpha_composite(im2, (int(cx - im2.width / 2), int(cy - im2.height / 2)))
    # LIKE (puzzles 1-3) / SUBSCRIBE (4-6) badge, top-left, animated
    kind = 'like' if i < 5 else 'sub'
    bi = fit(SOC[kind], 110, True)
    pop = ease_back(lt / 0.5)
    tap = (lt % 1.6) / 1.6
    sq = 1 - 0.18 * math.exp(-((tap - 0.08) / 0.05) ** 2)      # press
    ang = (14 * math.sin(lt * 9) * math.exp(-3 * ((lt - 0.2) % 1.6))) if kind == 'sub' else 10 * math.sin(lt * 5)
    b2 = xform(bi, pop * (2 - sq), pop * sq, ang)
    bx, byy = 40 + 55, 52 + 55
    glow = Image.new('RGBA', (W, H)); gd = ImageDraw.Draw(glow)
    rr = 70 + 40 * tap
    gd.ellipse((bx - rr, byy - rr, bx + rr, byy + rr), outline=(255, 255, 255, int(160 * (1 - tap))), width=6)
    for k in range(6):  # sparkle burst on each tap
        a = k * math.pi / 3 + 0.4; r1 = 60 + 70 * tap
        sx_, sy_ = bx + r1 * math.cos(a), byy + r1 * math.sin(a)
        rad = 7 * (1 - tap)
        if rad > 0.5: gd.ellipse((sx_ - rad, sy_ - rad, sx_ + rad, sy_ + rad), fill=(255, 220, 90, int(255 * (1 - tap))))
    im = Image.alpha_composite(im, glow)
    im.alpha_composite(b2, (int(bx - b2.width / 2), int(byy - b2.height / 2)))
    lab = 'LIKE' if kind == 'like' else 'SUBSCRIBE'
    ld = ImageDraw.Draw(im); lf = font('Bold', 34)
    lw = ld.textlength(lab, font=lf)
    lx = 40 + 110 + 14; la = int(255 * min(1, max(0, (lt - 0.15) / 0.3)))
    ld.rounded_rectangle((lx, byy - 28, lx + lw + 36, byy + 28), 28, fill=(230, 40, 60, la) if kind == 'sub' else (40, 120, 255, la))
    ld.text((lx + 18, byy - 24), lab, font=lf, fill=(255, 255, 255, la))
    # animated Hoot
    pose = 'cheer' if found else ('think' if lt < INTRO else 'magnify')
    hh = 300
    base = fit(HP[pose], hh)
    cx, by = 20 + base.width / 2, H - 20
    breath = 1 + 0.025 * math.sin(t * 4)
    sx, sy, ang, lift = 1 / breath, breath, 4 * math.sin(t * 2.2), 0
    if pose == 'magnify':                      # leaning in, searching
        ang = 7 * math.sin(t * 3.5); lift = 6 * abs(math.sin(t * 7))
    if found:                                   # jump + squash on landing
        rt = lt - INTRO - ASK
        ph = (rt * 2.2) % 1
        lift = 45 * 4 * ph * (1 - ph) * max(0, 1 - rt / 1.8)
        if ph < 0.12: sx, sy = 1.12, 0.88
        ang = 6 * math.sin(rt * 10)
    # pose switch pop
    for edge in (0, INTRO, INTRO + ASK):
        if 0 <= lt - edge < 0.25:
            k = ease_back((lt - edge) / 0.25); sx *= 0.85 + 0.15 * k; sy *= 0.85 + 0.15 * k
    h2 = xform(base, sx, sy, ang)
    paste_bottom(im, h2, cx, by - lift)
    return im.convert('RGB')

if __name__ == '__main__':
    out = sys.argv[1]
    if len(sys.argv) > 2:  # still frames for contact sheet
        ts = [float(x) for x in sys.argv[2:]]
        ims = [frame(t).resize((360, 640)) for t in ts]
        sh = Image.new('RGB', (360 * len(ims), 640))
        for k, m in enumerate(ims): sh.paste(m, (360 * k, 0))
        sh.save(out); sys.exit()
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for f in range(int(TOTAL * FPS)):
        p.stdin.write(frame(f / FPS).tobytes())
    p.stdin.close(); p.wait()
