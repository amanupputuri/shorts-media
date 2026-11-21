import random
N=7
def lines_at(b,r,c):
    out=[]
    a=b[r][c]
    if a is None: return out
    for dr,dc in((0,1),(1,0)):
        for s in range(-3,1):
            cells=[(r+dr*(s+k),c+dc*(s+k)) for k in range(4)]
            if all(0<=x<N and 0<=y<N and b[x][y]==a for x,y in cells): out.append(cells)
    return out
def any_line(b):
    for r in range(N):
        for c in range(N):
            if lines_at(b,r,c): return True
    return False
def build(seed,final=(3,3),order=None,win='panda'):
    rnd=random.Random(seed)
    b=[[None]*N for _ in range(N)]; b[final[0]][final[1]]=win
    moves=[]
    for an in reversed(order):   # reverse construction
        for _ in range(4000):
            dr,dc=rnd.choice(((0,1),(1,0))); r=rnd.randrange(N); c=rnd.randrange(N)
            cells=[(r+dr*k,c+dc*k) for k in range(4)]
            if not all(0<=x<N and 0<=y<N and b[x][y] is None for x,y in cells): continue
            p=rnd.choice(cells)
            nb=[(p[0]+a,p[1]+e) for a,e in((0,1),(1,0),(0,-1),(-1,0))]
            nb=[q for q in nb if 0<=q[0]<N and 0<=q[1]<N and q not in cells and b[q[0]][q[1]] is not None and b[q[0]][q[1]]!=an]
            if not nb: continue
            q=rnd.choice(nb)
            nbd=[row[:] for row in b]
            for x,y in cells: nbd[x][y]=an
            nbd[p[0]][p[1]],nbd[q[0]][q[1]]=nbd[q[0]][q[1]],nbd[p[0]][p[1]]
            if any_line(nbd): continue   # no premature lines before this move
            b=nbd; moves.append((q,p,cells,an)); break
        else: return None
    moves.reverse()
    return b,moves
def search(order,tries=3000):
    for s in range(tries):
        out=build(s,final=(random.Random(s).randrange(2,5),random.Random(s+1).randrange(2,5)),order=order)
        if out and all(v is not None for row in out[0] for v in row): return s,out
    return None
if __name__=='__main__':
    order=['pig','dog','panda','frog','cat','lion','panda','dog','pig','frog','cat','lion']
    r=search(order); print(r[0] if r else 'fail')
    if r:
        for row in r[1][0]: print(' '.join(x[:3] for x in row))
