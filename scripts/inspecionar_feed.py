"""Baixa o feed de produtos da Shopee e mostra só a estrutura (sem expor links)."""
import csv, io, os, re, sys, urllib.request
url = os.environ["SHOPEE_FEED_URL"].strip()
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=120) as r:
    print("status", r.status, "| tipo", r.headers.get("content-type"), "| tamanho", r.headers.get("content-length"))
    dados = r.read()
print("bytes baixados:", len(dados))
if dados[:2] == b"\x1f\x8b":
    import gzip; dados = gzip.decompress(dados); print("(gzip descompactado)", len(dados))
if dados[:2] == b"PK":
    import zipfile; z = zipfile.ZipFile(io.BytesIO(dados)); print("zip:", z.namelist()); dados = z.read(z.namelist()[0])
txt = dados.decode("utf-8-sig", errors="replace")
linhas = list(csv.reader(io.StringIO(txt)))
print("linhas:", len(linhas))
cab = linhas[0]
print("colunas:", cab)
mask = lambda v: re.sub(r"https?://\S+", lambda m: m.group(0).split("/")[2] + "/…", v)[:90]
for row in linhas[1:4]:
    print("---")
    for k, v in zip(cab, row):
        print(f"  {k}: {mask(v)}")
# contagem por categoria, se existir
for col in cab:
    if "categ" in col.lower():
        from collections import Counter
        i = cab.index(col); c = Counter(r[i] for r in linhas[1:] if len(r) > i)
        print("top categorias em", col, c.most_common(25)); break
