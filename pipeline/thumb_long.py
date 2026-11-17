"""Custom thumbnail for the 20-puzzle long video (1280x720 JPG).

  python3 thumb_long.py OUT.jpg "LINE1" "LINE2" [palette_index] [emoji,emoji,emoji,emoji]

Design: bright brand colour, huge "20" badge, two-word headline, Professor Hoot cheering, a mini puzzle card
(4 emoji, one highlighted) — readable on a phone at thumbnail size.
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from mascot import hoot
from engine import font, F_BOLD, emoji_img
import tools

def grad(W, H, a, b):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); u = (xx / W * 0.6 + yy / H * 0.4)
    arr = np.zeros((H, W, 3), np.float32)
    for i in range(3): arr[..., i] = a[i] + (b[i] - a[i]) * u
    return Image.fromarray(arr.astype(np.uint8)).convert("RGBA")

def make(out, line1, line2, pi=1, emojis=("🍎", "🍌", "🍇", "🍓")):
    W, H = 1280, 720; p = tools.PALETTES[pi % len(tools.PALETTES)]
    im = grad(W, H, p[0], p[1]); d = ImageDraw.Draw(im)
    rays = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rd = ImageDraw.Draw(rays); cx, cy = 980, 380
    for k in range(14):
        a0 = math.radians(k * 360 / 14); a1 = a0 + math.radians(360 / 28)
        rd.polygon([(cx, cy), (cx + 1500 * math.cos(a0), cy + 1500 * math.sin(a0)), (cx + 1500 * math.cos(a1), cy + 1500 * math.sin(a1))], fill=(255, 255, 255, 28))
    im.alpha_composite(rays)
    # mini puzzle card (right) with one answer circled
    card = Image.new("RGBA", (420, 420), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
    sh = Image.new("RGBA", (420, 420), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((20, 34, 400, 414), radius=46, fill=(10, 0, 40, 120))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    cd.rounded_rectangle((20, 20, 400, 400), radius=46, fill=(255, 255, 255))
    for k, e in enumerate(emojis[:4]):
        r_, q = divmod(k, 2); ex, ey = 115 + q * 190, 115 + r_ * 190
        card.alpha_composite(emoji_img(e, 130), (int(ex - 65), int(ey - 65)))
        if k == 3: cd.ellipse((ex - 88, ey - 88, ex + 88, ey + 88), outline=(40, 200, 90), width=14)
    card = card.rotate(-6, resample=Image.BICUBIC, expand=True)
    card = card.resize((int(card.width * 0.86), int(card.height * 0.86)), Image.LANCZOS)
    im.alpha_composite(card, (W - card.width - 200, 40))
    h = hoot(300, "cheer", 0.0); im.alpha_composite(h, (W - 300, H - h.height + 20))
    # big "20" badge
    bd = ImageDraw.Draw(im)
    bd.ellipse((40, 40, 300, 300), fill=(255, 210, 60), outline=(255, 255, 255), width=10)
    f = font(F_BOLD, 170); tw = bd.textlength("20", font=f); bd.text((170 - tw / 2, 58), "20", font=f, fill=(40, 20, 90))
    f = font(F_BOLD, 40); tw = bd.textlength("PUZZLES", font=f); bd.text((170 - tw / 2, 232), "PUZZLES", font=f, fill=(40, 20, 90))
    # headline
    for i, (txt, col, sz) in enumerate([(line1, (255, 255, 255), 112), (line2, (255, 210, 60), 112)]):
        f = font(F_BOLD, sz)
        while bd.textlength(txt, font=f) > 700 and sz > 60: sz -= 6; f = font(F_BOLD, sz)
        y = 345 + i * 130
        bd.text((48, y + 8), txt, font=f, fill=(15, 5, 45, 120)); bd.text((44, y), txt, font=f, fill=col)
    im.convert("RGB").save(out, quality=92)

if __name__ == "__main__":
    em = sys.argv[5].split(",") if len(sys.argv) > 5 else ("🍎", "🍌", "🍇", "🍓")
    make(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 1, em)
