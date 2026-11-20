import sys, math, subprocess
sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/spotlight'); sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/_shared')
from PIL import Image, ImageDraw
import sp, design as D
W,H,FPS=1080,1920,30
EXPL=6.0; GROW=0.7; HOLD=3.0; TR=0.55
EV=[]; t=0.0
def add(k,d,**kw):
    global t; EV.append(dict(kind=k,t0=t,dur=d,**kw)); t+=d
for i in range(6): add('p',0.6+EXPL+GROW+HOLD,i=i)
TOTAL=t
STAT={}
def render(e,lt):
    k=e['kind']
    if k in('hook','end'):
        if k not in STAT: STAT[k]=(sp.hook() if k=='hook' else sp.ending()).convert('RGB')
        return STAT[k]
    i=e['i']; a=0.6; tt=lt
    if lt<a+EXPL:
        el=max(0,lt-a); n=max(1,math.ceil(EXPL-el)); return sp.screen(i,t=tt,count=(n,1-el/EXPL)).convert('RGB')
    k2=min(1,(lt-a-EXPL)/GROW)
    if k2<1:
        im=sp.screen(i,t=a+EXPL,count=None)   # base layout
        st=sp.stage_grow(i,a+EXPL,k2); m=Image.new('L',st.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,st.width-1,st.height-1],48,fill=255)
        im.paste(st,(sp.ST[0],sp.ST[1]),m); ImageDraw.Draw(im).rounded_rectangle(sp.ST,48,outline=(255,255,255),width=8)
        return im.convert('RGB')
    key=('rev',i)
    if key not in STAT: STAT[key]=sp.screen(i,reveal=True).convert('RGB')
    return STAT[key]
LAST={}
def sm(x): return x*x*(3-2*x)
def frame(t):
    j=max(n for n,e in enumerate(EV) if e['t0']<=t); e=EV[j]; lt=t-e['t0']
    cur=render(e,lt)
    if lt<TR and j>0:
        pe=EV[j-1]; prev=LAST.get(j-1) or render(pe,pe['dur']-0.01); p=sm(lt/TR); off=int(W*0.25*(1-p))
        b=Image.new('RGB',(W,H)); b.paste(prev.crop((W-off,0,W,H)) if off else prev,(0,0)); b.paste(cur,(off,0)); return Image.blend(prev,b,p)
    LAST[j]=cur; return cur
if __name__=='__main__':
    out=sys.argv[1]; scale=float(sys.argv[2]) if len(sys.argv)>2 else 1
    w,h=int(W*scale)//2*2,int(H*scale)//2*2
    pr=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}','-r',str(FPS),'-i','-','-c:v','libx264','-preset','veryfast','-crf','22','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    for f in range(int(TOTAL*FPS)):
        im=frame(f/FPS)
        if scale!=1: im=im.resize((w,h))
        pr.stdin.write(im.tobytes())
    pr.stdin.close(); pr.wait(); print('done',TOTAL)
