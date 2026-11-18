import sys; sys.path.insert(0,'/home/claude/shorts-media/pipeline')
from PIL import Image, ImageDraw, ImageFilter
from engine import font, F_BOLD, emoji_img
from mascot import hoot
W,H=1080,1920
def ot(d,xy,t,sz,fill,sw=12):
    f=font(F_BOLD,sz)
    while d.textlength(t,font=f)>W-80: sz-=6; f=font(F_BOLD,sz)
    x=xy[0]-d.textlength(t,font=f)/2
    d.text((x,xy[1]),t,font=f,fill=fill,stroke_width=sw,stroke_fill=(0,0,0))
def make(out,bg,l1,l2,big,emos,qcard):
    im=Image.new("RGBA",(W,H),bg+(255,)); d=ImageDraw.Draw(im)
    for k in range(0,W+H,90): d.polygon([(k,0),(k+45,0),(k-H+45,H),(k-H,H)],fill=tuple(min(255,c+25) for c in bg))
    ot(d,(W/2,110),l1,130,(255,255,255)); ot(d,(W/2,260),l2,150,(255,225,60))
    # question card
    d.rounded_rectangle((70,520,W-70,560+86*len(qcard[0])+30+3*150+20),50,fill=(255,255,255),outline=(0,0,0),width=10)
    f=font(F_BOLD,70); y=560
    for ln in qcard[0]:
        d.text((W/2-d.textlength(ln,font=f)/2,y),ln,font=f,fill=(40,30,90)); y+=86
    for i,(o,ok) in enumerate(qcard[1]):
        yy=y+30+i*150; col=(240,240,250)
        d.rounded_rectangle((130,yy,W-130,yy+120),30,fill=col,outline=(40,30,90),width=5)
        d.text((180,yy+20),o,font=font(F_BOLD,66),fill=(40,30,90))
        d.text((W-230,yy+20),"?",font=font(F_BOLD,70),fill=(230,40,60))
    ot(d,(W/2,1300),big,190,(255,60,60),16)
    h=hoot(520,"cheer",0.0); im.alpha_composite(h,(W-h.width+10,H-h.height+20))
    for i,e in enumerate(emos): im.alpha_composite(emoji_img(e,170),(70+i*200,1560))
    im.convert("RGB").save(out,quality=92)
make("tA.jpg",(40,70,200),"ONLY 2% GET","ALL 6 RIGHT!","6/6?","🐙🍯⚖️",(["Capital of Australia?"],[("Sydney",False),("Canberra",True),("Melbourne",False)]))
make("tB.jpg",(230,60,120),"QUIZ TIME!","ACE ALL 6?","?!","🧠🦉🏆",(["1 kg feathers vs","1 kg iron?"],[("Feathers",False),("Iron",False),("Same",True)]))
make("tC.jpg",(20,150,90),"SMART QUIZ","99% GET IT WRONG","???","🐙❤️❤️",(["Which food","never spoils?"],[("Rice",False),("Honey",True),("Bread",False)]))
