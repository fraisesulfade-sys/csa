"""Busca no feed por palavras de dados/busca.txt (1ª linha: termos separados por |).
Gera dados/busca.json e dados/busca.jpg (miniaturas numeradas)."""
import csv, io, json, os, re, unicodedata, urllib.request, concurrent.futures as cf
from PIL import Image, ImageDraw, ImageFont
norm=lambda s: unicodedata.normalize("NFKD", s.lower()).encode("ascii","ignore").decode()
termos=[norm(t.strip()) for t in open("dados/busca.txt",encoding="utf-8").readline().split("|") if t.strip()]
url=os.environ["SHOPEE_FEED_URL"].strip()
txt=urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=180).read().decode("utf-8-sig","replace")
res=[]
for r in csv.DictReader(io.StringIO(txt)):
    t=norm(r.get("title",""))
    if not any(k in t for k in termos): continue
    try: nota=float(r.get("item_rating") or 0); preco=float(r.get("sale_price") or r.get("price") or 0)
    except ValueError: continue
    m=re.search(r"/(?:product/)?(\d+)/(\d+)",r.get("product_link","")) or re.search(r"i\.(\d+)\.(\d+)",r.get("product_link",""))
    res.append({"titulo":r["title"].strip(),"preco":preco,"nota":nota,"itemid":r.get("itemid"),"shopid":m.group(1) if m else None,"imagem":r.get("image_link")})
res.sort(key=lambda x:x["nota"],reverse=True); res=res[:60]
for i,x in enumerate(res,1): x["n"]=i
json.dump(res,open("dados/busca.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
def baixar(x):
    try: im=Image.open(io.BytesIO(urllib.request.urlopen(x["imagem"],timeout=30).read())).convert("RGB"); im.thumbnail((300,300)); return x["n"],im
    except Exception: return x["n"],None
with cf.ThreadPoolExecutor(16) as ex: th=dict(ex.map(baixar,res))
C=10; sheet=Image.new("RGB",(C*300,max(1,(len(res)+C-1)//C)*300),"white"); d=ImageDraw.Draw(sheet)
f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",28)
for k,x in enumerate(res):
    px,py=(k%C)*300,(k//C)*300
    if th.get(x["n"]): sheet.paste(th[x["n"]],(px,py))
    d.rectangle((px,py,px+70,py+38),fill="black"); d.text((px+6,py+4),str(x["n"]),font=f,fill="white")
sheet.save("dados/busca.jpg",quality=80); print(len(res),"resultados")
