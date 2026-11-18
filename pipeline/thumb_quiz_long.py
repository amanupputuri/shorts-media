import sys, math; sys.path.insert(0,'/home/claude/shorts-media/pipeline')
from PIL import Image, ImageDraw, ImageFilter
from engine import font, F_BOLD, emoji_img
from mascot import hoot
W,H=1280,720
def ot(d,xy,t,sz,fill,sw=10,anchor="l"):
    f=font(F_BOLD,sz)
    while d.textlength(t,font=f)>xy[2]: sz-=4; f=font(F_BOLD,sz)
    x=xy[0] if anchor=="l" else xy[0]-d.textlength(t,font=f)/2
    d.text((x,xy[1]),t,font=f,fill=fill,stroke_width=sw,stroke_fill=(0,0,0))
def bg(c1,c2):
    im=Image.new("RGBA",(W,H)); d=ImageDraw.Draw(im)
    for y in range(H):
        k=y/H; d.line([(0,y),(W,y)],fill=tuple(int(c1[i]*(1-k)+c2[i]*k) for i in range(3))+(255,))
    cx,cy=W*0.62,H*0.45
    ov=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov)
    for a in range(0,360,12):
        r=math.radians(a); r2=math.radians(a+6)
        d.polygon([(cx,cy),(cx+1500*math.cos(r),cy+1500*math.sin(r)),(cx+1500*math.cos(r2),cy+1500*math.sin(r2))],fill=(255,255,255,22))
    im.alpha_composite(ov); return im
def card(im,box,q,opts):
    d=ImageDraw.Draw(im); x0,y0,x1,y1=box
    sh=Image.new("RGBA",im.size,(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle((x0+10,y0+16,x1+10,y1+16),36,fill=(0,0,0,150)); im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    d=ImageDraw.Draw(im); d.rounded_rectangle(box,36,fill=(255,255,255),outline=(255,200,70),width=8)
    f=font(F_BOLD,46); d.text(((x0+x1)/2-d.textlength(q,font=f)/2,y0+26),q,font=f,fill=(30,20,80))
    for i,o in enumerate(opts):
        yy=y0+100+i*82; d.rounded_rectangle((x0+30,yy,x1-30,yy+66),20,fill=(238,236,250),outline=(30,20,80),width=3)
        d.text((x0+56,yy+10),f"{'ABC'[i]}  {o}",font=font(F_BOLD,40),fill=(30,20,80)); d.text((x1-80,yy+8),"?",font=font(F_BOLD,46),fill=(230,40,60))
    return d
def make(out,c1,c2,l1,l2,badge,q,opts,emos):
    im=bg(c1,c2); d=ImageDraw.Draw(im)
    ot(d,(40,30,700),l1,108,(255,255,255)); ot(d,(40,150,720),l2,118,(255,210,60),12)
    card(im,(60,330,640,690),q,opts); d=ImageDraw.Draw(im)
    h=hoot(470,"cheer",0.0); im.alpha_composite(h,(W-h.width+30,H-h.height+40))
    d=ImageDraw.Draw(im); d.ellipse((900,30,1240,370),fill=(230,40,60),outline=(255,255,255),width=10)
    f=font(F_BOLD,150); d.text((1070-d.textlength(badge[0],font=f)/2,70),badge[0],font=f,fill=(255,255,255),stroke_width=8,stroke_fill=(0,0,0))
    f=font(F_BOLD,50); d.text((1070-d.textlength(badge[1],font=f)/2,250),badge[1],font=f,fill=(255,255,255),stroke_width=5,stroke_fill=(0,0,0))
    for i,e in enumerate(emos): im.alpha_composite(emoji_img(e,120),(690+i*125,560))
    im.convert("RGB").save(out,quality=93)
make("lA.jpg",(20,22,70),(80,30,140),"ONLY GENIUSES","GET 20/20!",("20","QUESTIONS"),"Which one floats?",["Ice cube","Grape","Marble"],["🧊","🦈"])
make("lB.jpg",(120,20,60),(230,70,60),"99% FAIL","THIS QUIZ!",("1%","PASS"),"Biggest organ?",["Liver","Skin","Lungs"],["🧠","🪐"])
make("lC.jpg",(10,80,90),(20,150,120),"HOW SMART","ARE YOU?",("20","QUIZ"),"Capital of Turkey?",["Istanbul","Ankara","Izmir"],["🌍","🍌"])
