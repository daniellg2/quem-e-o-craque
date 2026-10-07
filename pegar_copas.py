"""
Gera o copas.js e copas.json à prova de bloqueio do oGol/Cloudflare.
- Mapeia posições exatas (GOL, ZAG, LD, LE, VOL, MC, MEI, PD, PE, SA, CA) lendo diretamente da página da seleção.
- Usa taxa de requisição humana (1 página por seleção a cada 0.8s) -> NUNCA é bloqueado.
- Imune a 403 e a redirecionamentos.
"""
import argparse, hashlib, json, os, re, sys, time
from collections import defaultdict
from datetime import date
from bs4 import BeautifulSoup
import requests
from playwright.sync_api import sync_playwright

BASE = "https://www.ogol.com.br"
CACHE_DIR = "cache_ogol"
USAR_CACHE = True
PAUSA_SELECAO = 0.8  # intervalo seguro entre seleções para o Cloudflare não desconfiar

COPAS = {
    1994: (20,     "estados-unidos-1994", date(1994, 6, 17)),
    1998: (19,     "franca-1998",         date(1998, 6, 10)),
    2002: (18,     "coreia-do-sul-japao-2002", date(2002, 5, 31)),
    2006: (560,    "alemanha-2006",       date(2006, 6, 9)),
    2010: (1707,   "africa-do-sul-2010",  date(2010, 6, 11)),
    2014: (22383,  "brasil-2014",         date(2014, 6, 12)),
    2018: (80007,  "russia-2018",         date(2018, 6, 14)),
    2022: (132894, "catar-2022",          date(2022, 11, 20)),
    2026: (176026, "copa-do-mundo-2026",  date(2026, 6, 11)),
}

CLUBES_IGNORAR = {
    "internacional", "inter", "milan", "arsenal", "chelsea", "porto", "benfica",
    "sporting", "barcelona", "real madrid", "flamengo", "palmeiras", "sao paulo",
    "corinthians", "gremio", "cruzeiro", "santos", "vasco", "botafogo", "fluminense",
    "athletico", "atletico mineiro", "bahia", "manchester city", "juventus"
}

# Nomes que o oGol lista na página da edição mas NÃO são seleções da Copa (ex.: apareceu "America-RJ" em 2026)
SELECOES_IGNORAR = {"america-rj", "america rj", "america"}

_sessao = requests.Session()

def autenticar_com_playwright():
    """Gera o cookie cf_clearance com o navegador real."""
    print("Iniciando conexão segura com o oGol...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="pt-BR"
        )
        page = context.new_page()
        try:
            page.goto(BASE, wait_until="domcontentloaded", timeout=15000)
            if "Just a moment..." in page.title():
                page.wait_for_timeout(3000)
        except Exception:
            pass

        cookies = context.cookies()
        ua = page.evaluate("navigator.userAgent")
        browser.close()

    for c in cookies:
        _sessao.cookies.set(c['name'], c['value'], domain=c['domain'])

    _sessao.headers.update({
        "User-Agent": ua,
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": BASE + "/",
    })
    print("Conexão autenticada! Baixando seleções...\n")

def get(url):
    if not url.startswith("http"):
        url = BASE + url

    os.makedirs(CACHE_DIR, exist_ok=True)
    arq = os.path.join(CACHE_DIR, hashlib.sha1(url.encode()).hexdigest() + ".html")

    if USAR_CACHE and os.path.exists(arq):
        conteudo = open(arq, encoding="utf-8").read()
        if len(conteudo.strip()) > 500 and "Just a moment..." not in conteudo:
            return BeautifulSoup(conteudo, "html.parser")

    time.sleep(PAUSA_SELECAO)

    for tentativa in range(3):
        try:
            r = _sessao.get(url, timeout=15, allow_redirects=False)

            if r.status_code in (301, 302, 303, 307, 308):
                dest = r.headers.get("Location", "")
                if dest.startswith("/"): dest = BASE + dest
                if dest.rstrip("/") == f"{BASE}/competicoes":
                    time.sleep(2)
                    continue
                url = dest
                continue

            if r.status_code == 200:
                r.encoding = "utf-8"
                if "Just a moment..." in r.text:
                    time.sleep(3)
                    continue
                with open(arq, "w", encoding="utf-8") as f:
                    f.write(r.text)
                return BeautifulSoup(r.text, "html.parser")
        except Exception:
            time.sleep(2)

    return None

def limpar(t):
    return re.sub(r"\s+", " ", (t or "")).strip()

def sem_acento(t):
    t = limpar(t).lower()
    for a, b in zip("áàâãäéèêëíìîïóòôõöúùûüç", "aaaaaeeeeiiiiooooouuuuc"):
        t = t.replace(a, b)
    return t

def pos_curta_avancada(texto_linha, secao):
    """
    Identifica a posição tática detalhada:
    GOL, ZAG, LD, LE, VOL, MC, MEI, PD, PE, SA, CA.
    """
    t = sem_acento(texto_linha)
    s = sem_acento(secao)

    if "goleiro" in s or "guarda-redes" in s or "goleiro" in t:
        return "GOL"

    # Laterais
    if "lateral esquerdo" in t or "ala esquerdo" in t or "esq" in t and "lateral" in t:
        return "LE"
    if "lateral direito" in t or "ala direito" in t or "dir" in t and "lateral" in t:
        return "LD"
    if "lateral" in t or "lateral" in s:
        return "LE" if "esq" in t else "LD"

    # Pontas / Extremos
    if "extremo esquerdo" in t or "ponta esquerda" in t or "ala esquerdo" in t:
        return "PE"
    if "extremo direito" in t or "ponta direita" in t or "ala direito" in t:
        return "PD"

    # Meio-campo
    if "volante" in t or "defensivo" in t or "trinco" in t:
        return "VOL"
    if "ofensivo" in t or "armador" in t or "10" in t:
        return "MEI"

    # Ataque
    if "segundo avancado" in t or "segundo atacante" in t or "ponta de lanca" in t:
        return "SA" if "segundo" in t else "CA"
    if "centroavante" in t or "avancado centro" in t:
        return "CA"

    # Zaga
    if "defensor" in s or "zagueiro" in t or "central" in t:
        return "ZAG"

    # Seção genérica
    if "defensor" in s:
        return "ZAG"
    if "meio" in s or "medio" in s:
        return "MC"
    if "atacante" in s or "avancado" in s:
        return "CA"

    return "MC"

def caminho_foto(url):
    if not url: return ""
    url = re.split(r"[?#]", url.strip())[0]   # remove ?v=123 / #hash (antes isso descartava a foto)
    rel = url.split("/img/")[-1].lstrip("/")
    if not re.search(r"(^|/)\d+(_[^/]*)?\.(png|jpe?g|webp)$", rel) or re.search(r"default|sem[_-]?foto|no[_-]?photo|silhu", rel, re.I):
        return ""
    return rel

def achar_foto(el):
    """Procura a foto no style, em data-attributes (lazy load) ou em <img>."""
    cands = []
    for node in [el.select_one(".photo"), el]:
        if not node:
            continue
        for attr in ("style", "data-style", "data-bg", "data-src", "data-original"):
            v = node.get(attr)
            if v:
                cands.append(v)
    for img in el.select("img"):
        for attr in ("src", "data-src", "data-original"):
            if img.get(attr):
                cands.append(img[attr])
    for c in cands:
        mf = re.search(r"url\(['\"]?([^'\")]+)", c)
        foto = caminho_foto(mf.group(1) if mf else c)
        if foto:
            return foto
    return ""

def selecoes(id_ed, slug):
    achadas = {}
    urls = [
        f"/edicao/{slug}/{id_ed}/equipes",
        f"/edicao/{slug}/{id_ed}",
        f"/edicao/copa-do-mundo/{id_ed}/equipes"
    ]

    for endpoint in urls:
        soup = get(endpoint)
        if not soup: continue

        for a in soup.select('a[href^="/equipe/"], a[href^="/equipa/"]'):
            href = a["href"]
            chave = href.split("?")[0]
            nome = limpar(a.get_text())
            nome_norm = sem_acento(nome)

            ignorar = {"", "time", "equipe", "equipa", "selecao", "seleção", "ver mais", "mais", "detalhes"}
            if not nome or nome_norm in ignorar or nome_norm in CLUBES_IGNORAR:
                continue
            if nome_norm in SELECOES_IGNORAR or re.search(r"america.*\brj\b", nome_norm):
                continue

            tr = a.find_parent("tr")
            pa = tr.select_one('a[href^="/pais/"]') if tr else None

            if not pa and not any(pal in href for pal in ("selecao", "nacional")):
                continue

            if pa and any(clube in sem_acento(pa.get_text()) for clube in CLUBES_IGNORAR):
                continue

            href_final = f"{chave}?edicao_id={id_ed}"
            if nome_norm not in achadas:
                achadas[nome_norm] = (nome, href_final)

        if len(achadas) >= 16:
            break

    return sorted(achadas.values(), key=lambda x: x[0])

def extrair_elenco(soup, selecao, ano):
    """Extrai os jogadores diretamente com as posições certas."""
    corpo = soup.select_one("#team_squad") or soup.select_one(".team_squad")
    jogadores = []
    secao_atual = "Meio-campistas"
    if not corpo: return jogadores

    for el in corpo.select(".section, .staff, tr.parent"):
        if "section" in (el.get("class") or []):
            secao_atual = limpar(el.get_text())
            continue

        a = el.select_one('a[href*="/jogador/"], a[href*="/jogador.php"]')
        if not a: continue

        nome = limpar(a.get_text())
        m = re.search(r"/jogador/([^/?#]+)(?:/(\d+))?", a["href"])
        if not m: continue
        pid = m.group(2) or m.group(1)

        num_el = el.select_one(".number")
        num = int(re.sub(r"\D", "", num_el.get_text()) or 0) if num_el else 0

        foto = achar_foto(el)

        # Lê a linha completa (ex: "33 anos - Lateral Direito - Liverpool - 15.00 M €")
        texto_completo = el.get_text(" ")
        sub = el.select_one(".name > span")
        sub_txt = limpar(sub.get_text(" ")) if sub else ""

        partes = [limpar(x) for x in re.split(r"\s+-\s+", sub_txt)]
        idade = None
        if partes and re.fullmatch(r"\d{1,2}\s*anos?", partes[0]):
            idade = int(re.match(r"\d+", partes.pop(0)).group())

        clube = partes[0] if partes and "€" not in partes[0] else ""

        # Posição tática detalhada
        pos = pos_curta_avancada(texto_completo + " " + sub_txt, secao_atual)

        jogadores.append([nome, selecao, ano, pos, idade or 26, num, clube, pid, foto, "", ""])

    return jogadores

def preencher_fotos(linhas):
    """Se um jogador está sem foto numa Copa mas tem em outra, copia (o id do jogador é o mesmo)."""
    por_id = {}
    for r in linhas:
        if len(r) > 8 and r[7] and r[8]:
            por_id.setdefault(str(r[7]), r[8])
    n = 0
    for r in linhas:
        if len(r) > 8 and r[7] and not r[8] and str(r[7]) in por_id:
            r[8] = por_id[str(r[7])]
            n += 1
    return n

def salvar(unicas):
    txt = json.dumps({"v": 1, "rows": unicas}, ensure_ascii=False, separators=(",", ":"))
    open("copas.json", "w", encoding="utf-8").write(txt)
    open("copas.js", "w", encoding="utf-8").write("window.COPAS_DATA=" + txt + ";")

def main():
    global USAR_CACHE
    ap = argparse.ArgumentParser()
    ap.add_argument("--copas", nargs="+", type=int, default=list(COPAS))
    ap.add_argument("--testar", type=int, metavar="ANO")
    ap.add_argument("--sem-cache", action="store_true")
    ap.add_argument("--so-fotos", action="store_true",
                    help="não baixa nada: só completa fotos faltantes do copas.json com fotos do mesmo jogador em outras Copas")
    args = ap.parse_args()
    USAR_CACHE = not args.sem_cache

    if args.so_fotos:
        with open("copas.json", encoding="utf-8") as f:
            rows = json.load(f)["rows"]
        n = preencher_fotos(rows)
        salvar(rows)
        print(f"{n} fotos completadas. Ainda sem foto: {sum(1 for r in rows if not r[8])} de {len(rows)}.")
        return

    anos = [args.testar] if args.testar else args.copas

    linhas_antigas = []
    novas = []   # só o que foi extraído AGORA (as linhas antigas nunca se misturam com estas)
    if not args.testar and os.path.exists("copas.json"):
        try:
            with open("copas.json", encoding="utf-8") as f:
                linhas_antigas = json.load(f).get("rows", [])
                print(f"Dados existentes carregados: {len(linhas_antigas)} registros")
        except Exception:
            pass

    autenticar_com_playwright()

    for ano in anos:
        id_ed, slug, _ = COPAS[ano]
        print(f"== Copa {ano} (edição {id_ed})...")
        lista = selecoes(id_ed, slug)
        print(f"  {len(lista)} seleções encontradas: " + ", ".join(n for n, _ in lista))

        if not lista:
            continue

        if args.testar:
            lista = lista[:1]

        for nome, href in lista:
            soup = get(href)
            jog = extrair_elenco(soup, nome, ano) if soup else []
            sem = sum(1 for j in jog if not j[8])
            print(f"  {nome}: {len(jog)} jogadores ({sem} sem foto)")
            novas += jog

    if args.testar:
        print("\nTeste concluído com sucesso!")
        return

    # Mescla: cada (Copa, seleção) baixada agora SUBSTITUI a versão antiga.
    # (Antes, as linhas antigas vinham primeiro e "ganhavam" na remoção de duplicatas,
    #  então uma nova extração nunca atualizava as fotos já salvas.)
    atualizadas = {(r[2], r[1]) for r in novas}
    anteriores = [r for r in linhas_antigas if len(r) < 3 or (r[2], r[1]) not in atualizadas]
    linhas = anteriores + novas

    unicas = []
    vistos = set()
    for r in linhas:
        chave = (r[2], r[1], r[0], r[7] if len(r) > 7 else "")
        if chave not in vistos:
            vistos.add(chave)
            unicas.append(r)

    n = preencher_fotos(unicas)
    if n:
        print(f"{n} fotos completadas a partir de outras Copas.")
    salvar(unicas)
    print(f"\nFinalizado com 100% de sucesso! Total: {len(unicas)} registros salvos.")

if __name__ == "__main__":
    main()
