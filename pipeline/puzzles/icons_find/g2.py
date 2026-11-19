import random, math, sys
import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
import grids
from grids import emo, fitbox, bg, F
W,H=1080,1920; COLS,ROWS=8,9; N=COLS*ROWS
CELL,GAP=94,6
GW=COLS*CELL+(COLS-1)*GAP; GH=ROWS*CELL+(ROWS-1)*GAP; GX=(W-COLS*CELL-(COLS-1)*GAP)//2; GY=540
CX=GX+GW//2  # content centre (right side kept clear for Shorts buttons)
LV={'EASY':((90,200,110),5,0),'MEDIUM':((255,170,40),8,10),'HARD':((240,70,80),10,20)}
def pen(L):
    P=0
    for i in range(N):
        r,c=divmod(i,COLS)
        for j in range(i+1,N):
            if L[i]!=L[j]: continue
            r2,c2=divmod(j,COLS); d=max(abs(r-r2),abs(c-c2))
            P+=100 if d<=1 else (10 if d==2 else 0)
    return P
def scatter(lay,rnd,iters=40000):
    L=lay[:]; rnd.shuffle(L); p=pen(L); T=30.0
    for _ in range(iters):
        i,j=rnd.randrange(N),rnd.randrange(N)
        if L[i]==L[j]: continue
        L[i],L[j]=L[j],L[i]; q=pen(L)
        if q<=p or rnd.random()<math.exp((p-q)/T): p=q
        else: L[i],L[j]=L[j],L[i]
        T=max(0.05,T*0.9998)
    return L
def header(im,d,lvl,k,n,tgt,top_y=None):
    lc=LV[lvl][0]; GAPV=30; f=ImageFont.truetype(F,40); lab=f'{lvl}  •  {k}/10'; w=d.textlength(lab,font=f)
    f2=ImageFont.truetype(F,92); t=f'FIND {n}'; tb=d.textbbox((0,0),t,font=f2); th=tb[3]-tb[1]
    pill_h=64; chip_h=130; top=GY-18-GAPV-chip_h-GAPV-th-GAPV-pill_h
    d.rounded_rectangle([CX-w/2-34,top,CX+w/2+34,top+pill_h],32,fill=lc); lb=d.textbbox((0,0),lab,font=f); d.text((CX-w/2,top+(pill_h-(lb[3]-lb[1]))/2-lb[1]),lab,font=f,fill='white')
    ty=top+pill_h+GAPV; w2=d.textlength(t,font=f2); d.text((CX-w2/2,ty-tb[1]),t,font=f2,fill='white',stroke_width=6,stroke_fill=(40,15,80))
    cy0=ty+th+GAPV; d.rounded_rectangle([CX-95,cy0,CX+95,cy0+chip_h],34,fill='white',outline=(255,214,90),width=8)
    ti=fitbox(emo(tgt),108); im.alpha_composite(ti,(CX-ti.width//2,int(cy0+chip_h/2-ti.height/2)))
def make(k,lvl,ems,layer=False,lay_in=None,ans=False):
    _,n,rot=LV[lvl]; rnd=random.Random(50+k); ems=ems.split(); tgt=ems[0]
    nt=N//n; lay=[t for t in ems[:nt] for _ in range(n)]; lay+=ems[nt:nt+N-len(lay)]
    assert len(lay)==N, (len(lay),len(ems))
    lay=lay_in or scatter(lay,rnd)
    im=Image.new('RGBA',(W,H),(0,0,0,0)) if layer else bg(); d=ImageDraw.Draw(im)
    header(im,d,lvl,k+1,n,tgt)
    d.rounded_rectangle([GX-18,GY-18,GX+GW+18,GY+GH+18],34,fill=(255,255,255,40))
    for c,e in enumerate(lay):
        r,q=divmod(c,COLS); x=GX+q*(CELL+GAP); y=GY+r*(CELL+GAP)
        d.rounded_rectangle([x,y,x+CELL,y+CELL],20,fill=(250,246,255))
        ic=emo(e)
        if rot: ic=ic.rotate(rnd.uniform(-rot,rot),expand=True,resample=Image.BICUBIC)
        ic=fitbox(ic,int(CELL*(0.86 if lvl=='EASY' else rnd.uniform(0.74,0.86))))
        im.alpha_composite(ic,(x+(CELL-ic.width)//2,y+(CELL-ic.height)//2))
        if ans and e==tgt: d.ellipse([x+4,y+4,x+CELL-4,y+CELL-4],outline=(255,30,60),width=8)
    return im,lay
def example(layer=False):
    # small 4x4 "HOW TO PLAY": find 3 apples, circled
    im=Image.new('RGBA',(W,H),(0,0,0,0)) if layer else bg(); d=ImageDraw.Draw(im)
    f=ImageFont.truetype(F,64); s='HOW TO PLAY'; w=d.textlength(s,font=f); d.text((CX-w/2,330),s,font=f,fill='white',stroke_width=5,stroke_fill=(40,15,80))
    f2=ImageFont.truetype(F,48); s='Find all the matching icons!'; w=d.textlength(s,font=f2); d.text((CX-w/2,430),s,font=f2,fill=(255,214,90))
    lay='🍎 🍓 🍒 🍅 🍒 🍅 🍎 🍓 🍓 🍎 🍅 🍒 🍅 🍒 🍓 🍎'.split()
    C,Gp=170,14; gw=4*C+3*Gp; gx=CX-gw//2; gy=560
    d.rounded_rectangle([gx-22,gy-22,gx+gw+22,gy+gw+22],36,fill=(255,255,255,40))
    for c,e in enumerate(lay):
        r,q=divmod(c,4); x=gx+q*(C+Gp); y=gy+r*(C+Gp)
        d.rounded_rectangle([x,y,x+C,y+C],26,fill=(250,246,255))
        ic=fitbox(emo(e),int(C*0.8)); im.alpha_composite(ic,(x+(C-ic.width)//2,y+(C-ic.height)//2))
        if e=='🍎': d.ellipse([x+6,y+6,x+C-6,y+C-6],outline=(255,30,60),width=10)
    f3=ImageFont.truetype(F,62); s='FIND 4  🍎  →  FOUND 4!'.replace('  🍎  ',' ')
    s='4 APPLES FOUND!'; w=d.textlength(s,font=f3); d.text((CX-w/2,gy+gw+60),s,font=f3,fill=(120,255,150),stroke_width=5,stroke_fill=(20,60,30))
    return im
