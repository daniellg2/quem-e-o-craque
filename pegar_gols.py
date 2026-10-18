"""
Gera o gols.json: estatisticas de gols de CLUBE de cada jogador + dados de selecao,
lendo a pagina "Todos os gols" do Transfermarkt (1 requisicao por jogador, 2 se tiver gol decisivo).

Fica na MESMA pasta do pegar_dados.py (reaproveita o cache/, os headers e a leitura do dados.txt).

Formato (chave = idJogador do Transfermarkt, o mesmo campo 8 do dados.txt):
  "225984": {
    "g": 91,                       gols de clube (selecao e times de base U19/U21 ficam de fora; "gb" = gols na base, se houver)
    "jg": 81,                      jogos em que marcou
    "dec": 31,                     gols decisivos ("Gamewinning-Goals" do Transfermarkt), null se nao deu para obter
    "pen": 9, "fal": 7,            penaltis e cobrancas de falta
    "best": ["15/16", 13],         melhor temporada [rotulo do site, gols]
    "cl": 0, "cli": 4,             gols na Champions League e na Libertadores (fase principal)
    "clubes": {"609": ["Cruzeiro EC", 33], ...},   gols por clube (id do clube -> [nome, gols])
    "sel": [1, 0, 0]               selecao principal: [jogos, gols, status]  status: 1 = jogador de selecao atual,
                                   0 = antigo jogador de selecao. Sem a chave "sel" = nunca defendeu selecao.
  }

Uso:
  python pegar_gols.py --arquivo "Neymar_-_Todos_os_gols___Transfermarkt.html"   # testa o parser numa pagina salva (sem internet)
  python pegar_gols.py --ids 54814 225984                                         # so esses jogadores
  python pegar_gols.py --limite 20                                                # os 20 mais famosos ainda sem dados
  python pegar_gols.py                                                            # todos com fama >= 44 (sem goleiros); retoma de onde parou
  python pegar_gols.py --sem-decisivos                                            # metade das requisicoes (sem o campo "dec")

Dicas:
  - Pode interromper (Ctrl+C) e rodar de novo: o gols.json e salvo a cada 25 jogadores e quem ja esta nele e pulado.
  - --refazer ignora o que ja esta no gols.json. --sem-cache baixa as paginas de novo.
"""
import argparse, collections, json, os, re, shutil, sys, time
from datetime import date

import requests
from bs4 import BeautifulSoup

import pegar_dados as pd

MIN = re.compile(r"(?:\d+'|-)(?:\+\d+)?")      # 13' | 90'+5 | - (minuto desconhecido) | -+6
SAIDA = "gols.json"


# ----------------------------------------------------------------------
#  Leitura da pagina
# ----------------------------------------------------------------------
def url_gols(pid, decisivos=False):
    if decisivos:   # o formulario da pagina envia estes parametros por GET
        return (f"{pd.BASE}/-/alletore/spieler/{pid}/plus/0?saison=&verein=0&liga=0&wettbewerb=&pos=0"
                f"&trainer_id=0&minute=0&torart=0&stand=gamewinning")
    return f"{pd.BASE}/-/alletore/spieler/{pid}/saison//verein/0/liga/0/wettbewerb//pos/0/trainer_id/0/minute/0/torart/0"


def achar_tabela(soup):
    for t in soup.select("table"):
        if "auflistung" in (t.get("class") or []):      # essa e a tabela de filtros, nao a de gols
            continue
        if any("minuto" in th.get_text(" ", strip=True).lower() for th in t.select("th")) \
                or any(MIN.fullmatch(td.get_text(" ", strip=True)) for td in t.select("td")):
            return t
    return None


def parse_selecao(soup):
    """Cabecalho: 'Selecao: Brasil' / 'Antigo jogador de Selecao: Brasil' + 'Jogos de Selecao/Gols: 130 / 80'."""
    jogos = gols = status = None
    for lab in soup.select(".data-header__label"):
        t = re.sub(r"\s+", " ", lab.get_text(" ", strip=True))
        m = re.match(r"Jogos de Sele[çc][ãa]o/Gols:\s*(\d+)\s*/\s*(\d+)", t)
        if m:
            jogos, gols = int(m.group(1)), int(m.group(2))
        elif re.search(r"Sele[çc][ãa]o:", t):
            status = 0 if t.lower().startswith("antigo") else 1
    if jogos is None:
        return None
    return [jogos, gols, status if status is not None else 0]


def parse_pagina(soup):
    """Devolve {clubes, gols, resumo, sel}. Cada gol: {temp, code, vid, tipo, novo}  (novo=True na 1a linha do jogo)."""
    clubes = {}
    for sel in soup.select("select[name=verein]"):
        for o in sel.find_all("option"):
            v = (o.get("value") or "").strip()
            if v and v != "0":
                clubes[v] = o.get_text(strip=True)

    m = re.search(r"Jogos:\s*(\d+);\s*Gols:\s*(\d+).*?Gamewinning-Goals:\s*(\d+)", soup.get_text(" ", strip=True))
    resumo = {"jogos": int(m.group(1)), "gols": int(m.group(2)), "dec": int(m.group(3))} if m else None

    gols, ctx, temp = [], None, None
    t = achar_tabela(soup)
    for tr in (t.find_all("tr") if t else []):
        tds = tr.find_all("td", recursive=False)
        if not tds:
            continue
        txt = [c.get_text(" ", strip=True) for c in tds]
        if len(tds) <= 2 and "Temporada" in tr.get_text():
            temp = txt[0].replace("Temporada", "").strip()
            continue
        if len(tds) >= 10 and MIN.fullmatch(txt[-3]):      # 1o gol do jogo (linha completa; o minuto e sempre txt[-3])
            img = tds[0].find("img")
            mc = re.search(r"/([a-z0-9]+)\.png", (img.get("src") or "") if img else "")
            a = tds[3].find("a")
            mv = re.search(r"/verein/(\d+)", a["href"]) if a and a.get("href") else None
            ctx = {"temp": temp, "code": mc.group(1).upper() if mc else "", "vid": mv.group(1) if mv else ""}
            gols.append(dict(ctx, tipo=txt[-1], novo=True))
        elif ctx and len(tds) <= 4 and re.match(r"(?:\d+'|-)(?:\+\d+)?\s", txt[0]):    # 2o, 3o... gol do mesmo jogo (linha curta)
            mm = re.match(r"(?:\d+'|-)(?:\+\d+)?\s+\d+:\d+\s+(.*)", txt[0])
            if mm:
                gols.append(dict(ctx, tipo=mm.group(1), novo=False))
    return {"clubes": clubes, "gols": gols, "resumo": resumo, "sel": parse_selecao(soup)}


# ----------------------------------------------------------------------
#  Estatisticas
# ----------------------------------------------------------------------
BASE_RE = re.compile(r"\bU-?\d{2}\b")          # "Brighton & Hove Albion U21", "NAC Breda U19"...


def clubes_pro(p):
    """Clubes do filtro, sem os times de base (U19, U21...). Times B (ex.: Sporting CP B) contam como clube."""
    return {v: n for v, n in p["clubes"].items() if not BASE_RE.search(n)}


def montar(p, decisivos=None):
    """Registro do gols.json. So conta gols de CLUBE: a selecao nao esta no filtro de clubes do site."""
    clubes = clubes_pro(p)
    gols = [g for g in p["gols"] if g["vid"] in clubes]
    gb = sum(1 for g in p["gols"] if g["vid"] in p["clubes"] and g["vid"] not in clubes)   # gols em times de base
    por_clube = collections.Counter(g["vid"] for g in gols)
    por_temp = collections.Counter(g["temp"] for g in gols)
    ordem = []
    for g in gols:
        if g["temp"] not in ordem:
            ordem.append(g["temp"])
    best = None
    for tp in ordem:                                   # empate: fica a mais recente
        if best is None or por_temp[tp] >= best[1]:
            best = [tp, por_temp[tp]]
    tipos = collections.Counter(pd._sem_acento(g["tipo"]) for g in gols)
    rec = {
        "g": len(gols),
        "jg": sum(1 for g in gols if g["novo"]),
        "dec": decisivos,
        "pen": tipos["penalti"],
        "fal": tipos["cobranca de falta"],
        "best": best,
        "cl": sum(1 for g in gols if g["code"] == "CL"),
        "cli": sum(1 for g in gols if g["code"] == "CLI"),
        "clubes": {vid: [clubes[vid], n] for vid, n in por_clube.most_common()},
    }
    if gb:
        rec["gb"] = gb                  # gols em times de base (nao entram em g)
    if p["sel"]:
        rec["sel"] = p["sel"]
    return rec


def conferir(p):
    """O total de gols lido tem que bater com a linha-resumo do site (se nao bater, o parser falhou)."""
    r = p["resumo"]
    if not r:
        return len(p["gols"]) == 0
    return r["gols"] == len(p["gols"])


# ----------------------------------------------------------------------
#  Rede
# ----------------------------------------------------------------------
def baixar(url):
    try:
        return pd.get(url)
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code in (403, 404):
            return None
        raise


def contar_decisivos(pid, p, avisos):
    """2a requisicao: o mesmo filtro 'So Gamewinning-Goals' do site. Confere com a linha-resumo antes de aceitar."""
    r = p["resumo"]
    pro = clubes_pro(p)
    if not r or r["dec"] == 0 or not any(g["vid"] in pro for g in p["gols"]):
        return 0
    if pd.USOU_REDE:
        time.sleep(1)                        # pausa entre as duas requisicoes do mesmo jogador
    soup = baixar(url_gols(pid, True))
    if soup is None:
        return None
    q = parse_pagina(soup)
    if len(q["gols"]) != r["dec"]:           # o filtro nao foi aplicado (ou o site mudou): nao confia
        if not avisos.get("dec"):
            avisos["dec"] = True
            print(f"  ! o filtro de gols decisivos nao bateu (esperado {r['dec']}, veio {len(q['gols'])}). "
                  f"Abra {url_gols(pid, True)} no navegador e me diga o que aparece.")
        pd.descartar_cache(url_gols(pid, True))
        return None
    return sum(1 for g in q["gols"] if g["vid"] in pro)


# ----------------------------------------------------------------------
#  Programa
# ----------------------------------------------------------------------
def salvar(rows, caminho):
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"v": 1, "gerado": date.today().isoformat(), "rows": rows}, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, caminho)
    # gols.js: mesma coisa em formato <script>, que o jogo carrega mesmo abrindo o index.html direto do disco
    with open(os.path.splitext(caminho)[0] + ".js", "w", encoding="utf-8") as f:
        f.write("window.GOLS_DATA=")
        json.dump({"v": 1, "gerado": date.today().isoformat(), "rows": rows}, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";")


def carregar(caminho):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f).get("rows", {})
    except (OSError, ValueError):
        return {}


def testar_arquivo(arq):
    with open(arq, encoding="utf-8", errors="replace") as f:
        p = parse_pagina(BeautifulSoup(f.read(), "html.parser"))
    r = p["resumo"]
    print(f"Resumo do site: {r}")
    print(f"Gols lidos (clube + selecao): {len(p['gols'])} -> {'OK, bate com o site' if conferir(p) else 'NAO BATE'}")
    print(f"Clubes no filtro: {p['clubes']}")
    rec = montar(p)
    print("\nRegistro gols.json (dec fica null no teste offline):")
    print(json.dumps(rec, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser(description="Gera gols.json (gols de clube + selecao) do Transfermarkt")
    ap.add_argument("--arquivo", help="testa o parser numa pagina 'Todos os gols' salva (HTML), sem internet")
    ap.add_argument("--dados", default="dados.txt", help="dados.txt ou HTML do jogo (padrao: dados.txt)")
    ap.add_argument("--saida", default=SAIDA)
    ap.add_argument("--ids", nargs="+", help="so estes idJogador do Transfermarkt")
    ap.add_argument("--fama-min", type=int, default=44, help="so jogadores com fama >= isto (padrao 44 = quem pode ser sorteado)")
    ap.add_argument("--incluir-goleiros", action="store_true")
    ap.add_argument("--limite", type=int, help="processa no maximo N jogadores (os mais famosos primeiro)")
    ap.add_argument("--refazer", action="store_true", help="ignora o que ja esta no gols.json")
    ap.add_argument("--sem-decisivos", action="store_true", help="pula a 2a requisicao (campo dec fica null)")
    ap.add_argument("--sem-cache", action="store_true")
    args = ap.parse_args()

    if args.arquivo:
        testar_arquivo(args.arquivo)
        return
    pd.USAR_CACHE = not args.sem_cache

    jogadores = []
    for linha in pd.ler_linhas_dados(args.dados):
        c = linha.split(",")
        if len(c) < 13 or not c[7]:
            continue
        fama = int(float(c[12] or 0))
        if args.ids:
            if c[7] not in args.ids:
                continue
        elif fama < args.fama_min or (c[2] == "GOL" and not args.incluir_goleiros):
            continue
        jogadores.append((fama, c[0], c[1], c[7]))
    jogadores.sort(key=lambda x: -x[0])

    rows = {} if args.refazer else carregar(args.saida)
    fila = [j for j in jogadores if j[3] not in rows]
    if args.limite:
        fila = fila[:args.limite]
    print(f"{len(jogadores)} jogadores elegiveis | {len(jogadores) - len([j for j in jogadores if j[3] not in rows])} ja no {args.saida} | "
          f"{len(fila)} para baixar agora")

    avisos, falhas, feitos = {}, 0, 0
    try:
        for i, (fama, nome, clube, pid) in enumerate(fila, 1):
            pd.USOU_REDE = False
            try:
                soup = baixar(url_gols(pid))
                if soup is None:
                    print(f"[{i}/{len(fila)}] {nome}: pagina indisponivel, pulei")
                    continue
                p = parse_pagina(soup)
                if not conferir(p):
                    dbg = f"debug_gols_{pid}.html"
                    try:
                        shutil.copy(pd._arquivo_cache(url_gols(pid)), dbg)
                    except OSError:
                        dbg = "(nao consegui salvar)"
                    print(f"[{i}/{len(fila)}] {nome} (id {pid}): ! gols lidos ({len(p['gols'])}) != resumo do site ({p['resumo']}), pulei. "
                          f"Pagina salva em {dbg}")
                    continue
                dec = None if args.sem_decisivos else contar_decisivos(pid, p, avisos)
                rec = montar(p, dec)
                rows[pid] = rec
                feitos += 1
                falhas = 0
                sel = f" | selecao {rec['sel'][0]}j/{rec['sel'][1]}g" if "sel" in rec else ""
                print(f"[{i}/{len(fila)}] {nome} ({clube}): {rec['g']} gols, {rec['jg']} jogos, dec {rec['dec']}{sel}")
            except Exception as e:
                falhas += 1
                print(f"[{i}/{len(fila)}] {nome}: erro ({e})", file=sys.stderr)
                if falhas >= 3:
                    print("  3 erros seguidos: aguardando 60s", file=sys.stderr)
                    time.sleep(60)
                    falhas = 0
                continue
            if feitos % 25 == 0:
                salvar(rows, args.saida)
            if pd.USOU_REDE:
                time.sleep(2)             # gentil com o site (pula a pausa quando veio do cache)
    except KeyboardInterrupt:
        print("\nInterrompido: salvando o que ja foi baixado...")
    finally:
        salvar(rows, args.saida)

    com_g = sorted(((r["g"], pid) for pid, r in rows.items()), reverse=True)[:5]
    print(f"\n{len(rows)} jogadores em {args.saida}. Maiores artilheiros: {com_g}")
    print(f"{sum(1 for r in rows.values() if 'sel' in r)} com selecao principal | "
          f"{sum(1 for r in rows.values() if r['dec'] is None)} sem o campo dec")


if __name__ == "__main__":
    main()
