# -*- coding: utf-8 -*-
"""Сборка: позы -> два атласа WebP (один файл на бойца), арена -> WebP, портреты
   inline. Файлы получают хеш в имени, sw.js кеширует их навсегда; index.html
   берётся из сети с запасным вариантом из кеша. Запуск: python3 build.py"""
import base64, glob, os, json, io, hashlib, shutil
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
POSES = os.path.join(HERE, "sprites", "poses")
ASSETS = os.path.join(HERE, "assets")
tpl = open(os.path.join(HERE, "src/template.html"), encoding="utf-8").read()

def h8(b): return hashlib.sha1(b).hexdigest()[:8]
def webp(im, q=86):
    buf = io.BytesIO(); im.save(buf, "WEBP", quality=q, method=6); return buf.getvalue()

if os.path.isdir(ASSETS): shutil.rmtree(ASSETS)
os.makedirs(ASSETS)
meta_in = json.load(open(os.path.join(POSES, "meta.json")))
META, FILES = {}, {}

# --- атласы: полки по высоте, ширина до 2048 ---
for who in ("alisa", "moustafa"):
    names = sorted(k for k in meta_in if k.startswith(who + "_"))
    ims = {n: Image.open(os.path.join(POSES, n + ".png")).convert("RGBA") for n in names}
    order = sorted(names, key=lambda n: -ims[n].height)
    W, PAD = 2048, 2
    x = y = rowh = 0; rects = {}
    for n in order:
        im = ims[n]
        if x + im.width + PAD > W: x = 0; y += rowh + PAD; rowh = 0
        rects[n] = (x, y); x += im.width + PAD; rowh = max(rowh, im.height)
    H = y + rowh; W = max(ax + ims[n].width for n, (ax, ay) in rects.items())
    atlas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for n, (ax, ay) in rects.items(): atlas.paste(ims[n], (ax, ay))
    data = webp(atlas, 80)
    fn = f"{who}-{h8(data)}.webp"; open(os.path.join(ASSETS, fn), "wb").write(data); FILES[who] = "assets/" + fn
    for n, (ax, ay) in rects.items():
        m = meta_in[n]; META[n] = {"a": who, "x": ax, "y": ay, "w": ims[n].width, "h": ims[n].height, "ax": m["ax"]}
    print(f"{who}: atlas {W}x{H}, {len(names)} poses, {len(data)/1024:.0f} KB")

# --- арена ---
arena = os.path.join(HERE, "raw", "arena.png")
if os.path.exists(arena):
    im = Image.open(arena).convert("RGB")
    im = im.resize((1280, round(im.height * 1280 / im.width)), Image.LANCZOS)
    data = webp(im, 80)
    fn = f"arena-{h8(data)}.webp"; open(os.path.join(ASSETS, fn), "wb").write(data); FILES["arena"] = "assets/" + fn
    print(f"arena: {len(data)/1024:.0f} KB")

# --- портреты inline (маленькие, нужны HUD сразу) ---
inline = []
for who in ("alisa", "moustafa"):
    im = Image.open(os.path.join(HERE, "sprites", f"{who}_portrait.png")).convert("RGB").resize((160, 160), Image.LANCZOS)
    inline.append(f'  {who}_portrait: "data:image/webp;base64,{base64.b64encode(webp(im, 82)).decode()}"')

out = tpl.replace("/*__SPRITES__*/{}", "{\n" + ",\n".join(inline) + "\n}")
out = out.replace("/*__META__*/{}", json.dumps(META, separators=(",", ":")))
out = out.replace("/*__FILES__*/{}", json.dumps(FILES, separators=(",", ":")))
cfg = os.path.join(HERE, "firebase.json")
if os.path.exists(cfg):
    out = out.replace("/*__FIREBASE__*/null", open(cfg, encoding="utf-8").read().strip()); print("firebase: config embedded")
else:
    print("firebase: none (online mode disabled - add firebase.json)")

# --- service worker: имя кеша = хеш всего содержимого ---
ver = h8((out + "".join(sorted(FILES.values()))).encode())
out = out.replace("/*__VER__*/''", repr(ver))
sw = open(os.path.join(HERE, "src/sw.js"), encoding="utf-8").read()
sw = sw.replace("__VER__", ver).replace("__ASSETS__", json.dumps(sorted(FILES.values())))
open(os.path.join(HERE, "sw.js"), "w", encoding="utf-8").write(sw)
open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(out)
tot = sum(os.path.getsize(os.path.join(ASSETS, f)) for f in os.listdir(ASSETS))
print(f"built index.html {len(out)/1024:.0f} KB + assets {tot/1024:.0f} KB, version {ver}")
