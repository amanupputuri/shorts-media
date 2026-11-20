import sys, math
sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/_shared')
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import design as D
import os
PH=os.environ.get('SPOT_PH',os.path.join(os.path.dirname(os.path.abspath(__file__)),'ph_animals'))
from design import F, INK, GOLD, W, H
EF=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',109)
def emo(e,size):
    im=Image.new('RGBA',(160,160),(0,0,0,0)); ImageDraw.Draw(im).text((80,80),e,font=EF,embedded_color=True,anchor='mm'); im=im.crop(im.getbbox())
    r=size/max(im.size); return im.resize((int(im.width*r),int(im.height*r)),Image.LANCZOS)
P=[(1,['Polar Bear','Panda','Raccoon'],1,118,'EASY',(0,0)),
   (2,['Zebra','Donkey','Horse'],0,108,'EASY',(0,0)),
   (3,['Lion','Cheetah','Tiger'],2,98,'MEDIUM',(0,0)),
   (4,['Sloth','Koala','Wombat'],1,88,'MEDIUM',(0,0)),
   (5,['Iguana','Gecko','Chameleon'],2,78,'HARD',(0,0)),
   (6,['Snow Leopard','Jaguar','Lynx'],0,70,'HARD',(0,0))]
LVC={'EASY':(30,170,90),'MEDIUM':(240,140,20),'HARD':(225,40,60)}
ST=(90,330,990,1230)   # stage box 900x900
WP=[[(0.30,0.22),(0.52,0.36),(0.66,0.50),(0.45,0.72)],
    [(0.60,0.15),(0.55,0.42),(0.50,0.75),(0.25,0.55)],
    [(0.35,0.35),(0.65,0.40),(0.72,0.75),(0.40,0.75)],
    [(0.25,0.25),(0.50,0.36),(0.45,0.60),(0.32,0.80)],
    [(0.55,0.25),(0.40,0.45),(0.30,0.75),(0.60,0.65)],
    [(0.45,0.30),(0.62,0.45),(0.40,0.68),(0.60,0.80)]]
def orbit(i,t,sw,sh):
    p=WP[i]; n=len(p); u=t/1.4+i*0.37; k=int(u)%n; f=u-int(u)
    pts=[p[(k+j-1)%n] for j in range(4)]
    def cr(a,b,c,d,f): return 0.5*(2*b+(c-a)*f+(2*a-5*b+4*c-d)*f*f+(3*b-a-3*c+d)*f**3)
    x=cr(*[q[0] for q in pts],f); y=cr(*[q[1] for q in pts],f)
    return sw*x, sh*y
def stage(i,t,reveal=False):
    e,_,_,R,_,fc=P[i]; sw,sh=ST[2]-ST[0],ST[3]-ST[1]
    obj=Image.open(PH+f'/s{e}.jpg').convert('RGBA').resize((sw,sh))
    if reveal: return obj
    # spotlight path: lissajous wander, mostly over edges/parts of the object
    cx,cy=orbit(i,t,sw,sh)
    m=Image.new('L',(sw,sh),0); d=ImageDraw.Draw(m); d.ellipse([cx-R,cy-R,cx+R,cy+R],fill=255); m=m.filter(ImageFilter.GaussianBlur(R*0.12))
    dark=Image.new('RGBA',(sw,sh),(6,4,12,255))
    # faint glimmer of the scene (2%) so the dark feels deep, not flat
    dark=Image.blend(dark,obj,0.025)
    out=Image.composite(obj,dark,m)
    halo=Image.new('L',(sw,sh),0); hd=ImageDraw.Draw(halo); hd.ellipse([cx-R*1.9,cy-R*1.9,cx+R*1.9,cy+R*1.9],fill=90); halo=halo.filter(ImageFilter.GaussianBlur(R*0.6))
    glow=Image.new('RGBA',(sw,sh),(255,190,80,0)); glow.putalpha(halo); out.alpha_composite(glow)
    ring=Image.new('RGBA',(sw,sh),(0,0,0,0)); rd=ImageDraw.Draw(ring)
    rd.ellipse([cx-R-4,cy-R-4,cx+R+4,cy+R+4],outline=(255,214,90,230),width=7)
    rg=ring.filter(ImageFilter.GaussianBlur(6)); out.alpha_composite(rg); out.alpha_composite(ring)
    return out
WARM=[((255,150,70),(205,55,85)),((255,175,85),(225,85,60)),((252,128,92),(168,52,108)),
      ((255,190,95),(232,104,52)),((246,118,74),(150,42,84)),((255,162,74),(196,70,72))]
def warm(i):
    a,b=WARM[i%6]; y=np.linspace(0,1,H)[:,None]; x=np.linspace(-1,1,W)[None,:]
    t=(y**1.1)[...,None]; base=np.array(a)*(1-t)+np.array(b)*t
    yy=np.linspace(0,1,H)[:,None]; g=np.exp(-((x/0.9)**2+((yy-0.18)/0.35)**2))[...,None]
    base=base+(np.array([255,235,200])-base)*g*0.28
    v=1-0.22*((x**2)*0.6+(yy-0.5)**2*0.8)[...,None]
    return Image.fromarray(np.clip(base*v,0,255).astype('uint8')).convert('RGBA')
def likebtn(im,t):
    p=0.5+0.5*math.sin(t*3.0)
    f=F('h',50); tw=ImageDraw.Draw(im).textlength('LIKE',font=f)
    x0,y0=48,114; x1,y1=int(x0+tw+68),y0+76
    mk=Image.new('L',im.size,0); ImageDraw.Draw(mk).rounded_rectangle([x0-8,y0-8,x1+8,y1+8],46,fill=int(200+55*p))
    mk=mk.filter(ImageFilter.GaussianBlur(18+10*p)); gl=Image.new('RGBA',im.size,(255,235,140,0)); gl.putalpha(mk)
    im.alpha_composite(gl); im.alpha_composite(gl)
    d=ImageDraw.Draw(im)
    d.rounded_rectangle([x0,y0,x1,y1],38,fill=(240,30,70),outline=(255,255,255),width=5)
    d.text(((x0+x1)/2,(y0+y1)/2+3),'LIKE',font=f,fill='white',anchor='mm',stroke_width=3,stroke_fill=(150,10,40))
def _oldlike(im,t):
    p=1+0.06*max(0,math.sin(t*3.2))**8
    cx,cy,r=100,140,int(58*p)
    sh=Image.new('RGBA',im.size,(0,0,0,0)); ImageDraw.Draw(sh).ellipse([cx-r,cy-r+10,cx+r,cy+r+10],fill=(0,0,0,90)); im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    g=Image.new('RGBA',(2*r,2*r)); gd=ImageDraw.Draw(g)
    for k in range(2*r): gd.line([(0,k),(2*r,k)],fill=(255,int(90-40*k/(2*r)),int(120-60*k/(2*r))))
    m=Image.new('L',(2*r,2*r),0); ImageDraw.Draw(m).ellipse([0,0,2*r-1,2*r-1],fill=255)
    im.paste(g,(cx-r,cy-r),m); d=ImageDraw.Draw(im)
    d.ellipse([cx-r,cy-r,cx+r,cy+r],outline='white',width=6)
    e=emo('👍',int(r*1.05)); im.alpha_composite(e,(cx-e.width//2,cy-e.height//2-4))
def screen(i,t=1.0,count=None,reveal=False):
    e,opts,ans,R,lvl,_=P[i]; im=warm(i)
    D.chip(im,f'{lvl}  •  SPOTLIGHT {i+1}/6',150,LVC[lvl],(255,255,255),36)
    D.htext(im,"WHAT'S HIDING IN THE DARK?",250,64)
    st=stage(i,t,reveal); box=list(ST); D.shadow_box(im,box,48)
    m=Image.new('L',st.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,st.width-1,st.height-1],48,fill=255)
    im.paste(st,(ST[0],ST[1]),m); d=ImageDraw.Draw(im); d.rounded_rectangle(box,48,outline=(255,255,255),width=8)
    oy=ST[3]+40
    for j,o in enumerate(opts):
        b=[150,oy,W-150,oy+104]; good=reveal and j==ans
        D.shadow_box(im,b,52,8,10,60); d=ImageDraw.Draw(im)
        d.rounded_rectangle(b,52,fill=(40,200,100) if good else ((255,255,255,150) if reveal else (255,255,255)))
        d.ellipse([b[0]+12,oy+10,b[0]+96,oy+94],fill=(255,255,255) if good else D.OPTC[j])
        d.text((b[0]+54,oy+54),'ABC'[j],font=F('h',56),fill=(40,200,100) if good else 'white',anchor='mm')
        d.text((b[0]+130,oy+54),o,font=F('b',56,'SemiBold'),fill='white' if good else INK,anchor='lm')
        if good: cx_,cy_=b[2]-62,oy+52; d.line([(cx_-24,cy_+2),(cx_-7,cy_+20),(cx_+26,cy_-20)],fill='white',width=13)
        oy+=104+26
    if count:
        n,frac=count; cy=oy-26+44+70; R2=70; d.ellipse([W/2-R2,cy-R2,W/2+R2,cy+R2],fill=(255,255,255,70))
        d.arc([W/2-R2,cy-R2,W/2+R2,cy+R2],-90,-90+360*frac,fill=GOLD if frac>0.34 else (255,70,70),width=16)
        d.text((W/2,cy+4),str(n),font=F('h',96),fill='white',anchor='mm',stroke_width=6,stroke_fill=INK)
    likebtn(im,t)
    D.hoot(im,'cheer' if reveal else 'magnify',230,140,1905)
    return im

# ---- reveal animation: hole grows to full ----
def stage_grow(i,t,k):
    e,_,_,R,_,fc=P[i]; sw,sh=ST[2]-ST[0],ST[3]-ST[1]
    obj=Image.open(PH+f'/s{e}.jpg').convert('RGBA').resize((sw,sh))
    cx,cy=orbit(i,t,sw,sh)
    RR=R+(900*k*k)
    m=Image.new('L',(sw,sh),0); ImageDraw.Draw(m).ellipse([cx-RR,cy-RR,cx+RR,cy+RR],fill=255); m=m.filter(ImageFilter.GaussianBlur(R*0.12))
    dark=Image.blend(Image.new('RGBA',(sw,sh),(6,4,12,255)),obj,0.025)
    return Image.composite(obj,dark,m)
def hook():
    im=D.grad(0); D.htext(im,"WHAT'S HIDING",420,120); D.htext(im,'IN THE DARK?',560,130,GOLD)
    D.chip(im,'6 ANIMALS  •  ONLY 2% GET ALL!',720,(255,255,255),INK,44)
    D.hoot(im,'magnify',560,W/2,1650); return im
def ending():
    im=D.grad(8); D.htext(im,'6/6?',620,200,GOLD); D.htext(im,'OWL EYES!',800,120); D.chip(im,'COMMENT YOUR SCORE!',950,(255,255,255),INK,46)
    D.hoot(im,'cheer',480,W/2,1700); return im
