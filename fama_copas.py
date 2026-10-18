"""
fama_copas.py: grava a fama de cada jogador de Copa no campo 22 do copas.js/copas.json.

  - Quem tem ID do Transfermarkt (campo 11) e está no dados.txt: usa a fama do Transfermarkt.
  - Quem não tem: fama de SUBSTITUIÇÃO, calculada só com os dados da Copa. Fica sempre abaixo de 60
    (teto FAMA_SUB_TETO), para não competir com a fama do Transfermarkt. É uma fama baixa, de propósito.

Fórmula da substituição (somada e limitada ao teto):
  base da Copa mais recente: 2026 = 20, 2022 = 16, 2018 = 12, 2014 = 8, 2010 = 4
  + jogos em Copa (todas as edições): 1 ponto a cada 4 jogos, até 10
  + Copas disputadas (no elenco): 2 por Copa, até 4
  + titular em alguma Copa (média de 60 minutos ou mais por jogo): +3
  + título de Copa do Mundo: +8 ; título de Copa América: +4

Uso (na pasta do projeto, com copas.js e dados.txt):
  python fama_copas.py
Depois rode o index de novo (ele lê este campo quando o Transfermarkt não tem o jogador).
"""
import json, re, sys
from collections import defaultdict

ARQ_JSON = "copas.json"
ARQ_JS = "copas.js"
DADOS = "dados.txt"
CAMPO = 22                          # índice do campo novo (0..21 já são usados)
FAMA_SUB_TETO = 59
BASE_ANO = {2026: 20, 2022: 16, 2018: 12, 2014: 8, 2010: 4}
TITULO_MUNDO = {"Copa do Mundo", "Copa del Mundo", "World Cup", "Mundial"}
TITULO_AMERICA = {"Copa América", "Copa America"}


def carregar():
    with open(ARQ_JSON, encoding="utf-8") as f:
        return json.load(f)["rows"]


def carregar_fama_dados(caminho=DADOS):
    """ID do Transfermarkt -> fama (campo 12 do dados.txt, a fama final)."""
    fama = {}
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            c = linha.strip().rstrip(";").split(",")
            if len(c) >= 13 and c[7]:
                try:
                    fama[c[7]] = int(float(c[12] or 0))
                except ValueError:
                    pass
    return fama


def fama_substituta(linhas_do_jogador):
    """linhas_do_jogador: todas as Copas de um mesmo jogador (mesmo id oGol)."""
    ano_max = max(int(r[2]) for r in linhas_do_jogador)
    base = BASE_ANO.get(ano_max, 0)
    jogos = sum(int(r[17] or 0) for r in linhas_do_jogador if r[17] is not None)
    pts_jogos = min(10, jogos // 4)
    copas = len({int(r[2]) for r in linhas_do_jogador})
    pts_copas = min(4, 2 * copas)
    titular = any(r[17] and r[19] and r[19] / r[17] >= 60 for r in linhas_do_jogador)
    tit = {}
    for r in linhas_do_jogador:
        for k, v in (r[21] or {}).items():
            tit[k] = max(tit.get(k, 0), v)
    pts_tit = (3 if titular else 0) \
        + (8 if sum(v for k, v in tit.items() if k in TITULO_MUNDO) else 0) \
        + (4 if sum(v for k, v in tit.items() if k in TITULO_AMERICA) else 0)
    return min(FAMA_SUB_TETO, base + pts_jogos + pts_copas + pts_tit)


def main():
    rows = carregar()
    fama_dados = carregar_fama_dados()
    por_jogador = defaultdict(list)
    for r in rows:
        if len(r) < 12:
            r.extend([""] * (12 - len(r)))
        por_jogador[str(r[7])].append(r)

    cont = {"transfermarkt": 0, "substituta": 0}
    for pid, linhas in por_jogador.items():
        sub = fama_substituta([r for r in linhas if len(r) > 21]) if any(len(r) > 21 for r in linhas) else None
        for r in linhas:
            while len(r) <= CAMPO:
                r.append(None)
            tm = r[11]
            if tm and tm in fama_dados:
                r[CAMPO] = fama_dados[tm]
                cont["transfermarkt"] += 1
            else:
                r[CAMPO] = sub
                cont["substituta"] += 1

    txt = json.dumps({"v": 2, "rows": rows}, ensure_ascii=False, separators=(",", ":"))
    with open(ARQ_JSON, "w", encoding="utf-8") as f:
        f.write(txt)
    with open(ARQ_JS, "w", encoding="utf-8") as f:
        f.write("window.COPAS_DATA=" + txt + ";")
    print(f"Fama gravada em {len(rows)} linhas: {cont['transfermarkt']} do Transfermarkt, "
          f"{cont['substituta']} de substituição (até {FAMA_SUB_TETO}).")


if __name__ == "__main__":
    sys.exit(main())
