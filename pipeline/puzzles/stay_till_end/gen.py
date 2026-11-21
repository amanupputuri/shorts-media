import sys,random,json;sys.path.insert(0,'/home/claude/shorts-media/pipeline/puzzles/stay_till_end');import m3
R=[('EASY',['dog','cat','panda','frog'],'panda'),('EASY',['pig','lion','frog','dog'],'frog'),
   ('MEDIUM',['cat','panda','pig','lion'],'cat'),('MEDIUM',['frog','dog','lion','panda'],'lion'),
   ('HARD',['pig','cat','frog','dog'],'dog'),('HARD',['panda','lion','pig','cat'],'pig')]
i=int(sys.argv[1]); lvl,an,win=R[i]
rnd=random.Random(i*99)
for attempt in range(200):
    others=[a for a in an if a!=win]
    order=[win]*3+others*3; rnd.shuffle(order)
    if win in order[-3:]: continue
    for s in range(400):
        fin=(random.Random(s).randrange(2,5),random.Random(s+1).randrange(2,5))
        out=m3.build(s,final=fin,order=order,win=win)
        if out and all(v is not None for row in out[0] for v in row):
            json.dump(dict(lvl=lvl,an=an,win=win,order=order,seed=s,fin=fin),open(f'r{i}.json','w')); print('ok',i,s); sys.exit()
print('fail',i)
