import sys, math, random
sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/which_heavier'); sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/spotlight'); sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/_shared')
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import design as D, sp, cnt2
from design import F, INK, W, H
COLS,ROWS=6,8; CS=116; BX=(W-COLS*CS)//2-30; BY=415
CC={'red':(240,50,70),'orange':(255,140,30),'yellow':(255,215,40),'green':(60,200,90),'blue':(50,140,255),'purple':(170,80,240)}
AN={'dog':'dog_face','cat':'cat_face','panda':'panda','lion':'lion','frog':'frog','pig':'pig_face','apple':'red_apple','banana':'banana','grapes':'grapes','strawberry':'strawberry','fish':'tropical_fish','octopus':'octopus','crab':'crab','whale':'spouting_whale','car':'automobile','bus':'bus','rocket':'rocket','helicopter':'helicopter','donut':'doughnut','lollipop':'lollipop','cupcake':'cupcake','icecream':'soft_ice_cream','sun':'sun','star':'star','cloud':'cloud','snowflake':'snowflake'}
NAMES=list(AN)
_C={}
def candy(c,s):
    if (c,s) in _C: return _C[(c,s)]
    if c in AN:
        im=Image.open(f'/home/claude/shorts-media/pipeline/puzzles/stay_till_end/ic/{AN[c]}.png').convert('RGBA').resize((s,s),Image.LANCZOS); _C[(c,s)]=im; return im
    S=s*4; im=Image.new('RGBA',(S,S),(0,0,0,0)); d=ImageDraw.Draw(im); col=CC[c]
    dark=tuple(int(v*0.6) for v in col); lite=tuple(min(255,int(v*1.25+40)) for v in col)
    m=Image.new('L',(S,S),0); md=ImageDraw.Draw(m); p=S*0.1
    shape={'red':'circle','orange':'oval','yellow':'drop','green':'square','blue':'diamond','purple':'hex'}[c]
    if shape=='circle': md.ellipse([p,p,S-p,S-p],fill=255)
    elif shape=='oval': md.ellipse([p*0.6,p*1.8,S-p*0.6,S-p*1.8],fill=255)
    elif shape=='square': md.rounded_rectangle([p*1.3,p*1.3,S-p*1.3,S-p*1.3],S*0.18,fill=255)
    elif shape=='diamond': md.polygon([(S/2,p*0.7),(S-p*0.9,S/2),(S/2,S-p*0.7),(p*0.9,S/2)],fill=255)
    elif shape=='hex': md.polygon([(S/2+(S/2-p)*math.cos(math.pi/3*k+math.pi/6),S/2+(S/2-p)*math.sin(math.pi/3*k+math.pi/6)) for k in range(6)],fill=255)
    else: md.ellipse([p*1.2,S*0.32,S-p*1.2,S-p],fill=255); md.polygon([(S/2,p*0.5),(p*1.6,S*0.6),(S-p*1.6,S*0.6)],fill=255)
    m=m.filter(ImageFilter.GaussianBlur(S*0.012))
    yy=np.linspace(0,1,S)[:,None,None]; g=(np.array(lite)*(1-yy)+np.array(dark)*yy)*np.ones((1,S,1))
    body=Image.fromarray(g.astype('uint8')).convert('RGBA'); body.putalpha(m)
    im.alpha_composite(body)
    # gloss
    gm=Image.new('L',(S,S),0); ImageDraw.Draw(gm).ellipse([S*0.26,S*0.18,S*0.6,S*0.4],fill=200)
    from PIL import ImageChops
    gm=ImageChops.multiply(gm.filter(ImageFilter.GaussianBlur(S*0.03)),m)
    gl=Image.new('RGBA',(S,S),(255,255,255,0)); gl.putalpha(gm); im.alpha_composite(gl)
    om=m.filter(ImageFilter.MaxFilter(9)); ring=Image.new('RGBA',(S,S),(255,255,255,0)); ring.putalpha(ImageChops.subtract(om,m).point(lambda v:min(255,v*2)))
    im.alpha_composite(ring)
    im=im.resize((s,s),Image.LANCZOS); _C[(c,s)]=im; return im
def board(seed=5,remain='panda'):
    random.seed(seed); flat=NAMES*((COLS*ROWS)//len(NAMES)); random.shuffle(flat); g=[flat[r*COLS:(r+1)*COLS] for r in range(ROWS)]
    # ensure final color count small; build clear order: all non-remain cells cleared over time in clusters
    cells=[(r,c) for r in range(ROWS) for c in range(COLS)]
    keep=[(r,c) for (r,c) in cells if g[r][c]==remain]; random.shuffle(keep)
    keepset=set(keep[:1])  # only one survives
    clear=[x for x in cells if x not in keepset]; random.shuffle(clear)
    dec=[x for x in clear if g[x[0]][x[1]] in ('lion','cat','frog')]; random.shuffle(dec); dec=set(dec[:3])
    clear.sort(key=lambda x:(random.random()*0.6+(x[0]/ROWS)*0.4+(0.25 if g[x[0]][x[1]]==remain else 0)+(2 if x in dec else 0)))
    return g,clear,keepset
def boardbg(im):
    x0,y0=BX-24,BY-24; x1,y1=BX+COLS*CS+24,BY+ROWS*CS+24
    gm=Image.new('L',im.size,0); ImageDraw.Draw(gm).rounded_rectangle([x0-10,y0-10,x1+10,y1+10],50,fill=170)
    gl=Image.new('RGBA',im.size,(255,240,200,0)); gl.putalpha(gm.filter(ImageFilter.GaussianBlur(26))); im.alpha_composite(gl)
    D.shadow_box(im,[x0,y0,x1,y1],46); d=ImageDraw.Draw(im)
    d.rounded_rectangle([x0,y0,x1,y1],46,fill=(70,30,110),outline=(255,255,255),width=8)
    for r in range(ROWS):
        for c in range(COLS):
            col=(95,50,140) if (r+c)%2 else (85,42,128)
            d.rounded_rectangle([BX+c*CS+4,BY+r*CS+4,BX+(c+1)*CS-4,BY+(r+1)*CS-4],18,fill=col)
def pop(im,x,y,k,col):
    d=ImageDraw.Draw(im)
    for j in range(8):
        a=j*math.pi/4; r=20+70*k; s=10*(1-k)+2
        d.ellipse([x+r*math.cos(a)-s,y+r*math.sin(a)-s,x+r*math.cos(a)+s,y+r*math.sin(a)+s],fill=col+(int(255*(1-k)),))
    d.ellipse([x-40*(1+k),y-40*(1+k),x+40*(1+k),y+40*(1+k)],outline=(255,255,255,int(200*(1-k))),width=5)
def screen(prog,t=1.0,reveal=False,count=None,seed=5,remain='panda',hand=True):
    im=sp.warm(5); g,clear,keep=board(seed,remain)
    cnt2.pill(im,'GUESS BEFORE TIME RUNS OUT!',140,'HARD')
    cnt2.gtext(im,'WHICH ANIMAL WILL',232,66); cnt2.gtext(im,'STAY TILL THE END?',312,72,(255,235,120),(255,170,40))
    boardbg(im)
    n=int(len(clear)*prog); gone=set(clear[:n]); popping=clear[max(0,n-5):n]
    for r in range(ROWS):
        for c in range(COLS):
            if (r,c) in gone: continue
            s=CS-14; ci=candy(g[r][c],s)
            if reveal and (r,c) in keep:
                gm=Image.new('L',im.size,0); ImageDraw.Draw(gm).ellipse([BX+c*CS-50,BY+r*CS-50,BX+(c+1)*CS+50,BY+(r+1)*CS+50],fill=255)
                gl=Image.new('RGBA',im.size,(255,240,140,0)); gl.putalpha(gm.filter(ImageFilter.GaussianBlur(20))); im.alpha_composite(gl)
            im.alpha_composite(ci,(BX+c*CS+7,BY+r*CS+7))
    lay=Image.new('RGBA',im.size,(0,0,0,0))
    for j,(r,c) in enumerate(popping):
        pop(lay,BX+c*CS+CS/2,BY+r*CS+CS/2,0.3+0.12*j,(255,230,120))
    im.alpha_composite(lay)
    if hand and not reveal and n>0:
        r,c=clear[n-1] if n<len(clear) else clear[-1]
        hx,hy=BX+c*CS+CS/2,BY+r*CS+CS/2
        hs=170; hi=Image.open('/home/claude/shorts-media/pipeline/puzzles/stay_till_end/ic/hand.png').convert('RGBA').resize((hs,hs),Image.LANCZOS).rotate(-18,resample=Image.BICUBIC)
        sh=Image.new('RGBA',(hs,hs),(40,10,60,255)); sh.putalpha(hi.split()[3].point(lambda v:int(v*0.4)))
        l2=Image.new('RGBA',im.size,(0,0,0,0)); l2.alpha_composite(sh,(int(hx-hs*0.38+10),int(hy-hs*0.04+14))); im.alpha_composite(l2.filter(ImageFilter.GaussianBlur(8)))
        d=ImageDraw.Draw(im); d.ellipse([hx-26,hy-26,hx+26,hy+26],outline=(255,255,255),width=5)
        im.alpha_composite(hi,(int(hx-hs*0.38),int(hy-hs*0.04)))
    oy=BY+ROWS*CS+80
    # colour option chips
    names=NAMES; bw=150; gap=12; x0=W/2-(6*bw+5*gap)/2
    for j,nm in enumerate(names):
        b=[x0+j*(bw+gap),oy,x0+j*(bw+gap)+bw,oy+150]; good=reveal and nm==remain; dim=reveal and not good
        D.shadow_box(im,b,30,6,8,60); d=ImageDraw.Draw(im)
        d.rounded_rectangle(b,30,fill=(40,200,100) if good else ((255,255,255,130) if dim else (255,255,255)),outline='white',width=4)
        ci=candy(nm,96)
        if dim: ci=ci.copy(); ci.putalpha(ci.split()[3].point(lambda v:v//3))
        im.alpha_composite(ci,(int(b[0]+bw/2-48),oy+10)); d=ImageDraw.Draw(im)
        d.text(((b[0]+b[2])/2,oy+124),nm.upper(),font=F('h',30),fill='white' if good else INK,anchor='mm')
    if count: cnt2.timer(im,oy+270,*count)
    if reveal: cnt2.gtext(im,f'THE {remain.upper()}!',oy+270,80,(140,255,170),(40,200,110))
    sp.likebtn(im,t); D.hoot(im,'cheer' if reveal else 'think',230,140,1905); return im
