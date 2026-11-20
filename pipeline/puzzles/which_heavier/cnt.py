import sys, math, random
sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/_shared'); sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/spotlight')
from PIL import Image, ImageDraw, ImageFilter
import design as D
from design import F, INK, GOLD, W, H
import sp
COL={'circle':(255,80,90),'square':(60,140,255),'triangle':(40,200,110),'star':(255,190,40),'heart':(240,90,200),'diamond':(150,90,240)}
LVC={'EASY':(30,170,90),'MEDIUM':(240,140,20),'HARD':(225,40,60)}
BOX=(110,330,970,1190)
def poly(kind,cx,cy,r,a):
    if kind=='circle': return None
    if kind=='square': n,ofs=4,math.pi/4
    elif kind=='triangle': n,ofs=3,-math.pi/2
    elif kind=='diamond': return [(cx+r*0.75*math.cos(a)-0,cy) for _ in []] or [(cx+math.cos(a)*dx-math.sin(a)*dy, cy+math.sin(a)*dx+math.cos(a)*dy) for dx,dy in [(0,-r),(r*0.68,0),(0,r),(-r*0.68,0)]]
    elif kind=='star':
        return [(cx+(r if k%2==0 else r*0.45)*math.cos(a-math.pi/2+k*math.pi/5), cy+(r if k%2==0 else r*0.45)*math.sin(a-math.pi/2+k*math.pi/5)) for k in range(10)]
    elif kind=='heart':
        pts=[]
        for k in range(40):
            t=2*math.pi*k/40; x=16*math.sin(t)**3; y=-(13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t))
            x,y=x*r/17,y*r/17; pts.append((cx+x*math.cos(a)-y*math.sin(a), cy+x*math.sin(a)+y*math.cos(a)))
        return pts
    return [(cx+r*math.cos(a+ofs+k*2*math.pi/n), cy+r*math.sin(a+ofs+k*2*math.pi/n)) for k in range(n)]
def layout(counts,seed):
    random.seed(seed); items=[]
    for k,c in counts.items(): items+=[k]*c
    random.shuffle(items); n=len(items)
    g=4
    x0,y0,x1,y1=BOX; pad=40; cw=(x1-x0-2*pad)/g; ch=(y1-y0-2*pad)/g
    r=min(cw,ch)*0.36
    cells=random.sample([(c,rw) for c in range(g) for rw in range(g)],n)
    pos=[]
    for kind,(c,rw) in zip(items,cells):
        j=(min(cw,ch)/2-r*1.08)
        cx=x0+pad+cw*(c+0.5)+random.uniform(-j,j); cy=y0+pad+ch*(rw+0.5)+random.uniform(-j,j)
        pos.append((kind,cx,cy,r,random.uniform(0,2*math.pi)))
    return pos
ICS={}
def icon(kind,size):
    k=(kind,size)
    if k not in ICS: ICS[k]=Image.open(f'/home/claude/shorts-media/pipeline/puzzles/which_heavier/ic/{kind}.png').convert('RGBA').resize((size,size),Image.LANCZOS)
    return ICS[k]
def draw_shape(im,kind,cx,cy,r,a,hl=None):
    s=int(r*2); ic=icon(kind,s).rotate((math.degrees(a)%40-20) if (kind!='circle' and a) else 0,resample=Image.BICUBIC)
    if hl is False:
        g=ic.convert('LA').convert('RGBA'); al=ic.split()[3].point(lambda v:int(v*0.35)); g.putalpha(al); ic=g
    sh=Image.new('RGBA',(s,s),(40,20,60,255)); sh.putalpha(ic.split()[3].point(lambda v:int(v*0.35)))
    lay=Image.new('RGBA',im.size,(0,0,0,0)); lay.alpha_composite(sh,(int(cx-s/2+6),int(cy-s/2+12)))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(8)))
    im.alpha_composite(ic,(int(cx-s/2),int(cy-s/2)))
def boxbg(im):
    D.shadow_box(im,list(BOX),48); d=ImageDraw.Draw(im)
    d.rounded_rectangle(BOX,48,fill=(255,250,240),outline='white',width=8)
    for x in range(BOX[0]+40,BOX[2],60):
        for y in range(BOX[1]+40,BOX[3],60): d.ellipse([x-3,y-3,x+3,y+3],fill=(235,225,210))
def show(lvl,i,counts,seed,t=1.0,count=None,hl=None):
    im=sp.warm(i); D.chip(im,f'{lvl}  •  {sum(counts.values())} SHAPES',140,LVC[lvl],(255,255,255),36)
    D.htext(im,'REMEMBER THE SHAPES!',232,64)
    boxbg(im)
    for kind,cx,cy,r,a in layout(counts,seed): draw_shape(im,kind,cx,cy,r,a,None if hl is None else (kind==hl))
    if count:
        n,frac=count; cy=1320; R2=72; d=ImageDraw.Draw(im)
        d.ellipse([W/2-R2,cy-R2,W/2+R2,cy+R2],fill=(255,255,255,70))
        d.arc([W/2-R2,cy-R2,W/2+R2,cy+R2],-90,-90+360*frac,fill=GOLD if frac>0.34 else (255,70,70),width=16)
        d.text((W/2,cy+4),str(n),font=F('h',96),fill='white',anchor='mm',stroke_width=6,stroke_fill=INK)
    sp.likebtn(im,t); D.hoot(im,'magnify',230,140,1905); return im
def question(lvl,i,kind,opts,ans=None,count=None,t=1.0):
    im=sp.warm(i); D.chip(im,f'{lvl}  •  QUESTION',140,LVC[lvl],(255,255,255),36)
    D.htext(im,'REMEMBER?',232,72)
    boxbg(im); draw_shape(im,kind,W/2,(BOX[1]+BOX[3])/2,250,0)
    D.htext(im,f'HOW MANY {kind.upper()}S',1275,70,(255,255,255))
    D.htext(im,'WERE THERE?',1365,70,GOLD)
    oy=1450; d=ImageDraw.Draw(im)
    for j,o in enumerate(opts):
        x0=130+j*285; b=[x0,oy,x0+250,oy+120]; good=ans is not None and j==ans
        D.shadow_box(im,b,40,8,10,60); d=ImageDraw.Draw(im)
        d.rounded_rectangle(b,40,fill=(40,200,100) if good else ((255,255,255,150) if ans is not None else (255,255,255)))
        d.ellipse([b[0]+14,oy+18,b[0]+98,oy+102],fill=(255,255,255) if good else D.OPTC[j])
        d.text((b[0]+56,oy+62),'ABC'[j],font=F('h',52),fill=(40,200,100) if good else 'white',anchor='mm')
        d.text((b[0]+170,oy+62),o,font=F('h',70),fill='white' if good else INK,anchor='mm')
    if count:
        n,frac=count; cy=1680; R2=66
        d.ellipse([W/2-R2,cy-R2,W/2+R2,cy+R2],fill=(255,255,255,70))
        d.arc([W/2-R2,cy-R2,W/2+R2,cy+R2],-90,-90+360*frac,fill=GOLD if frac>0.34 else (255,70,70),width=15)
        d.text((W/2,cy+4),str(n),font=F('h',88),fill='white',anchor='mm',stroke_width=6,stroke_fill=INK)
    sp.likebtn(im,t); D.hoot(im,'cheer' if ans is not None else 'think',230,140,1905); return im
