"""
Baixa os elencos do Transfermarkt (várias ligas) e gera o bloco DATA do jogo.

Posições (campo "pos"): GOL ZAG LD LE VOL MC MEI PD PE SA CA.
Cada linha gerada tem 14 campos:
  nome,clube,pos,idade,num,valor(mi €),liga,idJogador,arquivoFoto,idClube,nacionalidade,idBandeira,fama(0-100),famaBruta(0-100)
  - fama       = nota com o TETO do Fácil (sem sinal forte, trava em 77). Usada pelas faixas absolutas (Diário, Quem sou eu).
  - famaBruta  = a mesma nota SEM o teto. Usada pelo Personalizado para ordenar o elenco por fama relativa.
A fama usa famosos.txt (IDs de estrelas), copas.json (historico de Copas) e, se existir, ajustes_fama.json.

ajustes_fama.json (opcional, mesma pasta do script): correções pontuais por jogador, {"idJogador": pontos}.
  Ex.: {"114937": 10, "1004728": -20}  -> soma 10 pontos ao 114937 e tira 20 do 1004728.
  O ajuste entra ANTES do teto do Fácil. Depois de editar, rode: python pegar_dados.py --so-fama --html dados.js

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
  python pegar_dados.py --so-fama --html dados.js       # so recalcula a fama (13o campo), sem baixar nada
  python pegar_dados.py --so-fama --relatorio-fama fama.csv   # + CSV para conferir a nota de cada jogador
  python pegar_dados.py --lista-ligas                    # mostra os códigos disponíveis
  python pegar_dados.py --temporada 2026 --min-valor 0.5

As páginas baixadas ficam na pasta cache/, então rodar de novo é rápido e não sobrecarrega
o site. Use --sem-cache para forçar novo download.
Para adicionar uma liga, inclua uma linha em LIGAS (o código é o final da URL da liga
no Transfermarkt, ex.: .../wettbewerb/GB1).
"""
import argparse, base64, csv, hashlib, json, math, os, re, sys, time, unicodedata
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


# ======================================================================
#  FAMA (0-100) = "chance de um brasileiro que acompanha futebol reconhecer o jogador".
#  Vira o 13º campo de cada linha do DATA. O jogo usa essa nota para decidir QUEM PODE
#  aparecer em cada dificuldade:  Fácil >= 78 | Médio 60-77 | Especialista 44-59 | < 44 nunca.
#  (Os três cortes abaixo precisam ser iguais a FAMA.facil / FAMA.medio / FAMA.craque no index.html.)
#
#  TETO DO FÁCIL: ninguém chega a 78+ só com valor + clube + nacionalidade. É preciso ao menos
#  um SINAL FORTE: estrela manual (famosos.txt), Copa 2018/2022/2026 por seleção de grande alcance
#  (copas.json; nacionalidade com peso >= 8), clube de enorme alcance (CLUBES_S, jogador entre os 5
#  mais valiosos do clube), PROTAGONISTA (um dos 3 mais valiosos de um clube de CLUBES_A) ou valor de
#  elite (>= 40 mi). Sem isso a nota é travada em 77 (vira Médio) -- mas a nota bruta é guardada à parte
#  (14º campo) para o Personalizado ordenar o elenco sem perder a diferença entre um 78 e um 95.
# ======================================================================
FAMA_FACIL_MIN = 78
FAMA_MEDIO_MIN = 60
FAMA_CORTE = 44
VALOR_ELITE = 40.0          # mi €: a partir daqui o valor sozinho já é sinal forte
PROTAGONISTAS_TOP = 3       # os N mais valiosos de um clube de CLUBES_A contam como "protagonista" (sinal forte)

# 39 clubes de alcance grande (os mesmos FACIL_IDS do jogo): dão 25 pts de clube
CLUBES_A = set("418 131 13 281 985 31 11 631 148 762 583 27 16 15 46 5 506 6195 12 720 294 336 610 614 1023 199 585 221 2462 978 537 210 6600 330 609 189 209 1114 69261".split())
# clubes de ENORME alcance no Brasil (sinal forte). Santos, Grêmio, Inter etc. ficam fora de propósito.
CLUBES_S = set("418 131 281 985 31 11 631 583 27 506 46 5 13 614 199 1023 585 189 209".split())
# clubes conhecidos de nível B (20 pts de clube). Além destes, a força do elenco (soma dos 14 maiores
# valores) é calculada sozinha a cada rodada, então subidas/descidas de clube se ajustam sozinhas.
CLUBES_B = {'24': 'SG Eintracht Frankfurt', '29': 'FC Everton', '36': 'Fenerbahce', '114': 'Besiktas JK', '141': 'Galatasaray', '150': 'Real Betis Balompié', '162': 'AS Monaco', '234': 'Feyenoord', '244': 'Olympique Marselha', '288': 'Club Estudiantes de La Plata', '368': 'Sevilla FC', '371': 'Celtic FC', '379': 'West Ham United', '383': 'PSV Eindhoven', '398': 'SS Lazio', '405': 'Aston Villa FC', '430': 'ACF Fiorentina', '621': 'Athletic Bilbao', '681': 'Real Sociedad', '703': 'Nottingham Forest', '800': 'Atalanta BC', '861': 'CA Peñarol', '866': 'Club Nacional', '873': 'Crystal Palace FC', '1025': 'Bologna', '1041': 'Olympique Lyon', '1049': 'Valencia CF', '1050': 'FC Villarreal', '1061': 'Los Angeles Galaxy', '1082': 'LOSC Lille', '1234': 'CA Independiente', '1237': 'Brighton & Hove Albion', '1444': 'Racing Club', '1775': 'CA San Lorenzo de Almagro', '2282': 'Club Brugge', '2407': 'CF Monterrey', '3631': 'CF América', '3711': 'CD Cruz Azul', '8023': 'Al-Ittihad Club', '18487': 'Al-Ahli SFC', '18544': 'Al-Nassr FC', '23826': 'RB Leipzig', '51828': 'Los Angeles FC'}

PESO_LIGA = {"GB1": 10, "ES1": 10, "IT1": 10, "L1": 10, "FR1": 10, "BRA1": 11, "PO1": 7, "AR1N": 6, "NL1": 5, "SA1": 5,
             "TR1": 4, "MLS1": 4, "MEXA": 4, "BRA2": 4, "BE1": 3, "GB2": 3, "URU1": 2, "COLP": 2, "SC1": 2, "JAP1": 2,
             "GR1": 2, "BRA3": 2, "RU1": 1, "DK1": 1, "CSL": 1, "QSL": 1}
PESO_NAC = {"Brasil": 13, "Argentina": 12, "Uruguai": 10, "Portugal": 10, "França": 10, "Espanha": 10, "Inglaterra": 10,
            "Alemanha": 10, "Itália": 10, "Holanda": 9, "Colômbia": 8, "Bélgica": 8, "Croácia": 7, "México": 6,
            "Paraguai": 6, "Chile": 6, "Estados Unidos": 5, "Equador": 5, "Marrocos": 5, "Senegal": 5, "Nigéria": 4,
            "Japão": 4, "Coreia do Sul": 4, "Dinamarca": 4, "Suiça": 4, "Suíça": 4, "Polónia": 4, "Sérvia": 4,
            "Noruega": 4, "Costa do Marfim": 4, "Camarões": 4, "Gana": 4, "Egito": 4, "Venezuela": 4, "Peru": 4}
# o oGol (copas.json) e o Transfermarkt escrevem alguns países de formas diferentes
ALIAS_PAIS = {"irao": "ira", "republica tcheca": "tchequia", "turquia": "turquia", "polonia": "polonia"}


def _norm(t):
    t = unicodedata.normalize("NFD", (t or "").lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]", "", t).strip()


def _pais(p):
    n = _norm(p)
    return ALIAS_PAIS.get(n, n)


def _f(x, padrao=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return padrao


def _clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def faixa_fama(f):
    return "Fácil" if f >= FAMA_FACIL_MIN else "Médio" if f >= FAMA_MEDIO_MIN else "Especialista" if f >= FAMA_CORTE else "Fora"


def carregar_famosos(caminho):
    """IDs do Transfermarkt (um por linha, # = comentário). Sempre ID, nunca nome: há vários 'Paulinho'."""
    ids = set()
    try:
        with open(caminho, encoding="utf-8") as f:
            for linha in f:
                m = re.match(r"\s*(\d+)\b", linha)
                if m:
                    ids.add(m.group(1))
    except OSError:
        print(f"  ! {caminho} nao encontrado: a fama fica sem as estrelas manuais (qualidade menor no Facil).")
    return ids


def carregar_copas(caminho):
    """(nome, pais) normalizados -> ano da Copa mais recente em que o jogador esteve (de copas.json)."""
    mapa = {}
    try:
        with open(caminho, encoding="utf-8") as f:
            rows = json.load(f)["rows"]
    except (OSError, ValueError, KeyError):
        print(f"  ! {caminho} nao encontrado/ilegivel: a fama fica sem o sinal de Copa.")
        return mapa
    for r in rows:
        try:
            ano = int(r[2])
        except (TypeError, ValueError, IndexError):
            continue
        k = (_norm(r[0]), _pais(r[1]))
        if ano > mapa.get(k, 0):
            mapa[k] = ano
    return mapa


def carregar_ajustes(caminho):
    """Opcional. {"idJogador": pontos}: ajuste vindo do feedback dos jogadores (ex.: -8 ou +5)."""
    try:
        with open(caminho, encoding="utf-8") as f:
            d = json.load(f)
        return {str(k): _f(v) for k, v in d.items()}
    except (OSError, ValueError, AttributeError):
        return {}


# ---- bônus de gols (gols.json, vindo do pegar_gols.py) -------------------------------
GOLS_SEL_MIN = (10, 30, 60)     # jogos pela seleção principal: +4 / +8 / +12 (escala por PESO_NAC)
GOLS_SEL_FORTE = 30             # sinal forte "selecao": 30+ jogos por seleção de peso >= 8
GOLS_ARTILHEIRO = 150           # sinal forte "artilheiro": 150+ gols de clube
GOLS_CL, GOLS_CLI = 5, 3        # Champions 5+ ou Libertadores 3+: dá +4 de fama, mas NÃO libera o Fácil sozinho
GOLS_TETO = 12                  # o bônus de gols não passa disso (o valor de mercado já pesa até 40)
POS_ATAQUE = {"CA", "SA", "PE", "PD", "MEI"}   # quem recebe o bônus de gols inteiro (os demais, 40%)


def carregar_gols(caminho):
    """gols.json do pegar_gols.py: {idJogador: registro}. Vazio (sem bônus) se não existir."""
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f).get("rows", {})
    except (OSError, ValueError, AttributeError):
        print(f"  ! {caminho} nao encontrado/ilegivel: sem bonus de gols.")
        return {}


def bonus_gols(c, rec):
    """Pontos extras e sinais fortes vindos de gols.json. c = campos do jogador, rec = registro (ou None)."""
    if not rec:
        return 0.0, []
    pts, sinais = 0.0, []
    nac = c[10]
    sel = rec.get("sel")
    if sel and sel[0] >= GOLS_SEL_MIN[0]:
        pts += (12 if sel[0] >= GOLS_SEL_MIN[2] else 8 if sel[0] >= GOLS_SEL_MIN[1] else 4) * PESO_NAC.get(nac, 3) / 13
        if sel[0] >= GOLS_SEL_FORTE and PESO_NAC.get(nac, 3) >= 8:
            sinais.append("selecao")
    g = rec.get("g") or 0
    if g > 0:
        fator = 1.0 if c[2] in POS_ATAQUE else 0.4
        pts += 12 * fator * _clamp(math.log10(g) / math.log10(300))
    if g >= GOLS_ARTILHEIRO:
        sinais.append("artilheiro")
    if (rec.get("cl") or 0) >= GOLS_CL or (rec.get("cli") or 0) >= GOLS_CLI:
        pts += 4
    return min(pts, GOLS_TETO), sinais


# ---- bônus de Copa pelo ID do Transfermarkt (copas.json v2 + copas_tm.json do cruzar_copas.py) ----
COPA_TETO = 16
COPA_TITULO_MUNDO = {"Copa do Mundo", "Copa del Mundo", "World Cup", "Mundial"}   # "Mundial" sozinho = Copa do Mundo
COPA_TITULO_AMERICA = {"Copa América", "Copa America"}


def carregar_copas_tm(copas_json, copas_tm_json):
    """ID do Transfermarkt -> resumo da carreira em Copas. Vazio se faltar algum arquivo (cai no cálculo antigo)."""
    try:
        with open(copas_tm_json, encoding="utf-8") as f:
            pid_tm = {k: v["tm"] for k, v in json.load(f)["rows"].items()}
        with open(copas_json, encoding="utf-8") as f:
            rows = json.load(f)["rows"]
    except (OSError, ValueError, KeyError) as e:
        print(f"  ! sem bônus de Copa por ID ({e}): usando o sinal antigo por nome.")
        return {}
    agg = {}
    for r in rows:
        if len(r) <= 21 or r[17] is None or str(r[7]) not in pid_tm:
            continue
        a = agg.setdefault(pid_tm[str(r[7])], {"anos": set(), "anos_jogou": set(), "ultimo_ano": 0,
                                               "jc": 0, "titular": False, "mundo": 0, "america": 0})
        a["anos"].add(r[2])                                       # esteve no elenco
        a["ultimo_ano"] = max(a["ultimo_ano"], int(r[2]))
        if r[17] > 0:
            a["anos_jogou"].add(r[2])
            a["jc"] += r[17]
            if r[19] and r[19] / r[17] >= 60:              # minutos por jogo: titular
                a["titular"] = True
        tit = r[21] or {}
        a["mundo"] = max(a["mundo"], sum(v for k, v in tit.items() if k in COPA_TITULO_MUNDO))
        a["america"] = max(a["america"], sum(v for k, v in tit.items() if k in COPA_TITULO_AMERICA))
    return agg


def bonus_copa_tm(cr, nac):
    """Pontos e sinal forte vindos da carreira em Copas. cr = resumo do carregar_copas_tm.
    Base = a mesma escala do ano da Copa mais recente (2026: +10, 2022: +8, 2018: +5, 2014: +2),
    para não baixar quem já era famoso. Por cima entram o que o oGol traz de novo: jogos, titularidade e títulos."""
    ano = cr["ultimo_ano"]
    base = 10 if ano >= 2026 else 8 if ano >= 2022 else 5 if ano >= 2018 else 2 if ano >= 2014 else 0
    extra = 0
    if cr["jc"] >= 10:
        extra += 4
    elif cr["jc"] >= 4:
        extra += 2
    if cr["titular"]:
        extra += 2
    if cr["mundo"]:
        extra += 4
    if cr["america"]:
        extra += 2
    pts = min(base + min(extra, 6), COPA_TETO)
    sinal = []
    # mesma regra do sinal antigo: Copa de 2018 em diante por seleção de grande alcance (peso >= 8)
    if PESO_NAC.get(nac, 3) >= 8 and cr["ultimo_ano"] >= 2018:
        sinal.append(f"copa{cr['ultimo_ano']}")
    return pts, sinal


def calcular_fama(campos, famosos, copas, ajustes, gols=None, copas_tm=None):
    """campos: listas com os 12 campos de cada jogador.
    Devolve [(fama, sinais, travado, famaBruta)] na mesma ordem. famaBruta = nota sem o teto do Fácil."""
    por_clube = {}
    for i, c in enumerate(campos):
        por_clube.setdefault(c[9] or c[1], []).append(i)
    forca, rank = {}, {}
    for k, idxs in por_clube.items():
        idxs.sort(key=lambda i: -_f(campos[i][5]))
        forca[k] = sum(_f(campos[i][5]) for i in idxs[:14])      # força do elenco (14 maiores valores)
        for pos, i in enumerate(idxs, 1):
            rank[i] = pos                                         # 1 = jogador mais valioso do clube
    saida = []
    for i, c in enumerate(campos):
        nome, clube, _, idade, num, valor, liga, pid, _, idc, nac = c[:11]
        v, idade, n, r = _f(valor), int(_f(idade, 25)), (int(num) if str(num).isdigit() else 0), rank[i]
        ve = v * 1.25 if liga == "BRA1" else v                    # mercado brasileiro é subavaliado frente à fama
        pts_valor = 40 * _clamp(math.log10(max(ve, 0.05) * 20) / math.log10(2000))
        dyn = _clamp(math.log10(max(forca[idc or clube], 1) / 20) / math.log10(900 / 20))
        base_clube = max(20 * dyn, 25 if idc in CLUBES_A else 0, 20 if idc in CLUBES_B else 0, 9 if liga == "BRA1" else 0)
        rel = 1 if r <= 3 else .75 if r <= 7 else .5 if r <= 11 else .25   # reserva de clube grande vale menos
        pts_tit = (7 if r <= 3 else 5 if r <= 11 else 2 if r <= 16 else 0) + \
                  (3 if n in (1, 7, 9, 10, 11) else 2 if 2 <= n <= 8 else 1 if 12 <= n <= 25 else 0)
        f = pts_valor + base_clube * rel + PESO_LIGA.get(liga, 1) + PESO_NAC.get(nac, 3) + pts_tit
        if idade <= 20 and v < 10:
            f -= 6
        elif idade <= 22 and v < 5:
            f -= 3
        cr = (copas_tm or {}).get(pid)                            # pid = ID do jogador no Transfermarkt
        if cr is not None:                                        # bônus novo, pelo ID do Transfermarkt
            pc_pts, pc_sinal = bonus_copa_tm(cr, nac)
            f += pc_pts
            ano_copa = 0
        else:                                                     # antigo: ano da última Copa, pelo nome
            pc_sinal = []
            ano_copa = copas.get((_norm(nome), _pais(nac)), 0)
            f += 10 if ano_copa >= 2026 else 8 if ano_copa >= 2022 else 5 if ano_copa >= 2018 else 2 if ano_copa >= 2014 else 0
        bg, sg = bonus_gols(c, (gols or {}).get(pid))
        f += bg
        sinais = list(sg)
        if pid in famosos:
            sinais.append("estrela")
            f = max(f, 92)
        if cr is not None:
            sinais += pc_sinal
        elif ano_copa >= 2018 and PESO_NAC.get(nac, 3) >= 8:      # Copa só conta como sinal forte para seleções de grande alcance
            sinais.append(f"copa{ano_copa}")
        if idc in CLUBES_S and r <= 5:
            sinais.append("clube")
        if idc in CLUBES_A and r <= PROTAGONISTAS_TOP:            # craque do elenco de um clube de grande alcance
            sinais.append("protagonista")
        if v >= VALOR_ELITE:
            sinais.append("valor")
        f = int(round(_clamp(f + ajustes.get(pid, 0), 0, 100)))
        bruta = f                                                 # nota sem o teto (vai para o 14º campo)
        travado = False
        if f >= FAMA_FACIL_MIN and not sinais:                    # o teto: sem sinal forte, não entra no Fácil
            f, travado = FAMA_FACIL_MIN - 1, True
        saida.append((f, sinais, travado, bruta))
    return saida


def relatorio_fama(campos, res, famosos, caminho_csv=None):
    cont = Counter(faixa_fama(r[0]) for r in res)
    print("\nFama calculada:")
    for nome in ("Fácil", "Médio", "Especialista", "Fora"):
        print(f"  {nome:13} {cont.get(nome, 0):6}")
    travados = [(c, r[0]) for c, r in zip(campos, res) if r[2]]
    print(f"  {len(travados)} jogadores seriam Fácil mas foram travados em {FAMA_FACIL_MIN - 1} (sem sinal forte). Exemplos:")
    for c, _ in sorted(travados, key=lambda x: -_f(x[0][5]))[:8]:
        print(f"     {c[0]} ({c[1]}, {c[5]} mi)")
    por_sinal = Counter(s.rstrip("0123456789") for r in res if r[0] >= FAMA_FACIL_MIN for s in r[1])
    print("  Sinais fortes dos jogadores do Fácil:", dict(por_sinal))
    ids_base = {c[7] for c in campos}
    fora = sum(1 for i in famosos if i not in ids_base)
    if fora:
        print(f"  ({fora} IDs de famosos.txt nao estao na base atual: jogam fora das ligas coletadas, nao tem problema)")
    if caminho_csv:
        with open(caminho_csv, "w", encoding="utf-8-sig") as f:
            f.write("nome;clube;liga;valor_mi;nacionalidade;fama;fama_bruta;faixa;sinais;travado\n")
            for c, (fm, sig, t, br) in sorted(zip(campos, res), key=lambda x: -x[1][3]):
                f.write(";".join([c[0], c[1], c[6], c[5], c[10], str(fm), str(br), faixa_fama(fm), "+".join(sig), "sim" if t else ""]) + "\n")
        print(f"  Relatorio completo: {caminho_csv}")


def relatorio_gols(campos, antes, depois, gols, caminho_csv):
    """Compara a fama sem e com o bonus de gols. Só para calibrar: escreve o CSV e imprime o resumo."""
    trans, entrou = Counter(), []
    with_csv = []
    for c, a, b in zip(campos, antes, depois):
        rec = gols.get(c[7]) or {}
        bon, sig = bonus_gols(c, rec or None)
        fa, fb = faixa_fama(a[0]), faixa_fama(b[0])
        if fa != fb:
            trans[(fa, fb)] += 1
        if fb == "Fácil" and fa != "Fácil":
            entrou.append((b[0], c[0], c[1], c[5], rec))
        with_csv.append((b[0] - a[0], c, a[0], b[0], bon, sig, fa, fb, rec))
    print("\nBônus de gols (antes -> depois):")
    for (x, y), n in trans.most_common():
        print(f"  {x:13} -> {y:13} {n:6}")
    print(f"  Jogadores com algum bônus: {sum(1 for r in with_csv if r[4] > 0)} | "
          f"Fácil antes: {sum(1 for r in with_csv if r[6] == 'Fácil')} -> depois: {sum(1 for r in with_csv if r[7] == 'Fácil')}")
    sinais = Counter(s.rstrip("0123456789") for r in with_csv for s in r[5])
    print(f"  Sinais fortes que vieram dos gols: {dict(sinais)}")
    print(f"  Entraram no Fácil ({len(entrou)}). Os 25 de maior fama:")
    for f_, nome, clube, valor, rec in sorted(entrou, key=lambda x: -x[0])[:25]:
        print(f"     {f_:3} {nome} ({clube}, {valor} mi) | g={rec.get('g')} sel={(rec.get('sel') or [0])[0]}")
    if caminho_csv:
        with open(caminho_csv, "w", encoding="utf-8-sig") as f:
            f.write("nome;clube;pos;liga;valor_mi;nacionalidade;fama_antes;fama_depois;diferenca;bonus_gols;"
                    "faixa_antes;faixa_depois;sinais_gols;gols_clube;jogos_gols;sel_jogos;cl;cli\n")
            for d, c, a, b, bon, sig, fa, fb, rec in sorted(with_csv, key=lambda x: -x[0]):
                sel = rec.get("sel") or [0]
                f.write(";".join(map(str, [c[0], c[1], c[2], c[6], c[5], c[10], a, b, d, round(bon, 1), fa, fb,
                                           "+".join(sig), rec.get("g", ""), rec.get("jg", ""), sel[0],
                                           rec.get("cl", ""), rec.get("cli", "")])) + "\n")
        print(f"  Comparacao completa: {caminho_csv}")


def relatorio_copa(campos, antes, depois, copas_tm, caminho_csv):  # copas_tm: reservado
    """Antes/depois só do bônus de Copa (com os gols já aplicados nos dois lados)."""
    trans, entrou, linhas = Counter(), [], []
    for c, a, b in zip(campos, antes, depois):
        fa, fb = faixa_fama(a[0]), faixa_fama(b[0])
        if fa != fb:
            trans[(fa, fb)] += 1
        if fb == "Fácil" and fa != "Fácil":
            entrou.append((b[0], c[0], c[1], c[5]))
        linhas.append((b[0] - a[0], c, a[0], b[0], fa, fb))
    print("\nBônus de Copa (antes -> depois):")
    for (x, y), n in trans.most_common():
        print(f"  {x:13} -> {y:13} {n:6}")
    print(f"  Fácil antes: {sum(1 for r in linhas if r[4] == 'Fácil')} -> depois: {sum(1 for r in linhas if r[5] == 'Fácil')}")
    print(f"  Entraram no Fácil ({len(entrou)}). Os 25 de maior fama:")
    for f_, nome, clube, valor in sorted(entrou, key=lambda x: -x[0])[:25]:
        print(f"     {f_:3} {nome} ({clube}, {valor} mi)")
    if caminho_csv:
        with open(caminho_csv, "w", encoding="utf-8-sig") as f:
            f.write("nome;clube;liga;valor_mi;nacionalidade;fama_antes;fama_depois;diferenca;faixa_antes;faixa_depois\n")
            for d, c, a, b, fa, fb in sorted(linhas, key=lambda x: -x[0]):
                f.write(";".join(map(str, [c[0], c[1], c[6], c[5], c[10], a, b, d, fa, fb])) + "\n")
        print(f"  Comparacao completa: {caminho_csv}")


def aplicar_fama(linhas, args):
    """Recalcula a fama de TODAS as linhas (descarta 13º/14º campos antigos) e devolve linhas com 14 campos."""
    campos = []
    for l in linhas:
        c = l.split(",")[:12]
        campos.append(c + [""] * (12 - len(c)))
    famosos = carregar_famosos(args.famosos)
    copas = carregar_copas(args.copas_json)
    ajustes = carregar_ajustes(args.ajustes_fama)
    gols = carregar_gols(args.gols) if getattr(args, "gols", None) else None
    copas_tm = carregar_copas_tm(args.copas_json, args.copas_tm) if getattr(args, "copas_tm", None) else None
    res = calcular_fama(campos, famosos, copas, ajustes, gols, copas_tm)
    relatorio_fama(campos, res, famosos, args.relatorio_fama)
    if gols is not None:
        antes = calcular_fama(campos, famosos, copas, ajustes, None, copas_tm)
        relatorio_gols(campos, antes, res, gols, args.relatorio_gols)
    if copas_tm is not None:
        sem_copa = calcular_fama(campos, famosos, copas, ajustes, gols, None)
        relatorio_copa(campos, sem_copa, res, copas_tm, args.relatorio_copa)
    return [",".join(c + [str(r[0]), str(r[3])]) for c, r in zip(campos, res)]


def ler_linhas_dados(fonte):
    """Lê as linhas de jogadores de um dados.txt ou de um .js/.html com 'const DATA=`...`;'."""
    with open(fonte, encoding="utf-8") as f:
        txt = f.read()
    m = re.search(r"const DATA=`(.*?)`;", txt, re.S)
    corpo = m.group(1) if m else txt
    return [l.strip() for l in corpo.split(";") if l.strip() and len(l.split(",")) > 6]



# ======================================================================
#  ESCUDOS DOS CLUBES DA COPA (--escudos-copas)
#  1) acha o ID de cada clube do copas.json: pelo dados.txt (nome) ou pela busca no Transfermarkt;
#     os nomes diferentes podem ser informados em aliases_clubes.txt ("Nome na Copa ; nome no Transfermarkt"
#     ou "Nome na Copa ; ID:123456");
#  2) grava os IDs no campo 9 do copas.json/copas.js (já fica salvo mesmo se você interromper);
#  3) baixa os escudos que faltam e junta no bloco CRESTS do HTML (--html).
# ======================================================================
SIGLAS_CLUBE_ESC = {"fc", "cf", "ec", "sc", "se", "sl", "ad", "ca", "cr", "club", "de", "sp", "fk", "afc",
                    "ac", "as", "rb", "sd", "sv", "rc", "ud", "cd", "ss", "us", "ssc", "sc"}


def _chave_clube(nome):
    """'FC Liverpool' e 'Liverpool' viram a mesma chave. Hífen e apóstrofo viram espaço ('Umm-Salal' = 'Umm Salal')."""
    limpo = re.sub(r"[-'´`]", " ", nome or "")
    return " ".join(t for t in _norm(limpo).split() if t not in SIGLAS_CLUBE_ESC)


def _mesmo_clube(a, b):
    ta, tb = set(_chave_clube(a).split()), set(_chave_clube(b).split())
    return bool(ta) and bool(tb) and (ta <= tb or tb <= ta)


def carregar_aliases(caminho="aliases_clubes.txt"):
    """'Nome na Copa ; nome no Transfermarkt' ou 'Nome na Copa ; ID:123'. Linhas com # são ignoradas."""
    aliases = {}
    try:
        with open(caminho, encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha or linha.startswith("#") or ";" not in linha:
                    continue
                nome, alvo = [x.strip() for x in linha.split(";", 1)]
                aliases[nome] = alvo
    except OSError:
        pass
    return aliases


def buscar_clube_tm(nome, termo=None):
    """Procura o clube no Transfermarkt. 'termo' (do aliases) substitui o nome na busca e na comparação.
    Devolve (id, nome_no_tm) ou (None, None)."""
    from urllib.parse import quote
    busca = termo or nome
    try:
        soup = get(f"{BASE}/schnellsuche/ergebnis/schnellsuche?query={quote(busca)}")
    except requests.RequestException:
        return None, None
    if soup is None:
        return None, None
    for a in soup.select('a[href*="/verein/"]'):
        m = re.search(r"/verein/(\d+)", a.get("href", ""))
        txt = a.get_text(" ", strip=True)
        if m and txt and _mesmo_clube(txt, busca):
            return m.group(1), txt
    return None, None


def _gravar_relatorio(linhas):
    """Grava o CSV. Se ele estiver aberto no Excel (bloqueado), grava em outro nome e segue."""
    for nome in ("escudos_copas.csv", "escudos_copas_novo.csv"):
        try:
            with open(nome, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(["clube_copa", "linhas", "id_tm", "nome_tm", "origem"])
                w.writerows(linhas)
            return
        except PermissionError:
            print(f"  ! {nome} está aberto em outro programa (Excel?). Feche-o para atualizar.", flush=True)
    print("  ! relatório não gravado (arquivos bloqueados); os IDs no copas.json foram gravados normalmente.", flush=True)


def _gravar_copas(dados_copa, rows):
    txt = json.dumps({"v": dados_copa.get("v", 2), "rows": rows}, ensure_ascii=False, separators=(",", ":"))
    with open(dados_copa["_arq"], "w", encoding="utf-8") as f:
        f.write(txt)
    with open("copas.js", "w", encoding="utf-8") as f:
        f.write("window.COPAS_DATA=" + txt + ";")


def escudos_copas(args):
    with open(args.copas_json, encoding="utf-8") as f:
        dados_copa = json.load(f)
    dados_copa["_arq"] = args.copas_json
    rows = dados_copa["rows"]
    clubes = Counter(r[6] for r in rows if len(r) > 6 and r[6])
    aliases = carregar_aliases()
    print(f"{len(clubes)} clubes distintos nas Copas ({len(aliases)} apelidos em aliases_clubes.txt).")

    mapa = {}                                           # chave do nome -> (id, nome)
    for linha in ler_linhas_dados("dados.txt"):
        c = linha.split(",")
        if len(c) > 9 and c[9] and c[1]:
            mapa.setdefault(_chave_clube(c[1]), (c[9], c[1]))

    resolvidos, relatorio = {}, []
    pendentes = sum(1 for nome in clubes if _chave_clube(nome) not in mapa and nome not in aliases)
    print(f"  {pendentes} clubes sem correspondência no dados.txt: vão para a busca no Transfermarkt.")
    print("  (Pode interromper com Ctrl+C: o que já foi pesquisado fica no cache e não se repete.)", flush=True)
    feitos_busca = 0
    for nome, n in clubes.most_common():
        cid, tnome, origem = None, "", ""
        ch = _chave_clube(nome)
        alvo = aliases.get(nome)
        if alvo and alvo.upper().startswith("ID:"):
            cid, tnome, origem = alvo.split(":", 1)[1].strip(), alvo, "aliases_clubes.txt (id)"
        elif ch in mapa and not alvo:
            cid, tnome, origem = mapa[ch][0], mapa[ch][1], "dados.txt"
        else:
            global USOU_REDE
            USOU_REDE = False
            cid, tnome = buscar_clube_tm(nome, alvo)
            origem = ("aliases_clubes.txt" if alvo else "busca no Transfermarkt") if cid else "nao encontrado"
            feitos_busca += 1
            print(f"  [{feitos_busca}/{pendentes}] {nome} -> {origem}{(' ' + str(cid)) if cid else ''}", flush=True)
            if USOU_REDE:
                time.sleep(1.5)
            if feitos_busca % 25 == 0:
                _gravar_relatorio(relatorio + [[nome, n, cid or "", tnome, origem]])
        if cid:
            resolvidos[nome] = cid
        relatorio.append([nome, n, cid or "", tnome, origem])

    print(f"  {sum(1 for r in relatorio if r[4] == 'dados.txt')} pelo dados.txt, "
          f"{sum(1 for r in relatorio if r[4] == 'busca no Transfermarkt')} pela busca, "
          f"{sum(1 for r in relatorio if 'aliases' in r[4])} pelo aliases_clubes.txt, "
          f"{sum(1 for r in relatorio if r[4] == 'nao encontrado')} sem id.", flush=True)

    for r in rows:
        while len(r) < 10:
            r.append("")
        cid = resolvidos.get(r[6])
        if cid:
            r[9] = cid
    _gravar_copas(dados_copa, rows)
    _gravar_relatorio(relatorio)
    print("  IDs gravados no copas.json e copas.js (campo 9). Relatório: escudos_copas.csv", flush=True)

    ids = sorted(set(resolvidos.values()), key=int)
    print(f"\nBaixando escudos de {len(ids)} clubes (os que já estão no cache saem na hora)...", flush=True)
    escudos, falhas = {}, []
    for k, i in enumerate(ids, 1):
        uri = imagem_data_uri(f"escudo_{i}", [f"{TM_IMG}/wappen/{t}/{i}.png" for t in ("medium", "head", "normquad")])
        if uri:
            escudos[i] = uri
        else:
            falhas.append(i)
        if k % 20 == 0 or k == len(ids):
            print(f"  {k}/{len(ids)} escudos processados ({len(escudos)} ok, {len(falhas)} sem imagem)", flush=True)

    if args.html:
        with open(args.html, encoding="utf-8") as f:
            html = f.read()
        m = re.search(r"const CRESTS=(\{.*?\});", html, re.S)
        atuais = json.loads(m.group(1)) if m else {}
        atuais.update(escudos)
        novo, achou = trocar_bloco(html, "CRESTS", atuais)
        if achou:
            with open(args.html, "w", encoding="utf-8") as f:
                f.write(novo)
            print(f"  bloco CRESTS de {args.html} atualizado: {len(atuais)} escudos no total.")
        else:
            print(f"  ! nao achei 'const CRESTS={{}};' em {args.html}: escudos nao gravados no HTML.")
    print("Pronto.", flush=True)


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
    ap.add_argument("--so-fama", action="store_true",
                    help="NAO baixa nada: so recalcula a fama (13o e 14o campos) do --html (ou dados.txt) e regrava")
    ap.add_argument("--famosos", default="famosos.txt", help="IDs de jogadores estrela (padrao: famosos.txt)")
    ap.add_argument("--escudos-copas", action="store_true",
                    help="acha o id dos clubes das Copas (dados.txt ou busca no Transfermarkt) e baixa os escudos que faltam")
    ap.add_argument("--copas-json", default="copas.json", help="Copas (gerado por pegar_copas.py), sinal de historico internacional")
    ap.add_argument("--ajustes-fama", default="ajustes_fama.json", help="opcional: {idJogador: pontos} vindo do feedback")
    ap.add_argument("--relatorio-fama", metavar="ARQ.csv", help="grava um CSV com a fama de cada jogador para conferir")
    ap.add_argument("--gols", metavar="gols.json", help="liga o bonus de gols (gols.json do pegar_gols.py) e mostra o antes/depois")
    ap.add_argument("--relatorio-gols", default="comparacao_gols.csv", help="CSV do antes/depois (usado com --gols)")
    ap.add_argument("--copas-tm", metavar="copas_tm.json", help="liga o bonus de Copa pelo ID do Transfermarkt (cruzar_copas.py)")
    ap.add_argument("--relatorio-copa", default="comparacao_copa.csv", help="CSV do antes/depois do bonus de Copa (usado com --copas-tm)")
    args = ap.parse_args()
    if args.escudos_copas:
        USAR_CACHE = not args.sem_cache
        escudos_copas(args)
        return

    if args.lista_ligas:
        for cod, (_, nome) in LIGAS.items():
            print(f"  {cod:5} {nome}")
        return
    desconhecidas = [c for c in args.ligas if c not in LIGAS]
    if desconhecidas:
        sys.exit(f"Liga(s) desconhecida(s): {', '.join(desconhecidas)}. Use --lista-ligas.")
    USAR_CACHE = not args.sem_cache

    if args.so_fama:
        fonte = args.html or "dados.txt"
        linhas = ler_linhas_dados(fonte)
        print(f"--so-fama: {len(linhas)} jogadores lidos de {fonte}")
        gravar(aplicar_fama(linhas, args), args)
        return

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

    # Trava de seguranca: nunca regravar o dados.js com a raspagem vazia ou capenga.
    # (sem isso, um bloqueio do site zerava o arquivo e o site ia ao ar sem jogadores)
    anterior = 0
    try:
        anterior = len(ler_linhas_dados(args.html or "dados.txt"))
    except OSError:
        pass
    if not linhas:
        sys.exit("ERRO: nenhum jogador foi baixado (bloqueio do site, layout novo ou rede fora?). "
                 "Nada foi gravado.")
    if len(args.ligas) == len(LIGAS) and anterior > 1000 and len(linhas) < anterior // 2:
        sys.exit("ERRO: baixei apenas %d jogadores (a rodada anterior tinha %d). "
                 "Parece bloqueio parcial ou mudanca de layout; nada foi gravado." % (len(linhas), anterior))

    gravar(aplicar_fama(linhas, args), args)


def gravar(linhas, args):
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
