import sys, math, random
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import ws_core as ws, grids_emo
W,H=1080,1920
import os as _os; _D=_os.path.dirname(_os.path.abspath(__file__)); LIL=_os.path.join(_D,'LilitaOne-Regular.ttf'); FRE=_os.path.join(_D,'Fredoka%5Bwdth,wght%5D.ttf')
FC={}
def F(kind,sz,wt='Bold'):
    k=(kind,sz,wt)
    if k not in FC:
        f=ImageFont.truetype(LIL if kind=='h' else FRE,sz)
        if kind!='h':
            try: f.set_variation_by_name(wt)
            except Exception: pass
        FC[k]=f
    return FC[k]
GOLD=(255,214,64); INK=(46,22,84)
PAL=[((255,94,98),(255,154,72)),((72,190,255),(38,104,230)),((176,96,255),(98,82,240)),((46,214,150),(12,150,110)),((255,190,40),(245,120,20)),
     ((255,92,170),(190,40,140)),((40,200,240),(30,120,210)),((150,210,40),(60,150,40)),((255,130,190),(150,120,255)),((60,220,220),(50,130,250)),((255,120,40),(225,45,60))]
GC={}
def grad(i):
    if i not in GC:
        a,b=PAL[i%len(PAL)]; y=np.linspace(0,1,H)[:,None]; x=np.linspace(0,1,W)[None,:]; k=np.clip(0.8*y+0.2*x,0,1)[...,None]
        arr=(np.array(a)*(1-k)+np.array(b)*k).astype(np.uint8); im=Image.fromarray(np.ascontiguousarray(np.broadcast_to(arr,(H,W,3)))).convert('RGBA')
        ov=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov); r=random.Random(i)
        for _ in range(22):
            cx,cy,rr=r.randint(0,W),r.randint(0,H),r.randint(30,130); d.ellipse([cx-rr,cy-rr,cx+rr,cy+rr],fill=(255,255,255,r.randint(12,28)))
        for _ in range(30):
            cx,cy=r.randint(0,W),r.randint(0,H); s=r.choice([3,4,6]); d.ellipse([cx-s,cy-s,cx+s,cy+s],fill=(255,255,255,r.randint(60,140)))
        im.alpha_composite(ov); GC[i]=im
    return GC[i].copy()
def shadow_box(im,box,rad,off=12,blur=14,alpha=70):
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle([box[0],box[1]+off,box[2],box[3]+off],rad,fill=(20,0,40,alpha))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
def htext(im,s,cy,sz,fill='white',stroke=(46,22,84),sw=10,cx=W/2,shadow=True,maxw=960):
    f=F('h',sz); d=ImageDraw.Draw(im)
    while d.textlength(s,font=f)>maxw: sz-=4; f=F('h',sz)
    if shadow:
        sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).text((cx,cy+10),s,font=f,fill=(20,0,40,120),anchor='mm',stroke_width=sw,stroke_fill=(20,0,40,120))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    d=ImageDraw.Draw(im); d.text((cx,cy),s,font=f,fill=fill,anchor='mm',stroke_width=sw,stroke_fill=stroke)
def chip(im,s,cy,bg=(255,255,255),fg=INK,sz=40,cx=W/2,padx=36,pady=16):
    d=ImageDraw.Draw(im); f=F('b',sz,'Bold'); w=d.textlength(s,font=f); h=sz+pady*2
    box=[cx-w/2-padx,cy-h/2,cx+w/2+padx,cy+h/2]; shadow_box(im,box,h//2,6,8,60)
    d=ImageDraw.Draw(im); d.rounded_rectangle(box,h//2,fill=bg); d.text((cx,cy+2),s,font=f,fill=fg,anchor='mm')
def wrap(s,f,maxw,d):
    words=s.split()
    for n in range(1,5):
        best=None
        import itertools
        for cuts in itertools.combinations(range(1,len(words)),n-1):
            parts=[' '.join(words[a:b]) for a,b in zip((0,)+cuts,cuts+(len(words),))]
            ws_=[d.textlength(p,font=f) for p in parts]
            if max(ws_)<=maxw:
                sc=max(ws_)-min(ws_)
                if best is None or sc<best[0]: best=(sc,parts)
        if best: return best[1]
    lines=['']
    for w_ in words:
        t=(lines[-1]+' '+w_).strip()
        if d.textlength(t,font=f)<=maxw: lines[-1]=t
        else: lines.append(w_)
    return lines
HOOT={}
def hoot(im,pose,size,cx,bottom):
    k=(pose,size)
    if k not in HOOT: HOOT[k]=ws.fit(ws.HP[pose],size)
    h=HOOT[k]; im.alpha_composite(h,(int(cx-h.width/2),int(bottom-h.height)))
def social(im,kind,state=0,big=False,scale=1.0):
    d=ImageDraw.Draw(im)
    if kind=='like': w,h=(300,96) if not big else (560,150); x,y=(36,36) if not big else ((W-560)//2,880); bg=(255,255,255); fg=(30,30,30); txt=['LIKE','LIKED'][state]; e='👍'
    else: w,h=(390,96) if not big else (620,150); x,y=(36,36) if not big else ((W-620)//2,1070); bg=[(235,30,35),(110,110,120)][state]; fg=(255,255,255); txt=['SUBSCRIBE','SUBSCRIBED'][state]; e='🔔'
    ww,hh=w*scale,h*scale; X=x+(w-ww)/2; Y=y+(h-hh)/2; box=[X,Y,X+ww,Y+hh]
    shadow_box(im,box,int(hh/2),8,10,80); d=ImageDraw.Draw(im); d.rounded_rectangle(box,int(hh/2),fill=bg)
    if scale>0.9:
        ic=grids_emo.emo(e,int(hh*0.66)); im.alpha_composite(ic,(int(X+hh*0.22),int(Y+(hh-ic.height)/2)))
        d.text((X+hh*0.22+ic.width+18,Y+hh/2+2),txt,font=F('b',int(hh*0.42),'Bold'),fill=fg,anchor='lm')
# ---------------- screens ----------------
def title_screen(t=1.0):
    im=grad(2); htext(im,'CAN YOU',470,120); htext(im,'REMEMBER',600,150,GOLD)
    htext(im,'EVERYTHING?',740,130)
    chip(im,'3 VIDEOS  •  11 QUESTIONS',880,(255,255,255),INK,42)
    hoot(im,'cheer',560,W/2,1640); return im
ROUNDC=[(7,(46,214,150)),(4,(255,170,30)),(0,(255,80,90))]
def round_screen(ri,nq):
    gi,_=ROUNDC[ri]; im=grad(gi)
    htext(im,['EASY','MEDIUM','HARD'][ri],620,200,'white'); htext(im,'ROUND',790,110,GOLD)
    chip(im,f'{nq} QUESTION'+('S' if nq>1 else ''),930,(255,255,255),INK,46)
    hoot(im,'think',470,W/2,1640); return im
OPTC=[(255,94,98),(48,120,240),(30,180,100)]
def question_screen(gi,rname,qn,nq,q,opts,count=None,timesup=False,like='like',nopt=3):
    im=grad(gi); d=ImageDraw.Draw(im)
    social(im,like)
    chip(im,f'{rname}  •  QUESTION {qn}/{nq}',300,(46,22,84),(255,255,255),36)
    # question card with consistent line spacing
    f=F('h',76); lines=wrap(q,f,800,d); lh=96
    ch=len(lines)*lh+100; top=400; box=[80,top,W-80,top+ch]
    shadow_box(im,box,52); d=ImageDraw.Draw(im); d.rounded_rectangle(box,52,fill=(255,255,255))
    y=top+50+lh/2
    for l in lines: d.text((W/2,y),l,font=f,fill=INK,anchor='mm'); y+=lh
    # options
    oy=top+ch+60
    for j,o in enumerate(opts):
        if j>=nopt: oy+=124+34; continue
        b=[150,oy,W-150,oy+124]; shadow_box(im,b,62,8,10,60); d=ImageDraw.Draw(im)
        d.rounded_rectangle(b,62,fill=(255,255,255)); d.ellipse([b[0]+14,oy+14,b[0]+110,oy+110],fill=OPTC[j])
        d.text((b[0]+62,oy+64),'ABC'[j],font=F('h',62),fill='white',anchor='mm')
        d.text((b[0]+150,oy+64),o,font=F('b',60,'SemiBold'),fill=INK,anchor='lm')
        oy+=124+34
    # timer ring
    cy=oy+120; R=88
    if timesup: htext(im,"TIME'S UP!",cy,100,'white',(200,20,50),10)
    elif count is not None:
        n,frac=count; d.ellipse([W/2-R,cy-R,W/2+R,cy+R],fill=(255,255,255,70))
        d.arc([W/2-R,cy-R,W/2+R,cy+R],-90,-90+360*frac,fill=GOLD if frac>0.34 else (255,70,70),width=18)
        d.text((W/2,cy+4),str(n),font=F('h',110),fill='white',anchor='mm',stroke_width=6,stroke_fill=INK)
    hoot(im,'magnify' if count or timesup else 'think',300,175,1840); return im
def note_screen(kind,state=0):
    gi={'like':2,'pause':9,'comment':5}[kind]; im=grad(gi)
    if kind=='like':
        htext(im,'ENJOYING IT?',690,120); social(im,'like',state,True); social(im,'sub',state,True)
    elif kind=='pause':
        htext(im,'NEED MORE TIME?',700,104); htext(im,'PAUSE THE VIDEO!',840,104,GOLD)
    else:
        htext(im,'HOW MANY DID',700,104); htext(im,'YOU GET RIGHT?',840,104,GOLD); chip(im,'TELL HOOT IN THE COMMENTS 👇'.replace(' 👇',''),980,(255,255,255),INK,44)
    hoot(im,'cheer',460,W/2,1700); return im
def clip_overlay(frame,prog):
    im=frame.convert('RGBA'); chip(im,'WATCH CAREFULLY!',190,(235,40,80),(255,255,255),48)
    d=ImageDraw.Draw(im); d.rounded_rectangle([80,1800,1000,1824],12,fill=(255,255,255,110)); d.rounded_rectangle([80,1800,80+920*prog,1824],12,fill=GOLD)
    hoot(im,'magnify',210,150,1780); return im
