"""Busca no feed os links curtos de afiliada dos produtos de um post."""
import csv, io, json, os, sys, urllib.request
post = sys.argv[1]
itens = json.load(open(f"dados/{post}.json", encoding="utf-8"))
ids = {str(x["itemid"]): x for x in itens}
txt = urllib.request.urlopen(urllib.request.Request(os.environ["SHOPEE_FEED_URL"].strip(), headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read().decode("utf-8-sig", "replace")
for r in csv.DictReader(io.StringIO(txt)):
    it = ids.get(str(r.get("itemid")))
    if it: it["link"] = r.get("product_short link") or r.get("product_short_link") or r.get("product_link")
faltando = [x["ordem"] for x in itens if not x.get("link")]
json.dump(itens, open(f"dados/{post}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("links ok; sem link no feed de hoje:", faltando)
