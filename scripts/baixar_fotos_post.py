"""Baixa as fotos originais dos produtos de um post (dados/post-XX.json) para a pasta saida/."""
import json, os, sys, urllib.request
post = sys.argv[1]
itens = json.load(open(f"dados/{post}.json", encoding="utf-8"))
os.makedirs("saida", exist_ok=True)
for it in itens:
    url = it["imagem"]
    dados = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
    nome = f"saida/produto-{it['ordem']:02d}.jpg"
    open(nome, "wb").write(dados); print(nome, len(dados))
