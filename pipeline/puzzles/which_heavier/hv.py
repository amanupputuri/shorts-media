import sys, math
sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/which_heavier'); sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/spotlight'); sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/_shared')
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import sp, design as D, cnt2
_W={}
_warm=sp.warm
def _cw(i):
    if i not in _W: _W[i]=_warm(i)
    return _W[i].copy()
sp.warm=_cw
from design import F, INK, W, H
_GT={}
def _memo(fn):
    def w(im,*a,**k):
        key=(fn.__name__,a,tuple(sorted(k.items())))
        if key not in _GT:
            lay=Image.new('RGBA',im.size,(0,0,0,0)); fn(lay,*a,**k); bb=lay.getbbox(); _GT[key]=(lay.crop(bb),bb[:2])
        l,p=_GT[key]; im.alpha_composite(l,p)
    return w
gtext=_memo(cnt2.gtext); pill=_memo(cnt2.pill); timer=cnt2.timer
cnt2.LV  # level colours
# (left, right, answer 'L'/'R'/'S', left weight, right weight, level)
Q=[('elephant','Elephant','automobile','Car','L','Avg 5,000 kg','Avg 1,400 kg','EASY'),
   ('soccer_ball','Football','watermelon_whole','Watermelon','R','Avg 430 g','Avg 5 kg','EASY'),
   ('tomato','Tomato','strawberry','Strawberry','L','Avg 120 g','Avg 15 g','MEDIUM'),
   ('giraffe','Giraffe','camel','Camel','L','Avg 1,000 kg','Avg 500 kg','MEDIUM'),
   ('gorilla','Gorilla','lion','Lion','R','Avg 160 kg','Avg 190 kg','HARD'),
   ('feather','1 kg Feathers','brick','1 kg Bricks','S','1 kg','1 kg','HARD')]
IC={}
def icon(n,s):
    if (n,s) not in IC: IC[(n,s)]=Image.open(f'/home/claude/shorts-media/pipeline/puzzles/which_heavier/ic/{n}.png').convert('RGBA').resize((s,s),Image.LANCZOS)
    return IC[(n,s)]
CX,PY=540,450   # pivot
import random
BG={}
def backdrop(im,i,t):
    if 'g' not in BG:
        gm=Image.new('L',im.size,0); ImageDraw.Draw(gm).ellipse([CX-470,PY-200,CX+470,PY+700],fill=150)
        gl=Image.new('RGBA',im.size,(255,245,215,0)); gl.putalpha(gm.filter(ImageFilter.GaussianBlur(90))); BG['g']=gl
        sh=Image.new('L',im.size,0); ImageDraw.Draw(sh).ellipse([CX-330,PY+690,CX+330,PY+770],fill=140)
        shc=Image.new('RGBA',im.size,(60,10,40,0)); shc.putalpha(sh.filter(ImageFilter.GaussianBlur(18))); BG['s']=shc
    im.alpha_composite(BG['g'])
    d=ImageDraw.Draw(im); random.seed(i*7)
    for k in range(26):
        x=random.randint(60,1020); y=random.randint(PY-120,PY+700); r=random.choice([3,4,6]); tw=0.5+0.5*math.sin(t*3+k)
        c=(255,255,255,int(120+120*tw)); d.line([(x-r*2,y),(x+r*2,y)],fill=c,width=2); d.line([(x,y-r*2),(x,y+r*2)],fill=c,width=2)
    # podium
    pd=[CX-300,PY+655,CX+300,PY+725]
    im.alpha_composite(BG['s'])
    y=np.linspace(0,1,70)[:,None,None]; g=(np.array([255,255,255])*(1-y)+np.array([255,215,190])*y)*np.ones((1,600,1))
    gi=Image.fromarray(g.astype('uint8')).convert('RGBA'); mm=Image.new('L',gi.size,0); ImageDraw.Draw(mm).rounded_rectangle([0,0,599,69],35,fill=255)
    im.paste(gi,(CX-300,PY+655),mm)
def gold(w,h,vertical=True):
    if vertical: y=np.linspace(0,1,h)[:,None,None]*np.ones((1,w,1))
    else: y=np.linspace(0,1,w)[None,:,None]*np.ones((h,1,1))
    stops=np.array([[255,240,170],[255,200,70],[205,130,30],[255,215,110]])
    p=y*3; i0=np.clip(p.astype(int),0,2); f=p-i0
    c=stops[i0[...,0]]*(1-f)+stops[np.clip(i0[...,0]+1,0,3)]*f
    return Image.fromarray(c.astype('uint8')).convert('RGBA')
def scale(im,ang,l,r,winner=None,wl=None,wr=None,t=0):
    d=ImageDraw.Draw(im)
    # post
    post=gold(56,660,False); m=Image.new('L',post.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,55,post.height-1],20,fill=255)
    im.paste(post,(CX-28,PY),m)
    base=gold(260,40); m=Image.new('L',base.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,259,39],18,fill=255); im.paste(base,(CX-130,PY+625),m)
    L=300; a=math.radians(ang)
    lx,ly=CX-L*math.cos(a),PY-L*math.sin(a); rx,ry=CX+L*math.cos(a),PY+L*math.sin(a)
    for (x,y,n,win,side) in [(lx,ly,l,winner in('L','S'),'L'),(rx,ry,r,winner in('R','S'),'R')]:
        py=y+330
        d=ImageDraw.Draw(im)
        for dx in (-125,125): d.line([(x,y),(x+dx,py)],fill=(255,225,140),width=5)
        if win:
            gm=Image.new('L',im.size,0); ImageDraw.Draw(gm).ellipse([x-210,py-330,x+210,py+60],fill=200)
            gl=Image.new('RGBA',im.size,(255,240,120,0)); gl.putalpha(gm.filter(ImageFilter.GaussianBlur(40))); im.alpha_composite(gl)
        s=260; ic=icon(n,s)
        sh=Image.new('RGBA',(s,s),(60,20,40,255)); sh.putalpha(ic.split()[3].point(lambda v:int(v*0.35)))
        lay=Image.new('RGBA',im.size,(0,0,0,0)); lay.alpha_composite(sh,(int(x-s/2+8),int(py-s+28))); im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(10)))
        im.alpha_composite(ic,(int(x-s/2),int(py-s+16)))
        pan=gold(320,70); m=Image.new('L',pan.size,0); ImageDraw.Draw(m).chord([0,-60,319,69],0,180,fill=255)
        im.paste(pan,(int(x-160),int(py-4)),m); d=ImageDraw.Draw(im)
        d.ellipse([x-160,py-14,x+160,py+14],fill=(255,236,170),outline=(255,250,225),width=4)
    # beam
    bl=int(2*L+40); beam=gold(bl,30); m=Image.new('L',beam.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,bl-1,29],15,fill=255); beam.putalpha(m)
    br=beam.rotate(-ang,expand=True,resample=Image.BICUBIC); im.alpha_composite(br,(int(CX-br.width/2),int(PY-br.height/2)))
    d=ImageDraw.Draw(im)
    for x,y in [(lx,ly),(rx,ry)]: d.ellipse([x-12,y-12,x+12,y+12],fill=(255,215,110),outline='white',width=3)
    d.ellipse([CX-38,PY-38,CX+38,PY+38],fill=(255,200,80),outline='white',width=7)
    d.polygon([(CX,PY-95),(CX-24,PY-40),(CX+24,PY-40)],fill=(255,210,90),outline='white')
    return (lx,ly+390),(rx,ry+390)
def name_tags(im,lpos,rpos,ln,rn,wl=None,wr=None,dim=None):
    for (x,y),nm,w,side in [(lpos,ln,wl,'L'),(rpos,rn,wr,'R')]:
        f=F('h',42); d=ImageDraw.Draw(im); tw=d.textlength(nm,font=f)+50; b=[x-tw/2,y-34,x+tw/2,y+34]
        D.shadow_box(im,b,34,6,8,60); d=ImageDraw.Draw(im)
        d.rounded_rectangle(b,34,fill=(255,255,255),outline=(255,225,140),width=4)
        d.text((x,y+2),nm,font=f,fill=INK,anchor='mm')
        if w:
            f2=F('h',40); tw=d.textlength(w,font=f2)+40; b=[x-tw/2,y+50,x+tw/2,y+108]
            d.rounded_rectangle(b,29,fill=(60,30,100)); d.text((x,y+80),w,font=f2,fill=(255,225,120),anchor='mm')
def opts(im,oy,i,ans=None):
    l,ln,r,rn,a=Q[i][:5]; three=(a=='S') or i==5
    items=[('A',ln.split()[-1].upper()),('B',rn.split()[-1].upper())]+([('C','SAME')] if three else [])
    n=len(items); bw=290 if n==3 else 400; gap=24; x0=W/2-(n*bw+(n-1)*gap)/2
    for j,(k,txt) in enumerate(items):
        b=[x0+j*(bw+gap),oy,x0+j*(bw+gap)+bw,oy+110]; key='LRS'[j]; good=ans is not None and key==ans; dim=ans is not None and not good
        D.shadow_box(im,b,40,8,10,60); d=ImageDraw.Draw(im)
        d.rounded_rectangle(b,40,fill=(40,200,100) if good else ((255,255,255,140) if dim else (255,255,255)),outline='white',width=4)
        d.ellipse([b[0]+12,oy+15,b[0]+92,oy+95],fill='white' if good else D.OPTC[j])
        d.text((b[0]+52,oy+57),k,font=F('h',50),fill=(40,200,100) if good else 'white',anchor='mm')
        fs=46 if len(txt)<=7 else 40
        d.text(((b[0]+92+b[2])/2,oy+57),txt,font=F('h',fs),fill='white' if good else (INK if not dim else (150,140,160)),anchor='mm')
def screen(i,t=1.0,count=None,tilt=0.0,reveal=False):
    l,ln,r,rn,a,wl,wr,lvl=Q[i]; im=sp.warm(i)
    pill(im,f'{lvl}  •  {i+1}/6',140,lvl)
    gtext(im,'WHICH IS HEAVIER?',240,76)
    backdrop(im,i,t)
    target={'L':-14,'R':14,'S':0}[a]; ang=target*tilt+ (1.5*math.sin(t*2.5) if tilt==0 else 0)
    lp,rp=scale(im,ang,l,r,winner=a if reveal else None,t=t)
    name_tags(im,lp,rp,ln,rn,wl if reveal else None,wr if reveal else None)
    if not reveal:
        d=ImageDraw.Draw(im); vy=PY+390
        gm=Image.new('L',im.size,0); ImageDraw.Draw(gm).ellipse([CX-80,vy-80,CX+80,vy+80],fill=200)
        gl=Image.new('RGBA',im.size,(255,90,120,0)); gl.putalpha(gm.filter(ImageFilter.GaussianBlur(22))); im.alpha_composite(gl); d=ImageDraw.Draw(im)
        d.ellipse([CX-58,vy-58,CX+58,vy+58],fill=(235,40,90),outline='white',width=6)
        d.text((CX,vy+3),'VS',font=F('h',56),fill='white',anchor='mm')
    oy=PY+795; opts(im,oy,i,a if reveal else None)
    if count: timer(im,PY+1045,*count)
    if reveal:
        msg={'L':f'{ln.upper()}!','R':f'{rn.upper()}!','S':'THE SAME!'}[a]
        gtext(im,msg,PY+1045,70,(140,255,170),(40,200,110))
    sp.likebtn(im,t); D.hoot(im,'cheer' if reveal else 'think',230,140,1905); return im
