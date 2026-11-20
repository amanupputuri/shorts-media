import sys, os; _H=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(_H,'..','_shared')); sys.path.insert(0,_H); os.chdir(_H)
import final, audio, subprocess
audio.build(final.TOTAL, final.events(), 'mix0.wav', [(os.path.join(final.VD,f'l{li:02d}.wav'),t) for li,t in final.VOICE])
inp=['-i','mix0.wav']; fl=[]
for k,(ri,t0) in enumerate(final.CLIPT):
    inp+=['-i',final.CLIPS[ri]]; ms=int(t0*1000); fl.append(f'[{k+1}:a]volume=0.35,adelay={ms}|{ms}[c{k}]')
fl.append('[0:a]'+''.join(f'[c{k}]' for k in range(3))+'amix=inputs=4:normalize=0:duration=first[a]')
subprocess.run(['ffmpeg','-y','-loglevel','error',*inp,'-filter_complex',';'.join(fl),'-map','[a]','mix.wav'],check=True)
