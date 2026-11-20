import sys; sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/which_heavier'); sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/_shared')
import hvv as sfv, audio_smooth
vo=[(f'/home/claude/shorts-media/pipeline/puzzles/which_heavier/vo/l{k:02d}.wav',t) for k,t in sfv.VOICE]
print(audio_smooth.build(sfv.TOTAL,[(k,t) for k,t in sfv.SFX],'/home/claude/shorts-media/pipeline/puzzles/which_heavier/mix.wav',vo), sfv.TOTAL)
