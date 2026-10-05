"""
Baixa os elencos do Transfermarkt (várias ligas) e gera o bloco DATA do jogo.

Posições (campo "pos"): GOL ZAG LD LE VOL MC MEI PD PE SA CA.
Cada linha gerada tem 12 campos:
  nome,clube,pos,idade,num,valor(mi €),liga,idJogador,arquivoFoto,idClube,nacionalidade,idBandeira

Fotos dos jogadores: o jogo monta a URL e o navegador carrega direto do Transfermarkt.
Escudos e bandeiras: com --embutir-imagens o script baixa cada imagem uma vez e grava
dentro do HTML (base64), então o jogo mostra escudos/bandeiras sem depender da internet.

Uso:
  pip install requests beautifulsoup4
  python pegar_dados.py                                  # todas as ligas -> dados.txt
  python pegar_dados.py --html quem-e-o-craque.html      # já troca o DATA dentro do HTML
  python pegar_dados.py --html quem-e-o-craque.html --embutir-imagens   # + escudos e bandeiras no HTML
  python pegar_dados.py --ligas BRA1 GB1 ES1             # só algumas ligas (CUIDADO: o DATA fica só com elas)
  python pegar_dados.py --ligas BRA3 MEXA --html dados.js --embutir-imagens --acrescentar   # adiciona ligas sem perder as outras
  python pegar_dados.py --lista-ligas                    # mostra os códigos disponíveis
  python pegar_dados.py --temporada 2026 --min-valor 0.5

As páginas baixadas ficam na pasta cache/, então rodar de novo é rápido e não sobrecarrega
o site. Use --sem-cache para forçar novo download.
Para adicionar uma liga, inclua uma linha em LIGAS (o código é o final da URL da liga
no Transfermarkt, ex.: .../wettbewerb/GB1).
"""
import argparse, base64, hashlib, json, os, re, sys, time, unicodedata
from collections import Counter
import requests
from bs4 import BeautifulSoup

BASE = "https://www.transfermarkt.com.br"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
}

# código -> (slug da URL, nome). O Transfermarkt identifica a liga pelo código;
# se alguma der 0 clubes, abra a liga no site e copie o slug da URL.
LIGAS = {
    "BRA1": ("campeonato-brasileiro-serie-a", "Brasileirão Série A"),
    "BRA2": ("campeonato-brasileiro-serie-b", "Brasileirão Série B"),
    "GB1":  ("premier-league", "Premier League"),
    "ES1":  ("laliga", "La Liga"),
    "IT1":  ("serie-a", "Serie A (Itália)"),
    "L1":   ("bundesliga", "Bundesliga"),
    "FR1":  ("ligue-1", "Ligue 1"),
    "PO1":  ("liga-portugal", "Liga Portugal"),
    "NL1":  ("eredivisie", "Eredivisie"),
    "AR1N": ("liga-profesional-de-futbol", "Liga Profesional (Argentina)"),
    "MLS1": ("major-league-soccer", "MLS"),
    "SA1":  ("saudi-pro-league", "Saudi Pro League"),
    "TR1":  ("super-lig", "Süper Lig (Turquia)"),
    "CSL":  ("chinese-super-league", "Superliga Chinesa"),
    "BE1":  ("jupiler-pro-league", "Pro League (Bélgica)"),
    "SC1":  ("scottish-premiership", "Scottish Premiership"),
    "GB2":  ("championship", "Championship (Inglaterra)"),
    "GR1":  ("super-league-1", "Super League (Grécia)"),
    "JAP1": ("j1-league", "J1 League (Japão)"),
    "DK1":  ("superligaen", "Superliga (Dinamarca)"),
    # --- adicionadas depois (confira o código/slug no site se der 0 clubes) ---
    "BRA3": ("campeonato-brasileiro-serie-c", "Brasileirão Série C"),
    "MEXA": ("liga-mx-apertura", "Liga MX (México)"),
    "COLP": ("primera-a", "Liga Colombiana"),
    "URU1": ("liga-auf-uruguaya", "Primera División (Uruguai)"),
    "RU1":  ("premier-liga", "Premier Liga (Rússia)"),
    "QSL":  ("qatar-stars-league", "Qatar Stars League"),
}

# Ligas de ano-calendário: usam --temporada-elenco-ano-civil (padrão 2025).
# As demais usam --temporada-elenco (padrão 2026 = temporada 26/27).
ANO_CIVIL = {"BRA1", "BRA2", "BRA3", "AR1N", "MLS1", "CSL", "COLP", "URU1"}

CACHE_DIR = "cache"
IMG_DIR = os.path.join(CACHE_DIR, "img")
USAR_CACHE = True
MAPA_POS = Counter()   # (texto do site, código) -> quantos, para conferir no final
USOU_REDE = False   # vira True quando get() precisa ir ao site (para pular a pausa entre clubes em cache)
TM_IMG = "https://tmssl.akamaized.net/images"


def _arquivo_cache(url):
    return os.path.join(CACHE_DIR, hashlib.sha1(url.encode()).hexdigest() + ".html")


def descartar_cache(url):
    try:
        os.remove(_arquivo_cache(url))
    except OSError:
        pass


def get(url):
    """Baixa a página (com cache em disco e novas tentativas em caso de 429/5xx)."""
    global USOU_REDE
    arq = _arquivo_cache(url)
    if USAR_CACHE and os.path.exists(arq):
        with open(arq, encoding="utf-8") as f:
            return BeautifulSoup(f.read(), "html.parser")
    for tentativa in range(4):
        USOU_REDE = True
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code in (429, 500, 502, 503, 504):
            espera = 10 * (tentativa + 1)
            print(f"    ... HTTP {r.status_code}, aguardando {espera}s", file=sys.stderr)
            time.sleep(espera)
            continue
        r.raise_for_status()
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(arq, "w", encoding="utf-8") as f:
            f.write(r.text)
        return BeautifulSoup(r.text, "html.parser")
    r.raise_for_status()


def limpar(txt):
    """Remove o que quebraria o formato do bloco DATA (vírgula, ponto e vírgula, crase)."""
    return re.sub(r"[,;`$\\]", "", txt).strip()


def _sem_acento(t):
    return unicodedata.normalize("NFD", t.lower()).encode("ascii", "ignore").decode()


def pos_curta(txt):
    """Texto de posição do Transfermarkt -> código do jogo.
    GOL ZAG LD LE VOL MC MEI PD PE SA CA   (None se não reconhecer)"""
    t = re.sub(r"[-–]", " ", _sem_acento(txt))
    lado = "E" if re.search(r"\besq", t) else "D" if re.search(r"\bdir", t) else ""   # esquerdo/esquerda/esq. e direito/direita/dir.
    if "goleiro" in t: return "GOL"
    if "lateral" in t or re.search(r"\bala\b", t): return ("L" + lado) if lado else "LAT"   # sem lado no texto -> resolve pelo perfil
    if "zagueiro" in t or "defensor" in t or t.startswith("defesa"): return "ZAG"
    if "volante" in t or "defensivo" in t: return "VOL"
    if "segundo atacante" in t: return "SA"
    if "ofensivo" in t or "meia atacante" in t: return "MEI"
    if "ponta" in t: return "P" + (lado or "D")
    if "meia" in t or "meio" in t:
        return ("P" + lado) if lado else "MC"      # meia direita/esquerda -> ponta do lado; central/genérico -> MC
    if "centroavante" in t or "atacante" in t: return "CA"
    return None


def valor_mi(txt):
    """'8,00 mi. €' / '€8.00 mi.' -> 8.0 | '500 mil €' -> 0.5 | '1,20 bi' -> 1200.0"""
    m = re.search(r"([\d.,]+)\s*(bi|mil|mi)\b", txt.lower())
    if not m:
        return None
    num, un = m.group(1).strip(".,"), m.group(2)
    if "," in num:                       # 1.234,56
        num = num.replace(".", "").replace(",", ".")
    elif num.count(".") == 1 and un == "mil" and len(num.split(".")[1]) == 3:
        num = num.replace(".", "")       # 1.200 mil (ponto como milhar)
    return float(num) * {"bi": 1000, "mi": 1, "mil": 0.001}[un]


def foto_arquivo(tr):
    """Nome do arquivo da foto (ex.: '128223-1682681364.jpg'). Vazio se for a foto padrão."""
    for img in tr.select("img"):
        for attr in ("data-src", "src"):          # a página usa lazy-load: a URL real fica em data-src
            u = (img.get(attr) or "").split("?")[0]
            if "/portrait/" in u:
                arq = u.rsplit("/", 1)[-1]
                return "" if arq.startswith("default") else arq
    return ""


def nacionalidade(tr):
    """(nome, idBandeira) da primeira bandeira da linha = nacionalidade principal."""
    for img in tr.select("img.flaggenrahmen"):
        nome = limpar(img.get("title") or img.get("alt") or "")
        u = img.get("data-src") or img.get("src") or ""
        m = re.search(r"/flagge/[^/]+/(\d+)\.", u)
        if nome or m:
            return nome, (m.group(1) if m else "")
    return "", ""


def lado_pelo_perfil(pid):
    """Abre o perfil do jogador e devolve 'LE' ou 'LD' (None se não achar).
    Usado quando a tabela do elenco só diz 'Lateral', sem o lado.
    Prioriza 'Posição principal' (a posição secundária pode ser do outro lado)."""
    if not pid:
        return None
    url = f"{BASE}/-/profil/spieler/{pid}"
    em_cache = USAR_CACHE and os.path.exists(_arquivo_cache(url))
    soup = get(url)
    if not em_cache:
        time.sleep(1)                               # pausa só quando foi ao site
    for no in soup.find_all(string=re.compile(r"posi[çc][ãa]o principal", re.I)):
        for pai in (no.parent, no.parent.parent if no.parent else None):
            if pai is None:
                continue
            txt = re.sub(r"(?i)posi[çc][ãa]o principal:?", "", pai.get_text(" ", strip=True)).split("Posições")[0]
            p = pos_curta(txt)
            if p in ("LE", "LD"):
                return p
    linhas = [l.strip() for l in soup.get_text("\n", strip=True).split("\n") if l.strip()]
    for prefixo in ("posicao principal", "posicao"):
        for i, l in enumerate(linhas):
            if _sem_acento(l).startswith(prefixo):
                for cand in linhas[i:i + 4]:        # o texto da posição vem na mesma linha ou logo depois
                    p = pos_curta(cand)
                    if p in ("LE", "LD"):
                        return p
                    if p:                           # achou outra posição: não é lateral, segue para o próximo rótulo
                        break
    return None


def _extrair_clubes(soup):
    achados = {}
    links = soup.select('table.items td.hauptlink a[href*="/startseite/verein/"]')
    if not links:                                   # layout diferente: qualquer link de clube dentro das tabelas
        links = soup.select('table.items a[href*="/startseite/verein/"]')
    for a in links:
        m = re.match(r"/([^/]+)/startseite/verein/(\d+)", a["href"])
        nome = a.get_text(strip=True)
        if m and nome:
            achados.setdefault(m.group(2), (m.group(1), nome))
    return achados


def clubes(liga_url, temporada, slug_liga=None, cod=None):
    achados = _extrair_clubes(get(f"{liga_url}/plus/?saison_id={temporada}"))
    if not achados and slug_liga and cod:
        # Ligas com fase de grupos (ex.: Série C) são "pokalwettbewerb" no Transfermarkt:
        # a lista de clubes fica na página de participantes, não em /startseite/wettbewerb/.
        for ano in (temporada, temporada - 1):
            url = f"{BASE}/{slug_liga}/teilnehmer/pokalwettbewerb/{cod}/saison_id/{ano}"
            achados = _extrair_clubes(get(url))
            if achados:
                print(f"  (lista de clubes lida da página de participantes, temporada {ano})")
                break
            descartar_cache(url)
    return [(slug, vid, nome) for vid, (slug, nome) in achados.items()]


def elenco(slug, vid, nome, liga, temporada, min_valor):
    tabela, url = None, None
    for ano in (temporada, temporada - 1, temporada - 2):
        url = f"{BASE}/{slug}/kader/verein/{vid}/saison_id/{ano}/plus/1"
        soup = get(url)
        tabela = soup.select_one("table.items")
        # só vale se a tabela tiver jogadores; senão tenta a temporada anterior
        if tabela and tabela.find("td", class_="posrela"):
            if ano != temporada:
                print(f"    ! {nome}: usando elenco de {ano} (o de {temporada} veio vazio)")
            break
        tabela = None
        descartar_cache(url)
        time.sleep(1)
    if not tabela:
        titulo = soup.title.get_text(strip=True) if soup.title else "?"
        print(f"    ! tabela nao encontrada (titulo da pagina: {titulo}). Salvei debug.html")
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(str(soup))
        return []

    saida, vistos = [], 0
    rej = {"sem_numero": 0, "sem_posicao": 0, "sem_idade": 0, "sem_valor": 0, "valor_baixo": 0}
    nome_clube = limpar(nome)
    for tr in tabela.find_all("tr"):
        if not tr.find("td", class_="posrela"):
            continue
        link = tr.select_one('a[href*="/profil/spieler/"]')
        if not link:
            continue
        vistos += 1
        texto = tr.get_text(" ", strip=True)
        el = tr.select_one(".rn_nummer")
        num = re.sub(r"\D", "", el.get_text()) if el else ""
        inline = tr.select("table.inline-table tr")
        raw_pos = inline[-1].get_text(" ", strip=True) if inline else texto
        pos = pos_curta(raw_pos)
        if pos == "LAT":                          # lateral sem lado: tenta a linha inteira e depois o perfil
            pos = pos_curta(texto) if pos_curta(texto) in ("LE", "LD") else None
            if not pos:
                mp0 = re.search(r"/profil/spieler/(\d+)", link["href"])
                try:
                    pos = lado_pelo_perfil(mp0.group(1) if mp0 else "")
                except Exception as e:
                    print(f"    ! perfil de {link.get_text(strip=True)}: {e}", file=sys.stderr)
                    pos = None
            if not pos:
                pos = "LD"                        # último recurso
                print(f"    ? lado do lateral nao encontrado: {link.get_text(strip=True)}")
        MAPA_POS[(raw_pos[:40], pos or "??")] += 1
        m = re.search(r"\((\d{1,2})\)", texto)
        idade = int(m.group(1)) if m else None
        tds = tr.find_all("td", recursive=False)
        valor = valor_mi(tds[-1].get_text()) if tds else None
        if valor is None:
            m2 = re.search(r"([\d.,]+\s*(?:bi|mi|mil)\.?\s*€)", texto)
            valor = valor_mi(m2.group(1)) if m2 else None
        if not num: rej["sem_numero"] += 1   # clube sem numeração no site: mantém o jogador, com número vazio
        if not pos: rej["sem_posicao"] += 1; continue
        if not idade: rej["sem_idade"] += 1; continue
        if valor is None:                      # sem valor de mercado no site
            rej["sem_valor"] += 1
            if min_valor > 0: continue         # com filtro de valor, descarta
            valor = 0.0                        # senão mantém (o jogo mostra "€—")
        if valor < min_valor: rej["valor_baixo"] += 1; continue
        mp = re.search(r"/profil/spieler/(\d+)", link["href"])
        pid = mp.group(1) if mp else ""
        nome_j = limpar(link.get_text(strip=True))
        nac, nac_id = nacionalidade(tr)
        saida.append(",".join([nome_j, nome_clube, pos, str(idade), num,
                               f"{round(valor, 3):g}", liga, pid, foto_arquivo(tr), vid, nac, nac_id]))
    if saida and (rej["sem_numero"] or rej["sem_valor"]):
        print(f"    (aviso: {rej['sem_numero']} sem número de camisa e {rej['sem_valor']} sem valor de mercado no site)")
    if not saida:
        print(f"    ! linhas de jogador vistas: {vistos} | descartados: {rej}")
        if vistos == 0:
            with open("debug.html", "w", encoding="utf-8") as f:
                f.write(str(soup))
            print("    ! nenhuma linha de jogador. Salvei debug.html")
    return saida


def imagem_data_uri(nome, urls):
    """Baixa a 1ª URL que responder, guarda em cache/img e devolve 'data:image/...;base64,...'."""
    arq = os.path.join(IMG_DIR, nome + ".txt")
    if USAR_CACHE and os.path.exists(arq):
        with open(arq, encoding="utf-8") as f:
            return f.read()
    os.makedirs(IMG_DIR, exist_ok=True)
    for u in urls:
        try:
            r = requests.get(u, headers=HEADERS, timeout=30)
        except requests.RequestException:
            continue
        tipo = r.headers.get("content-type", "").split(";")[0]
        if r.status_code == 200 and r.content and tipo.startswith("image"):
            uri = f"data:{tipo};base64," + base64.b64encode(r.content).decode()
            with open(arq, "w", encoding="utf-8") as f:
                f.write(uri)
            time.sleep(0.3)
            return uri
    return ""


def baixar_imagens(linhas):
    """Escudos (por idClube) e bandeiras (por idBandeira) de todas as linhas."""
    campos = [l.split(",") for l in linhas]
    ids_clube = sorted({c[9] for c in campos if len(c) > 9 and c[9]}, key=int)
    ids_flag = sorted({c[11] for c in campos if len(c) > 11 and c[11]}, key=int)
    cods_liga = sorted({c[6] for c in campos if len(c) > 6 and c[6]})
    escudos, bandeiras, logos = {}, {}, {}
    print(f"\nBaixando {len(ids_clube)} escudos, {len(ids_flag)} bandeiras e {len(cods_liga)} logos de liga...")
    for i in ids_clube:
        uri = imagem_data_uri(f"escudo_{i}", [f"{TM_IMG}/wappen/{t}/{i}.png" for t in ("medium", "head", "normquad")])
        if uri: escudos[i] = uri
        else: print(f"  ! sem escudo para o clube {i}")
    for i in ids_flag:
        uri = imagem_data_uri(f"bandeira_{i}", [f"{TM_IMG}/flagge/{t}/{i}.png" for t in ("medium", "head", "small", "verysmall")])
        if uri: bandeiras[i] = uri
        else: print(f"  ! sem bandeira para o pais {i}")
    for cod in cods_liga:
        uri = imagem_data_uri(f"liga_{cod}", [f"{TM_IMG}/logo/{t}/{cod.lower()}.png" for t in ("normal", "header", "small")])
        if uri: logos[cod] = uri
        else: print(f"  ! sem logo para a liga {cod}")
    print(f"  {len(escudos)} escudos, {len(bandeiras)} bandeiras e {len(logos)} logos embutidos")
    return escudos, bandeiras, logos


def trocar_bloco(html, nome, dados):
    """Troca 'const NOME={...};' pelo JSON novo. Devolve (html, achou)."""
    js = json.dumps(dados, separators=(",", ":"), ensure_ascii=False)
    return re.subn(rf"const {nome}=\{{.*?\}};", lambda _: f"const {nome}={js};", html, count=1, flags=re.S)


def main():
    global USAR_CACHE, USOU_REDE
    ap = argparse.ArgumentParser()
    ap.add_argument("--ligas", nargs="+", default=list(LIGAS), metavar="COD",
                    help="códigos das ligas (padrão: todas). Ex.: BRA1 GB1 ES1")
    ap.add_argument("--lista-ligas", action="store_true", help="mostra os códigos e sai")
    ap.add_argument("--temporada", type=int, default=2026)
    ap.add_argument("--temporada-elenco", type=int, default=2026,
                    help="temporada usada nas paginas de elenco (ele tenta essa e as 2 anteriores)")
    ap.add_argument("--temporada-elenco-ano-civil", type=int, default=2025,
                    help="temporada de elenco das ligas de ano-calendario (BRA1, BRA2, AR1N, MLS1, CSL)")
    ap.add_argument("--min-valor", type=float, default=0.0, help="em milhões de euros")
    ap.add_argument("--html", help="arquivo HTML do jogo para atualizar o bloco DATA")
    ap.add_argument("--embutir-imagens", action="store_true",
                    help="com --html: baixa escudos e bandeiras e grava dentro do HTML (funciona offline)")
    ap.add_argument("--sem-cache", action="store_true", help="ignora a pasta cache/ e baixa tudo de novo")
    ap.add_argument("--acrescentar", action="store_true",
                    help="mantém os jogadores das outras ligas que já estão no --html (ou dados.txt) e só troca/adiciona as ligas de --ligas")
    args = ap.parse_args()

    if args.lista_ligas:
        for cod, (_, nome) in LIGAS.items():
            print(f"  {cod:5} {nome}")
        return
    desconhecidas = [c for c in args.ligas if c not in LIGAS]
    if desconhecidas:
        sys.exit(f"Liga(s) desconhecida(s): {', '.join(desconhecidas)}. Use --lista-ligas.")
    USAR_CACHE = not args.sem_cache

    linhas = []
    for cod in args.ligas:
        slug_liga, nome_liga = LIGAS[cod]
        liga_url = f"{BASE}/{slug_liga}/startseite/wettbewerb/{cod}"
        print(f"\n== {nome_liga} ({cod}) ==")
        try:
            lista = clubes(liga_url, args.temporada, slug_liga, cod)
        except Exception as e:
            print(f"  ! nao consegui listar os clubes: {e}", file=sys.stderr)
            continue
        print(f"{len(lista)} clubes encontrados")
        total_liga = 0
        for slug, vid, nome in lista:
            USOU_REDE = False
            try:
                temp_elenco = args.temporada_elenco_ano_civil if cod in ANO_CIVIL else args.temporada_elenco
                jogadores = elenco(slug, vid, nome, cod, temp_elenco, args.min_valor)
            except Exception as e:
                print(f"  ! {nome}: {e}", file=sys.stderr)
                continue
            fotos = sum(1 for j in jogadores if j.split(",")[8])
            print(f"  {nome}: {len(jogadores)} jogadores ({fotos} com foto)")
            linhas += jogadores
            total_liga += len(jogadores)
            if USOU_REDE:
                time.sleep(2)  # seja gentil com o site (pula a pausa quando veio do cache)
        print(f"  -> {total_liga} jogadores em {nome_liga}")

    if MAPA_POS:
        print("\nPosições do site -> código do jogo (confira se está certo):")
        for (raw, cod), n in sorted(MAPA_POS.items(), key=lambda x: (x[0][1], -x[1])):
            print(f"  {cod:3} <- {raw}  ({n})")
        if any(c == "??" for _, c in MAPA_POS):
            print("  ! Os marcados com ?? foram descartados: me mande esses textos para eu ajustar.")

    if args.acrescentar:
        fonte = args.html or "dados.txt"
        texto = ""
        try:
            with open(fonte, encoding="utf-8") as f:
                antigo = f.read()
            m = re.search(r"const DATA=`(.*?)`;", antigo, re.S)
            texto = m.group(1) if m else (antigo if fonte.endswith(".txt") else "")
        except OSError:
            pass
        mantidas = [l.strip() for l in texto.split(";")
                    if l.strip() and len(l.split(",")) > 6 and l.split(",")[6] not in args.ligas]
        print(f"\n--acrescentar: {len(mantidas)} jogadores de outras ligas mantidos de {fonte}")
        linhas = mantidas + linhas

    bloco = ";\n".join(linhas)
    with open("dados.txt", "w", encoding="utf-8") as f:
        f.write(bloco)
    print(f"\nTotal: {len(linhas)} jogadores -> dados.txt")

    if args.html:
        with open(args.html, encoding="utf-8") as f:
            html = f.read()
        novo, n = re.subn(r"const DATA=`.*?`;", lambda _: f"const DATA=`{bloco}`;", html, count=1, flags=re.S)
        if n == 0:
            sys.exit(f"Nao encontrei 'const DATA=`...`;' em {args.html}")
        if args.embutir_imagens:
            escudos, bandeiras, logos = baixar_imagens(linhas)
            novo, a = trocar_bloco(novo, "CRESTS", escudos)
            novo, b = trocar_bloco(novo, "FLAGS", bandeiras)
            novo, c = trocar_bloco(novo, "LOGOS", logos)
            if not (a and b and c):
                print("  ! nao achei 'const CRESTS={};' / 'const FLAGS={};' / 'const LOGOS={};' no HTML (use o HTML mais novo)")
        with open(args.html, "w", encoding="utf-8") as f:
            f.write(novo)
        print(f"{args.html} atualizado")


if __name__ == "__main__":
    main()
