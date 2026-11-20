import sys,subprocess,math
sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/spotlight'); sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/_shared')
import spv
part,n=int(sys.argv[1]),int(sys.argv[2])
N=int(spv.TOTAL*spv.FPS); a=N*part//n; b=N*(part+1)//n
pr=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','30','-i','-','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',f'part{part}.tmp.mp4'],stdin=subprocess.PIPE)
for f in range(a,b): pr.stdin.write(spv.frame(f/30).tobytes())
pr.stdin.close(); pr.wait()
import os; os.rename(f'part{part}.tmp.mp4',f'part{part}.mp4'); print('ok',part)
