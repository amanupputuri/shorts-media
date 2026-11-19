import sys, colorsys
from PIL import Image, ImageDraw, ImageFont
EF=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',109)
def stat(e):
    im=Image.new('RGBA',(160,160),(0,0,0,0)); ImageDraw.Draw(im).text((80,80),e,font=EF,embedded_color=True,anchor='mm')
    px=[p for p in im.resize((40,40)).getdata() if p[3]>200]
    if not px: return None
    hs=[colorsys.rgb_to_hsv(*(c/255 for c in p[:3])) for p in px]
    # fraction of pixels in pink hue range / white / blue
    pink=sum(1 for h,s,v in hs if (h>0.85 or h<0.02) and s>0.2 and v>0.6)/len(hs)
    blue=sum(1 for h,s,v in hs if 0.5<h<0.7 and s>0.3)/len(hs)
    white=sum(1 for h,s,v in hs if s<0.15 and v>0.8)/len(hs)
    black=sum(1 for h,s,v in hs if v<0.3)/len(hs)
    return round(pink,2),round(blue,2),round(white,2),round(black,2)
for e in sys.argv[1:]: print(e,stat(e))
