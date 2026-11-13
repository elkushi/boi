# -*- coding: utf-8 -*-
"""Вырезает нужные позы из AI-листов. Координаты — доли ширины/высоты листа,
   чтобы не зависеть от точного размера файла. Фон (тёмный) снимается заливкой."""
from PIL import Image
import numpy as np, os, sys
from collections import deque

HERE=os.path.dirname(os.path.abspath(__file__))
RAW=os.path.join(HERE,"raw"); OUT=os.path.join(HERE,"sprites","poses")
os.makedirs(OUT, exist_ok=True)

# (x0,y0,x1,y1) как доли от размера листа — ПРИБЛИЗИТЕЛЬНО, правятся после просмотра
ALISA = {                       # лист ~квадратный
  "idle":  (0.025,0.064,0.105,0.170),
  "walk":  (0.300,0.064,0.385,0.170),
  "jump":  (0.355,0.239,0.440,0.335),
  "block": (0.110,0.399,0.205,0.495),
  "hurt":  (0.325,0.399,0.410,0.495),
  "jab":   (0.615,0.399,0.700,0.495),
  "kick":  (0.800,0.399,0.900,0.495),
  "heavy": (0.025,0.554,0.120,0.655),
  "down":  (0.012,0.884,0.118,0.955),
}
MOUSTAFA = {                    # лист ~3:2
  "idle":  (0.010,0.069,0.080,0.195),
  "walk":  (0.215,0.069,0.290,0.195),
  "jump":  (0.010,0.269,0.085,0.395),
  "block": (0.665,0.269,0.740,0.395),
  "hurt":  (0.815,0.269,0.890,0.395),
  "jab":   (0.010,0.474,0.085,0.595),
  "kick":  (0.145,0.474,0.230,0.595),
  "heavy": (0.295,0.474,0.380,0.595),
  "down":  (0.562,0.874,0.665,0.955),
}

def cut(img, tol=88):
    a=np.array(img.convert("RGB")).astype(int); h,w,_=a.shape
    ring=np.concatenate([a[0:3].reshape(-1,3),a[-3:].reshape(-1,3),a[:,0:3].reshape(-1,3),a[:,-3:].reshape(-1,3)])
    bg=np.median(ring,axis=0); dist=np.abs(a-bg).sum(axis=2); cand=dist<tol
    seen=np.zeros((h,w),bool); q=deque()
    for y,x in [(0,x) for x in range(w)]+[(h-1,x) for x in range(w)]+[(y,0) for y in range(h)]+[(y,w-1) for y in range(h)]:
        if cand[y,x] and not seen[y,x]: seen[y,x]=True; q.append((y,x))
    while q:
        y,x=q.popleft()
        for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
            ny,nx=y+dy,x+dx
            if 0<=ny<h and 0<=nx<w and not seen[ny,nx] and cand[ny,nx]: seen[ny,nx]=True; q.append((ny,nx))
    alpha=np.where(seen,0,255).astype(np.uint8)
    soft=np.clip((dist-tol*.45)/(tol*.75)*255,0,255).astype(np.uint8)
    b=np.zeros_like(seen); b[1:,:]|=seen[:-1,:]; b[:-1,:]|=seen[1:,:]; b[:,1:]|=seen[:,:-1]; b[:,:-1]|=seen[:,1:]
    bd=b&~seen; alpha[bd]=np.minimum(alpha[bd],soft[bd])
    out=Image.fromarray(np.dstack([np.array(img.convert("RGB")),alpha]),"RGBA")
    ar=np.array(out); ys,xs=np.where(ar[:,:,3]>10)
    if len(ys)==0: return out
    return out.crop((max(0,xs.min()-2),max(0,ys.min()-2),min(w,xs.max()+3),min(h,ys.max()+3)))

def run(who, sheet, boxes, H=260):
    im=Image.open(os.path.join(RAW,sheet)).convert("RGB"); W,Hh=im.size
    for name,(x0,y0,x1,y1) in boxes.items():
        box=(int(x0*W),int(y0*Hh),int(x1*W),int(y1*Hh))
        fr=cut(im.crop(box))
        fr=fr.resize((max(1,round(fr.width*H/fr.height)),H),Image.LANCZOS)
        fr.save(os.path.join(OUT,f"{who}_{name}.png"),optimize=True)
        print(f"  {who}_{name}: {fr.size}")

if __name__=="__main__":
    run("alisa","alisa.png",ALISA)
    run("moustafa","moustafa.png",MOUSTAFA)
    # контрольный лист
    import glob
    fs=sorted(glob.glob(os.path.join(OUT,"*.png")))
    ims=[Image.open(f) for f in fs]; h=150
    s=[i.resize((max(1,int(i.width*h/i.height)),h),Image.LANCZOS) for i in ims]
    sh=Image.new("RGB",(sum(i.width+6 for i in s),h),(255,0,255)); x=0
    for i in s: sh.paste(i,(x,0),i); x+=i.width+6
    sh.save(os.path.join(HERE,"poses_check.png")); print("poses_check.png written")
