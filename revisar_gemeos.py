"""Confere a coleta do Wikidata contra fichas e tabelas da Wikipedia inglesa.

python revisar_gemeos.py             # revisa a lista ja coletada, com cache
python revisar_gemeos.py --offline   # refaz a revisao sem acessar a rede

Mantem gemeos.json intacto. Gera gemeos_revisados.json/.js e REVISAO_GEMEOS.md.
Estatisticas de liga e de todas as competicoes sao campos diferentes. Uma soma
consistente numa fonte secundaria nao equivale a confirmacao por fonte oficial.
"""
import argparse
import re
import sys
from urllib.parse import quote
from urllib.parse import unquote

from bs4 import BeautifulSoup

import pegar_gemeos as g

WIKIPEDIA = "https://en.wikipedia.org/w/api.php"
CACHE = g.AQUI / "cache/gemeos/revisao"
# Conferencias pontuais externas ao par Wikipedia/Wikidata. O escopo e explicito:
# uma estatistica institucional de clube nao vira automaticamente total oficial.
CONFERENCIAS = {
    "Q12897": [{"clube": "New York Cosmos", "jogos": 64, "gols": 37,
                 "escopo": "NASL, liga e playoffs", "fonte": "https://www.ussoccerhistory.org/national-soccer-hall-of-fame-biographies/national-soccer-hall-of-fame-player-biographies/pele/",
                 "nota": "O registro 65 jogos/111 gols do Wikidata nao foi utilizado."}],
    "Q164546": [{"clube": "Real Madrid", "jogos": 396, "gols": 308, "escopo": "partidas oficiais pelo clube",
                  "fonte": "https://www.realmadrid.com/en-US/the-club/history/football-legends/alfredo-di-stefano-laulhe",
                  "nota": "O clube confirma a estreia profissional no River Plate, corrigindo o vinculo ao Boca na coleta."}],
    "Q20110": [{"clube": "Roma", "jogos": 786, "gols": 307, "escopo": "partidas oficiais pelo clube",
                "fonte": "https://www.asroma.com/en/club/history/hall-of-fame/15259/francesco-totti"}],
    "Q483027": [{"clube": "Milan", "jogos": 902, "escopo": "partidas oficiais pelo clube",
                 "fonte": "https://www.acmilan.com/en/club/legends/players/paolo-maldini"}],
    "Q189984": [{"clube": "Milan", "jogos": 719, "gols": 33, "escopo": "partidas oficiais pelo clube",
                 "fonte": "https://www.acmilan.com/en/hall-of-fame/inductees/franco-baresi"}],
    "Q10524": [{"clube": "Manchester United", "jogos": 963, "gols": 168, "escopo": "partidas oficiais pelo clube",
                "fonte": "https://www.thefa.com/news/2014/may/19/ryan-giggs-retirement-greg-dyke"}],
    "Q342474": [{"clube": "Palmeiras", "jogos": 533, "escopo": "contagem institucional do clube",
                 "fonte": "https://www.palmeiras.com.br/craques/marcos/"}],
    "Q1249859": [{"clube": "Sao Paulo", "jogos": 1237, "gols": 131, "escopo": "contagem institucional do clube",
                  "fonte": "https://www.saopaulofc.net/o-clube/grandes-idolos/",
                  "nota": "A tabela secundaria informa outros numeros/criterios. Nao produzir total unico sem reconciliar amistosos e demais competicoes."}],
    "Q180642": [{"selecao": "Brasil", "jogos": 50, "gols": 12, "escopo": "selecao principal, internacionais reconhecidos",
                 "fonte": "https://www.rsssf.org/miscellaneous/garrincha-intl.html",
                 "nota": "O Wikidata informava 17 gols; a revisao usa 12."}],
    "Q167828": [{"selecao": "Uniao Sovietica", "jogos": 74, "gols": 0, "escopo": "selecao principal, internacionais reconhecidos",
                 "fonte": "https://www.rsssf.org/miscellaneous/yashin-intl.html",
                 "nota": "O Wikidata informava 78 jogos; a revisao separa a equipe olimpica."}],
}


def texto(node):
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()


def numero(value):
    value = value.strip().strip("()").strip().replace(",", "").replace("\xa0", "")
    return int(value) if re.fullmatch(r"\d+", value) else None


def extrair(html, title, revision):
    soup = BeautifulSoup(html, "html.parser")
    for note in soup.select("sup.reference, .sortkey"):
        note.decompose()
    source = {"url": "https://en.wikipedia.org/wiki/" + quote(title.replace(" ", "_")),
              "revisao": revision, "licenca": "CC BY-SA; estatisticas factuais com fonte indicada"}
    box = soup.select_one("table.infobox")
    if not box:
        raise ValueError("Ficha do jogador nao encontrada")
    section, clubs, youth, national, total = None, [], [], [], None
    position = None
    for row in box.find_all("tr"):
        cells = row.find_all(["th", "td"], recursive=False)
        if not cells or any(c.find("table") for c in cells):
            continue
        labels = [texto(c) for c in cells]
        if len(cells) == 1:
            header = labels[0].lower()
            if "senior career" in header:
                section = "clubes"
            elif "youth career" in header:
                section = "base"
            elif "international career" in header:
                section = "selecoes"
            elif "managerial career" in header or "medal record" in header or "club domestic" in header:
                section = None
            continue
        if re.fullmatch(r"Position(?:s|\(s\))?", labels[0]):
            position = labels[1]
        if section == "base" and len(cells) == 2 and re.search(r"\d{4}", labels[0]):
            youth.append({"periodo": labels[0], "clube": labels[1]})
        if section not in ("clubes", "selecoes") or len(cells) != 4:
            continue
        if labels[0] == "Total" and section == "clubes":
            total = {"jogos": numero(labels[2]), "gols": numero(labels[3])}
            continue
        if not re.search(r"\d{4}", labels[0]):
            continue
        link = next((a for a in cells[1].select("a[href]") if a["href"].startswith("/wiki/")), None)
        years = [int(n) for n in re.findall(r"\d{4}", labels[0])]
        item = {"nome": labels[1].lstrip("→ "), "periodo": labels[0],
                "inicio": years[0], "fim": years[-1], "emprestimo": "loan" in labels[1].lower(),
                "pagina": "https://en.wikipedia.org" + link["href"] if link else None,
                "jogos": numero(labels[2]), "gols": numero(labels[3])}
        if section == "selecoes":
            name = (item["nome"] + " " + (item["pagina"] or "")).lower()
            item["categoria"] = "alternativa" if re.search(
                r"under[ _-]?\d+|u[ -]?\d{2}\b|olympic|amateur|beach|_b(?:_|\b)|\bb\b|great britain|catalonia", name
            ) else "principal"
            national.append(item)
        else:
            name = item["nome"]
            item["categoria"] = "reserva" if re.search(r"\s(?:II|B|C)(?:\s*\(loan\))?$|Castilla|reserves", name, re.I) else "principal"
            clubs.append(item)
    if not clubs:
        raise ValueError("Nenhuma passagem profissional extraida; formato nao reconhecido")
    if total is None and all(p["jogos"] is not None and p["gols"] is not None for p in clubs):
        total = {"jogos": sum(p["jogos"] for p in clubs), "gols": sum(p["gols"] for p in clubs),
                 "origem": "soma_das_passagens_da_ficha"}
    league_ok = bool(total and all(p["jogos"] is not None and p["gols"] is not None for p in clubs)
                     and sum(p["jogos"] for p in clubs) == total["jogos"]
                     and sum(p["gols"] for p in clubs) == total["gols"])
    candidates = []
    for table in soup.select("table.wikitable"):
        rows = table.find_all("tr")
        header = " ".join(texto(r) for r in rows[:3]).lower()
        if not ("club" in header and "league" in header and
                re.search(r"cup|coppa|pokal|europe|continental|regional", header) and "total" in header):
            continue
        table_clubs = {unquote(a["href"].split("#", 1)[0]) for a in table.select("a[href]")}
        missing_clubs = [p["nome"] for p in clubs if p["categoria"] == "principal" and p["pagina"] and
                         unquote(p["pagina"].replace("https://en.wikipedia.org", "").split("#", 1)[0]) not in table_clubs]
        single_club = len({p["pagina"] for p in clubs if p["categoria"] == "principal"}) == 1
        for row in rows:
            cells = row.find_all(["th", "td"], recursive=False)
            if not cells or not (re.fullmatch(r"(?:Senior )?Career total", texto(cells[0]), re.I) or
                                 single_club and texto(cells[0]) == "Total"):
                continue
            labels = [texto(c) for c in cells[1:]]
            numbers = [0 if t in ("–", "—", "-") else numero(t) for t in labels]
            ok = len(numbers) >= 6 and len(numbers) % 2 == 0 and all(n is not None for n in numbers)
            ok = ok and sum(numbers[:-2:2]) == numbers[-2] and sum(numbers[1:-2:2]) == numbers[-1]
            lower_bound = {k: sum(p[k] or 0 for p in clubs if p["categoria"] == "principal") for k in ("jogos", "gols")}
            scope_ok = bool(ok and not missing_clubs and numbers[-2] >= lower_bound["jogos"] and numbers[-1] >= lower_bound["gols"])
            candidates.append({"jogos": numero(labels[-2]) if len(labels) >= 2 else None,
                               "gols": numero(labels[-1]) if labels else None,
                               "somaConsistente": bool(ok), "coberturaCompativel": scope_ok,
                               "clubesAusentes": missing_clubs, "linha": labels, "cabecalho": header})
    consistent = [c for c in candidates if c["somaConsistente"] and c["coberturaCompativel"]]
    unique = {(c["jogos"], c["gols"]) for c in consistent}
    all_stats = None
    if len(unique) == 1:
        games, goals = next(iter(unique))
        all_stats = {"jogos": games, "gols": goals, "escopo": "competicoes_da_tabela_de_clubes",
                     "status": "fonte_secundaria_soma_consistente", "fonte": source}
    warnings = []
    if total and not league_ok:
        warnings.append("Total da ficha nao confere com todas as passagens ou ha numeros ausentes.")
    if not all_stats:
        warnings.append("Total em todas as competicoes nao aprovado: tabela ausente, inconsistente ou ambigua.")
    if candidates and any(not c["somaConsistente"] for c in candidates):
        warnings.append("Existe tabela com soma inconsistente; os numeros dessa tabela nao foram aprovados.")
    if any(not c["coberturaCompativel"] for c in candidates):
        warnings.append("Tabela com cobertura incompleta ou total inferior aos numeros da ficha: nao usar como carreira completa.")
    return {"fonte": source, "posicao": position, "clubes": clubs, "base": youth,
            "selecoes": national, "totalFichaLigas": total, "somaFichaLigasConfere": league_ok,
            "estatisticasClubes": all_stats, "tabelasEncontradas": candidates, "avisos": warnings}


def conferir_original(raw, wiki):
    issues = []
    if any(p["tipo"] == "nao_classificado" for p in raw["passagens"]):
        issues.append("classificacao_incompleta_no_wikidata")
    senior = wiki["clubes"]
    for passage in raw["passagens"]:
        if passage["tipo"] != "nao_classificado":
            continue
        matches = [p for p in senior if passage["inicio"] is not None and p["inicio"] == passage["inicio"]
                   and passage["fim"] is not None and p["fim"] == passage["fim"]]
        for match in matches:
            if (passage["jogos"] is not None and passage["gols"] is not None and
                (passage["jogos"], passage["gols"]) != (match["jogos"], match["gols"])):
                issues.append({"tipo": "numeros_divergentes_ou_escopos_distintos", "periodo": match["periodo"],
                               "wikidata": {"clube": passage["clube"]["nome"], "jogos": passage["jogos"], "gols": passage["gols"]},
                               "wikipediaFichaLigas": {"clube": match["nome"], "jogos": match["jogos"], "gols": match["gols"]}})
    return issues


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    raw = g.ler_json(g.AQUI / "gemeos.json", {"rows": {}})["rows"]
    if not raw:
        raise ValueError("Nao ha jogadores em gemeos.json")
    CACHE.mkdir(parents=True, exist_ok=True)
    api = g.Api(g.AQUI / "cache/gemeos", offline=args.offline)
    titles = g.ler_json(CACHE / "titulos.json", {})
    missing = [q for q in raw if q not in titles]
    for offset in range(0, len(missing), 50):
        data = api.get(g.WIKIDATA, {"action": "wbgetentities", "ids": "|".join(missing[offset:offset+50]),
                                  "props": "sitelinks", "sitefilter": "enwiki"})
        for q, e in data.get("entities", {}).items():
            title = e.get("sitelinks", {}).get("enwiki", {}).get("title")
            if title:
                titles[q] = title
        g.salvar_json(CACHE / "titulos.json", titles)
    reviewed = g.ler_json(g.AQUI / "gemeos_revisados.json", {"rows": {}}).get("rows", {})
    if not isinstance(reviewed, dict):
        raise ValueError("A base revisada existente tem formato invalido; ela foi preservada.")
    failures = []
    for i, (qid, row) in enumerate(raw.items(), 1):
        print(f"[{i}/{len(raw)}] {row['nome']}", flush=True)
        try:
            path = CACHE / (qid + ".json")
            data = g.ler_json(path, None)
            if data is None:
                data = api.get(WIKIPEDIA, {"action": "parse", "page": titles[qid], "redirects": 1,
                                          "prop": "text|revid", "formatversion": 2})
                g.salvar_json(path, data)
            parsed = data["parse"]
            wiki = extrair(parsed["text"], parsed["title"], parsed.get("revid"))
            # Casos cujo contexto nao cabe no nome da equipe ou na ficha resumida.
            for selection in wiki["selecoes"]:
                if qid == "Q164546" and selection["nome"] == "Colombia":
                    selection["categoria"] = "nao_fifa"
                if selection["nome"] in ("Castile", "Catalonia"):
                    selection["categoria"] = "regional"
                if qid == "Q4261" and selection["nome"] == "Kuwait":
                    selection["categoria"] = "participacao_excepcional_criterio_pendente"
            for passage in wiki["clubes"]:
                if qid == "Q45613" and passage["nome"] == "Royton Town":
                    passage["categoria"] = "amador_pos_aposentadoria"
            if qid == "Q1249859":
                wiki["estatisticasClubes"] = None
                wiki["avisos"].append("Contagem institucional do Sao Paulo diverge da tabela: total de carreira bloqueado ate reconciliar os criterios.")
            wiki["divergencias"] = conferir_original(row, wiki)
            reviewed[qid] = {"id": qid, "nome": row["nome"], "transfermarktId": row["transfermarktId"],
                             "foto": row["foto"], "nacionalidades": row["nacionalidades"], **wiki,
                             "titulos": None, "statusTitulos": "nao_conferidos",
                             "conferenciasExternas": CONFERENCIAS.get(qid, []),
                             "statusRevisao": "conferido_com_fonte_secundaria"}
            if not row.get("foto") or not all(row["foto"].get(k) for k in ("autor", "licenca", "pagina")):
                reviewed[qid]["avisos"].append("Foto com creditos incompletos; conferir antes de exibir.")
        except (KeyError, ValueError, g.requests.RequestException, RuntimeError) as exc:
            failures.append({"id": qid, "nome": row["nome"], "erro": str(exc)})
            print(f"  Pendente: {exc}", flush=True)
    api.session.close()
    result = {"v": 1, "gerado": g.agora(), "nota": "Liga e todas as competicoes sao escopos diferentes; estatisticas nao confirmadas permanecem desconhecidas.",
              "rows": reviewed, "falhas": failures}
    # A saida original e seu cache ficam intactos, permitindo auditar cada diferenca.
    g.salvar_json(g.AQUI / "gemeos_revisados.json", result)
    g.salvar_json(g.AQUI / "gemeos_revisados.js", result, "window.GEMEOS_REVISADOS=")
    lines = ["# Revisão dos Gêmeos de Carreira", "", f"Revisado em {result['gerado']}.", "",
             "Os 50 registros originais do Wikidata foram preservados em `gemeos.json`. Esta revisão usa as fichas e tabelas da Wikipédia em inglês como segunda fonte, com revisão identificada. Concordância entre essas fontes não equivale a confirmação oficial independente.", "",
             "As passagens profissionais, base e seleções estão separadas. As fichas contabilizam ligas domésticas, conforme os critérios de cada artigo. Somente tabelas de clubes com total explícito e soma consistente são candidatas a totais de todas as competições. Títulos coletivos ainda não foram aprovados.", "",
             "| Jogador | Clubes/passagens profissionais | Seleções principais | Total da tabela de clubes (J/G) | Soma da ficha de liga | Observações | Fonte |",
             "|---|---:|---|---|---|---|---|"]
    for row in reviewed.values():
        stats = row["estatisticasClubes"]
        national = "; ".join(f"{p['nome']}: {p['jogos']}/{p['gols']}" for p in row["selecoes"] if p["categoria"] == "principal")
        total = f"{stats['jogos']}/{stats['gols']}" if stats else "Não aprovado"
        professional = sum(p["categoria"] in ("principal", "reserva") for p in row["clubes"])
        lines.append(f"| {row['nome']} | {professional} | {national or 'Ausente'} | {total} | {'Confere' if row['somaFichaLigasConfere'] else 'Pendente'} | {' '.join(row['avisos'])} | [Artigo]({row['fonte']['url']}?oldid={row['fonte']['revisao']}) |")
    lines.extend(["", "## Conferências externas e correções relevantes", ""])
    for row in reviewed.values():
        for check in row["conferenciasExternas"]:
            numbers = f"{check['jogos']} jogos" + (f", {check['gols']} gols" if "gols" in check else "")
            lines.append(f"- **{row['nome']} — {check.get('clube', check.get('selecao'))}:** {numbers}; {check['escopo']}. [Fonte]({check['fonte']}). {check.get('nota', '')}")
    if failures:
        lines.extend(["", "## Falhas de coleta/revisão", ""] + [f"- {f['nome']}: {f['erro']}" for f in failures])
    (g.AQUI / "REVISAO_GEMEOS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nRevisados: {len(reviewed)} | falhas: {len(failures)} | totais de clubes consistentes: {sum(bool(r['estatisticasClubes']) for r in reviewed.values())}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
