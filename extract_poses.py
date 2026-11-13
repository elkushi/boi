# -*- coding: utf-8 -*-
"""Вырезает позы из AI-листов raw/alisa.png (1254x1254) и raw/moustafa.png (1536x1024).
   Координаты — пиксели листа (подобраны по сетке). Фон панели снимается заливкой
   от краёв; фон оценивается по строкам, чтобы градиент панели не мешал.
   Все позы одного бойца масштабируются одним коэффициентом (idle -> IDLE_H px),
   поэтому пропорции между позами сохраняются. Пишет sprites/poses/*.png и
   sprites/poses/meta.json (ширина, высота, якорь по X)."""
from PIL import Image
import numpy as np, os, json, glob
from collections import deque

HERE=os.path.dirname(os.path.abspath(__file__))
RAW=os.path.join(HERE,"raw"); OUT=os.path.join(HERE,"sprites","poses")
os.makedirs(OUT, exist_ok=True)
IDLE_H=258          # высота idle-позы в игре (хитбокс 214 + запас)

# name: (x0,y0,x1,y1[,anchor_x 0..1])
ALISA = {
  "idle":    (20,55,110,215),   "idle2":  (120,55,210,215),
  "walk1":   (365,55,455,215),  "walk2":  (560,55,655,215),
  "run1":    (785,55,880,215),  "run2":   (885,55,980,215),
  "dash":    (50,290,185,415,.6),
  "jump":    (455,290,545,415), "jump2":  (550,285,655,415),
  "fall":    (780,285,870,415), "land":   (1075,290,1165,415),
  "block":   (150,490,245,615), "guard":  (25,490,120,615),
  "hurt":    (415,490,510,615), "hurt2":  (515,490,610,615),
  "jab":     (760,490,860,615), "straight":(875,490,975,615),
  "kick":    (990,490,1095,615),"sidekick":(1105,490,1240,615,.35),
  "heavy":   (25,690,125,815),  "uppercut":(150,690,250,815),
  "heavykick":(270,690,380,815),"spin":   (400,685,520,808,.45),
  "special": (595,690,720,815,.38),"wave": (745,690,870,815,.3),
  "dragon":  (910,685,1060,815,.4),"power":(1090,680,1250,815),
  "grab":    (10,895,105,1015), "throw":  (190,895,290,1015),
  "counter": (855,895,960,1015),"dodge":  (1160,895,1254,1015),
  "down":    (5,1110,135,1215), "getup":  (140,1085,235,1215),
  "airkick": (370,1085,460,1215),"airpunch":(470,1085,565,1215),
  "charge":  (725,1090,835,1215),
  "taunt1":  (985,1085,1075,1215),"taunt2":(1075,1085,1165,1215),"taunt3":(1165,1085,1254,1215),
}
MOUSTAFA = {
  "idle":    (10,58,95,198),    "idle2":  (120,58,205,198),
  "walk1":   (325,58,410,198),  "walk2":  (505,58,595,198),
  "run1":    (700,58,800,198),  "run2":   (805,58,905,198),
  "dash":    (1160,58,1290,198,.6),
  "jump":    (10,262,110,402),  "jump2":  (120,262,220,402),
  "fall":    (375,262,470,402), "land":   (670,262,775,402),
  "block":   (1005,262,1100,402),"guard": (905,262,1000,402),
  "hurt":    (1225,262,1320,402),"hurt2": (1330,262,1425,402),
  "jab":     (8,472,100,605),   "straight":(115,472,210,605),
  "kick":    (220,472,320,605), "sidekick":(330,472,425,605),
  "heavy":   (448,472,545,605), "uppercut":(670,470,765,605),
  "heavykick":(560,472,660,605),"spin":   (770,468,900,605,.45),
  "special": (920,470,1115,605,.27),"wave":(1370,468,1536,605,.3),
  "dragon":  (1230,468,1360,605,.4),"power":(1075,672,1180,800),
  "grab":    (8,672,100,800),   "throw":  (255,672,350,800),
  "counter": (420,672,545,800), "dodge":  (790,672,890,800),
  "down":    (850,925,985,1005),"getup":  (990,880,1085,1005),
  "airkick": (1225,672,1320,800),"airpunch":(1325,672,1420,800),
  "charge":  (920,672,1035,800),
  "taunt1":  (1240,880,1330,1005),"taunt2":(1335,880,1425,1005),"taunt3":(1430,880,1536,1005),
}

def bglike(a, who):
    """Пиксели, похожие на фон панели: тёмные и синеватые/фиолетовые.
       Чёрная одежда Мустафы по яркости почти как фон, но не синеватая."""
    r,g,b=a[...,0],a[...,1],a[...,2]
    mx=a.max(axis=2); mn=a.min(axis=2)
    if who=="moustafa": return (b-r>=8)&(mx<150)
    return (b>=r-2)&(mx<140)&((mx-mn)<60)

GLOBAL={"special","wave","spin","dragon","power","charge","counter","down","sidekick","dodge"}

def cut(img, who, tol=75, glob_rm=False):
    """Убирает фон: оценка фона по строкам по «фоновым» пикселям, кандидаты —
       фоновые и близкие к оценке, заливка от краёв, мягкий край."""
    a=np.array(img.convert("RGB")).astype(int); h,w,_=a.shape
    like=bglike(a,who)
    bg=np.zeros((h,3)); ok=np.zeros(h,bool)
    for y in range(h):
        m=like[y]
        if m.sum()>=max(6,w*0.12): bg[y]=np.median(a[y][m],axis=0); ok[y]=True
    if not ok.any(): bg[:]=np.median(a.reshape(-1,3),axis=0); ok[:]=True
    idx=np.where(ok)[0]
    for c in range(3): bg[:,c]=np.interp(np.arange(h),idx,bg[idx,c])
    k=7; pad=np.pad(bg,((k//2,k//2),(0,0)),mode='edge')
    bg=np.stack([np.median(pad[i:i+k],axis=0) for i in range(h)])
    dist=np.abs(a-bg[:,None,:]).sum(axis=2)
    cand=like&(dist<tol)
    seen=np.zeros((h,w),bool); q=deque()
    for y,x in [(0,x) for x in range(w)]+[(h-1,x) for x in range(w)]+[(y,0) for y in range(h)]+[(y,w-1) for y in range(h)]:
        if cand[y,x] and not seen[y,x]: seen[y,x]=True; q.append((y,x))
    while q:
        y,x=q.popleft()
        for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
            ny,nx=y+dy,x+dx
            if 0<=ny<h and 0<=nx<w and not seen[ny,nx] and cand[ny,nx]: seen[ny,nx]=True; q.append((ny,nx))
    if glob_rm: seen|=like&(dist<tol*1.6)&(a.max(axis=2)<(185 if glob_rm=='hard' else 110))
    alpha=np.where(seen,0,255).astype(np.uint8)
    soft=np.clip((dist-tol*.35)/(tol*.6)*255,0,255).astype(np.uint8)
    b=np.zeros_like(seen); b[1:,:]|=seen[:-1,:]; b[:-1,:]|=seen[1:,:]; b[:,1:]|=seen[:,:-1]; b[:,:-1]|=seen[:,1:]
    bd=b&~seen; alpha[bd]=np.minimum(alpha[bd],soft[bd])
    # убираем мелкие островки (пыль, частицы): компоненты меньше 80 px
    fg=alpha>10; lab=np.zeros((h,w),int); n=0
    for y0 in range(h):
        for x0 in range(w):
            if fg[y0,x0] and not lab[y0,x0]:
                n+=1; comp=[(y0,x0)]; lab[y0,x0]=n; qq=deque(comp)
                while qq:
                    y,x=qq.popleft()
                    for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                        ny,nx=y+dy,x+dx
                        if 0<=ny<h and 0<=nx<w and fg[ny,nx] and not lab[ny,nx]:
                            lab[ny,nx]=n; qq.append((ny,nx)); comp.append((ny,nx))
                if len(comp)<80:
                    for y,x in comp: alpha[y,x]=0
    out=Image.fromarray(np.dstack([np.array(img.convert("RGB")),alpha]),"RGBA")
    ar=np.array(out); ys,xs=np.where(ar[:,:,3]>10)
    if len(ys)==0: return out
    return out.crop((max(0,xs.min()-1),max(0,ys.min()-1),min(w,xs.max()+2),min(h,ys.max()+2)))

def run(who, sheet, boxes, meta):
    im=Image.open(os.path.join(RAW,sheet)).convert("RGB")
    frames={}
    for name,b in boxes.items():
        x0,y0,x1,y1=b[:4]; ax=b[4] if len(b)>4 else .5
        frames[name]=(cut(im.crop((x0,y0,x1,y1)),who,glob_rm=('hard' if name=='down' else name in GLOBAL)),ax)
    k=IDLE_H/frames["idle"][0].height
    for name,(fr,ax) in frames.items():
        fr=fr.resize((max(1,round(fr.width*k)),max(1,round(fr.height*k))),Image.LANCZOS)
        q=fr.quantize(colors=200,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE)
        q.save(os.path.join(OUT,f"{who}_{name}.png"),optimize=True)
        meta[f"{who}_{name}"]={"w":fr.width,"h":fr.height,"ax":ax}
        print(f"  {who}_{name}: {fr.size}")

if __name__=="__main__":
    for f in glob.glob(os.path.join(OUT,"*.png")): os.remove(f)
    meta={}
    run("alisa","alisa.png",ALISA,meta)
    run("moustafa","moustafa.png",MOUSTAFA,meta)
    json.dump(meta,open(os.path.join(OUT,"meta.json"),"w"))
    # контрольный лист: по строке на бойца
    rows=[]
    for who in ("alisa","moustafa"):
        fs=[os.path.join(OUT,f"{who}_{n}.png") for n in (ALISA if who=="alisa" else MOUSTAFA)]
        ims=[Image.open(f).convert("RGBA") for f in fs]; h=120
        s=[i.resize((max(1,int(i.width*h/i.height)),h),Image.LANCZOS) for i in ims]
        sh=Image.new("RGB",(sum(i.width+4 for i in s),h),(255,0,255)); x=0
        for i in s: sh.paste(i,(x,0),i); x+=i.width+4
        rows.append(sh)
    W=max(r.width for r in rows); H=sum(r.height+6 for r in rows)
    out=Image.new("RGB",(W,H),(255,0,255)); y=0
    for r in rows: out.paste(r,(0,y)); y+=r.height+6
    out.save(os.path.join(HERE,"poses_check.png")); print("poses_check.png written")
    tot=sum(os.path.getsize(f) for f in glob.glob(os.path.join(OUT,"*.png")))
    print(f"total {tot/1024:.0f} KB in {len(meta)} poses")
