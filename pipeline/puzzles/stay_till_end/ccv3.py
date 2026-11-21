import sys, math, subprocess, os
sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/stay_till_end'); sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/_shared')
from PIL import Image, ImageDraw, ImageFilter
import cc, m3
cc.NAMES=['dog','cat','panda','frog']
cc.COLS=cc.ROWS=7; cc.CS=110; cc.BX=(cc.W-7*cc.CS)//2-30; cc.BY=415
W,H,FPS=1080,1920,30; PRE,PLAY,POST=1.5,10.0,3.0; RT=PRE+PLAY+POST
import json
ROUNDS=[]
for i in range(6):
    d=json.load(open(f'/home/claude/shorts-media/pipeline/puzzles/stay_till_end/rounds/r{i}.json'))
    B0,MOVES=m3.build(d['seed'],final=tuple(d['fin']),order=d['order'],win=d['win'])
    STATES=[[row[:] for row in B0]]; b=[row[:] for row in B0]
    for q,p,cells,an in MOVES:
        b[p[0]][p[1]],b[q[0]][q[1]]=b[q[0]][q[1]],b[p[0]][p[1]]
        assert all(b[x][y]==an for x,y in cells)
        for x,y in cells: b[x][y]=None
        assert not m3.any_line(b)
        STATES.append([row[:] for row in b])
    left=[b[r][c] for r in range(7) for c in range(7) if b[r][c]]; assert left==[d['win']],left
    ROUNDS.append(dict(d,MOVES=MOVES,STATES=STATES))
TOTAL=RT*6
HAND=Image.open('/home/claude/shorts-media/pipeline/puzzles/stay_till_end/ic/hand.png').convert('RGBA')
def xy(rc): return cc.BX+rc[1]*cc.CS+cc.CS/2, cc.BY+rc[0]*cc.CS+cc.CS/2
def ease(x): x=max(0,min(1,x)); return x*x*(3-2*x)
def rframe(R,i,t):
    MOVES,STATES=R['MOVES'],R['STATES']; MT=PLAY/len(MOVES); cc.NAMES=R['an']
    reveal=t>=PRE+PLAY
    k=int(max(0,min(len(MOVES)-1,(t-PRE)//MT))) if t>=PRE else -1
    f=((t-PRE)-k*MT)/MT if t>=PRE else 0
    if reveal: k=len(MOVES); f=0
    im=cc.sp.warm(i)
    cc.cnt2.pill(im,f"{R['lvl']}  •  ROUND {i+1}/6",140,R['lvl'])
    cc.cnt2.gtext(im,'WHICH ONE WILL',232,66); cc.cnt2.gtext(im,'STAY TILL THE END?',312,72,(255,235,120),(255,170,40))
    cc.ROWS=cc.COLS=7; cc.boardbg(im)
    st=STATES[max(0,k)] if not reveal else STATES[-1]
    q=p=cells=None
    if 0<=k<len(MOVES) and not reveal: q,p,cells,an=MOVES[k]
    s=cc.CS-14
    sw=ease((f-0.4)/0.25) if q else 0   # swap progress
    burst=(f-0.68)/0.32 if q else -1
    for r in range(7):
        for c in range(7):
            a=st[r][c]
            if a is None: continue
            x,y=xy((r,c))
            if q and (r,c)==q: tx,ty=xy(p); x,y=x+(tx-x)*sw,y+(ty-y)*sw
            elif q and (r,c)==p: tx,ty=xy(q); x,y=x+(tx-x)*sw,y+(ty-y)*sw
            if q and burst>=0:
                # after swap the line cells hold 'an'; hide them
                pos_after=(p if (r,c)==q else (q if (r,c)==p else (r,c)))
                if pos_after in cells: continue
            sz=s
            if reveal:
                kk=min(1,(t-PRE-PLAY)/0.6); GR=60+40*kk
                gm=Image.new('L',im.size,0); ImageDraw.Draw(gm).ellipse([x-GR,y-GR,x+GR,y+GR],fill=int(255*kk))
                gl=Image.new('RGBA',im.size,(255,240,140,0)); gl.putalpha(gm.filter(ImageFilter.GaussianBlur(22))); im.alpha_composite(gl)
                sz=int(s*(1+0.25*math.sin(kk*math.pi)))
            im.alpha_composite(cc.candy(a,sz),(int(x-sz/2),int(y-sz/2)))
    if q and 0.62<=f<0.72:   # flash line before burst
        d=ImageDraw.Draw(im); x0,y0=xy(cells[0]); x1,y1=xy(cells[-1])
        d.rounded_rectangle([min(x0,x1)-52,min(y0,y1)-52,max(x0,x1)+52,max(y0,y1)+52],30,outline=(255,240,140),width=8)
    if q and burst>=0:
        lay=Image.new('RGBA',im.size,(0,0,0,0))
        for rc in cells: x,y=xy(rc); cc.pop(lay,x,y,min(1,burst),(255,230,120))
        im.alpha_composite(lay)
    # hand: move to q (0-0.35), drag to p (0.4-0.65), lift
    if PRE-0.4<=t<PRE+PLAY and q:
        prv=xy(MOVES[k-1][1]) if k>0 else (900,1250)
        if f<0.35: m=ease(f/0.35); hx=prv[0]+(xy(q)[0]-prv[0])*m; hy=prv[1]+(xy(q)[1]-prv[1])*m
        else: hx,hy=xy(q); tx,ty=xy(p); hx,hy=hx+(tx-hx)*sw,hy+(ty-hy)*sw
        hs=int(170*(0.88 if 0.35<f<0.68 else 1)); hi=HAND.resize((hs,hs),Image.LANCZOS).rotate(-18,resample=Image.BICUBIC)
        im.alpha_composite(hi,(int(hx-hs*0.38),int(hy-hs*0.04)))
    oy=cc.BY+7*cc.CS+80; bw=190; gap=20; x0=cc.W/2-(4*bw+3*gap)/2-30
    for j,nm in enumerate(cc.NAMES):
        bb=[x0+j*(bw+gap),oy,x0+j*(bw+gap)+bw,oy+150]; good=reveal and nm==R['win']; dim=reveal and not good
        cc.D.shadow_box(im,bb,30,6,8,60); d=ImageDraw.Draw(im)
        d.rounded_rectangle(bb,30,fill=(40,200,100) if good else ((255,255,255,130) if dim else (255,255,255)),outline='white',width=4)
        ci=cc.candy(nm,100)
        if dim: ci=ci.copy(); ci.putalpha(ci.split()[3].point(lambda v:v//3))
        im.alpha_composite(ci,(int(bb[0]+bw/2-50),oy+8)); d=ImageDraw.Draw(im)
        LB={'icecream':'ICE CREAM','helicopter':'HELICOPTER'}.get(nm,nm.upper()); d.text(((bb[0]+bb[2])/2,oy+124),LB,font=cc.F('h',34 if len(LB)<=7 else (28 if len(LB)<=9 else 24)),fill='white' if good else cc.INK,anchor='mm')
    if not reveal:
        rem=PLAY-max(0,t-PRE); cc.cnt2.timer(im,oy+270,max(1,math.ceil(rem)) if t>=PRE else 10,rem/PLAY)
    else: cc.cnt2.gtext(im,f"THE {({'icecream':'ICE CREAM'}).get(R['win'],R['win'].upper())}!",oy+270,80,(140,255,170),(40,200,110))
    cc.sp.likebtn(im,t); cc.D.hoot(im,'cheer' if reveal else 'think',230,140,1905)
    return im.convert('RGB')
def sm(x): return x*x*(3-2*x)
def frame(t):
    i=min(5,int(t//RT)); lt=t-i*RT; cur=rframe(ROUNDS[i],i,lt)
    if lt<0.5 and i>0:
        prev=rframe(ROUNDS[i-1],i-1,RT-0.01); p=sm(lt/0.5); off=int(W*0.25*(1-p))
        bb=Image.new('RGB',(W,H)); bb.paste(prev.crop((W-off,0,W,H)) if off else prev,(0,0)); bb.paste(cur,(off,0)); return Image.blend(prev,bb,p)
    return cur
EV=[]
for i,R in enumerate(ROUNDS):
    o=i*RT; MT=PLAY/len(R['MOVES'])
    EV+=[('tick',o+PRE+k) for k in range(10)]+[('swish',o+PRE+k*MT+0.4*MT) for k in range(len(R['MOVES']))]+[('pop',o+PRE+k*MT+0.68*MT) for k in range(len(R['MOVES']))]+[('ding',o+PRE+PLAY+0.05)]
    if i: EV.append(('whoosh',o-0.2))
if __name__=='__main__':
    part,n=int(sys.argv[1]),int(sys.argv[2]); N=int(TOTAL*FPS); a=N*part//n; b2=N*(part+1)//n; out=f'/home/claude/shorts-media/pipeline/puzzles/stay_till_end/part{part}'
    pr=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',out+'.tmp.mp4'],stdin=subprocess.PIPE)
    for fr in range(a,b2): pr.stdin.write(frame(fr/FPS).tobytes())
    pr.stdin.close(); pr.wait(); os.rename(out+'.tmp.mp4',out+'.mp4'); print('ok',part)
