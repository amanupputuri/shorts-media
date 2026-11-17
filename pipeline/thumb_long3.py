"""Long thumbnail layout C (1280x720): split-screen spot-the-difference, big owl centre, bold headline.
  python3 thumb_long3.py OUT.jpg "HEADLINE" "SUB" """
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFilter
from mascot import hoot
from engine import font, F_BOLD, emoji_img

def panel(diff):
    p = Image.new("RGBA", (500, 400), (255, 255, 255, 255)); d = ImageDraw.Draw(p)
    d.rectangle((0, 260, 500, 400), fill=(120, 200, 110)); d.rectangle((0, 0, 500, 260), fill=(150, 210, 255))
    p.alpha_composite(emoji_img("🌞" if not diff else "🌙", 90), (370, 20))
    p.alpha_composite(emoji_img("🏠", 170), (40, 120))
    p.alpha_composite(emoji_img("🌳", 150), (260, 140))
    p.alpha_composite(emoji_img("🐶" if not diff else "🐱", 90), (380, 290))
    return p, (415, 65), (425, 335)

def make(out, head, sub):
    W, H = 1280, 720
    im = Image.new("RGBA", (W, H), (255, 120, 40, 255)); d = ImageDraw.Draw(im)
    d.polygon([(0, 0), (W, 0), (W, 140), (0, 200)], fill=(20, 20, 30))
    f = font(F_BOLD, 110); sz = 110
    while d.textlength(head, font=f) > 1200: sz -= 4; f = font(F_BOLD, sz)
    d.text((40, 30), head, font=f, fill=(255, 225, 60))
    for i, x in enumerate((50, 730)):
        p, a, b = panel(i == 1)
        fr = Image.new("RGBA", (520, 420), (255, 255, 255, 255)); fr.alpha_composite(p, (10, 10))
        if i == 1:
            fd = ImageDraw.Draw(fr)
            for cx, cy in (a, b): fd.ellipse((cx - 65 + 10, cy - 65 + 10, cx + 65 + 10, cy + 65 + 10), outline=(230, 30, 40), width=10)
        fr = fr.rotate(3 if i == 0 else -3, expand=True, resample=Image.BICUBIC)
        im.alpha_composite(fr, (x, 215))
    h = hoot(300, "cheer", 0.0); im.alpha_composite(h, (W // 2 - h.width // 2, H - h.height + 30))
    d = ImageDraw.Draw(im); f = font(F_BOLD, 64)
    tw = d.textlength(sub, font=f); d.rounded_rectangle((W // 2 - tw / 2 - 30, 128, W // 2 + tw / 2 + 30, 212), 40, fill=(255, 255, 255))
    d.text((W // 2 - tw / 2, 136), sub, font=f, fill=(230, 30, 40))
    im.convert("RGB").save(out, quality=92)

if __name__ == "__main__": make(sys.argv[1], sys.argv[2], sys.argv[3])
