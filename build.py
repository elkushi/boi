import base64, glob, os, json, io
HERE = os.path.dirname(os.path.abspath(__file__))
tpl  = open(os.path.join(HERE,"src/template.html"), encoding="utf-8").read()
entries=[]
def add(key, path, mime="image/png"):
    entries.append(f'  {key}: "data:{mime};base64,{base64.b64encode(open(path,"rb").read()).decode()}"')
for f in sorted(glob.glob(os.path.join(HERE,"sprites","*_portrait.png"))):
    add(os.path.splitext(os.path.basename(f))[0], f)
for f in sorted(glob.glob(os.path.join(HERE,"sprites","poses","*.png"))):
    add(os.path.splitext(os.path.basename(f))[0], f)
meta=json.load(open(os.path.join(HERE,"sprites","poses","meta.json")))
# арена -> jpeg 1280 шириной, чтобы страница не раздулась
arena=os.path.join(HERE,"raw","arena.png")
if os.path.exists(arena):
    from PIL import Image
    im=Image.open(arena).convert("RGB")
    im=im.resize((1280, round(im.height*1280/im.width)), Image.LANCZOS)
    buf=io.BytesIO(); im.save(buf,"JPEG",quality=84,optimize=True)
    entries.append(f'  arena: "data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"')
    print(f"arena: embedded ({len(buf.getvalue())/1024:.0f} KB)")
out = tpl.replace("/*__SPRITES__*/{}", "{\n"+",\n".join(entries)+"\n}")
out = out.replace("/*__META__*/{}", json.dumps(meta,separators=(",",":")))
cfg = os.path.join(HERE, "firebase.json")
if os.path.exists(cfg):
    out = out.replace("/*__FIREBASE__*/null", open(cfg, encoding="utf-8").read().strip())
    print("firebase: config embedded")
else:
    print("firebase: none (online mode disabled - add firebase.json)")
dst = os.path.join(HERE,"index.html")
open(dst,"w",encoding="utf-8").write(out)
print(f"built {dst} - {len(out)/1024:.0f} KB, {len(entries)} images")
