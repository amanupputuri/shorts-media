import sys, math, json, pickle, wave, subprocess
import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw
import ws, ws2, g2
from plan import PLAN
from ws import W,H,FPS,GOLD,font,xform,fit,paste_bottom,ease_back,HP
VD=os.environ.get('VOICE_DIR',os.path.join(os.path.dirname(os.path.abspath(__file__)),'sample_voice'))
SEG=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'segs.json'))); VL=[b-a for a,b in SEG]
LAYS=pickle.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'lays.pkl'),'rb'))
LINES=[(2,None,3),(4,5,6),(7,None,8),(9,None,10),(11,12,13),(14,None,15),(16,None,17),(18,None,None),(19,None,20),(21,None,None)]
MID_IN_ANN={1}
ASK=[4,4,5,5,5,5,6,6,6,6]; TR,OUT=0.5,0.35
VOICE=[(0,0.25),(1,0.25+VL[0]+0.3)]
EX_DUR=0.25+VL[0]+0.3+VL[1]+0.35
EX_CIRC=0.25+VL[0]+0.3+2.2      # circles start around "like these four apples"
P=[]; t=EX_DUR
for k,(a,m,e) in enumerate(LINES):
    ann=VL[a]*0.9
    if k in MID_IN_ANN: ann=VL[a]+0.25+VL[m]
    end=max(1.0,(VL[e]-0.25) if e is not None else 1.0)
    p=dict(t0=t,ann=ann,ask=ASK[k],end=end); p['dur']=TR+ann+ASK[k]+end
    VOICE.append((a,t+TR-0.1))
    if m is not None: VOICE.append((m,t+TR-0.1+VL[a]+0.25) if k in MID_IN_ANN else (m,t+TR+ann+0.2))
    if e is not None: VOICE.append((e,t+TR+ann+ASK[k]+0.15))
    P.append(p); t+=p['dur']
BAR=240/118; pad=math.ceil(t/BAR)*BAR-t; P[-1]['end']+=pad; P[-1]['dur']+=pad; TOTAL=t+pad
SR=44100; env=np.zeros(int(TOTAL*SR)+SR)
for li,vt in VOICE:
    with wave.open(os.path.join(VD,f'l{li:02d}.wav')) as w: a=np.abs(np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(float)/32768)
    s=int(vt*SR); env[s:s+len(a)]=np.maximum(env[s:s+len(a)],a[:len(env)-s])
kk=int(.06*SR); env=np.convolve(env,np.ones(kk)/kk,'same'); env/=env.max()
talk=lambda t: float(env[min(len(env)-1,int(t*SR))])
LAYER={}
def layer(i):
    if i not in LAYER: LAYER[i]=g2.make(i,PLAN[i][0],PLAN[i][1],layer=True,lay_in=LAYS[i])[0]
    return LAYER[i]
# example layer without circles + apple cells for animated circles
EXL=None; EXC=[]
def exlayer():
    global EXL,EXC
    if EXL is None:
        import grids
        EXL=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(EXL)
        f=font('Bold',64); s='HOW TO PLAY'; w=d.textlength(s,font=f); d.text((W/2-w/2,330),s,font=f,fill='white',stroke_width=5,stroke_fill=(40,15,80))
        f2=font('Bold',48); s='Find all the matching icons!'; w=d.textlength(s,font=f2); d.text((W/2-w/2,430),s,font=f2,fill=(255,214,90))
        lay='🍎 🍓 🍒 🍅 🍒 🍅 🍎 🍓 🍓 🍎 🍅 🍒 🍅 🍒 🍓 🍎'.split()
        C,Gp=170,14; gw=4*C+3*Gp; gx=(W-gw)//2; gy=560
        d.rounded_rectangle([gx-22,gy-22,gx+gw+22,gy+gw+22],36,fill=(255,255,255,40))
        for c,e in enumerate(lay):
            r,q=divmod(c,4); x=gx+q*(C+Gp); y=gy+r*(C+Gp)
            d.rounded_rectangle([x,y,x+C,y+C],26,fill=(250,246,255))
            ic=grids.fitbox(grids.emo(e),int(C*0.8)); EXL.alpha_composite(ic,(x+(C-ic.width)//2,y+(C-ic.height)//2))
            if e=='🍎': EXC.append((x,y,C))
        EXC.append(gy+gw)
    return EXL
BY=g2.GY+g2.GH+48
def hoot(im,t,pose):
    base=fit(HP[pose],200); tk=talk(t); br=1+0.025*math.sin(t*4)
    h2=xform(base,(1/br)*(1-0.035*tk),br*(1+0.07*tk),4*math.sin(t*2.2)+6*tk*math.sin(t*14)+(5*math.sin(t*3.5) if pose=='magnify' else 0))
    paste_bottom(im,h2,25+base.width/2,1690-14*tk); return im
def ctext(d,s,y,sz,fill,st=5,cx=W/2):
    f=font('Bold',sz); w=d.textlength(s,font=f); d.text((cx-w/2,y),s,font=f,fill=fill,stroke_width=st,stroke_fill=(20,10,40))
def frame(t):
    im=ws.bg(t)
    if t<EX_DUR:
        L=exlayer(); s=ease_back(t/0.45) if t<0.45 else 1
        if s<1:
            L2=L.resize((max(1,int(W*s)),max(1,int(H*s)))); im.alpha_composite(L2,((W-L2.width)//2,(H-L2.height)//2))
        else: im.alpha_composite(L)
        d=ImageDraw.Draw(im)
        for k,(x,y,C) in enumerate(EXC[:-1]):
            lt=t-(EX_CIRC+k*0.45)
            if lt>0:
                pr=min(1,lt/0.35); d.arc([x+6,y+6,x+C-6,y+C-6],-90,-90+360*pr,fill=(255,30,60),width=10)
        if t>EX_CIRC+4*0.45: ctext(d,'4 APPLES FOUND!',EXC[-1]+60,62,(120,255,150))
        ex=t>EX_DUR-0.35 and (t-(EX_DUR-0.35))/0.35
        return hoot(im,t,'cheer' if t>EX_CIRC+2 else 'think').convert('RGB')
    i=max(k for k in range(10) if P[k]['t0']<=t); p=P[i]; lt=t-p['t0']
    a0=TR+p['ann']; a1=a0+p['ask']
    if lt<TR: off=W*(1-ease_back(lt/TR))
    elif lt>p['dur']-OUT: off=-W*((lt-(p['dur']-OUT))/OUT)**2
    else: off=0
    L=layer(i)
    if off>=0:
        if off<W: im.alpha_composite(L,(int(off),0))
    else: im.alpha_composite(L.crop((int(-off),0,W,H)),(0,0))
    d=ImageDraw.Draw(im)
    if off==0:
        x0,x1=250,g2.GX+g2.GW; cx=(x0+x1)/2
        d.rounded_rectangle((x0,BY,x1,BY+28),14,fill=(90,70,140))
        if a0<=lt<a1:
            k=(lt-a0)/p['ask']; d.rounded_rectangle((x0,BY,x0+(x1-x0)*(1-k),BY+28),14,fill=GOLD if k<0.75 else (255,90,90))
            n=math.ceil(p['ask']-(lt-a0)); sc=1+0.25*max(0,1-((lt-a0)%1)/0.2)
            ctext(d,str(n),BY+40-20*(sc-1),int(70*sc),'white',cx=cx)
            if i==4:
                hf=font('Bold',28); tx='II  PAUSE FOR MORE TIME'; tw=d.textlength(tx,font=hf)
                d.rounded_rectangle((cx-tw/2-18,BY+120,cx+tw/2+18,BY+166),23,fill='white'); d.text((cx-tw/2,BY+126),tx,font=hf,fill=(60,30,110))
        elif lt<a0: ctext(d,'GET READY…',BY+50,54,'white',4,cx)
        else: ctext(d,"TIME'S UP!",BY+46,66,(255,120,120),5,cx)
    im=ws2.badge(im,'like' if i<5 else 'sub',lt)
    pose='magnify' if a0<=lt<a1 else ('cheer' if lt>=a1 else 'think')
    return hoot(im,t,pose).convert('RGB')
def events():
    ev=[('pop',0.2)]+[('pop',EX_CIRC+k*0.45) for k in range(4)]+[('ding',EX_CIRC+1.9)]
    for p in P:
        s=p['t0']; a0=s+TR+p['ann']
        ev+=[('whoosh',s),('pop',s+TR*0.8)]+[('tick',a0+j) for j in range(p['ask'])]+[('ding',a0+p['ask']),('whoosh',s+p['dur']-OUT)]
    return ev
if __name__=='__main__':
    out=sys.argv[1]
    if len(sys.argv)>2:
        ts=[float(x) for x in sys.argv[2:]]; ims=[frame(x).resize((360,640)) for x in ts]
        sh=Image.new('RGB',(360*len(ims),640))
        for k,m in enumerate(ims): sh.paste(m,(360*k,0))
        sh.save(out); print(TOTAL); sys.exit()
    pr=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    for f in range(int(TOTAL*FPS)): pr.stdin.write(frame(f/FPS).tobytes())
    pr.stdin.close(); pr.wait(); print('done',TOTAL)
