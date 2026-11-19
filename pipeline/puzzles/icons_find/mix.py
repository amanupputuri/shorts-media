import sys; import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import vid2, audio
print(audio.build(vid2.TOTAL, vid2.events(), 'mix.wav', [(os.path.join(vid2.VD,f'l{li:02d}.wav'),t) for li,t in vid2.VOICE]))
