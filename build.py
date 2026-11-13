import base64, glob, os
HERE = os.path.dirname(os.path.abspath(__file__))
SPR  = os.path.join(HERE, "sprites")
tpl  = open(os.path.join(HERE,"src/template.html"), encoding="utf-8").read()
entries=[]
for f in sorted(glob.glob(os.path.join(SPR,"*.png"))):
    key=os.path.splitext(os.path.basename(f))[0]
    b64=base64.b64encode(open(f,"rb").read()).decode()
    entries.append(f'  {key}: "data:image/png;base64,{b64}"')
# позы с листов
for f in sorted(glob.glob(os.path.join(HERE,"sprites","poses","*.png"))):
    key=os.path.splitext(os.path.basename(f))[0]
    entries.append(f'  {key}: "data:image/png;base64,{base64.b64encode(open(f,"rb").read()).decode()}"')
# арена -> jpeg 1280 шириной, чтобы страница не раздулась
arena=os.path.join(HERE,"raw","arena.png")
if os.path.exists(arena):
    from PIL import Image
    import io as _io
    im=Image.open(arena).convert("RGB")
    im=im.resize((1280, round(im.height*1280/im.width)), Image.LANCZOS)
    buf=_io.BytesIO(); im.save(buf,"JPEG",quality=86,optimize=True)
    entries.append(f'  arena: "data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"')
    print(f"arena: embedded ({len(buf.getvalue())/1024:.0f} KB)")
else:
    print("arena: none (raw/arena.png) - using drawn columns")
out = tpl.replace("/*__SPRITES__*/{}", "{\n"+",\n".join(entries)+"\n}")

# Firebase config (optional): put it in firebase.json next to this script
cfg = os.path.join(HERE, "firebase.json")
if os.path.exists(cfg):
    raw = open(cfg, encoding="utf-8").read().strip()
    out = out.replace("/*__FIREBASE__*/null", raw)
    print("firebase: config embedded")
else:
    print("firebase: none (online mode disabled - add coop/firebase.json)")
dst = os.path.join(HERE,"index.html")
open(dst,"w",encoding="utf-8").write(out)
print(f"built {dst} — {len(out)/1024:.0f} KB, {len(entries)} sprites")
