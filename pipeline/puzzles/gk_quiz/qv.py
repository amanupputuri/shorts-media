import sys, os, math, json, subprocess
import os; _H=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(_H,'..','_shared')); sys.path.insert(0,_H); os.chdir(_H)
from PIL import Image
import qd, design as D
W,H,FPS=1080,1920,30
SEG=json.load(open('segs.json')); VD=os.environ.get('VOICE_DIR','sample_voice'); VL=[b-a for a,b in SEG]
ASK=3.0; REV=0.25; TR=0.55
# line map: 0 intro; Qi line = 1+2i (+shifts), answer after
QL=[(1,2),(3,4),(6,7),(8,9),(10,11),(13,14),(15,16),(17,18),(19,20),(22,23)]
NOTES={9:('comment',21)}   # note shown before Q index
TEASE={4:'halfway',9:'q10'}
EV=[]; VOICE=[]; t=0.0
def add(kind,dur,**k):
    global t; EV.append(dict(kind=kind,t0=t,dur=dur,**k)); t+=dur
VOICE.append((0,0.3)); add('hook',0.3+VL[0]+0.5)
for i,(ql,al) in enumerate(QL):
    if i in NOTES:
        nk,li=NOTES[i]; VOICE.append((li,t+0.4)); add('note',0.4+VL[li]+0.4,note=nk)
    if i==9: add('q10',2.2)
    VOICE.append((ql,t+0.45)); a0=0.45+VL[ql]+0.2
    rv=a0+ASK+REV; VOICE.append((al,t+rv+0.1))
    add('q',rv+VL[al]+0.6,i=i,a0=a0,rv=rv)
add('end',3.2)
BAR=240/118; pad=math.ceil(t/BAR)*BAR-t; EV[-1]['dur']+=pad; TOTAL=t+pad
def screen(e,lt):
    k=e['kind']
    if k=='hook': return qd.hook_screen()
    if k=='q10': return qd.q10_tease()
    if k=='end': return qd.ending()
    if k=='note': return D.note_screen(e['note'],1 if (e['note']=='like' and lt>1.5) else 0)
    i=e['i']; nopt=sum(1 for j in range(3) if lt>=0.5+0.25*j)
    like='like' if i<5 else 'sub'
    if lt>=e['rv']: return qd.qscreen(i,reveal=True,like=like)
    if lt>=e['a0']:
        el=lt-e['a0']; return qd.qscreen(i,(max(1,math.ceil(ASK-el)),1-el/ASK),like=like)
    return qd.qscreen(i,None,nopt=nopt,like=like)
def key(e,lt):
    k=e['kind']
    if k in ('hook','q10','end'): return (id(e),)
    if k=='note': return (id(e),e['note']=='like' and lt>1.5)
    if lt>=e['rv']: return (id(e),'rv')
    if lt>=e['a0']: return (id(e),'c',int((lt-e['a0'])*15))
    return (id(e),'o',sum(1 for j in range(3) if lt>=0.5+0.25*j))
CACHE={}; LAST={}
def get(e,lt):
    kk=key(e,lt)
    if kk not in CACHE:
        if len(CACHE)>6: CACHE.clear()
        CACHE[kk]=screen(e,lt).convert('RGB')
    return CACHE[kk]
def smooth(x): return x*x*(3-2*x)
def frame(t):
    i=max(j for j,e in enumerate(EV) if e['t0']<=t); e=EV[i]; lt=t-e['t0']
    cur=get(e,lt)
    if lt<TR and i>0:
        p=smooth(lt/TR); pe=EV[i-1]; prev=get(pe,pe['dur']-0.001)
        # smooth push: previous slides left & fades, new slides in from right with crossfade
        off=int(W*0.25*(1-p))
        a=prev.crop((0,0,W,H)); b=Image.new('RGB',(W,H)); b.paste(cur,(off,0)); 
        if off>0: b.paste(prev.crop((W-off,0,W,H)),(0,0))
        return Image.blend(a,b,p)
    return cur
def events():
    ev=[]
    for e in EV:
        s=e['t0']; ev.append(('whoosh',s))
        if e['kind']=='q':
            ev+=[('pop',s+0.5+0.25*j) for j in range(3)]
            a=s+e['a0']; ev+=[('tick',a+j) for j in range(int(ASK))]+[('ding',s+e['rv'])]
        if e['kind']=='note' and e['note']=='like': ev+=[('boop',s+1.5)]
    return ev
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
