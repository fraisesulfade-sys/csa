"""Gera docs/index.html (vitrine/link na bio) a partir dos posts em dados/post-XX.json."""
import glob, html, json, re
NOMES = {}
cards, posts = [], sorted(glob.glob("dados/post-[0-9][0-9].json"), reverse=True)
for arq in posts:
    num = re.search(r"post-(\d+)", arq).group(1)
    car = json.load(open(f"dados/post-{num}-carrossel.json", encoding="utf-8"))
    precos = {p["n"]: p for p in car["produtos"]}
    for it in json.load(open(arq, encoding="utf-8")):
        p = precos.get(it["ordem"], {}); preco = p.get("preco", it["preco"])
        txt = ("a partir de " if p.get("a_partir") else "") + "R$ " + f"{preco:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        link = it.get("link")
        botao = (f'<a class="btn" href="{html.escape(link)}" target="_blank" rel="sponsored noopener">ver na Shopee</a>'
                 if link else '<span class="btn off">link em breve</span>')
        cards.append(f'''<li class="card" data-n="{it['ordem']}" data-post="{num}">
<img src="posts/{num}/mini/{it['ordem']:02d}.jpg" alt="{html.escape(p.get('nome', it['nome']))}" loading="lazy" width="600" height="600">
<div class="txt"><span class="tag">post {int(num)} · nº {it['ordem']}</span><h3>{html.escape(p.get('nome', it['nome']))}</h3><p class="preco">{txt}</p>{botao}</div></li>''')
pagina = open("scripts/vitrine_modelo.html", encoding="utf-8").read().replace("__CARDS__", "\n".join(cards))
open("docs/index.html", "w", encoding="utf-8").write(pagina); print(len(cards), "produtos na vitrine")
