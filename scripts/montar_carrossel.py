"""Monta o carrossel: capa com título, slides com etiqueta discreta (nº · nome / preço) e slide final."""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H = 1080, 1920
FONTE = os.environ.get("FONTE", "/tmp/tiktok.ttf")

def fonte(tam, peso="SemiBold"):
    f = ImageFont.truetype(FONTE, tam)
    try: f.set_variation_by_name(peso)
    except Exception: pass
    return f

def ajustar(caminho):
    im = Image.open(caminho).convert("RGB")
    esc = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * esc), round(im.height * esc)), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((x, y, x + W, y + H))

def estrela(d, cx, cy, r, cor=(255, 255, 255)):
    q = r * 0.28
    d.polygon([(cx, cy - r), (cx + q, cy - q), (cx + r, cy), (cx + q, cy + q), (cx, cy + r), (cx - q, cy + q), (cx - r, cy), (cx - q, cy - q)], fill=cor)

def texto_sombra(base, xy, linhas, fontes, alinhar="left", entre=8):
    """Texto branco com sombra suave (estilo legenda do TikTok)."""
    camada = Image.new("RGBA", base.size, (0, 0, 0, 0)); sombra = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d, ds = ImageDraw.Draw(camada), ImageDraw.Draw(sombra)
    x, y = xy
    for linha, f in zip(linhas, fontes):
        larg = d.textlength(linha, font=f)
        px = x - larg / 2 if alinhar == "center" else (x - larg if alinhar == "right" else x)
        ds.text((px + 2, y + 3), linha, font=f, fill=(0, 0, 0, 185))
        d.text((px, y), linha, font=f, fill=(255, 255, 255, 255))
        y += f.size + entre
    sombra = sombra.filter(ImageFilter.GaussianBlur(5))
    out = Image.alpha_composite(base.convert("RGBA"), sombra)
    return Image.alpha_composite(out, camada).convert("RGB")

def brl(v): return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def montar(pasta_img, cfg_json, saida):
    cfg = json.load(open(cfg_json, encoding="utf-8"))
    os.makedirs(saida, exist_ok=True)
    # capa
    capa = ajustar(os.path.join(pasta_img, cfg["capa"]["arquivo"]))
    f1 = fonte(66, "Bold")
    linhas = cfg["capa"]["titulo"]
    capa = texto_sombra(capa, (W // 2, cfg["capa"].get("y", 330)), linhas, [f1] * len(linhas), "center", 14)
    d = ImageDraw.Draw(capa); y0 = cfg["capa"].get("y", 330)
    estrela(d, 175, y0 - 30, 16); estrela(d, 905, y0 + 40, 11); estrela(d, 880, y0 + len(linhas) * 80 + 10, 18)
    capa.save(os.path.join(saida, "01.jpg"), quality=92)
    # produtos
    fn, fp = fonte(36, "SemiBold"), fonte(32, "Medium")
    for i, p in enumerate(cfg["produtos"], 2):
        im = ajustar(os.path.join(pasta_img, p["arquivo"]))
        preco = ("a partir de " if p.get("a_partir") else "") + brl(p["preco"])
        im = texto_sombra(im, tuple(p["xy"]), [f'{p["n"]} · {p["nome"]}', preco], [fn, fp], p.get("alinhar", "left"), 6)
        im.save(os.path.join(saida, f"{i:02d}.jpg"), quality=92)
    # final
    fim = ajustar(os.path.join(pasta_img, cfg["capa"]["arquivo"])).filter(ImageFilter.GaussianBlur(28))
    fim = Image.blend(fim, Image.new("RGB", (W, H), (60, 40, 30)), 0.25)
    fim = texto_sombra(fim, (W // 2, 760), cfg["final"], [fonte(60, "Bold")] + [fonte(40, "Medium")] * (len(cfg["final"]) - 1), "center", 18)
    d = ImageDraw.Draw(fim); estrela(d, W // 2, 690, 20)
    fim.save(os.path.join(saida, f"{len(cfg['produtos']) + 2:02d}.jpg"), quality=92)
    print("slides:", len(cfg["produtos"]) + 2)

if __name__ == "__main__":
    montar(sys.argv[1], sys.argv[2], sys.argv[3])
