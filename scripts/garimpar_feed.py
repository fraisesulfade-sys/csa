"""Filtra o feed da Shopee buscando produtos de casa com estética sofisticada/aconchegante.
Gera dados/candidatos.json e dados/prancha.jpg (miniaturas numeradas) para curadoria."""
import csv, io, json, os, re, unicodedata, urllib.request, concurrent.futures as cf
from PIL import Image, ImageDraw, ImageFont

def norm(s): return unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()

BONS = {  # peso estético
 "rattan":3,"palha":3,"bambu":2,"madeira":2,"macica":2,"ceramica":3,"terracota":3,"canelad":3,"vidro":1,
 "linho":2,"algodao":1,"boho":2,"retro":2,"vintage":2,"cogumelo":3,"bauhaus":3,"xadrez":2,"organic":3,
 "abajur":3,"luminaria":2,"bandeja":2,"cesto":2,"castical":3,"porta vela":2,"espelho":2,
 "tapete":1,"manta":2,"almofada":1,"jogo americano":2,"taca":2,"copo":1,"fruteira":2,"aparador":3,
 "cabeceira":2,"banqueta":2,"poltrona":2,"puff":1,"mesa lateral":2,"carrinho":2,"prateleira":1,
 "porcelana":2,"artesanal":2,"crochet":1,"croche":1,"tricot":1,"veludo":1,"boucle":3,"marmore":2,
 "dourado":1,"latao":2,"minimalista":1,"escandinav":2,"nordico":2,"decorativ":1,"azulejo":2,"fruta":1,
 "bowl":1,"tigela":1,"travessa":2,"bule":2,"chaleira":1,"pano de prato":1,"guardanapo":1,"sousplat":3,
}
RUINS = ["flor","flores","floral","vaso de vidro","vaso para","arranjo","planta artificial","plastico","pvc","adesivo","tinta","ferramenta","parafus","mangueira","rodo","vassoura","lixeira pedal",
 "silicone","kit limpeza","escova","refil","cabo usb","led rgb","pilha","fita","capa protetora","organizador de cabos",
 "infantil","bebe","pet","cachorro","gato","carro","moto","chuveiro","torneira","ralo","vaso sanitario","desentup"]

url = os.environ["SHOPEE_FEED_URL"].strip()
dados = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read()
linhas = list(csv.DictReader(io.StringIO(dados.decode("utf-8-sig", errors="replace"))))
cands = []
for r in linhas:
    if r.get("global_category1") != "Home & Living": continue
    t = norm(r.get("title", ""))
    if any(b in t for b in RUINS): continue
    peso = sum(v for k, v in BONS.items() if k in t)
    if peso < 2: continue
    try:
        nota = float(r.get("item_rating") or 0); preco = float(r.get("sale_price") or r.get("price") or 0)
    except ValueError: continue
    if nota < 4.6 or preco < 25: continue
    m = re.search(r"/(?:product/)?(\d+)/(\d+)", r.get("product_link", "")) or re.search(r"i\.(\d+)\.(\d+)", r.get("product_link", ""))
    cands.append({"titulo": r["title"].strip(), "preco": preco, "preco_original": float(r.get("price") or preco),
        "desconto": r.get("discount_percentage"), "nota": nota, "categoria": r.get("global_category2"),
        "itemid": r.get("itemid"), "shopid": m.group(1) if m else None,
        "imagem": r.get("image_link"), "imagem2": r.get("image_link_3"),
        "pontos": round(peso + (nota - 4.6) * 5 + min(preco, 400) / 200, 2)})
cands.sort(key=lambda c: c["pontos"], reverse=True)
cands = cands[:160]
for i, c in enumerate(cands, 1): c["n"] = i
os.makedirs("dados", exist_ok=True)
json.dump(cands, open("dados/candidatos.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("total linhas", len(linhas), "| candidatos", len(cands))

def baixar(c):
    try:
        im = Image.open(io.BytesIO(urllib.request.urlopen(c["imagem"], timeout=30).read())).convert("RGB")
        im.thumbnail((300, 300)); return c["n"], im
    except Exception as e: return c["n"], None
with cf.ThreadPoolExecutor(16) as ex: thumbs = dict(ex.map(baixar, cands))
COLS, T = 10, 300; rows = (len(cands) + COLS - 1) // COLS
for parte in range(0, rows, 8):
    sub = cands[parte*COLS:(parte+8)*COLS]
    sheet = Image.new("RGB", (COLS*T, ((len(sub)+COLS-1)//COLS)*T), "white"); d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    for k, c in enumerate(sub):
        x, y = (k % COLS)*T, (k // COLS)*T
        if thumbs.get(c["n"]): sheet.paste(thumbs[c["n"]], (x, y))
        d.rectangle((x, y, x+70, y+38), fill="black"); d.text((x+6, y+4), str(c["n"]), font=f, fill="white")
    sheet.save(f"dados/prancha_{parte//8+1}.jpg", quality=80)
print("pranchas ok")
