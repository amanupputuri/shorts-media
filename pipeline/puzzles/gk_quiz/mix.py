import sys, os; _H=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(_H,'..','_shared')); sys.path.insert(0,_H); os.chdir(_H)
import qv, audio_smooth
audio_smooth.build(qv.TOTAL, qv.events(), 'mix.wav', [(os.path.join(qv.VD,f'l{li:02d}.wav'),t) for li,t in qv.VOICE])
print(qv.TOTAL)
