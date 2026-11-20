import sys, math, subprocess, json, os
sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/which_heavier'); sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/_shared')
from PIL import Image
import hv
W,H,FPS=1080,1920,30; TR=0.5; TIMER=3.0; TILT=1.0
L=json.load(open('/home/claude/shorts-media/pipeline/puzzles/which_heavier/vo/lens.json'))
EV=[]; VOICE=[]; SFX=[]; t=0.0
for i in range(6):
    t0=t; lt=0.3
    if i==0: VOICE.append((0,t0+lt)); lt+=L[0]+0.35
    VOICE.append((1+2*i,t0+lt)); ts=lt+L[1+2*i]+0.2; ds=ts+TIMER; ae=ds+TILT
    VOICE.append((2+2*i,t0+ae-0.2)); dur=ae+L[2+2*i]+(1.4 if i==5 else 0.8)
    for k in range(3): SFX.append(('tick',t0+ts+k))
    SFX.append(('swish',t0+ds)); SFX.append(('ding',t0+ds+0.7))
    if i>0: SFX.append(('whoosh',t0-0.2))
    EV.append(dict(i=i,t0=t0,ts=ts,ds=ds,ae=ae,dur=dur)); t+=dur
TOTAL=t
def ease(k):  # overshoot bounce
    return 1-math.cos(k*math.pi*2.2)*math.exp(-4*k) if k<1 else 1
def render(e,lt):
    i=e['i']
    if lt<e['ts']: return hv.screen(i,lt).convert('RGB')
    if lt<e['ds']:
        el=lt-e['ts']; return hv.screen(i,lt,count=(max(1,math.ceil(TIMER-el)),1-el/TIMER)).convert('RGB')
    k=min(1,(lt-e['ds'])/TILT)
    return hv.screen(i,lt,tilt=ease(k),reveal=k>=0.7).convert('RGB')
def sm(x): return x*x*(3-2*x)
def frame(t):
    j=max(n for n,e in enumerate(EV) if e['t0']<=t); e=EV[j]; lt=t-e['t0']; cur=render(e,lt)
    if lt<TR and j>0:
        pe=EV[j-1]; prev=render(pe,pe['dur']-0.01); p=sm(lt/TR); off=int(W*0.25*(1-p))
        b=Image.new('RGB',(W,H)); b.paste(prev.crop((W-off,0,W,H)) if off else prev,(0,0)); b.paste(cur,(off,0)); return Image.blend(prev,b,p)
    return cur
if __name__=='__main__':
    part,n=int(sys.argv[1]),int(sys.argv[2])
    N=int(TOTAL*FPS); a=N*part//n; b=N*(part+1)//n; out=f'/home/claude/shorts-media/pipeline/puzzles/which_heavier/part{part}'
    pr=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',out+'.tmp.mp4'],stdin=subprocess.PIPE)
    for f in range(a,b): pr.stdin.write(frame(f/FPS).tobytes())
    pr.stdin.close(); pr.wait(); os.rename(out+'.tmp.mp4',out+'.mp4'); print('ok',part)
