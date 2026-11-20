import sys, os, math, json, subprocess
import os; _H=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(_H,'..','_shared')); sys.path.insert(0,_H); os.chdir(_H)
from PIL import Image
import design as D
from ws_core import ease_back
W,H,FPS=1080,1920,30
SEG=json.load(open('segs.json')); VD=os.environ.get('VOICE_DIR','sample_voice'); VL=[b-a for a,b in SEG]
CLIPS=['clips/easy.mp4','clips/medium.mp4','clips/hard.mp4']; CLEN=7.9; ASK=3.0; TU=0.8; TR=0.4
ROUNDS=[dict(name='EASY',intro=1,during=(2,3),qs=[(4,'How many times did Mia jump?',['2','3','4']),(5,"What colour was her brother's shirt?",['Red','Blue','Green']),(6,'How many people were there?',['2','3','4'])],after=[('like',7)]),
 dict(name='MEDIUM',intro=8,during=(9,10),qs=[(11,'What colour was the ball?',['Blue','Red','Yellow']),(12,'How many dogs did you see?',['1','2','3']),(14,'What colour was the umbrella?',['Yellow','Pink','Green']),(15,'Was Grandma jumping?',['Yes','No','Only once'])],before={14:('pause',13)}),
 dict(name='HARD',intro=16,during=(17,18),qs=[(19,'What colour were the birds in the sky?',['White','Black','Blue']),(20,"What colour was Mia's ribbon?",['Pink','Yellow','Blue']),(21,'How many YELLOW balloons were there?',['1','2','3']),(23,'How many cats were in the video?',['1','2','3'])],before={23:('comment',22)})]
EV=[]; VOICE=[]; t=0.0; gi=0
def add(kind,dur,**k):
    global t; EV.append(dict(kind=kind,t0=t,dur=dur,**k)); t+=dur
VOICE.append((0,0.4)); add('title',0.4+VL[0]+0.4)
for ri,R in enumerate(ROUNDS):
    VOICE.append((R['intro'],t+0.35)); add('round',0.35+VL[R['intro']]+0.35,r=ri)
    VOICE.append((R['during'][0],t+0.6)); VOICE.append((R['during'][1],t+max(4.4,0.6+VL[R['during'][0]]+0.4))); add('clip',CLEN,r=ri)
    for qn,(li,q,opts) in enumerate(R['qs']):
        b=R.get('before',{}).get(li)
        if b: VOICE.append((b[1],t+0.35)); add('note',0.35+VL[b[1]]+0.35,note=b[0])
        VOICE.append((li,t+0.3)); a0=0.3+VL[li]+0.15
        add('q',a0+ASK+TU,r=ri,qn=qn,q=q,opts=opts,gi=gi,a0=a0); gi+=1
    for nk,li in R.get('after',[]):
        VOICE.append((li,t+0.35)); add('note',0.35+VL[li]+0.35,note=nk)
BAR=240/118; pad=math.ceil(t/BAR)*BAR-t; EV[-1]['dur']+=pad; TOTAL=t+pad
class Reader:
    def __init__(s,f): s.p=subprocess.Popen(['ffmpeg','-loglevel','error','-i',f,'-vf',f'scale={W}:{H},fps={FPS}','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE); s.last=None
    def next(s):
        b=s.p.stdout.read(W*H*3)
        if len(b)==W*H*3: s.last=Image.frombytes('RGB',(W,H),b)
        return s.last
READ={}; CACHE={}
def render(e,lt):
    k=e['kind']
    if k=='title': return D.title_screen()
    if k=='round': return D.round_screen(e['r'],len(ROUNDS[e['r']]['qs']))
    if k=='note':
        st=1 if (e['note']=='like' and lt>1.6) else 0
        return D.note_screen(e['note'],st)
    if k=='clip':
        ri=e['r']
        if ri not in READ: READ[ri]=Reader(CLIPS[ri])
        return D.clip_overlay(READ[ri].next(),min(1,lt/CLEN))
    R=ROUNDS[e['r']]; a0=e['a0']; nopt=sum(1 for j in range(3) if lt>=0.35+0.22*j)
    count=None; tu=False
    if lt>=a0+ASK: tu=True
    elif lt>=a0: el=lt-a0; count=(math.ceil(ASK-el),1-el/ASK)
    return D.question_screen(e['gi'],R['name'],e['qn']+1,len(R['qs']),e['q'],e['opts'],count,tu,'like' if e['r']==0 else 'sub',nopt)
def static_key(e,lt):
    k=e['kind']
    if k in ('title','round'): return (id(e),)
    if k=='note': return (id(e), e['note']=='like' and lt>1.6)
    if k=='q':
        a0=e['a0']; nopt=sum(1 for j in range(3) if lt>=0.35+0.22*j)
        c=None if lt<a0 else ('tu' if lt>=a0+ASK else int((lt-a0)*15))
        return (id(e),nopt,c)
    return None
LASTIMG={}
def frame(t):
    i=max(j for j,e in enumerate(EV) if e['t0']<=t); e=EV[i]; lt=t-e['t0']
    key=static_key(e,lt)
    if key is not None and key in CACHE: cur=CACHE[key]
    else:
        cur=render(e,lt).convert('RGB')
        if key is not None: CACHE.clear(); CACHE[key]=cur
    LASTIMG[i]=cur
    if lt<TR and i>0 and (i-1) in LASTIMG:
        p=ease_back(lt/TR) if e['kind']!='clip' else lt/TR
        prev=LASTIMG[i-1]
        if e['kind']=='clip':      # white flash + zoom in
            z=1.15-0.15*p; c=cur.resize((int(W*z),int(H*z))); c=c.crop(((c.width-W)//2,(c.height-H)//2,(c.width-W)//2+W,(c.height-H)//2+H))
            fl=Image.new('RGB',(W,H),'white'); return Image.blend(fl,c,min(1,p*1.4))
        out=prev.copy(); x=int(W*(1-p)); out.paste(prev.crop((0,0,W,H)),(-int(W-x)//3,0)); out.paste(cur,(max(0,x),0)); return out
    return cur
def events():
    ev=[]
    for e in EV:
        s=e['t0']
        if e['kind']=='clip': ev+=[('swish',s),('ding',s+0.05)]
        else: ev+=[('whoosh',s)]
        if e['kind'] in ('title','round','note'): ev+=[('pop',s+0.3)]
        if e['kind']=='q':
            ev+=[('pop',s+0.35+0.22*j) for j in range(3)]
            a=s+e['a0']; ev+=[('tick',a+j) for j in range(int(ASK))]+[('ding',a+ASK)]
    return ev
CLIPT=[(e['r'],e['t0']) for e in EV if e['kind']=='clip']
if __name__=='__main__':
    out=sys.argv[1]
    if len(sys.argv)>2:
        ts=[float(x) for x in sys.argv[2:]]; ims=[frame(x).resize((360,640)) for x in ts]
        sh=Image.new('RGB',(360*len(ims),640))
        for k,m in enumerate(ims): sh.paste(m,(360*k,0))
        sh.save(out); print(TOTAL); sys.exit()
    pr=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    for f in range(int(TOTAL*FPS)): pr.stdin.write(frame(f/FPS).tobytes())
    pr.stdin.close(); pr.wait(); print('done',TOTAL)
