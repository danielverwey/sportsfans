import json,base64,io,numpy as np,re,sys
from PIL import Image
from skimage.morphology import skeletonize, closing, disk
from skimage.measure import label
from scipy import ndimage

def prune(sk, iters=40):
    sk=sk.copy()
    k=np.ones((3,3),int)
    for _ in range(iters):
        nb=ndimage.convolve(sk.astype(int),k,mode='constant')-sk
        ends=sk&(nb<=1)
        if not ends.any(): break
        sk[ends]=False
    return sk

def order_loop(sk):
    ys,xs=np.where(sk); pts=set(zip(ys.tolist(),xs.tolist()))
    start=min(pts); path=[start]; visited={start}; cur=start
    nbrs=[(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
    while True:
        y,x=cur; nxt=None
        for dy,dx in nbrs:
            p=(y+dy,x+dx)
            if p in pts and p not in visited: nxt=p; break
        if nxt is None: break
        path.append(nxt); visited.add(nxt); cur=nxt
    return path, len(pts)

def rdp(points, eps):
    if len(points)<3: return points
    a=np.array(points[0]); b=np.array(points[-1]); P=np.array(points)
    ab=b-a; n=np.linalg.norm(ab)
    if n==0: d=np.linalg.norm(P-a,axis=1)
    else: d=np.abs(np.cross(ab,P-a))/n
    i=int(np.argmax(d))
    if d[i]>eps:
        return rdp(points[:i+1],eps)[:-1]+rdp(points[i:],eps)
    return [points[0],points[-1]]

def trace(png_bytes, closing_rad=5, eps=1.2):
    im=Image.open(io.BytesIO(png_bytes)).convert('RGBA')
    a=np.array(im)[:,:,3]>80
    if a.sum()==0: return None
    filled=closing(a,disk(closing_rad))
    sk=skeletonize(filled)
    lab,n=label(sk,connectivity=2,return_num=True)
    if n>1:
        sizes=ndimage.sum(sk,lab,range(1,n+1)); keep=int(np.argmax(sizes))+1; sk=lab==keep
    sk=prune(sk)
    path,total=order_loop(sk)
    cov=len(path)/max(1,total)
    # scale into 500x500 with padding 30, preserve aspect
    P=np.array([(x,y) for y,x in path],float)
    mn=P.min(axis=0); mx=P.max(axis=0); span=(mx-mn).max()
    P=(P-mn)/span*440+30; off=(440-(mx-mn)/span*440)/2; P+=off
    pts=rdp([tuple(p) for p in P],eps)
    d='M'+'L'.join(f'{x:.1f} {y:.1f}' for x,y in pts)+'Z'
    return d,cov,len(pts),im.size

if __name__=='__main__':
    d=json.load(open('motogp_data.json'));C=d['circuits']
    out={}
    for k,v in C.items():
        u=v.get('image')
        if not u: continue
        b=base64.b64decode(u.split(',',1)[1])
        if not b.startswith(b'\x89PNG'): continue
        r=trace(b)
        print(v['name'],'cov %.2f'%r[1],'pts',r[2])
        out[k]=r[0]
    json.dump(out,open('motogp_traced.json','w'))
