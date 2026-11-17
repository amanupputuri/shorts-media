"""Alternative long-video thumbnail layout B (1280x720): odd-one-out emoji grid + top banner + bottom ribbon.
  python3 thumb_long2.py OUT.jpg "BANNER TEXT" "RIBBON TEXT" [common_emoji] [odd_emoji]"""
import sys, os, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFilter
from mascot import hoot
from engine import font, F_BOLD, emoji_img

def make(out, banner, ribbon, common="🍔", odd="🌭"):
    W, H = 1280, 720
    im = Image.new("RGBA", (W, H), (22, 18, 60, 255)); d = ImageDraw.Draw(im)
    for k in range(0, W + H, 60):  # diagonal stripes
        d.polygon([(k, 0), (k + 30, 0), (k - H + 30, H), (k - H, H)], fill=(34, 28, 88, 255))
    # grid panel (left/centre)
    gx, gy, cw, ch, cols, rows = 40, 150, 118, 118, 6, 4
    pw, ph = cols * cw + 30, rows * ch + 30
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((gx + 8, gy + 14, gx + pw + 8, gy + ph + 14), 36, fill=(0, 0, 0, 140))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10))); d = ImageDraw.Draw(im)
    d.rounded_rectangle((gx, gy, gx + pw, gy + ph), 36, fill=(255, 255, 255))
    random.seed(7); oi = (2, 3)
    for r in range(rows):
        for c in range(cols):
            e = odd if (r, c) == oi else common
            x = gx + 15 + c * cw + cw // 2; y = gy + 15 + r * ch + ch // 2
            im.alpha_composite(emoji_img(e, 92), (x - 46, y - 46))
    ox = gx + 15 + oi[1] * cw + cw // 2; oy = gy + 15 + oi[0] * ch + ch // 2
    d = ImageDraw.Draw(im); d.ellipse((ox - 62, oy - 62, ox + 62, oy + 62), outline=(255, 60, 70), width=12)
    # top banner
    d.rounded_rectangle((40, 28, 900, 128), 28, fill=(255, 210, 60))
    f = font(F_BOLD, 84); sz = 84
    while d.textlength(banner, font=f) > 800 and sz > 40: sz -= 4; f = font(F_BOLD, sz)
    d.text((470 - d.textlength(banner, font=f) / 2, 36), banner, font=f, fill=(40, 20, 90))
    # owl right, big
    h = hoot(420, "cheer", 0.0); im.alpha_composite(h, (W - 400, 40))
    # bottom ribbon
    d.rounded_rectangle((40, 640, 1000, 710), 22, fill=(255, 70, 110))
    f = font(F_BOLD, 54); d.text((70, 645), ribbon, font=f, fill=(255, 255, 255))
    # 20 badge
    d.ellipse((1030, 470, 1250, 690), fill=(255, 210, 60), outline=(255, 255, 255), width=8)
    f = font(F_BOLD, 120); d.text((1140 - d.textlength("20", font=f) / 2, 488), "20", font=f, fill=(40, 20, 90))
    f = font(F_BOLD, 30); d.text((1140 - d.textlength("PUZZLES", font=f) / 2, 622), "PUZZLES", font=f, fill=(40, 20, 90))
    im.convert("RGB").save(out, quality=92)

if __name__ == "__main__":
    a = sys.argv
    make(a[1], a[2], a[3], a[4] if len(a) > 4 else "🍔", a[5] if len(a) > 5 else "🌭")
