import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from collections import Counter
F='/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
EF=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',109)
W,H=1080,1920; COLS,ROWS=6,7; CELL,GAP=150,12
GW=COLS*CELL+(COLS-1)*GAP; GH=ROWS*CELL+(ROWS-1)*GAP; GX=(W-GW)//2; GY=560
LV={'EASY':((90,200,110),3,0),'MEDIUM':((255,170,40),4,10),'HARD':((240,70,80),5,22)}
PLAN=[('EASY','orange','🦁 🍊 🎃 🥕 🦊 🏀 🧡 🐯 🍑 🥭 🦧 🐠 🔶 🍁'),
('EASY','green','🐸 🍏 🥝 🥦 🌵 🐢 🦎 🐊 🍀 🌲 🥒 🫑 🐉 💚'),
('MEDIUM','yellow','🐥 🍋 🍌 🌻 ⭐ 🌞 🧀 🌽 🐝 🌙 💛 🍯'),
('MEDIUM','red','🍓 🍎 🍒 🍅 🐞 ❤️ 🌹 🦀 🌶️ 🎈 🚗 🧨'),
('MEDIUM','blue','🐳 🐬 🔷 💙 🫐 🧢 👖 💎 🐟 🌀 🧊 🔵'),
('MEDIUM','purple','🍇 🍆 🔮 💜 ☂️ 🟣 👾 🪻 😈 💟 🔯 🦄'),
('HARD','brown','🐻 🐵 🐶 🐴 🦔 🌰 🍪 🦉 🐿️ 🥔 🥥 🦫'),
('HARD','grey','🐘 🐭 🐨 🦛 🦏 🐺 🦈 🪨 🐀 🦍 🦡 🐹'),
('HARD','pink','🐷 🌸 💗 💕 💓 💞 🩷 🧠 🦩 💖 💘 👛'),
('HARD','black','🐈‍⬛ ♣️ 🕷️ 🎱 🖤 🐦‍⬛ 🎩 🕶️ ♠️ ⚫ 💣 🐜')]
cache={}
import colorsys
def pinkify(im):
    px=im.load()
    for y in range(im.height):
        for x in range(im.width):
            r,g,b,a=px[x,y]
            if a<10: continue
            h,s_,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
            if v>0.35 and (h<0.12 or h>0.85):
                s_=min(0.62,s_*1.5+0.12); h=0.94; v=v*0.97
                rr,gg,bb=colorsys.hsv_to_rgb(h,s_,v); px[x,y]=(int(rr*255),int(gg*255),int(bb*255),a)
    return im
def emo(e):
    if e in cache: return cache[e]
    im=Image.new('RGBA',(160,160),(0,0,0,0)); ImageDraw.Draw(im).text((80,80),e,font=EF,embedded_color=True,anchor='mm')
    im=im.crop(im.getbbox()); sh=Image.new('RGBA',(im.width+24,im.height+24),(0,0,0,0)); a=im.split()[3]
    s=Image.new('RGBA',im.size,(40,20,70,0)); s.putalpha(a.point(lambda v:int(v*.35))); sh.alpha_composite(s,(12,18)); sh=sh.filter(ImageFilter.GaussianBlur(5)); sh.alpha_composite(im,(12,12))
    if e=='🐷': sh=pinkify(sh)
    cache[e]=sh; return sh
def fitbox(im,s): r=s/max(im.size); return im.resize((max(1,int(im.width*r)),max(1,int(im.height*r))),Image.LANCZOS)
def bg():
    im=Image.new('RGB',(W,H)); d=ImageDraw.Draw(im)
    for y in range(H): t=y/H; d.line([(0,y),(W,y)],fill=(int(52+30*t),int(24+14*t),int(104+40*t)))
    return im.convert('RGBA')
used=set()
def pen(lay):
    P=0
    for i in range(42):
        r,c=divmod(i,COLS)
        for j in range(i+1,42):
            if lay[i]!=lay[j]: continue
            r2,c2=divmod(j,COLS); d=max(abs(r-r2),abs(c-c2))
            P+= 100 if d<=1 else (12 if d==2 else (3 if d==3 else 0))
            if r==r2 or c==c2: P+=2
    return P
def scatter(lay,rnd):
    best=None
    for _ in range(6):
        L=lay[:]; rnd.shuffle(L); p=pen(L); T=30.0
        for it in range(20000):
            i,j=rnd.randrange(42),rnd.randrange(42)
            if L[i]==L[j]: continue
            L[i],L[j]=L[j],L[i]; q=pen(L)
            if q<=p or rnd.random()<__import__('math').exp((p-q)/T): p=q
            else: L[i],L[j]=L[j],L[i]
            T=max(0.05,T*0.9997)
        if best is None or p<best[0]: best=(p,L[:])
    return best[1]
def adj(lay):
    n=0
    for i in range(42):
        r,c=divmod(i,COLS)
        for j in range(i+1,42):
            r2,c2=divmod(j,COLS)
            if lay[i]==lay[j] and max(abs(r-r2),abs(c-c2))<=1: n+=1
    return n
def make(k,lvl,setn,ems,ans=False,layer=False,lay_in=None):
    lc,n,rot=LV[lvl]; rnd=random.Random(11+k); ems=ems.split(); tgt=ems[0]
    nt=42//n; types=ems[:nt]; lay=[t for t in types for _ in range(n)]; lay+=ems[nt:nt+42-len(lay)]
    assert len(lay)==42 and len(set(ems))==len(ems); lay=lay_in if lay_in else scatter(lay,rnd)
    im=Image.new('RGBA',(W,H),(0,0,0,0)) if layer else bg(); d=ImageDraw.Draw(im)
    GAPV=34; f=ImageFont.truetype(F,40); lab=f'{lvl}  •  {k+1}/10'; w=d.textlength(lab,font=f)
    f2=ImageFont.truetype(F,96); t=f'FIND {n}'; tb=d.textbbox((0,0),t,font=f2); th=tb[3]-tb[1]
    pill_h=66; chip_h=140; top=GY-22-GAPV-chip_h-GAPV-th-GAPV-pill_h
    d.rounded_rectangle([W/2-w/2-36,top,W/2+w/2+36,top+pill_h],33,fill=lc); lb=d.textbbox((0,0),lab,font=f); d.text((W/2-w/2,top+(pill_h-(lb[3]-lb[1]))/2-lb[1]),lab,font=f,fill='white')
    ty=top+pill_h+GAPV; w2=d.textlength(t,font=f2); d.text((W/2-w2/2,ty-tb[1]),t,font=f2,fill='white',stroke_width=6,stroke_fill=(40,15,80))
    cy0=ty+th+GAPV; d.rounded_rectangle([W/2-100,cy0,W/2+100,cy0+chip_h],36,fill='white',outline=(255,214,90),width=8)
    ti=fitbox(emo(tgt),118); im.alpha_composite(ti,(W//2-ti.width//2,int(cy0+chip_h/2-ti.height/2)))
    d.rounded_rectangle([GX-22,GY-22,GX+GW+22,GY+GH+22],40,fill=(255,255,255,40))
    for c,e in enumerate(lay):
        r,q=divmod(c,COLS); x=GX+q*(CELL+GAP); y=GY+r*(CELL+GAP)
        d.rounded_rectangle([x,y,x+CELL,y+CELL],26,fill=(250,246,255))
        ic=emo(e)
        if rot: ic=ic.rotate(rnd.uniform(-rot,rot),expand=True,resample=Image.BICUBIC)
        ic=fitbox(ic,int(CELL*(0.84 if lvl=='EASY' else rnd.uniform(0.70,0.84))))
        im.alpha_composite(ic,(x+(CELL-ic.width)//2,y+(CELL-ic.height)//2))
        if ans and e==tgt: d.ellipse([x+5,y+5,x+CELL-5,y+CELL-5],outline=(255,30,60),width=10)
    return (im if layer else im.convert('RGB')),lay
