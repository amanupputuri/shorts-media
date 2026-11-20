import sys, os; _H=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(_H,'..','_shared')); sys.path.insert(0,_H)
from PIL import Image, ImageDraw
import design as D
from design import F, INK, GOLD, W, H
Q=[('EASY',"How many days are there in a leap year?",['365','366','364'],1),
('EASY','Which is the largest planet in our solar system?',['Jupiter','Mars','Saturn'],0),
('EASY','What colour do you get by mixing blue and yellow?',['Purple','Orange','Green'],2),
('MEDIUM','How many continents are there?',['5','7','6'],1),
('MEDIUM','Which gas do plants take in from the air?',['Oxygen','Nitrogen','Carbon dioxide'],2),
('MEDIUM','Which is the fastest land animal?',['Cheetah','Horse','Lion'],0),
('MEDIUM','How many bones are in an adult human body?',['186','206','226'],1),
('HARD','What is the hardest natural substance?',['Gold','Iron','Diamond'],2),
('HARD','Which is the largest ocean?',['Pacific','Atlantic','Indian'],0),
('HARD','Who painted the Mona Lisa?',['Picasso','Leonardo da Vinci','Van Gogh'],1)]
LVC={'EASY':(30,170,90),'MEDIUM':(240,140,20),'HARD':(225,40,60)}
def qscreen(i,count=None,timesup=False,reveal=False,nopt=3,like='like'):
    lvl,q,opts,ans=Q[i]; im=D.grad(i); d=ImageDraw.Draw(im)
    D.social(im,like)
    # score chip top-right
    D.chip(im,'SCORE: ?/10',84,(46,22,84),GOLD,34,cx=W-200)
    D.chip(im,f'{lvl}  •  QUESTION {i+1}/10',270,LVC[lvl],(255,255,255),36)
    # stock photo
    ph=Image.open(os.path.join(_H,'photos',f'q{i+1:02d}.jpg')).convert('RGB'); pw,phh=880,340
    r=max(pw/ph.width,phh/ph.height); ph=ph.resize((int(ph.width*r)+1,int(ph.height*r)+1)); ph=ph.crop(((ph.width-pw)//2,(ph.height-phh)//2,(ph.width-pw)//2+pw,(ph.height-phh)//2+phh))
    pbox=[100,360,100+pw,360+phh]; D.shadow_box(im,pbox,40)
    m=Image.new('L',(pw,phh),0); ImageDraw.Draw(m).rounded_rectangle([0,0,pw-1,phh-1],40,fill=255)
    im.paste(ph,(100,360),m); d=ImageDraw.Draw(im); d.rounded_rectangle(pbox,40,outline=(255,255,255),width=8)
    f=F('h',68); lines=D.wrap(q,f,820,d); lh=84; ch=len(lines)*lh+70; top=740; box=[80,top,W-80,top+ch]
    D.shadow_box(im,box,52); d=ImageDraw.Draw(im); d.rounded_rectangle(box,52,fill=(255,255,255))
    y=top+35+lh/2
    for l in lines: d.text((W/2,y),l,font=f,fill=INK,anchor='mm'); y+=lh
    oy=top+ch+40
    for j,o in enumerate(opts):
        if j>=nopt: oy+=140; continue
        b=[150,oy,W-150,oy+112]; good=reveal and j==ans; dim=reveal and j!=ans
        D.shadow_box(im,b,62,8,10,60); d=ImageDraw.Draw(im)
        d.rounded_rectangle(b,62,fill=(40,200,100) if good else ((255,255,255,150) if dim else (255,255,255)),outline=(255,255,255) if good else None,width=6)
        d.ellipse([b[0]+12,oy+10,b[0]+104,oy+102],fill=(255,255,255) if good else D.OPTC[j])
        d.text((b[0]+58,oy+58),'✓' if False else 'ABC'[j],font=F('h',62),fill=(40,200,100) if good else 'white',anchor='mm')
        fs=60 if d.textlength(o,font=F('b',60,'SemiBold'))<560 else 50
        d.text((b[0]+140,oy+58),o,font=F('b',fs,'SemiBold'),fill='white' if good else INK,anchor='lm')
        if good:
            cx_,cy_=b[2]-66,oy+56; d.line([(cx_-26,cy_+2),(cx_-8,cy_+22),(cx_+28,cy_-22)],fill='white',width=14,joint='curve')
        oy+=140
    cy=oy+95; R=80
    if reveal: D.htext(im,'CORRECT ANSWER!',cy,86,'white',(20,120,60),9)
    elif timesup: D.htext(im,"TIME'S UP!",cy,100,'white',(200,20,50),10)
    elif count:
        n,frac=count; d=ImageDraw.Draw(im); d.ellipse([W/2-R,cy-R,W/2+R,cy+R],fill=(255,255,255,70))
        d.arc([W/2-R,cy-R,W/2+R,cy+R],-90,-90+360*frac,fill=GOLD if frac>0.34 else (255,70,70),width=18)
        d.text((W/2,cy+4),str(n),font=F('h',110),fill='white',anchor='mm',stroke_width=6,stroke_fill=INK)
    D.hoot(im,'cheer' if reveal else ('magnify' if count or timesup else 'think'),240,150,1905); return im
def hook_screen():
    im=D.grad(2); D.htext(im,'STOP SCROLLING!',330,110,GOLD)
    D.htext(im,'QUESTION 10',500,120); D.htext(im,'FOOLED 97%!',640,130,(255,90,110))
    D.chip(im,'CAN YOU SCORE 10/10?',800,(255,255,255),INK,48)
    D.hoot(im,'magnify',600,W/2,1700); return im
def q10_tease():
    im=D.grad(10); D.htext(im,'QUESTION 10',640,130); D.htext(im,'FOOLED 97%!',800,130,GOLD); D.chip(im,'ARE YOU READY?',950,(255,255,255),INK,50)
    D.hoot(im,'think',480,W/2,1700); return im
def halfway():
    im=D.grad(4); D.htext(im,'HALFWAY THERE!',680,110); D.htext(im,'STILL PERFECT?',820,110,GOLD); D.chip(im,'QUESTION 10 IS COMING...',960,(255,255,255),INK,44)
    D.hoot(im,'cheer',460,W/2,1700); return im
def ending():
    im=D.grad(8); D.htext(im,'10/10?',640,200,GOLD); D.htext(im,"YOU'RE A GENIUS!",820,104); D.chip(im,'CAN YOU DO IT AGAIN? 🔁'.replace(' 🔁',''),960,(255,255,255),INK,46)
    D.hoot(im,'cheer',480,W/2,1700); return im
