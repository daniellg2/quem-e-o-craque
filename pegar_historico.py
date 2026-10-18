"""
Gera o historico.json: TÍTULOS (página "Conquistas" do Transfermarkt) + HISTÓRICO DE CLUBES
(API interna de transferências do site) de cada jogador — a base do Gêmeo de Carreira.

Fica na MESMA pasta do pegar_dados.py (reaproveita o cache/, os headers e a leitura do dados.txt).
São 1 ou 2 requisições por jogador, com pausa entre elas, igual ao pegar_gols.py.

Formato (chave = idJogador do Transfermarkt, o mesmo campo 8 do dados.txt):
  "8198": {
    "t": { "bolaOuro": 5, "champions": 5, "liga": 7, ... },   chaves iguais às do car.titulos do jogo
    "clubes": [["63438","Nacional","95/96"], ...]             clubes do mais antigo para o mais novo
  }
  Só entram no "t" as conquistas que o jogo entende (Bola de Ouro, Champions, libertadores,
  ligas nacionais, copas...). O que não for reconhecido aparece no resumo final para conferência.
  Times de base (U19, "Jgd." etc.) e "Sem clube" ficam de fora dos clubes.

Uso:
  python pegar_historico.py --ids 8198 28003       # só esses jogadores (idJogador do Transfermarkt)
  python pegar_historico.py --limite 100           # os 100 mais famosos ainda sem dados
  python pegar_historico.py                        # todos com fama >= 44 (inclui goleiros); retoma de onde parou
  python pegar_historico.py --so-titulos           # metade das requisições (só "Conquistas")
  python pegar_historico.py --so-clubes            # metade das requisições (só a API de clubes)

Dicas:
  - Pode interromper (Ctrl+C) e rodar de novo: o historico.json é salvo a cada 25 jogadores.
  - --refazer ignora o que já está no historico.json. --sem-cache baixa as páginas de novo.
  - Ao terminar (ou a qualquer momento), o historico.js já sai pronto para o index6.
"""
import argparse, collections, json, os, re, sys, time
from datetime import date

import requests
from bs4 import BeautifulSoup

import pegar_dados as pd

SAIDA = "historico.json"
BASE_RE = re.compile(r"\bU-?\d{2}\b|\bjgd\b|\byouth\b|\bacademy\b|\bsub-?\d+\b|\bii\b", re.I)

# Conquistas que NÃO entram no gêmeo (prêmios de mídia, supercopas, seleções de base...).
# A checagem vem antes de tudo: a conquista é ignorada de propósito (não vai para o relatório).
IGNORAR = re.compile(
    r"melhor jogador|melhor goleiro|jogador da (?:epoca|temporada|partida|competi)|jogador d[oa] (?:ano|mes)"
    r"|futebolista d[oa]|golden boy|\bmvp\b|usuario|nations league|super ?cup|supertaca|supercopa|copa de la liga"
    r"|super cup|cup of champions|leagues cup|supporters|campeones|olimpic|sub-?\d|u-?\d{2}|youth"
    r"|confederac|confederation|\bvdv\b|recopa|videos|todos os titulos"
)


def url_conquistas(pid):
    return f"{pd.BASE}/-/erfolge/spieler/{pid}"


def chave_titulo(nome):
    """Nome da conquista (Transfermarkt) -> chave do car.titulos do jogo (ou None se não entra)."""
    t = re.sub(r"\s+", " ", pd._sem_acento(nome)).strip()
    if IGNORAR.search(t):
        return None
    if "ballon" in t or "bola de ouro" in t:
        return "bolaOuro"
    if "bota de ouro" in t or "chuteira de ouro" in t or "golden boot" in t or "golden shoe" in t:
        return "chuteiraOuro"
    if "luva de ouro" in t or "golden glove" in t:
        return "luvaOuro"
    if "artilheiro" in t or "top scorer" in t or "topscorer" in t:
        return "artilharias"
    if "copa do mundo de clubes" in t or "mundo de clubes" in t or "club world cup" in t or "intercontinental" in t:
        return "mundial"
    if "copa do mundo" in t or "world cup" in t or "campeao do mundo" in t:
        return "copaMundo"
    if ("champions league" in t or "liga dos campeoes" in t or "copa dos campeoes da europa" in t
            or "copa dos campeoes europeus" in t or "european cup" in t or "taca dos campeoes" in t):
        if "afc" in t or "asia" in t or "asiatica" in t:
            return "aclElite"
        if "concacaf" in t:
            return "concacaf"
        return "champions"
    if ("europa league" in t or "liga europa" in t or "taca uefa" in t or "uefa cup" in t
            or "cup winners" in t or "vencedores de taca" in t):
        return "euroLeague"
    if "libertadores" in t:
        return "libertadores"
    if "sul-americana" in t or "sulamericana" in t or "sudamericana" in t:
        return "sudamericana"
    if "copa america" in t:
        return "copaAmerica"
    if ("eurocopa" in t or "campeonato europeu" in t or "european championship" in t
            or "campeao da europa" in t or "campeao europeu" in t):
        return "euro"
    if "copa africana" in t or "africa cup" in t or "campeao da africa" in t or "african cup" in t:
        return "afcon"
    if "copa da asia" in t or "copa asiatica" in t or "asian cup" in t or "campeao da asia" in t:
        return "asianCup"
    if "copa ouro" in t or "gold cup" in t or "goldcup" in t:
        return "goldCup"
    if "mls cup" in t:                       # MLS Cup é o título da liga, não copa
        return "liga"
    if any(x in t for x in ("taca", "copa", " cup", "pokal", "copa del rey", "coppa")):
        return "copaNac"
    if "campeao" in t or "champion" in t or "winner" in t:
        return "liga"
    return None


def parse_conquistas(soup):
    """Lê as caixas '5x Vencedor Ballon d'Or' da página de Conquistas.
    Devolve (títulos por chave do jogo, conquistas não reconhecidas para o relatório)."""
    titulos, nao_vistas = collections.Counter(), collections.Counter()
    for h in soup.select(".content-box-headline"):
        txt = re.sub(r"\s+", " ", h.get_text(" ", strip=True))
        m = re.match(r"(\d+)\s*x\s+(.+)", txt)
        if not m:
            continue
        n, nome = int(m.group(1)), m.group(2).strip()
        chave = chave_titulo(nome)
        if chave:
            titulos[chave] += n
        elif not IGNORAR.search(pd._sem_acento(nome)):
            nao_vistas[nome] += n
    return dict(titulos), nao_vistas


def _cache_json(pid):
    return os.path.join("cache", f"hist_{pid}.json")


def baixar(url):
    try:
        return pd.get(url)
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code in (403, 404):
            return None
        raise


def clubes_json(pid):
    """Histórico de clubes via API interna do Transfermarkt. Devolve (estacoes, obtido).
    obtido=False quando a requisição falhou (o jogador fica para a próxima rodada)."""
    arq = _cache_json(pid)
    if pd.USAR_CACHE and os.path.exists(arq):
        with open(arq, encoding="utf-8") as f:
            d = json.load(f)
        return estacoes(d, pid), True
    url = f"{pd.BASE}/ceapi/transferHistory/list/{pid}"
    pd.USOU_REDE = True
    r = requests.get(url, headers=pd.HEADERS, timeout=30)
    if r.status_code in (403, 404):
        return [], False
    r.raise_for_status()
    d = r.json()
    os.makedirs("cache", exist_ok=True)
    with open(arq, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    return estacoes(d, pid), True


def estacoes(d, pid=""):
    """Transforma o JSON de transferências na lista de clubes do jogador
    (do mais antigo para o mais novo), sem 'Sem clube' nem times de base."""
    saida = []
    for x in reversed(d.get("transfers") or []):
        for lado in ("from", "to"):
            c = x.get(lado) or {}
            nome = (c.get("clubName") or "").strip()
            if c.get("isSpecial") or not nome or BASE_RE.search(nome):
                continue
            m = re.search(r"/verein/(\d+)", c.get("href") or "")
            vid = m.group(1) if m else ""
            if not vid:
                continue
            temp = x.get("season") or ""
            if not saida or saida[-1][0] != vid:
                saida.append([vid, nome, temp])
    return saida


def salvar(rows, caminho):
    tmp = caminho + ".tmp"
    dados = {"v": 1, "gerado": date.today().isoformat(), "rows": rows}
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, caminho)
    # historico.js: mesma coisa em formato <script>, que o jogo carrega abrindo o index.html direto do disco
    with open(os.path.splitext(caminho)[0] + ".js", "w", encoding="utf-8") as f:
        f.write("window.HIST_DATA=")
        json.dump(dados, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";")


def carregar(caminho):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f).get("rows", {})
    except (OSError, ValueError):
        return {}


def main():
    ap = argparse.ArgumentParser(description="Gera historico.json (títulos + histórico de clubes) do Transfermarkt")
    ap.add_argument("--dados", default="dados.txt", help="dados.txt ou HTML do jogo (padrao: dados.txt)")
    ap.add_argument("--saida", default=SAIDA)
    ap.add_argument("--ids", nargs="+", help="so estes idJogador do Transfermarkt")
    ap.add_argument("--fama-min", type=int, default=44, help="so jogadores com fama >= isto (padrao 44 = quem pode ser sorteado)")
    ap.add_argument("--pular-goleiros", action="store_true", help="nao baixa goleiros (por padrao eles entram: luva de ouro/paredões)")
    ap.add_argument("--limite", type=int, help="processa no maximo N jogadores (os mais famosos primeiro)")
    ap.add_argument("--refazer", action="store_true", help="ignora o que ja esta no historico.json")
    ap.add_argument("--so-titulos", action="store_true", help="pula a API de clubes (metade das requisicoes)")
    ap.add_argument("--so-clubes", action="store_true", help="pula a pagina de Conquistas (metade das requisicoes)")
    ap.add_argument("--sem-cache", action="store_true")
    args = ap.parse_args()

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
        elif fama < args.fama_min or (c[2] == "GOL" and args.pular_goleiros):
            continue
        jogadores.append((fama, c[0], c[1], c[7]))
    jogadores.sort(key=lambda x: -x[0])

    rows = {} if args.refazer else carregar(args.saida)
    fila = [j for j in jogadores if j[3] not in rows]
    if args.limite:
        fila = fila[:args.limite]
    print(f"{len(jogadores)} jogadores elegiveis | {len(jogadores) - len(fila)} ja no {args.saida} | "
          f"{len(fila)} para baixar agora")

    nao_vistas = collections.Counter()
    falhas, feitos = 0, 0
    try:
        for i, (fama, nome, clube, pid) in enumerate(fila, 1):
            pd.USOU_REDE = False
            try:
                rec, ok, resumo = {}, False, []
                if not args.so_clubes:
                    soup = baixar(url_conquistas(pid))
                    if soup is not None:
                        ok = True
                        t, nv = parse_conquistas(soup)
                        nao_vistas.update(nv)
                        if t:
                            rec["t"] = t
                        resumo.append(f"{len(t)} tipos de titulo" + (f" ({t['bolaOuro']}x Bola de Ouro)" if t.get("bolaOuro") else ""))
                if not args.so_titulos:
                    if pd.USOU_REDE:
                        time.sleep(1)                    # pausa entre as duas requisicoes do mesmo jogador
                    est, obtido = clubes_json(pid)
                    if obtido:
                        ok = True
                        if est:
                            rec["clubes"] = est
                        resumo.append(f"{len(est)} clubes")
                if not ok:
                    print(f"[{i}/{len(fila)}] {nome}: pagina indisponivel, pulei")
                    continue
                rows[pid] = rec
                feitos += 1
                falhas = 0
                print(f"[{i}/{len(fila)}] {nome} ({clube}): " + " | ".join(resumo))
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

    com_t = sum(1 for r in rows.values() if r.get("t"))
    com_c = sum(1 for r in rows.values() if r.get("clubes"))
    print(f"\n{len(rows)} jogadores em {args.saida} ({com_t} com titulos, {com_c} com clubes).")
    if nao_vistas:
        print("Conquistas nao mapeadas (confira se alguma merece entrar):")
        for nome_c, n in nao_vistas.most_common(15):
            print(f"  {n}x {nome_c}")
    print("Pronto: o historico.js saiu junto e o index6 ja usa no Gêmeo de Carreira.")


if __name__ == "__main__":
    main()
