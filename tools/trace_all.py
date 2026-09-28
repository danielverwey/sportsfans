import json,sys,os,io,numpy as np,warnings
warnings.filterwarnings('ignore')
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parent)); import vectorise as V
from PIL import Image
from skimage.morphology import skeletonize, closing, disk
from skimage.measure import label
from scipy import ndimage

def trace_png(path,eps=1.2):
    im=Image.open(path).convert('RGBA'); a=np.array(im)[:,:,3]>80
    if a.sum()==0: return None
    # remove tiny specks (labels, markers)
    lab,n=label(a,connectivity=2,return_num=True)
    if n>1:
        sizes=ndimage.sum(a,lab,range(1,n+1)); a=lab==(int(np.argmax(sizes))+1)
    sk=skeletonize(a)
    lab,n=label(sk,connectivity=2,return_num=True)
    if n>1:
        sizes=ndimage.sum(sk,lab,range(1,n+1)); sk=lab==(int(np.argmax(sizes))+1)
    sk=V.prune(sk,80)
    k=np.ones((3,3),int); nb=ndimage.convolve(sk.astype(int),k,mode='constant')-sk
    ends=int((sk&(nb==1)).sum()); junc=int((sk&(nb>=3)).sum())
    path,total=V.order_loop(sk); cov=len(path)/max(1,total)
    P=np.array([(x,y) for y,x in path],float)
    mn=P.min(axis=0); mx=P.max(axis=0); span=(mx-mn).max()
    P=(P-mn)/span*440+30; off=(440-(mx-mn)/span*440)/2; P+=off
    pts=V.rdp([tuple(p) for p in P],eps)
    d='M'+'L'.join(f'{x:.1f} {y:.1f}' for x,y in pts)+'Z'
    return dict(d=d,cov=round(cov,3),ends=ends,junc=junc,n=len(pts))

out={}
for f in sorted(os.listdir('png')):
    tag,cid=f[:-4].split('_',1)
    r=trace_png('png/'+f)
    out.setdefault(tag,{})[cid]=r
    flag='' if (r and r['cov']>0.97 and r['ends']==0 and r['junc']==0) else '  <-- CHECK'
    print(tag,cid[:12],r and (r['cov'],r['ends'],r['junc'],r['n']),flag)
json.dump(out,open('traced.json','w'))
