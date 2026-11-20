import sys, math
sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/which_heavier'); sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/spotlight'); sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/_shared')
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import cnt, sp, design as D
from design import F, INK, GOLD, W, H
BOX=cnt.BOX
LV={'EASY':((70,220,140),(20,160,110)),'MEDIUM':((255,190,70),(245,120,30)),'HARD':((255,100,120),(210,30,80))}
def gtext(im,s,cy,size,c1=(255,255,255),c2=(255,225,140),cx=W/2,outline=(60,20,90),ow=10):
    f=F('h',size); d=ImageDraw.Draw(im); w=d.textlength(s,font=f)
    m=Image.new('L',im.size,0); ImageDraw.Draw(m).text((cx,cy),s,font=f,anchor='mm',fill=255)
    o=Image.new('L',im.size,0); ImageDraw.Draw(o).text((cx,cy),s,font=f,anchor='mm',stroke_width=ow,stroke_fill=255)
    sh=Image.new('RGBA',im.size,(40,10,60,0)); sh.putalpha(o.filter(ImageFilter.GaussianBlur(10)).point(lambda v:int(v*0.6)))
    im.alpha_composite(sh,(0,8))
    ol=Image.new('RGBA',im.size,outline+(0,)); ol.putalpha(o); im.alpha_composite(ol)
    y=np.linspace(0,1,H)[:,None,None]; g=(np.array(c1)*(1-y)+np.array(c2)*y)*np.ones((1,W,1))
    gi=Image.fromarray(g.astype('uint8')).convert('RGBA'); gi.putalpha(m); im.alpha_composite(gi)
    hl=Image.new('RGBA',im.size,(255,255,255,0)); top=Image.new('L',im.size,0)
    ImageDraw.Draw(top).rectangle([0,0,W,int(cy-size*0.05)],fill=70)
    from PIL import ImageChops
    hl.putalpha(ImageChops.multiply(m,top)); im.alpha_composite(hl)
def pill(im,s,cy,lv):
    c1,c2=LV[lv]; f=F('h',38); d=ImageDraw.Draw(im); w=d.textlength(s,font=f)+70; x0=W/2-w/2; b=[x0,cy-32,x0+w,cy+32]
    gm=Image.new('L',im.size,0); ImageDraw.Draw(gm).rounded_rectangle([b[0]-6,b[1]-6,b[2]+6,b[3]+6],40,fill=200)
    gl=Image.new('RGBA',im.size,c1+(0,)); gl.putalpha(gm.filter(ImageFilter.GaussianBlur(16))); im.alpha_composite(gl)
    y=np.linspace(0,1,64)[:,None,None]; g=(np.array(c1)*(1-y)+np.array(c2)*y)*np.ones((1,int(w),1))
    gi=Image.fromarray(g.astype('uint8')).convert('RGBA'); mm=Image.new('L',gi.size,0); ImageDraw.Draw(mm).rounded_rectangle([0,0,gi.width-1,63],32,fill=255)
    im.paste(gi,(int(x0),int(cy-32)),mm); d=ImageDraw.Draw(im)
    d.rounded_rectangle(b,32,outline=(255,255,255),width=4); d.text((W/2,cy+2),s,font=f,fill='white',anchor='mm')
def glassbox(im):
    x0,y0,x1,y1=BOX
    gm=Image.new('L',im.size,0); ImageDraw.Draw(gm).rounded_rectangle([x0-10,y0-10,x1+10,y1+10],60,fill=170)
    gl=Image.new('RGBA',im.size,(255,240,200,0)); gl.putalpha(gm.filter(ImageFilter.GaussianBlur(28))); im.alpha_composite(gl)
    D.shadow_box(im,list(BOX),52)
    y=np.linspace(0,1,y1-y0)[:,None,None]; g=(np.array([255,253,248])*(1-y)+np.array([250,240,228])*y)*np.ones((1,x1-x0,1))
    gi=Image.fromarray(g.astype('uint8')).convert('RGBA'); mm=Image.new('L',gi.size,0); ImageDraw.Draw(mm).rounded_rectangle([0,0,gi.width-1,gi.height-1],52,fill=255)
    im.paste(gi,(x0,y0),mm); d=ImageDraw.Draw(im)
    for x in range(x0+45,x1,58):
        for yy in range(y0+45,y1,58): d.ellipse([x-3,yy-3,x+3,yy+3],fill=(238,228,214))
    d.rounded_rectangle(BOX,52,outline=(255,255,255),width=9)
cnt.boxbg=glassbox
def timer(im,cy,n,frac):
    d=ImageDraw.Draw(im); R2=70
    gm=Image.new('L',im.size,0); ImageDraw.Draw(gm).ellipse([W/2-R2-14,cy-R2-14,W/2+R2+14,cy+R2+14],fill=150)
    gl=Image.new('RGBA',im.size,(255,220,120,0)); gl.putalpha(gm.filter(ImageFilter.GaussianBlur(18))); im.alpha_composite(gl); d=ImageDraw.Draw(im)
    d.ellipse([W/2-R2,cy-R2,W/2+R2,cy+R2],fill=(255,255,255))
    d.arc([W/2-R2+4,cy-R2+4,W/2+R2-4,cy+R2-4],-90,-90+360*frac,fill=(255,170,40) if frac>0.34 else (255,70,70),width=14)
    d.text((W/2,cy+4),str(n),font=F('h',84),fill=INK,anchor='mm')
def show(lvl,i,counts,seed,t=1.0,count=None,hl=None):
    im=sp.warm(i); pill(im,f'{lvl}  •  {sum(counts.values())} SHAPES',140,lvl)
    gtext(im,'REMEMBER THE SHAPES!',240,70)
    glassbox(im)
    for kind,cx,cy,r,a in cnt.layout(counts,seed): cnt.draw_shape(im,kind,cx,cy,r,a,None if hl is None else (kind==hl))
    if count: timer(im,1320,*count)
    sp.likebtn(im,t); D.hoot(im,'magnify',230,140,1905); return im
def ansrow(im,oy,opts,ans):
    for j,o in enumerate(opts):
        x0=130+j*285; b=[x0,oy,x0+250,oy+120]; good=ans is not None and j==ans; dim=ans is not None and not good
        D.shadow_box(im,b,40,8,10,60); d=ImageDraw.Draw(im)
        d.rounded_rectangle(b,40,fill=(40,200,100) if good else ((255,255,255,140) if dim else (255,255,255)),outline=(255,255,255),width=4)
        d.ellipse([b[0]+14,oy+18,b[0]+98,oy+102],fill=(255,255,255) if good else D.OPTC[j])
        d.text((b[0]+56,oy+62),'ABC'[j],font=F('h',52),fill=(40,200,100) if good else 'white',anchor='mm')
        d.text((b[0]+172,oy+62),o,font=F('h',72),fill='white' if good else (INK if not dim else (150,140,160)),anchor='mm')
NAME={'circle':'CIRCLES','square':'CUBES','triangle':'TRIANGLES','star':'STARS','heart':'HEARTS','diamond':'DIAMONDS'}
def question(lvl,i,qn,kind,opts,count=None,t=1.0):
    im=sp.warm(i); pill(im,f'{lvl}  •  QUESTION {qn}',140,lvl)
    gtext(im,'DO YOU REMEMBER?',240,70)
    glassbox(im); cnt.draw_shape(im,kind,W/2,(BOX[1]+BOX[3])/2,250,0)
    gtext(im,f'HOW MANY {NAME[kind]}',1275,68); gtext(im,'WERE THERE?',1360,68,(255,235,120),(255,170,40))
    ansrow(im,1450,opts,None)
    if count: timer(im,1690,*count)
    sp.likebtn(im,t); D.hoot(im,'think',230,140,1905); return im
def reveal(lvl,i,qn,kind,opts,ans,counts,seed,t=1.0):
    im=sp.warm(i); pill(im,f'{lvl}  •  ANSWER',140,lvl)
    gtext(im,f'{opts[ans]} {NAME[kind]}!',240,76,(140,255,170),(40,200,110))
    glassbox(im)
    for k,cx,cy,r,a in cnt.layout(counts,seed): cnt.draw_shape(im,k,cx,cy,r,a,k==kind)
    gtext(im,f'HOW MANY {NAME[kind]}',1275,68); gtext(im,'WERE THERE?',1360,68,(255,235,120),(255,170,40))
    ansrow(im,1450,opts,ans)
    sp.likebtn(im,t); D.hoot(im,'cheer',230,140,1905); return im
LEVELS=[('EASY',0,{'circle':4,'square':3,'triangle':2,'star':1},1,5,[('circle',['3','4','5'],1),('square',['2','3','4'],1)]),
        ('MEDIUM',2,{'star':5,'heart':4,'circle':2,'square':1},2,6,[('star',['4','5','6'],1),('heart',['3','4','5'],1)]),
        ('HARD',4,{'circle':5,'star':4,'heart':3,'square':2,'diamond':1},3,7,[('circle',['5','6','4'],0),('heart',['2','4','3'],2)])]
