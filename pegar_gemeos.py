"""Coletor independente dos Gemeos de Carreira: Wikidata + fotos do Commons.

Nao acessa o Transfermarkt e nao modifica dados.js, gols.json ou historico.json.
Usa requests (ja usado pelos outros coletores). Execute de qualquer pasta:

  python pegar_gemeos.py                       # selecao inicial de 50 aposentados
  python pegar_gemeos.py --ids Q12897 Q47526   # Pele e Zico
  python pegar_gemeos.py --lista jogadores.txt # um QID por linha
  python pegar_gemeos.py --atualizar           # atualiza inclusive os ja coletados
  python pegar_gemeos.py --offline             # reconstroi usando apenas o cache

Saidas: gemeos.json, gemeos.js e gemeos_relatorio.json, ao lado deste script.
Os arquivos ainda precisam ser integrados ao jogo; nao alteram o album.
Estatisticas por passagem sao registros da fonte, nao totais completos da carreira.
Premios individuais do Wikidata NAO sao um inventario de titulos coletivos.
"""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from email.utils import parsedate_to_datetime
import html
import json
from pathlib import Path
import re
import sys
import time

import requests

AQUI = Path(__file__).resolve().parent
WIKIDATA = "https://www.wikidata.org/w/api.php"
COMMONS = "https://commons.wikimedia.org/w/api.php"
# IDs conferidos pela API de pageprops da Wikipedia em 2026-11-03.
INICIAIS = {
    "Q12897": "Pele", "Q47526": "Zico", "Q178649": "Romario",
    "Q17163": "Johan Cruyff", "Q17515": "Diego Maradona", "Q180642": "Garrincha",
    "Q529207": "Ronaldo", "Q39444": "Ronaldinho", "Q483577": "Rivaldo",
    "Q531814": "Kaka", "Q204825": "Bebeto", "Q67964": "Roberto Baggio",
    "Q20110": "Francesco Totti", "Q624": "Alessandro Del Piero",
    "Q483027": "Paolo Maldini", "Q189984": "Franco Baresi",
    "Q102027": "Fabio Cannavaro", "Q429039": "Roberto Carlos", "Q178683": "Cafu",
    "Q172720": "Dani Alves", "Q295262": "Carlos Alberto Torres", "Q215890": "Dunga",
    "Q203451": "Juninho Pernambucano", "Q507815": "Alex",
    "Q342474": "Marcos", "Q1249859": "Rogerio Ceni", "Q188544": "Dida",
    "Q68060": "Gianluigi Buffon", "Q11584": "Iker Casillas", "Q131261": "Oliver Kahn",
    "Q167828": "Lev Yashin", "Q182314": "Peter Schmeichel", "Q1835": "Zinedine Zidane",
    "Q4261": "Michel Platini", "Q45901": "Thierry Henry", "Q170328": "Eric Cantona",
    "Q10520": "David Beckham", "Q459830": "Steven Gerrard", "Q41533": "Frank Lampard",
    "Q45613": "Paul Scholes", "Q10524": "Ryan Giggs", "Q483583": "Alan Shearer",
    "Q266613": "Wayne Rooney", "Q48892": "Didier Drogba", "Q1255625": "Samuel Eto'o",
    "Q173139": "George Weah", "Q483145": "Luis Figo", "Q162043": "Eusebio",
    "Q482931": "Ferenc Puskas", "Q164546": "Alfredo Di Stefano",
}
PROPRIEDADES = {"P18", "P27", "P1532", "P413", "P54", "P166", "P2446"}


def agora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def salvar_json(caminho, dados, prefixo=""):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_name(caminho.name + ".tmp")
    texto = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    tmp.write_text(prefixo + texto + (";" if prefixo else ""), encoding="utf-8")
    tmp.replace(caminho)


def ler_json(caminho, padrao):
    try:
        return json.loads(Path(caminho).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return padrao
    except (OSError, ValueError) as e:
        # Um arquivo existente danificado nao pode ser tratado como uma base vazia.
        raise ValueError(f"Nao foi possivel ler {caminho}: {e}") from e


def valor(snak):
    return snak.get("datavalue", {}).get("value")


def valores(entity, prop):
    return [valor(c["mainsnak"]) for c in entity.get("claims", {}).get(prop, [])
            if c.get("rank") != "deprecated" and valor(c.get("mainsnak", {})) is not None]


def qids(values):
    return [v["id"] for v in values if isinstance(v, dict) and "id" in v]


def rotulo(entity, fallback=""):
    labels = entity.get("labels", {})
    return (labels.get("pt") or labels.get("en") or next(iter(labels.values()), {})).get("value", fallback)


class Api:
    """Um cliente com conexoes reutilizadas, cache por entidade e tentativas limitadas."""
    def __init__(self, cache, atualizar=False, offline=False):
        self.cache = Path(cache)
        self.atualizar, self.offline = atualizar, offline
        self.session = requests.Session()
        self.session.headers["User-Agent"] = (
            "QuemEOCraque-Gemeos/1.0 (local data importer; https://github.com/daniellg2/quem-e-o-craque)"
        )
        self.requisicoes = 0
        self.falhas = []

    def get(self, url, params):
        if self.offline:
            raise RuntimeError("Modo offline: resposta ausente no cache")
        for tentativa in range(3):
            espera = 2 ** (tentativa + 1)
            try:
                self.requisicoes += 1
                r = self.session.get(url, params={"format": "json", "maxlag": 5, **params},
                                     timeout=(8, 35))
                if r.status_code in (429, 500, 502, 503, 504):
                    retry = r.headers.get("Retry-After", "")
                    if retry.isdigit():
                        espera = int(retry)
                    elif retry:
                        try:
                            espera = max(espera, (parsedate_to_datetime(retry) -
                                                 datetime.now(timezone.utc)).total_seconds())
                        except (ValueError, TypeError):
                            pass
                    raise requests.ConnectionError(f"HTTP {r.status_code}")
                # Um 403 nao dispara novas tentativas que poderiam agravar o bloqueio.
                r.raise_for_status()
                if r.status_code != 200:
                    raise ValueError(f"HTTP {r.status_code}: resposta nao confirmada")
                data = r.json()
                if "error" in data:
                    error = data["error"]
                    if error.get("code") in ("maxlag", "ratelimited", "readonly"):
                        raise requests.ConnectionError(error.get("info", error["code"]))
                    raise ValueError(f"API: {error.get('code')}: {error.get('info')}")
                return data
            except (requests.Timeout, requests.ConnectionError) as e:
                if tentativa == 2:
                    raise
                print(f"  Rede temporariamente indisponivel ({e}); nova tentativa em {min(espera, 45):.0f}s.", flush=True)
                time.sleep(min(espera, 45))

    def entidades(self, ids, completas=True):
        ids = list(dict.fromkeys(ids))
        result, pendentes = {}, []
        for qid in ids:
            path = self.cache / ("entidades" if completas else "rotulos") / (qid + ".json")
            # O cache completo tambem serve para resolver nomes.
            full = self.cache / "entidades" / (qid + ".json")
            cached = ler_json(full if not completas and full.exists() else path, None)
            if cached:
                result[qid] = cached
            if not cached or (self.atualizar and not self.offline):
                pendentes.append(qid)
        tamanho = 25 if completas else 50
        for offset in range(0, len(pendentes), tamanho):
            lote = pendentes[offset:offset + tamanho]
            print(f"  API: {len(lote)} {'entidades' if completas else 'nomes'} em uma consulta...", flush=True)
            try:
                params = {"action": "wbgetentities", "ids": "|".join(lote),
                          "props": "labels|claims" if completas else "labels"}
                if completas:
                    params["languages"] = "pt|en"
                data = self.get(WIKIDATA, params)
                entities = data.get("entities")
                if not isinstance(entities, dict):
                    raise ValueError("API retornou entidades em formato inesperado")
                for qid in lote:
                    entity = entities.get(qid, {})
                    if not entity or "missing" in entity:
                        self.falhas.append({"id": qid, "erro": "Entidade ausente"})
                        continue
                    thin = {"id": qid, "labels": entity.get("labels", {}), "lastrevid": entity.get("lastrevid"),
                            "coletado": agora()}
                    if completas:
                        thin["claims"] = {k: v for k, v in entity.get("claims", {}).items() if k in PROPRIEDADES}
                    salvar_json(self.cache / ("entidades" if completas else "rotulos") / (qid + ".json"), thin)
                    result[qid] = thin
            except (requests.RequestException, ValueError, RuntimeError) as e:
                print(f"  Lote nao atualizado: {e}", flush=True)
                self.falhas.append({"ids": lote, "erro": str(e)})
        return result

    def fotos(self, arquivos):
        arquivos = list(dict.fromkeys(arquivos))
        result, pendentes = ler_json(self.cache / "fotos.json", {}), []
        for arquivo in arquivos:
            # Um unico indice evita usar nomes de arquivos externos como caminhos locais.
            if arquivo not in result or (self.atualizar and not self.offline):
                pendentes.append(arquivo)
        for offset in range(0, len(pendentes), 20):
            lote = pendentes[offset:offset + 20]
            print(f"  Commons: {len(lote)} fotos e creditos em uma consulta...", flush=True)
            try:
                data = self.get(COMMONS, {"action": "query", "titles": "|".join("File:" + f for f in lote),
                                         "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": 240,
                                         "redirects": 1})
                query = data.get("query")
                if not isinstance(query, dict) or not isinstance(query.get("pages"), dict):
                    raise ValueError("Commons retornou fotos em formato inesperado")
                aliases = {x["from"]: x["to"] for x in query.get("normalized", []) + query.get("redirects", [])}
                pages = {p["title"]: p for p in query["pages"].values()}
                for arquivo in lote:
                    title, vistos = "File:" + arquivo, set()
                    while title in aliases and title not in vistos:
                        vistos.add(title)
                        title = aliases[title]
                    infos = pages.get(title, {}).get("imageinfo", [])
                    if not infos:
                        self.falhas.append({"foto": arquivo, "erro": "Arquivo sem imageinfo no Commons"})
                        continue
                    info, meta = infos[0], infos[0].get("extmetadata", {})
                    clean = lambda k: html.unescape(re.sub(r"<[^>]+>", "", meta.get(k, {}).get("value", ""))).strip()
                    result[arquivo] = {"arquivo": arquivo, "url": info.get("thumburl", info.get("url")),
                                       "pagina": info.get("descriptionurl"), "autor": clean("Artist"),
                                       "licenca": clean("LicenseShortName"), "licencaUrl": clean("LicenseUrl"),
                                       "credito": clean("Credit"), "restricoes": clean("Restrictions")}
                salvar_json(self.cache / "fotos.json", result)
            except (requests.RequestException, ValueError, RuntimeError) as e:
                self.falhas.append({"fotos": lote, "erro": str(e)})
                print(f"  Fotos nao atualizadas: {e}", flush=True)
        return result


def quantidade(snaks):
    numbers = set()
    for snak in snaks:
        raw = valor(snak)
        if not isinstance(raw, dict) or raw.get("unit") != "1":
            continue
        try:
            number = Decimal(raw["amount"])
            if number.is_finite() and number >= 0 and number == int(number):
                numbers.add(int(number))
        except (KeyError, InvalidOperation, ValueError, OverflowError):
            pass
    return next(iter(numbers)) if len(numbers) == 1 else None


def ano(snaks):
    years = set()
    for snak in snaks:
        raw = valor(snak)
        if isinstance(raw, dict) and raw.get("precision", 0) >= 9:
            match = re.match(r"\+(\d{4})-", raw.get("time", ""))
            if match:
                years.add(int(match[1]))
    return next(iter(years)) if len(years) == 1 else None


def referencias(claim):
    urls = set()
    for ref in claim.get("references", []):
        snaks = ref.get("snaks", {})
        urls.update(v for v in (valor(s) for s in snaks.get("P854", [])) if isinstance(v, str))
        urls.update("https://www.wikidata.org/wiki/" + q for q in qids([valor(s) for s in snaks.get("P248", [])]))
    return sorted(urls)


def ids_relacionados(entity):
    ids = set()
    for prop in ("P27", "P1532", "P413", "P54", "P166"):
        ids.update(qids(valores(entity, prop)))
    for claim in entity.get("claims", {}).get("P54", []):
        if claim.get("rank") == "deprecated":
            continue
        for prop in ("P5102", "P2094", "P118"):
            ids.update(qids([valor(s) for s in claim.get("qualifiers", {}).get(prop, [])]))
    return ids


def montar(entity, relacionados, fotos):
    qid = entity["id"]
    describe = lambda q: {"id": q, "nome": rotulo(relacionados.get(q, {}), q)}
    imagem = next(iter(valores(entity, "P18")), None)
    passagens, warnings = [], []
    for claim in entity.get("claims", {}).get("P54", []):
        team = valor(claim.get("mainsnak", {}))
        if claim.get("rank") == "deprecated" or not isinstance(team, dict) or "id" not in team:
            continue
        qualifiers = claim.get("qualifiers", {})
        nome = describe(team["id"])["nome"]
        classes = qids([valor(s) for s in qualifiers.get("P2094", [])])
        tipo = "base" if "Q599867" in classes or re.search(r"\b(under-?\d+|sub-?\d+|youth)\b", nome, re.I) else "nao_classificado"
        if tipo != "base" and re.search(r"national.*team|sele[cç][aã]o", nome, re.I):
            tipo = "selecao"
        passagens.append({"clube": describe(team["id"]), "tipo": tipo,
                          "inicio": ano(qualifiers.get("P580", [])), "fim": ano(qualifiers.get("P582", [])),
                          "jogos": quantidade(qualifiers.get("P1350", [])),
                          "gols": quantidade(qualifiers.get("P1351", [])),
                          "escopo": [describe(q) for p in ("P5102", "P2094", "P118")
                                     for q in qids([valor(s) for s in qualifiers.get(p, [])])],
                          "declaracao": claim.get("id"), "referencias": referencias(claim)})
    passagens.sort(key=lambda p: (p["inicio"] is None, p["inicio"] or 0, p["clube"]["id"]))
    ids = [p["clube"]["id"] for p in passagens]
    if len(ids) != len(set(ids)):
        warnings.append("Ha retornos ou registros repetidos do mesmo time; nao somar sem conferir os periodos.")
    warnings.append("Numeros por passagem podem ter escopos diferentes e precisam de revisao antes de virar totais.")
    if not passagens:
        warnings.append("Sem trajetoria disponivel.")
    foto = fotos.get(imagem)
    if imagem and (not foto or not foto.get("licenca") or not foto.get("pagina")):
        warnings.append("Foto ainda sem metadados completos de licenca/creditos.")
    return {"id": qid, "nome": rotulo(entity, INICIAIS.get(qid, qid)),
            "transfermarktId": next(iter(valores(entity, "P2446")), None),
            "nacionalidades": [describe(q) for q in qids(valores(entity, "P1532") or valores(entity, "P27"))],
            "posicoes": [describe(q) for q in qids(valores(entity, "P413"))],
            "passagens": passagens,
            "premios": [{**describe(v["id"]), "referencias": referencias(c)}
                        for c in entity.get("claims", {}).get("P166", [])
                        if c.get("rank") != "deprecated" and isinstance(v := valor(c.get("mainsnak", {})), dict) and "id" in v],
            "titulos": None, "totaisCarreira": None, "foto": foto, "arquivoFoto": imagem,
            "revisaoPendente": True, "avisos": warnings,
            "fonte": {"url": "https://www.wikidata.org/wiki/" + qid,
                      "revisao": entity.get("lastrevid"), "coletado": entity.get("coletado")}}


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ids", nargs="+", help="IDs do Wikidata, como Q12897 (nao IDs do Transfermarkt)")
    ap.add_argument("--lista", type=Path, help="arquivo de QIDs, um por linha; # inicia comentario")
    ap.add_argument("--limite", type=int, help="limita a selecao de jogadores")
    ap.add_argument("--saida", type=Path, default=AQUI / "gemeos.json")
    ap.add_argument("--cache", type=Path, default=AQUI / "cache" / "gemeos")
    ap.add_argument("--atualizar", action="store_true", help="consulta novamente inclusive registros existentes")
    ap.add_argument("--offline", action="store_true", help="usa apenas os arquivos locais, sem rede")
    ap.add_argument("--sem-fotos", action="store_true", help="pula a consulta dos metadados das fotos")
    args = ap.parse_args(argv)
    if args.saida.suffix.lower() != ".json":
        ap.error("--saida precisa terminar em .json")
    if args.limite is not None and args.limite < 1:
        ap.error("--limite precisa ser maior que zero")
    ids = list(args.ids or [])
    if args.lista:
        ids.extend(line.split("#", 1)[0].strip() for line in args.lista.read_text(encoding="utf-8-sig").splitlines())
    ids = list(dict.fromkeys(q.strip().upper() for q in ids if q.strip())) if args.ids or args.lista else list(INICIAIS)
    if not ids or any(not re.fullmatch(r"Q[1-9]\d*", q) for q in ids):
        ap.error("Informe QIDs validos do Wikidata, por exemplo --ids Q12897 Q47526")
    if args.limite:
        ids = ids[:args.limite]
    existing = ler_json(args.saida, {"rows": {}})
    if not isinstance(existing, dict) or not isinstance(existing.get("rows"), dict):
        raise ValueError("A saida existente nao tem um objeto rows valido; ela foi preservada.")
    rows = existing["rows"]
    pending = [q for q in ids if args.atualizar or q not in rows or rows[q].get("coletaIncompleta")]
    api = Api(args.cache, args.atualizar, args.offline)
    inicio = time.monotonic()
    print(f"Selecionados: {len(ids)} | retomados da saida: {len(ids)-len(pending)} | para coletar: {len(pending)}", flush=True)
    interrupted = False
    try:
        entities = api.entidades(pending)
        linked = set()
        for entity in entities.values():
            linked.update(ids_relacionados(entity))
        labels = api.entidades(sorted(linked), completas=False)
        images = [v for e in entities.values() for v in valores(e, "P18")[:1] if isinstance(v, str)]
        photos = ler_json(args.cache / "fotos.json", {}) if args.sem_fotos else api.fotos(images)
        for qid, entity in entities.items():
            record = montar(entity, labels, photos)
            if not valores(entity, "P54") or not valores(entity, "P413"):
                # Entidades que nao parecem perfis de atleta nao entram na base.
                api.falhas.append({"id": qid, "erro": "Perfil sem equipe ou posicao; registro anterior preservado"})
                continue
            record["coletaIncompleta"] = any(q not in labels for q in ids_relacionados(entity)) or (
                not args.sem_fotos and record["arquivoFoto"] is not None and record["foto"] is None)
            old = rows.get(qid)
            if old and record["coletaIncompleta"]:
                api.falhas.append({"id": qid, "erro": "Atualizacao incompleta; registro anterior preservado"})
                continue
            rows[qid] = record
            print(f"  {record['nome']}: {len(record['passagens'])} passagens | foto {'sim' if record['foto'] else 'pendente/ausente'} | revisao numerica pendente", flush=True)
    except KeyboardInterrupt:
        interrupted = True
        print("\nInterrompido. Registros existentes preservados; respostas ja recebidas estao no cache.")
    finally:
        api.session.close()
    dados = {"v": 1, "gerado": agora(), "fonte": "Wikidata / Wikimedia Commons", "licencaDados": "CC0",
             "nota": "Coleta para revisao. Nao inferir titulos nem totais completos a partir de dados ausentes.", "rows": rows}
    faltantes = [q for q in ids if q not in rows or rows[q].get("coletaIncompleta")]
    report = {"gerado": dados["gerado"], "selecionados": len(ids), "registrosSalvos": len(rows),
              "pendentesColeta": faltantes, "revisaoPendente": [q for q in ids if rows.get(q, {}).get("revisaoPendente")],
              "falhas": api.falhas, "requisicoes": api.requisicoes,
              "segundos": round(time.monotonic() - inicio, 2), "interrompido": interrupted}
    # Nao substitui uma base existente se nenhuma coleta valida foi produzida.
    if rows or not args.saida.exists():
        salvar_json(args.saida, dados)
        salvar_json(args.saida.with_suffix(".js"), dados, "window.GEMEOS_DATA=")
    salvar_json(args.saida.with_name(args.saida.stem + "_relatorio.json"), report)
    print(f"\nSalvos: {len(rows)} | pendentes de coleta: {len(faltantes)} | {api.requisicoes} requisicoes | {report['segundos']}s")
    print(f"Saida: {args.saida}\nO jogo ainda nao carrega esta base automaticamente.")
    return 130 if interrupted else 1 if faltantes or api.falhas else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        sys.exit(1)
