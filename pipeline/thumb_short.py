"""Shorts thumbnail 1080x1920: python3 thumb_short.py PANEL.jpg OUT.jpg LINE1 LINE2 BADGE x0,y0,x1,y1 (panel = crop of a hard-level frame)."""
import sys
sys.path.insert(0, '/home/claude/shorts-media/pipeline')
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from mascot import hoot
from engine import font, F_BOLD
src, out, l1, l2, badge = sys.argv[1:6]; box = [int(v) for v in sys.argv[6].split(',')]
W, H = 1080, 1920
pan = Image.open(src).convert('RGBA').crop(box)
import numpy as np
c = np.array(pan.convert('RGB').crop((0,0,12,12))).reshape(-1,3).mean(0)
yy = np.linspace(0,1,H)[:,None,None]; top = np.minimum(c*1.6+30,255); bot = c*0.7
bg = Image.fromarray(np.broadcast_to(top*(1-yy)+bot*yy,(H,W,3)).astype(np.uint8)).convert('RGBA')
im = bg.copy(); d = ImageDraw.Draw(im)
def title(txt, y, col, maxw, sz):
    f = font(F_BOLD, sz)
    while d.textlength(txt, font=f) > maxw: sz -= 6; f = font(F_BOLD, sz)
    tw = d.textlength(txt, font=f)
    d.text(((W - tw) / 2, y), txt, font=f, fill=col, stroke_width=14, stroke_fill=(25, 20, 50))
title(l1, 120, (255, 255, 255), 900, 170); title(l2, 300, (255, 214, 40), 980, 180)
maxw, maxh = (1010, 1050) if pan.height > pan.width else (930, 1000)
sc = min(maxw / pan.width, maxh / pan.height); pan = pan.resize((int(pan.width * sc), int(pan.height * sc)), Image.LANCZOS)
py = 520 + (maxh - pan.height) // 2; px = (W - pan.width) // 2
mask = Image.new('L', pan.size, 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, pan.width - 1, pan.height - 1), 40, fill=255)
sh = Image.new('RGBA', (W, H), (0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle((px+10, py+20, px+pan.width+10, py+pan.height+20), 40, fill=(0,0,0,110))
im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16))); im.paste(pan, (px, py), mask)
h = hoot(260, "think"); im.alpha_composite(h, (W - h.width - 10, min(1600, py + pan.height + 90) - h.height))
d = ImageDraw.Draw(im); f = font(F_BOLD, 96); tw = d.textlength(badge, font=f)
while tw > 880: f = font(F_BOLD, f.size - 6); tw = d.textlength(badge, font=f)
d.rounded_rectangle(((W - tw) / 2 - 50, 1620, (W + tw) / 2 + 50, 1770), 75, fill=(232, 52, 92))
d.text(((W - tw) / 2, 1695), badge, font=f, fill=(255, 255, 255), anchor='lm' if False else 'lm')
im.convert('RGB').save(out, quality=90)
