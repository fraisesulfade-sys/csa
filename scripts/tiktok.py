"""Integração TikTok (Login Kit + Content Posting API, modo rascunho).
Token guardado criptografado em dados/tiktok_token.enc (chave = TIKTOK_CLIENT_SECRET).
Uso: python tiktok.py trocar <codigo> | python tiktok.py postar <pasta_publica_url> <n_fotos> <arquivo_legenda>"""
import base64, hashlib, json, os, subprocess, sys, time, urllib.parse, urllib.request
API = "https://open.tiktokapis.com"
KEY = os.environ["TIKTOK_CLIENT_KEY"].strip(); SECRET = os.environ["TIKTOK_CLIENT_SECRET"].strip()
REDIRECT = "https://fraisesulfade-sys.github.io/csa/conectado.html"
ARQ = "dados/tiktok_token.enc"

def _openssl(args, dados):
    return subprocess.run(["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-pass", "env:TIKTOK_CLIENT_SECRET", *args],
                          input=dados, capture_output=True, check=True).stdout
def salvar(tok):
    tok["obtido_em"] = int(time.time())
    open(ARQ, "wb").write(_openssl(["-salt", "-a"], json.dumps(tok).encode()))
def carregar(): return json.loads(_openssl(["-d", "-a"], open(ARQ, "rb").read()))

def post_form(url, dados):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(dados).encode(), headers={"Content-Type": "application/x-www-form-urlencoded"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())
def post_json(url, token, corpo):
    req = urllib.request.Request(url, data=json.dumps(corpo).encode(), headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"})
    try: return json.loads(urllib.request.urlopen(req, timeout=60).read())
    except urllib.error.HTTPError as e: return json.loads(e.read() or b"{}")

def trocar(codigo):
    codigo = urllib.parse.unquote(codigo.strip())
    t = post_form(f"{API}/v2/oauth/token/", {"client_key": KEY, "client_secret": SECRET, "code": codigo,
                                             "grant_type": "authorization_code", "redirect_uri": REDIRECT})
    if "access_token" not in t: sys.exit(f"Falhou: { {k: v for k, v in t.items() if 'token' not in k} }")
    salvar(t); print("Conta conectada. Escopos:", t.get("scope"), "| open_id termina em", t.get("open_id", "")[-4:])

def token():
    t = carregar()
    if time.time() < t["obtido_em"] + t.get("expires_in", 0) - 300: return t["access_token"]
    n = post_form(f"{API}/v2/oauth/token/", {"client_key": KEY, "client_secret": SECRET, "grant_type": "refresh_token", "refresh_token": t["refresh_token"]})
    if "access_token" not in n: sys.exit(f"Não renovou o token: {n.get('error')} {n.get('error_description')}")
    salvar(n); print("token renovado"); return n["access_token"]

def postar(base_url, n, arq_legenda):
    tk = token()
    legenda = open(arq_legenda, encoding="utf-8").read().strip()
    titulo = legenda.split("\n")[0][:90]
    fotos = [f"{base_url.rstrip('/')}/{i:02d}.jpg" for i in range(1, int(n) + 1)]
    r = post_json(f"{API}/v2/post/publish/content/init/", tk, {
        "post_info": {"title": titulo, "description": legenda[:4000]},
        "source_info": {"source": "PULL_FROM_URL", "photo_cover_index": 0, "photo_images": fotos},
        "post_mode": "MEDIA_UPLOAD", "media_type": "PHOTO"})
    print("init:", json.dumps(r, ensure_ascii=False))
    pid = (r.get("data") or {}).get("publish_id")
    if not pid: sys.exit(1)
    for _ in range(12):
        time.sleep(10)
        s = post_json(f"{API}/v2/post/publish/status/fetch/", tk, {"publish_id": pid})
        st = (s.get("data") or {}).get("status"); print("status:", st, (s.get("data") or {}).get("fail_reason", ""))
        if st in ("SEND_TO_USER_INBOX", "PUBLISH_COMPLETE", "FAILED"): break

def quem():
    tk = token()
    req = urllib.request.Request(f"{API}/v2/user/info/?fields=display_name,username", headers={"Authorization": f"Bearer {tk}"})
    try: r = json.loads(urllib.request.urlopen(req, timeout=30).read())
    except urllib.error.HTTPError as e: r = json.loads(e.read() or b"{}")
    print("CONTA:", json.dumps(r.get("data", {}).get("user", {}), ensure_ascii=False), r.get("error", {}).get("code"))
    if len(sys.argv) > 2:
        s = post_json(f"{API}/v2/post/publish/status/fetch/", tk, {"publish_id": sys.argv[2]}); print("STATUS:", json.dumps(s, ensure_ascii=False))

def testar():
    t = post_form(f"{API}/v2/oauth/token/", {"client_key": KEY, "client_secret": SECRET, "grant_type": "client_credentials"})
    print("CHAVE OK" if "access_token" in t else f"CHAVE ERRADA: {t.get('error')} {t.get('error_description')}")

if __name__ == "__main__":
    {"quem": quem, "testar": testar, "trocar": lambda: trocar(sys.argv[2]), "postar": lambda: postar(*sys.argv[2:5])}[sys.argv[1]]()
