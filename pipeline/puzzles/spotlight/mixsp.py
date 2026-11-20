import sys; sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/spotlight'); sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/_shared')
import spv, audio_smooth, math
ev=[];vo=[]
for e in spv.EV[1:]: ev.append(('whoosh',max(0,e['t0']-0.2)))
k=0
for e in spv.EV:
    if e['kind']!='p': continue
    s=e['t0']
    vo.append((f'/home/claude/shorts-media/pipeline/puzzles/spotlight/vo/l{2*k:02d}.wav',s+0.5)); vo.append((f'/home/claude/shorts-media/pipeline/puzzles/spotlight/vo/l{2*k+1:02d}.wav',s+6.75))
    for j in range(6): ev.append(('tick',s+0.6+j))
    ev.append(('swish',s+6.6)); ev.append(('ding',s+7.3)); k+=1
print(audio_smooth.build(spv.TOTAL,ev,'/home/claude/shorts-media/pipeline/puzzles/spotlight/mix.wav',vo), spv.TOTAL)
