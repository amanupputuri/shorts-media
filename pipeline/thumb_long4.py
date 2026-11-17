"""Long thumbnail layout D (1280x720): high-CTR style. Huge outlined text, one big puzzle, red arrow, big owl.
  python3 thumb_long4.py OUT.jpg "TOP" "BIG" common odd"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFilter
from mascot import hoot
from engine import font, F_BOLD, emoji_img

def otext(d, xy, t, f, fill, ow=10):
    d.text(xy, t, font=f, fill=fill, stroke_width=ow, stroke_fill=(0, 0, 0))

def make(out, top, big, common, odd):
    W, H = 1280, 720
    im = Image.new("RGBA", (W, H), (255, 214, 0, 255)); d = ImageDraw.Draw(im)
    cx, cy = 360, 420
    for k in range(18):
        a0 = math.radians(k * 20); a1 = a0 + math.radians(10)
        d.polygon([(cx, cy), (cx + 1600*math.cos(a0), cy + 1600*math.sin(a0)), (cx + 1600*math.cos(a1), cy + 1600*math.sin(a1))], fill=(255, 236, 90))
    # big puzzle card 3x3, left
    sh = Image.new("RGBA", (W, H), (0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle((52, 188, 652, 708), 40, fill=(0,0,0,170))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14))); d = ImageDraw.Draw(im)
    d.rounded_rectangle((40, 170, 640, 690), 40, fill=(255,255,255), outline=(0,0,0), width=8)
    oi = 5
    for k in range(9):
        r, c = divmod(k, 3); x = 80 + c*180; y = 200 + r*160
        im.alpha_composite(emoji_img(odd if k == oi else common, 140), (x, y))
    # text
    d = ImageDraw.Draw(im)
    f = font(F_BOLD, 96); otext(d, (40, 30), top, f, (255,255,255), 9)
    f = font(F_BOLD, 200); otext(d, (690, 150), big, f, (255, 40, 40), 14)
    f = font(F_BOLD, 64); otext(d, (700, 380), "CAN YOU", f, (255,255,255), 8)
    otext(d, (700, 450), "SPOT IT?", f, (255,255,255), 8)
    # red arrow pointing into card
    ax, ay = 760, 600; tx, ty = 600, 440
    d.line((ax, ay, tx+30, ty+30), fill=(0,0,0), width=40); d.line((ax, ay, tx+30, ty+30), fill=(230,20,30), width=26)
    d.polygon([(tx, ty), (tx+90, ty+20), (tx+20, ty+90)], fill=(230,20,30), outline=(0,0,0))
    h = hoot(380, "cheer", 0.0); im.alpha_composite(h, (W - h.width + 20, H - h.height + 40))
    im.convert("RGB").save(out, quality=93)

if __name__ == "__main__":
    a = sys.argv; make(a[1], a[2], a[3], a[4], a[5])
