"""
pegar_copas2.py: versão 2 do pegar_copas.py.

Mantém tudo do v1 (elenco, posição tática, foto) e, para cada linha jogador-Copa,
acrescenta dados lidos da página do jogador no oGol (1 requisição por linha, com cache):

  [0..10]  igual ao v1 (nome, seleção, ano, pos, idade, nº, clube, id oGol, foto, "", "")
  [11] tm         ID do Transfermarkt (vazio aqui; preenchido pelo cruzar_copas.py)
  [12] nasc       data de nascimento AAAA-MM-DD
  [13] pos_ogol   posição detalhada do oGol, ex.: "Lateral Direito Zagueiro"
  [14] caps_sel   jogos pela seleção principal (carreira toda)
  [15] gols_sel   gols pela seleção principal (carreira toda)
  [16] caps_base  jogos por seleções de base (carreira toda)
  [17] jc         jogos nesta Copa (None = não achei a tabela)
  [18] gols_copa  gols marcados nesta Copa
  [19] min_copa   minutos nesta Copa
  [20] gols_sof   gols sofridos nesta Copa (só goleiro; None para os demais)
  [21] titulos    dict {"Mundial de Clubes": 1, ...} (carreira toda)

O index.html lê só as 11 primeiras posições, então nada quebra.

Uso:
  python pegar_copas2.py --testar-arquivo "pagina_do_jogador.html" --ano 2022   # teste offline
  python pegar_copas2.py                       # todas as Copas que estão no copas.json
  python pegar_copas2.py --copas 2022 2026     # só estas
  python pegar_copas2.py --sem-cache

Pode interromper (Ctrl+C): o copas.json é salvo ao fim de cada Copa, e o cache evita baixar de novo.
Precisa estar na mesma pasta do pegar_copas.py e do copas.json.
"""
import argparse, json, re, sys
from bs4 import BeautifulSoup

try:
    import pegar_copas as pc   # reaproveita get(), selecoes(), autenticar_com_playwright(), COPAS
except ModuleNotFoundError as e:
    sys.exit(
        f"\nFaltou um módulo: {e.name}.\n"
        "- Se for 'pegar_copas': copie o pegar_copas.py (o original, não é o v2) para ESTA mesma pasta.\n"
        "- Se for 'playwright' ou 'bs4'/'requests': rode  pip install playwright beautifulsoup4 requests  "
        "e depois  python -m playwright install chromium\n"
    )

ARQ_JSON = "copas.json"
ARQ_JS = "copas.js"
VERSAO = 2
NUM_CAMPOS_V1 = 11
NOMES_COPA = {"FIFA World Cup", "Copa do Mundo"}


def _texto(soup):
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True))


def _int(x):
    try:
        return int(re.sub(r"\D", "", str(x)) or 0)
    except ValueError:
        return None


def links_elenco(soup):
    """{id_oGol: href da página do jogador}. Mesma regra de pid do pegar_copas.extrair_elenco."""
    corpo = soup.select_one("#team_squad") or soup.select_one(".team_squad")
    saida = {}
    if not corpo:
        return saida
    for el in corpo.select(".section, .staff, tr.parent"):
        if "section" in (el.get("class") or []):
            continue
        a = el.select_one('a[href*="/jogador/"], a[href*="/jogador.php"]')
        if not a:
            continue
        m = re.search(r"/jogador/([^/?#]+)(?:/(\d+))?", a["href"])
        if not m:
            continue
        pid = m.group(2) or m.group(1)
        saida.setdefault(pid, a["href"])
    return saida


def parse_pagina_jogador(soup, ano_esperado):
    """Lê a página do jogador no oGol. Devolve dict com carreira e os números da Copa de ano_esperado."""
    txt = _texto(soup)
    info = {
        "nasc": None, "pos_ogol": None, "caps_sel": None, "gols_sel": None, "caps_base": None,
        "jc": None, "gols_copa": None, "min_copa": None, "gols_sof": None, "titulos": {},
        "ano_pagina": None, "avisos": [],
    }

    m = re.search(r"Data de Nascimento\s+(\d{4}-\d{2}-\d{2})", txt)
    if m:
        info["nasc"] = m.group(1)

    m = re.search(r"Posição\s+(.+?)\s+Pé preferencial", txt)
    if m:
        info["pos_ogol"] = m.group(1).strip()

    m = re.search(r"Jogos pela seleção\s+(\d+)\s+Jogos\s*/\s*(\d+)\s+Gols", txt)
    if m:
        info["caps_sel"], info["gols_sel"] = int(m.group(1)), int(m.group(2))
    else:
        info["caps_sel"], info["gols_sel"] = 0, 0          # nunca defendeu a seleção principal

    m = re.search(r"Jogos por seleções de base\s+(\d+)\s+Jogos", txt)
    info["caps_base"] = int(m.group(1)) if m else 0

    # títulos: cada troféu é um div.trophy-icon com "Nome do título N"
    for el in soup.select("div.trophy-icon"):
        mt = re.match(r"^(.*\D)\s+(\d+)$", el.get_text(" ", strip=True))
        if mt:
            info["titulos"][mt.group(1).strip()] = int(mt.group(2))

    # ano da edição mostrada na página ("resumo da temporada Catar 2022 ...")
    m = re.search(r"resumo da temporada\s+(.*?)\s+(\d{4})", txt)
    if m:
        info["ano_pagina"] = int(m.group(2))
    edicao_errada = (info["ano_pagina"] is not None and ano_esperado
                     and info["ano_pagina"] != int(ano_esperado))
    if edicao_errada:
        pass   # a página mostra outra edição: a carreira vale, a tabela não (seria de outra Copa)

    # tabela da edição: linha "FIFA World Cup" / "Copa do Mundo" com J, M, GM (ou GC para goleiro)
    tabela_achada = False
    for tabela in ([] if edicao_errada else soup.select("table")):
        linhas = tabela.find_all("tr")
        if not linhas:
            continue
        cab = [c.get_text(" ", strip=True) for c in linhas[0].find_all(["th", "td"])]
        if "J" not in cab or "M" not in cab:
            continue
        tabela_achada = True
        idx = {nome: cab.index(nome) for nome in cab if nome in ("J", "M", "GM", "GC")}
        for tr in linhas[1:]:
            cel = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
            if not cel or cel[0] not in NOMES_COPA:
                continue
            info["jc"] = _int(cel[idx["J"]]) if "J" in idx else None
            info["min_copa"] = _int(cel[idx["M"]]) if "M" in idx else None
            if "GM" in idx:
                info["gols_copa"] = _int(cel[idx["GM"]])
            if "GC" in idx:                                   # tabela de goleiro: GC = gols sofridos
                info["gols_sof"] = _int(cel[idx["GC"]])
                if "GM" not in idx:
                    info["gols_copa"] = 0                     # goleiro não marca gol
            break
        if info["jc"] is not None:
            break

    # Sem linha de Copa = não entrou em campo. Vale para dois casos:
    #  - a página tem tabela mas não tem a linha da Copa;
    #  - a página não tem tabela nenhuma, mas é válida (tem data de nascimento): o oGol só monta
    #    a tabela para quem jogou. Só avisa se a página parecer incompleta (sem data de nascimento).
    if info["jc"] is None:
        if tabela_achada or info["nasc"]:
            info["jc"], info["gols_copa"], info["min_copa"] = 0, 0, 0
        else:
            info["avisos"].append("página incompleta (sem data de nascimento nem tabela): verifique à mão")
    return info


def url_jogador(href, id_ed):
    """Garante que o link da página do jogador aponta para a edição da Copa (edicao_id)."""
    if "edicao_id=" in href:
        return href
    return href + ("&" if "?" in href else "?") + f"edicao_id={id_ed}"


# rótulos do oGol (do mais longo para o mais curto) e o código do jogo
ROTULOS_POS = [
    ("Ponta Esquerda", "PE"), ("Ponta Direita", "PD"),
    ("Lateral Direito", "LD"), ("Lateral Esquerdo", "LE"),
    ("Meia Central", "MC"), ("Meia Ofensivo", "MEI"), ("Meia Direita", "MC"), ("Meia Esquerda", "MC"),
    ("2º Atacante", "SA"), ("Centroavante", "CA"), ("Atacante", "CA"),
    ("Zagueiro", "ZAG"), ("Defensor", "ZAG"), ("Líbero", "ZAG"),
    ("Volante", "VOL"), ("Goleiro", "GOL"), ("Meia", "MC"),
]


def codigo_posicao(texto):
    """Converte o texto do perfil do oGol no código do jogo. O texto lista a posição principal
    primeiro, e as secundárias depois, sem separador: vale o primeiro rótulo reconhecido.
    Ex.: 'Lateral Direito Zagueiro' -> LD ; 'Ponta Esquerda Centroavante' -> PE ; 'Volante' -> VOL."""
    t = (texto or "").strip()
    for rotulo, cod in ROTULOS_POS:
        if t.startswith(rotulo):
            return cod
    return None


def completar_linha(linha, info):
    """Acrescenta os campos v2 à linha (lista com 11 campos ou mais). Não mexe nos 11 primeiros."""
    while len(linha) < NUM_CAMPOS_V1:
        linha.append("")
    extra = [
        "",                       # 11 tm (cruzar_copas.py)
        info["nasc"],             # 12
        info["pos_ogol"],         # 13
        info["caps_sel"],         # 14
        info["gols_sel"],         # 15
        info["caps_base"],        # 16
        info["jc"],               # 17
        info["gols_copa"],        # 18
        info["min_copa"],         # 19
        info["gols_sof"],         # 20
        info["titulos"],          # 21
    ]
    linha[NUM_CAMPOS_V1:] = extra
    cod = codigo_posicao(info["pos_ogol"])
    if cod:
        linha[3] = cod                      # posição do jogo: código detalhado (GOL, ZAG, LD, ... SA, CA)
    return linha


def salvar(rows):
    txt = json.dumps({"v": VERSAO, "rows": rows}, ensure_ascii=False, separators=(",", ":"))
    with open(ARQ_JSON, "w", encoding="utf-8") as f:
        f.write(txt)
    with open(ARQ_JS, "w", encoding="utf-8") as f:
        f.write("window.COPAS_DATA=" + txt + ";")


def carregar():
    with open(ARQ_JSON, encoding="utf-8") as f:
        return json.load(f)["rows"]


def testar_arquivo(arq, ano):
    with open(arq, encoding="utf-8", errors="replace") as f:
        info = parse_pagina_jogador(BeautifulSoup(f.read(), "html.parser"), ano)
    print(json.dumps(info, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser(description="Completa o copas.json com dados de carreira e de cada Copa (oGol)")
    ap.add_argument("--copas", nargs="+", type=int, help="só estas Copas (padrão: as que estão no copas.json)")
    ap.add_argument("--testar-arquivo", metavar="HTML", help="testa o leitor numa página de jogador salva")
    ap.add_argument("--ano", type=int, help="ano da Copa para o --testar-arquivo")
    ap.add_argument("--sem-cache", action="store_true")
    ap.add_argument("--so-posicoes", action="store_true",
                    help="não baixa nada: só regrava o campo 3 (posição) do copas.json a partir do texto detalhado já salvo")
    ap.add_argument("--refazer", action="store_true",
                    help="relê TODAS as linhas, mesmo as que já têm dados (padrão: só as que faltam)")
    args = ap.parse_args()

    if args.testar_arquivo:
        testar_arquivo(args.testar_arquivo, args.ano)
        return

    if args.so_posicoes:
        rows = carregar()
        mudou = 0
        for r in rows:
            if len(r) > NUM_CAMPOS_V1 + 2 and r[13]:
                cod = codigo_posicao(r[13])
                if cod and r[3] != cod:
                    r[3] = cod
                    mudou += 1
        salvar(rows)
        print(f"{mudou} posições atualizadas de {len(rows)} linhas. copas.json e copas.js regravados.")
        return

    pc.USAR_CACHE = not args.sem_cache
    rows = carregar()
    for r in rows:
        while len(r) < NUM_CAMPOS_V1:
            r.append("")
    indice = {(str(r[7]), int(r[2]), r[1]): r for r in rows}
    anos = args.copas or sorted({int(r[2]) for r in rows})

    def pronta(linha):
        return len(linha) > NUM_CAMPOS_V1 + 6 and linha[NUM_CAMPOS_V1 + 6] is not None  # jc = campo 17

    pendentes = sum(1 for r in rows if args.refazer or not pronta(r))
    print(f"{len(rows)} linhas no copas.json, {pendentes} para processar agora")
    if pendentes == 0:
        print("Nada a fazer: todas as linhas já têm os dados da v2. Use --refazer para reler tudo.")
        return
    # seleções que ainda têm algum jogador pendente (as outras são puladas sem nem abrir o elenco)
    com_pendencia = {(int(r[2]), r[1]) for r in rows if args.refazer or not pronta(r)}

    pc.autenticar_com_playwright()          # só abre o navegador se houver algo a baixar
    falhas = 0
    for ano in anos:
        id_ed, slug, _ = pc.COPAS[ano]
        if not any(a == ano for a, _ in com_pendencia):
            continue
        print(f"== Copa {ano}")
        for nome, href_sel in pc.selecoes(id_ed, slug):
            if (ano, nome) not in com_pendencia:
                continue                    # seleção já completa: não abre nada dela
            soup = pc.get(href_sel)
            if not soup:
                continue
            for pid, href in links_elenco(soup).items():
                linha = indice.get((pid, ano, nome))
                if linha is None:
                    continue
                if not args.refazer and pronta(linha):
                    continue                # já tem os dados: não lê a página de novo
                url = url_jogador(href, id_ed)
                ps = pc.get(url)
                if not ps:
                    falhas += 1
                    continue
                info = parse_pagina_jogador(ps, ano)
                completar_linha(linha, info)
                if info["avisos"]:
                    print(f"  ! {linha[0]} ({nome}): {'; '.join(info['avisos'])}")
            print(f"  {nome}: ok")
        salvar(rows)
        print(f"  copas.json salvo ({len(rows)} linhas)")

    print(f"\nFinalizado. Falhas de download: {falhas}. Próximo passo: python cruzar_copas.py")


if __name__ == "__main__":
    sys.exit(main())
